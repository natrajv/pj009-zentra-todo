from __future__ import annotations

from app.extensions import db
from app.models import AuditEvent, Department, Task, User
from app.permissions import can_update_task
from tests.factories import add_membership, make_department, make_user


def login(client, username):
    return client.post(
        "/auth/login",
        data={"username": username, "password": "correct horse battery staple"},
    )


def test_member_can_create_task_only_for_self_even_with_forged_assignee(client, app):
    with app.app_context():
        member = make_user("member")
        other = make_user("other")
        department = make_department()
        add_membership(member, department)
        add_membership(other, department)
        db.session.commit()
        department_id, other_id, member_id = department.id, other.id, member.id

    login(client, "member")
    client.post(f"/departments/{department_id}/switch")
    response = client.post(
        "/tasks/new",
        data={
            "title": "Prepare the weekly report",
            "description": "Gather updates",
            "priority": "high",
            "assignee_user_id": str(other_id),
        },
    )
    assert response.status_code == 302
    with app.app_context():
        task = db.session.scalar(db.select(Task).where(Task.title == "Prepare the weekly report"))
        assert task is not None
        assert task.assignee_user_id == member_id
        assert task.department_id == department_id
        assert db.session.scalar(
            db.select(AuditEvent).where(AuditEvent.action == "task.create")
        )


def test_department_admin_can_assign_and_user_can_update_only_own_task(app):
    with app.app_context():
        admin = make_user("lead")
        member = make_user("member")
        other = make_user("other")
        department = make_department()
        add_membership(admin, department, role="department_admin")
        add_membership(member, department)
        add_membership(other, department)
        db.session.commit()
        department_id, member_id, other_id = department.id, member.id, other.id

    admin_client = app.test_client()
    login(admin_client, "lead")
    admin_client.post(f"/departments/{department_id}/switch")
    profile_response = admin_client.get("/tasks")
    assert b"Account menu for lead" in profile_response.data
    assert b"Department Admin" in profile_response.data
    assert b"Operations" in profile_response.data
    assert b"user-menu-panel" in profile_response.data
    assert b"/auth/logout" in profile_response.data
    admin_client.post(
        "/tasks/new",
        data={
            "title": "Assigned to member",
            "priority": "normal",
            "assignee_user_id": str(member_id),
        },
    )
    admin_client.post(
        "/tasks/new",
        data={
            "title": "Assigned to other",
            "priority": "normal",
            "assignee_user_id": str(other_id),
        },
    )
    with app.app_context():
        member_task_id = db.session.scalar(
            db.select(Task.id).where(Task.title == "Assigned to member")
        )
        other_task_id = db.session.scalar(
            db.select(Task.id).where(Task.title == "Assigned to other")
        )
        member_user = db.session.scalar(db.select(User).where(User.username == "member"))
        department = db.session.get(Department, department_id)
        other_task = db.session.get(Task, other_task_id)
        assert other_task.assignee_user_id == other_id
        assert not can_update_task(member_user, department, other_task.assignee_user_id)

    admin_client.post("/auth/logout")
    member_login = login(admin_client, "member")
    assert member_login.status_code == 302 and member_login.location.endswith("/tasks")
    switch_response = admin_client.post(f"/departments/{department_id}/switch")
    assert switch_response.location.endswith("/tasks")
    own_update = admin_client.post(
        f"/tasks/{member_task_id}/status", data={"status": "in_progress"}
    )
    assert own_update.status_code == 302 and "/tasks?selected=" in own_update.location
    other_update = admin_client.post(
        f"/tasks/{other_task_id}/status", data={"status": "completed"}
    )
    assert other_update.status_code == 404, (other_update.status_code, other_update.location)
    member_delete = admin_client.post(f"/tasks/{member_task_id}/delete")
    assert member_delete.status_code == 404
    with app.app_context():
        assert db.session.get(Task, member_task_id).status == "in_progress"
        assert db.session.get(Task, other_task_id).status == "open"


def test_task_list_search_and_self_filter_are_department_scoped(client, app):
    with app.app_context():
        member = make_user("member")
        other = make_user("other")
        department = make_department("Operations")
        outside_department = make_department("Finance")
        add_membership(member, department)
        add_membership(other, department)
        db.session.add_all(
            [
                Task(
                    department_id=department.id,
                    title="My weekly report",
                    assignee_user_id=member.id,
                    created_by_user_id=member.id,
                ),
                Task(
                    department_id=department.id,
                    title="Other review",
                    assignee_user_id=other.id,
                    created_by_user_id=other.id,
                ),
                Task(
                    department_id=outside_department.id,
                    title="Secret finance task",
                    assignee_user_id=other.id,
                    created_by_user_id=other.id,
                ),
            ]
        )
        db.session.commit()
        department_id = department.id
        own_task_id = db.session.scalar(
            db.select(Task.id).where(Task.title == "My weekly report")
        )

    login(client, "member")
    client.post(f"/departments/{department_id}/switch")
    response = client.get("/tasks?q=weekly")
    assert b"My weekly report" in response.data
    assert b"Secret finance task" not in response.data
    selected_response = client.get(f"/tasks?selected={own_task_id}&q=weekly")
    assert b"<h3>My weekly report</h3>" in selected_response.data
    assert b"task-table" in selected_response.data
    assert b"<dialog class=\"task-dialog\" open" in selected_response.data
    search_page = client.get("/tasks/search?q=Secret")
    assert b"Secret finance task" not in search_page.data
    client.post("/tasks/filter", data={"task_list_filter": "self"})
    response = client.get("/tasks")
    assert b"My weekly report" in response.data
    assert b"Other review" not in response.data


def test_task_status_cannot_be_changed_outside_active_department(client, app):
    with app.app_context():
        user = make_user("member")
        own_department = make_department("Operations")
        other_department = make_department("Finance")
        add_membership(user, own_department)
        task = Task(
            department=other_department,
            title="Scoped task",
            assignee=user,
            created_by=user,
        )
        db.session.add(task)
        db.session.commit()
        own_department_id, task_id = own_department.id, task.id

    login(client, "member")
    client.post(f"/departments/{own_department_id}/switch")
    response = client.post(f"/tasks/{task_id}/status", data={"status": "completed"})
    assert response.status_code == 404


def test_task_detail_is_readonly_until_update_is_selected(client, app):
    with app.app_context():
        user = make_user("member")
        department = make_department()
        add_membership(user, department)
        task = Task(
            department=department,
            title="Review proposal",
            assignee=user,
            created_by=user,
        )
        db.session.add(task)
        db.session.commit()
        department_id, task_id = department.id, task.id

    login(client, "member")
    client.post(f"/departments/{department_id}/switch")
    response = client.get(f"/tasks?selected={task_id}")
    assert response.status_code == 200
    assert b'<form id="task-edit-form"' in response.data
    assert b"hidden>" in response.data
    assert b"Update</a>" in response.data
    assert b"Delete task" not in response.data
    assert b"Enter a task" not in response.data


def test_create_task_dialog_and_workspace_navigation(client, app):
    with app.app_context():
        user = make_user("member")
        department = make_department()
        add_membership(user, department)
        db.session.commit()
        department_id = department.id
    login(client, "member")
    client.post(f"/departments/{department_id}/switch")

    create_response = client.get("/tasks?mode=create")
    assert create_response.status_code == 200
    assert b"Create Task" in create_response.data
    assert b"/tasks/new" in create_response.data
    assert b"Work Package" in create_response.data
    assert b"Search" in create_response.data

    package_response = client.get("/tasks/work-packages")
    assert package_response.status_code == 200
    assert b"Department Work Packages" in package_response.data

    search_response = client.get("/tasks/search?q=report")
    assert search_response.status_code == 200
    assert b"Search grid" in search_response.data
    assert b"Task results" in search_response.data


def test_user_can_edit_own_task_from_detail_editor(client, app):
    with app.app_context():
        user = make_user("member")
        department = make_department()
        add_membership(user, department)
        task = Task(
            department=department,
            title="Original title",
            description="Original description",
            assignee=user,
            created_by=user,
        )
        db.session.add(task)
        db.session.commit()
        department_id, task_id = department.id, task.id

    login(client, "member")
    client.post(f"/departments/{department_id}/switch")
    response = client.post(
        f"/tasks/{task_id}/update",
        data={
            "title": "Updated title",
            "description": "Updated details",
            "status": "completed",
            "priority": "high",
            "due_date": "2030-05-10",
        },
    )
    assert response.status_code == 302
    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.title == "Updated title"
        assert task.description == "Updated details"
        assert task.status == "completed"
        assert task.priority == "high"
        assert task.due_date.isoformat() == "2030-05-10"


def test_task_delete_removes_record_and_retains_audit_event(client, app):
    with app.app_context():
        user = make_user("lead")
        department = make_department()
        add_membership(user, department, role="department_admin")
        task = Task(
            department=department,
            title="Task to delete",
            assignee=user,
            created_by=user,
        )
        db.session.add(task)
        db.session.commit()
        department_id, task_id, task_public_id = department.id, task.id, task.public_id

    login(client, "lead")
    client.post(f"/departments/{department_id}/switch")
    response = client.post(f"/tasks/{task_id}/delete", data={"q": "Task to delete"})
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Task, task_id) is None
        deletion = db.session.scalar(
            db.select(AuditEvent).where(
                AuditEvent.action == "task.delete",
                AuditEvent.target_public_id == task_public_id,
            )
        )
        assert deletion is not None


def test_task_grid_pagination_has_navigation(client, app):
    with app.app_context():
        user = make_user("member")
        department = make_department()
        add_membership(user, department)
        db.session.add_all(
            [
                Task(
                    department=department,
                    title=f"Task {number:02d}",
                    assignee=user,
                    created_by=user,
                )
                for number in range(51)
            ]
        )
        db.session.commit()
        department_id = department.id

    login(client, "member")
    client.post(f"/departments/{department_id}/switch")
    first_page = client.get("/tasks")
    assert b"Page 1 of 2" in first_page.data
    assert b">Next</a>" in first_page.data
    second_page = client.get("/tasks?page=2")
    assert b"Page 2 of 2" in second_page.data
    assert b">Previous</a>" in second_page.data
