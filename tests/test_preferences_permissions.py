from __future__ import annotations

from app.extensions import db
from app.models import UserPreference
from app.permissions import can_access_department, can_manage_department, can_update_task
from tests.factories import add_membership, make_department, make_master_admin, make_user


def test_list_preferences_persist_per_user(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        db.session.commit()
        user_id = user.id

    client.post(
        "/auth/login", data={"username": "ava", "password": "correct horse battery staple"}
    )
    response = client.post(
        "/preferences",
        data={"task_list_filter": "self", "work_package_list_filter": "all"},
    )
    assert response.status_code == 302
    client.post("/auth/logout")
    client.post(
        "/auth/login", data={"username": "ava", "password": "correct horse battery staple"}
    )
    with app.app_context():
        preference = db.session.get(UserPreference, user_id)
        assert preference.task_list_filter == "self"
        assert preference.work_package_list_filter == "all"


def test_filter_values_are_validated(client, app):
    with app.app_context():
        make_user()
        db.session.commit()
    client.post(
        "/auth/login", data={"username": "ava", "password": "correct horse battery staple"}
    )
    response = client.post(
        "/preferences", data={"task_list_filter": "admin", "work_package_list_filter": "all"}
    )
    assert response.status_code == 400


def test_department_roles_and_task_update_policy(app):
    with app.app_context():
        department = make_department()
        user = make_user("member")
        another = make_user("other")
        admin = make_user("lead")
        add_membership(user, department, role="user")
        add_membership(admin, department, role="department_admin")
        master = make_master_admin()
        db.session.commit()

        assert can_access_department(user, department)
        assert not can_manage_department(user, department)
        assert can_update_task(user, department, user.id)
        assert not can_update_task(user, department, another.id)
        assert can_manage_department(admin, department)
        assert can_update_task(admin, department, another.id)
        assert can_update_task(master, department, another.id)

        outside = make_department("Outside")
        db.session.commit()
        assert not can_access_department(user, outside)
        assert not can_update_task(user, outside, user.id)
