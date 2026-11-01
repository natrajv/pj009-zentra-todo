from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import AuditEvent, Department, DepartmentMembership, User
from . import bp

MEMBERSHIP_ROLES = {"user", "department_admin"}


def _require_master_admin() -> None:
    if not current_user.is_master_admin:
        abort(404)


def _audit(action: str, target_type: str, target_public_id: str, department_id: int | None = None):
    db.session.add(
        AuditEvent(
            actor_user_id=current_user.id,
            action=action,
            target_type=target_type,
            target_public_id=target_public_id,
            department_id=department_id,
        )
    )


@bp.get("/identity")
@login_required
def identity():
    _require_master_admin()
    users = db.session.scalars(select(User).order_by(User.username)).all()
    departments = db.session.scalars(select(Department).order_by(Department.name)).all()
    memberships = db.session.scalars(
        select(DepartmentMembership)
        .join(DepartmentMembership.user)
        .join(DepartmentMembership.department)
        .order_by(User.username, Department.name)
    ).all()
    return render_template(
        "admin/identity.html", users=users, departments=departments, memberships=memberships
    )


@bp.post("/departments")
@login_required
def create_department():
    _require_master_admin()
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip() or None
    if not name or len(name) > 120 or (description and len(description) > 2000):
        flash("Enter a department name and a description within the allowed lengths.", "error")
        return redirect(url_for("admin.identity")), 400

    department = Department(name=name, description=description)
    db.session.add(department)
    try:
        db.session.flush()
        _audit("department.create", "department", department.public_id, department.id)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("A department with that name already exists.", "error")
        return redirect(url_for("admin.identity")), 409

    flash("Department created.", "success")
    return redirect(url_for("admin.identity"))


@bp.post("/users")
@login_required
def create_user():
    _require_master_admin()
    username = request.form.get("username", "").strip().lower()
    display_name = request.form.get("display_name", "").strip()
    password = request.form.get("password", "")
    department_id = request.form.get("department_id", type=int)
    role = request.form.get("role", "user")

    if (
        not username
        or len(username) > 80
        or not display_name
        or len(display_name) > 120
        or len(password) < 12
        or role not in MEMBERSHIP_ROLES
        or department_id is None
    ):
        flash(
            "Provide valid account details, a department, and a password of at least "
            "12 characters.",
            "error",
        )
        return redirect(url_for("admin.identity")), 400

    department = db.session.get(Department, department_id)
    if department is None or not department.is_active:
        abort(404)

    user = User(username=username, display_name=display_name)
    user.set_password(password)
    membership = DepartmentMembership(department=department, role=role)
    user.memberships.append(membership)
    db.session.add(user)
    try:
        db.session.flush()
        _audit("user.create", "user", user.public_id, department.id)
        _audit("membership.create", "user", user.public_id, department.id)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("An account with that username already exists.", "error")
        return redirect(url_for("admin.identity")), 409

    flash("User account and department membership created.", "success")
    return redirect(url_for("admin.identity"))


@bp.post("/memberships")
@login_required
def assign_membership():
    _require_master_admin()
    user_id = request.form.get("user_id", type=int)
    department_id = request.form.get("department_id", type=int)
    role = request.form.get("role", "user")
    if user_id is None or department_id is None or role not in MEMBERSHIP_ROLES:
        flash("Choose a user, active department, and valid department role.", "error")
        return redirect(url_for("admin.identity")), 400

    user = db.session.get(User, user_id)
    department = db.session.get(Department, department_id)
    if user is None or not user.is_active or department is None or not department.is_active:
        abort(404)

    membership = db.session.scalar(
        select(DepartmentMembership).where(
            DepartmentMembership.user_id == user.id,
            DepartmentMembership.department_id == department.id,
        )
    )
    if membership is None:
        membership = DepartmentMembership(user=user, department=department, role=role)
        db.session.add(membership)
        action = "membership.create"
    elif membership.is_active:
        flash("That user already has an active membership in this department.", "error")
        return redirect(url_for("admin.identity")), 409
    else:
        membership.is_active = True
        membership.role = role
        action = "membership.reactivate"

    _audit(action, "user", user.public_id, department.id)
    db.session.commit()
    flash("Department membership saved.", "success")
    return redirect(url_for("admin.identity"))
