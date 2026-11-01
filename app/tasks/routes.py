from __future__ import annotations

from datetime import date

from flask import abort, flash, g, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import String, cast, func, or_, select

from ..extensions import db
from ..models import AuditEvent, DepartmentMembership, Task, User, UserPreference
from ..permissions import can_access_department, can_manage_department, can_update_task
from . import bp

TASK_STATUSES = {"open", "in_progress", "completed"}
TASK_PRIORITIES = {"low", "normal", "high", "urgent"}
PAGE_SIZE = 50


def _require_active_department():
    if g.active_department is None:
        flash("Choose an active department before opening tasks.", "info")
        return redirect(url_for("departments.index"))
    return None


def _active_department_users(department_id: int) -> list[User]:
    return db.session.scalars(
        select(User)
        .join(DepartmentMembership)
        .where(
            DepartmentMembership.department_id == department_id,
            DepartmentMembership.is_active.is_(True),
            User.is_active.is_(True),
        )
        .order_by(User.display_name, User.username)
    ).all()


@bp.get("")
@login_required
def index():
    no_department = _require_active_department()
    if no_department:
        return no_department

    preference = db.session.get(UserPreference, current_user.id)
    selected_filter = preference.task_list_filter if preference else "all"
    search = request.args.get("q", "").strip()[:120]
    page = max(request.args.get("page", 1, type=int), 1)

    conditions = [
        Task.department_id == g.active_department.id,
        Task.is_archived.is_(False),
    ]
    if selected_filter == "self":
        conditions.append(Task.assignee_user_id == current_user.id)
    if search:
        pattern = f"%{search}%"
        conditions.append(
            or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
        )

    total = db.session.scalar(select(func.count(Task.id)).where(*conditions)) or 0
    page_count = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = min(page, page_count)
    tasks = db.session.scalars(
        select(Task)
        .where(*conditions)
        .order_by(Task.due_date.is_(None), Task.due_date, Task.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    ).all()
    selected_id = request.args.get("selected", type=int)
    selected_task = next((task for task in tasks if task.id == selected_id), None)
    mode = request.args.get("mode", "view")
    can_assign = can_manage_department(current_user, g.active_department)
    assignees = _active_department_users(g.active_department.id) if can_assign else []
    editable_task_ids = {
        task.id
        for task in tasks
        if can_update_task(current_user, g.active_department, task.assignee_user_id)
    }
    deletable_task_ids = {
        task.id for task in tasks if can_manage_department(current_user, g.active_department)
    }
    return render_template(
        "tasks/index.html",
        tasks=tasks,
        search=search,
        selected_filter=selected_filter,
        page=page,
        page_size=PAGE_SIZE,
        total=total,
        can_assign=can_assign,
        assignees=assignees,
        statuses=sorted(TASK_STATUSES),
        priorities=["low", "normal", "high", "urgent"],
        editable_task_ids=editable_task_ids,
        deletable_task_ids=deletable_task_ids,
        selected_task=selected_task,
        mode=mode,
        page_count=page_count,
        page_numbers=range(max(1, page - 2), min(page_count, page + 2) + 1),
    )


@bp.get("/work-packages")
@login_required
def work_packages():
    no_department = _require_active_department()
    if no_department:
        return no_department
    # Work packages are a later data-model phase; keep the workspace navigable
    # without fabricating rows or implying CRUD support that does not exist.
    return render_template("tasks/work_packages.html")


@bp.get("/search")
@login_required
def search():
    no_department = _require_active_department()
    if no_department:
        return no_department
    search_text = request.args.get("q", "").strip()[:120]
    page = max(request.args.get("page", 1, type=int), 1)
    conditions = [Task.department_id == g.active_department.id, Task.is_archived.is_(False)]
    if search_text:
        pattern = f"%{search_text}%"
        conditions.append(
            or_(
                Task.title.ilike(pattern), Task.description.ilike(pattern),
                Task.status.ilike(pattern), Task.priority.ilike(pattern),
                cast(Task.due_date, String).ilike(pattern),
                Task.assignee.has(User.display_name.ilike(pattern)),
                Task.created_by.has(User.display_name.ilike(pattern)),
            )
        )
    total = db.session.scalar(select(func.count(Task.id)).where(*conditions)) or 0
    page_count = max((total + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = min(page, page_count)
    tasks = db.session.scalars(
        select(Task).where(*conditions).order_by(Task.created_at.desc())
        .offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    ).all()
    return render_template(
        "tasks/search.html", tasks=tasks, search=search_text, total=total, page=page,
        page_count=page_count, page_numbers=range(max(1, page - 2), min(page_count, page + 2) + 1),
    )


@bp.post("/new")
@login_required
def create():
    no_department = _require_active_department()
    if no_department:
        return no_department

    department = g.active_department
    if not can_access_department(current_user, department):
        abort(404)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    priority = request.form.get("priority", "normal")
    due_date_value = request.form.get("due_date", "").strip()
    if not title or len(title) > 200 or (description and len(description) > 4000):
        flash("Enter a task title and keep the description within 4,000 characters.", "error")
        return redirect(url_for("tasks.index", mode="create")), 400
    if priority not in TASK_PRIORITIES:
        flash("Choose a valid task priority.", "error")
        return redirect(url_for("tasks.index", mode="create")), 400
    try:
        due_date = date.fromisoformat(due_date_value) if due_date_value else None
    except ValueError:
        flash("Enter a valid due date.", "error")
        return redirect(url_for("tasks.index", mode="create")), 400

    if can_manage_department(current_user, department):
        assignee_id = request.form.get("assignee_user_id", type=int)
        active_assignee_ids = {user.id for user in _active_department_users(department.id)}
        valid_assignee = assignee_id in active_assignee_ids
        if not valid_assignee:
            flash("Choose an active member of this department as the assignee.", "error")
            return redirect(url_for("tasks.index", mode="create")), 400
    else:
        # Ordinary users cannot choose another account as the task assignee.
        assignee_id = current_user.id

    task = Task(
        department_id=department.id,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        assignee_user_id=assignee_id,
        created_by_user_id=current_user.id,
    )
    db.session.add(task)
    db.session.flush()
    db.session.add(
        AuditEvent(
            actor_user_id=current_user.id,
            action="task.create",
            target_type="task",
            target_public_id=task.public_id,
            department_id=department.id,
        )
    )
    db.session.commit()
    flash("Task created.", "success")
    return redirect(url_for("tasks.index", selected=task.id))


@bp.get("/new")
@login_required
def new():
    no_department = _require_active_department()
    if no_department:
        return no_department
    if not can_access_department(current_user, g.active_department):
        abort(404)
    # Render the established task table behind a focused create dialog.
    return redirect(url_for("tasks.index", mode="create"))


@bp.post("/<int:task_id>/status")
@login_required
def update_status(task_id: int):
    no_department = _require_active_department()
    if no_department:
        return no_department

    task = db.session.get(Task, task_id)
    if (
        task is None
        or task.department_id != g.active_department.id
        or task.is_archived
    ):
        abort(404)
    if not can_update_task(current_user, g.active_department, task.assignee_user_id):
        abort(404)

    status = request.form.get("status", "")
    if status not in TASK_STATUSES:
        flash("Choose a valid task status.", "error")
        return redirect(url_for("tasks.index")), 400

    task.status = status
    db.session.add(
        AuditEvent(
            actor_user_id=current_user.id,
            action="task.status.update",
            target_type="task",
            target_public_id=task.public_id,
            department_id=task.department_id,
            details={"status": status},
        )
    )
    db.session.commit()
    flash("Task status updated.", "success")
    return redirect(
        url_for("tasks.index", selected=task.id, q=request.form.get("q", "").strip() or None)
    )


@bp.post("/<int:task_id>/update")
@login_required
def update(task_id: int):
    no_department = _require_active_department()
    if no_department:
        return no_department

    task = db.session.get(Task, task_id)
    if task is None or task.department_id != g.active_department.id or task.is_archived:
        abort(404)
    if not can_update_task(current_user, g.active_department, task.assignee_user_id):
        abort(404)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip() or None
    status = request.form.get("status", "")
    priority = request.form.get("priority", "")
    due_date_value = request.form.get("due_date", "").strip()
    if not title or len(title) > 200 or (description and len(description) > 4000):
        flash("Enter a task title and keep the description within 4,000 characters.", "error")
        return redirect(url_for("tasks.index", selected=task.id)), 400
    if status not in TASK_STATUSES or priority not in TASK_PRIORITIES:
        flash("Choose a valid task status and priority.", "error")
        return redirect(url_for("tasks.index", selected=task.id)), 400
    try:
        due_date = date.fromisoformat(due_date_value) if due_date_value else None
    except ValueError:
        flash("Enter a valid due date.", "error")
        return redirect(url_for("tasks.index", selected=task.id)), 400

    if can_manage_department(current_user, g.active_department):
        assignee_id = request.form.get("assignee_user_id", type=int)
        active_assignee_ids = {user.id for user in _active_department_users(g.active_department.id)}
        if assignee_id not in active_assignee_ids:
            flash("Choose an active member of this department as the assignee.", "error")
            return redirect(url_for("tasks.index", selected=task.id)), 400
        task.assignee_user_id = assignee_id

    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.due_date = due_date
    db.session.add(
        AuditEvent(
            actor_user_id=current_user.id,
            action="task.update",
            target_type="task",
            target_public_id=task.public_id,
            department_id=task.department_id,
            details={"fields": ["title", "description", "status", "priority", "due_date"]},
        )
    )
    db.session.commit()
    flash("Task updated.", "success")
    return redirect(
        url_for(
            "tasks.index",
            selected=task.id,
            q=request.form.get("q", "").strip() or None,
            page=request.form.get("page", 1, type=int),
        )
    )


@bp.post("/<int:task_id>/delete")
@login_required
def delete(task_id: int):
    no_department = _require_active_department()
    if no_department:
        return no_department

    task = db.session.get(Task, task_id)
    if task is None or task.department_id != g.active_department.id or task.is_archived:
        abort(404)
    if not can_manage_department(current_user, g.active_department):
        abort(404)

    db.session.add(
        AuditEvent(
            actor_user_id=current_user.id,
            action="task.delete",
            target_type="task",
            target_public_id=task.public_id,
            department_id=task.department_id,
            details={"title": task.title},
        )
    )
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect(url_for("tasks.index", q=request.form.get("q", "").strip() or None))


@bp.post("/filter")
@login_required
def save_filter():
    no_department = _require_active_department()
    if no_department:
        return no_department

    selected_filter = request.form.get("task_list_filter", "")
    if selected_filter not in {"all", "self"}:
        abort(400)
    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)
    preference.task_list_filter = selected_filter
    db.session.commit()
    return redirect(url_for("tasks.index", q=request.form.get("q", "").strip() or None))
