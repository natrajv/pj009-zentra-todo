from __future__ import annotations

from app.extensions import db
from app.models import AuditEvent, Department, DepartmentMembership, User
from tests.factories import add_membership, make_department, make_master_admin, make_user


def login(client, username, password="correct horse battery staple"):
    return client.post("/auth/login", data={"username": username, "password": password})


def test_master_admin_can_create_department_and_user_with_membership(client, app):
    with app.app_context():
        make_master_admin()
        db.session.commit()

    login(client, "root")
    response = client.get("/departments", follow_redirects=True)
    assert b"Set up departments and users" in response.data

    response = client.post("/admin/departments", data={"name": "Operations"})
    assert response.status_code == 302

    with app.app_context():
        department = db.session.scalar(db.select(Department).where(Department.name == "Operations"))
        department_id = department.id
        assert db.session.scalar(
            db.select(AuditEvent).where(AuditEvent.action == "department.create")
        )

    response = client.post(
        "/admin/users",
        data={
            "username": "Priya",
            "display_name": "Priya Shah",
            "password": "initial-strong-password",
            "department_id": str(department_id),
            "role": "department_admin",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "priya"))
        assert user is not None
        assert user.password_hash != "initial-strong-password"
        assert user.check_password("initial-strong-password")
        membership = db.session.scalar(
            db.select(DepartmentMembership).where(
                DepartmentMembership.user_id == user.id,
                DepartmentMembership.department_id == department_id,
            )
        )
        assert membership is not None
        assert membership.role == "department_admin"
        assert db.session.scalar(
            db.select(AuditEvent).where(AuditEvent.action == "user.create")
        )


def test_master_admin_can_add_user_to_second_department(client, app):
    with app.app_context():
        make_master_admin()
        user = make_user("member")
        first = make_department("Operations")
        second = make_department("People")
        add_membership(user, first)
        db.session.commit()
        user_id, department_id = user.id, second.id

    login(client, "root")
    response = client.post(
        "/admin/memberships",
        data={"user_id": str(user_id), "department_id": str(department_id), "role": "user"},
    )
    assert response.status_code == 302
    with app.app_context():
        membership = db.session.scalar(
            db.select(DepartmentMembership).where(
                DepartmentMembership.user_id == user_id,
                DepartmentMembership.department_id == department_id,
            )
        )
        assert membership is not None and membership.is_active


def test_non_master_admin_cannot_open_or_post_admin_routes(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        db.session.commit()

    login(client, "ava")
    assert client.get("/admin/identity").status_code == 404
    assert client.post("/admin/departments", data={"name": "Forbidden"}).status_code == 404
    with app.app_context():
        assert db.session.scalar(
            db.select(Department).where(Department.name == "Forbidden")
        ) is None


def test_admin_rejects_weak_password_and_invalid_role(client, app):
    with app.app_context():
        make_master_admin()
        department = make_department()
        db.session.commit()
        department_id = department.id

    login(client, "root")
    weak = client.post(
        "/admin/users",
        data={
            "username": "weak",
            "display_name": "Weak User",
            "password": "short",
            "department_id": str(department_id),
            "role": "user",
        },
    )
    invalid_role = client.post(
        "/admin/users",
        data={
            "username": "invalid",
            "display_name": "Invalid User",
            "password": "a-long-enough-password",
            "department_id": str(department_id),
            "role": "master_admin",
        },
    )
    assert weak.status_code == 400
    assert invalid_role.status_code == 400
    with app.app_context():
        assert db.session.scalar(db.select(User).where(User.username == "weak")) is None
        assert db.session.scalar(db.select(User).where(User.username == "invalid")) is None
