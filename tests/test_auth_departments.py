from __future__ import annotations

import re

from app.extensions import db
from app.models import DepartmentMembership, User, UserPreference
from tests.factories import add_membership, make_department, make_master_admin, make_user


def login(client, username="ava", password="correct horse battery staple"):
    return client.post(
        "/auth/login", data={"username": username, "password": password}, follow_redirects=True
    )


def test_login_and_logout(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        db.session.commit()

    response = login(client)
    assert response.status_code == 200
    assert b"Departments" in response.data

    response = client.post("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in to Zentra" in response.data


def test_bad_or_inactive_login_is_generic(client, app):
    with app.app_context():
        make_user(active=False)
        db.session.commit()

    response = client.post("/auth/login", data={"username": "ava", "password": "wrong"})
    assert response.status_code == 401
    assert b"The username or password is incorrect." in response.data
    assert b"inactive" not in response.data.lower()


def test_user_can_switch_only_to_active_memberships(client, app):
    with app.app_context():
        user = make_user()
        allowed = make_department("Operations")
        second_allowed = make_department("People")
        denied = make_department("Finance")
        add_membership(user, allowed)
        add_membership(user, second_allowed)
        db.session.commit()
        allowed_id, second_allowed_id, denied_id = allowed.id, second_allowed.id, denied.id

    login(client)
    response = client.post(f"/departments/{allowed_id}/switch", follow_redirects=True)
    assert response.status_code == 200
    assert b"Tasks" in response.data and b"Operations" in response.data
    response = client.post(f"/departments/{second_allowed_id}/switch", follow_redirects=True)
    assert response.status_code == 200
    assert b"Tasks" in response.data and b"People" in response.data

    assert client.post(f"/departments/{denied_id}/switch").status_code == 404

    client.post("/auth/logout")
    response = login(client)
    assert b"Tasks" in response.data and b"People" in response.data


def test_master_admin_can_switch_to_any_active_department(client, app):
    with app.app_context():
        make_master_admin()
        department = make_department("Research")
        db.session.commit()
        department_id = department.id

    login(client, username="root")
    response = client.post(f"/departments/{department_id}/switch", follow_redirects=True)
    assert response.status_code == 200
    assert b"Tasks" in response.data and b"Research" in response.data


def test_membership_revocation_invalidates_active_department(client, app):
    with app.app_context():
        user = make_user()
        first = make_department("Operations")
        second = make_department("People")
        membership = add_membership(user, first)
        add_membership(user, second)
        db.session.commit()
        first_id = first.id
        membership_id = membership.id

    login(client)
    client.post(f"/departments/{first_id}/switch")
    with app.app_context():
        db.session.get(DepartmentMembership, membership_id).is_active = False
        db.session.commit()

    response = client.get("/departments", follow_redirects=True)
    assert response.status_code == 200
    assert b"People" in response.data
    assert b"Current department:" not in response.data
    assert client.post(f"/departments/{first_id}/switch").status_code == 404


def test_stale_last_department_is_cleared_on_login(client, app):
    with app.app_context():
        user = make_user()
        permitted = make_department("Operations")
        stale = make_department("Closed")
        add_membership(user, permitted)
        preference = db.session.get(UserPreference, user.id)
        preference.last_department_id = stale.id
        db.session.commit()
        user_id = user.id

    response = login(client)
    assert response.status_code == 200
    assert b"Current department:" not in response.data
    with app.app_context():
        assert db.session.get(UserPreference, user_id).last_department_id is None


def test_inactive_membership_is_not_shown_or_switchable(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department, active=False)
        db.session.commit()
        department_id = department.id

    login(client)
    response = client.get("/departments")
    assert b"Operations" not in response.data
    assert client.post(f"/departments/{department_id}/switch").status_code == 404


def test_password_hash_is_not_plaintext(app):
    with app.app_context():
        user = make_user()
        assert user.password_hash != "correct horse battery staple"
        assert user.check_password("correct horse battery staple")
        assert not user.check_password("wrong")


def test_login_form_has_csrf_token(app):
    app.config["WTF_CSRF_ENABLED"] = True
    response = app.test_client().get("/auth/login")
    token = re.search(rb'name="csrf_token" value="[^"]+"', response.data)
    assert token
    denied = app.test_client().post(
        "/auth/login", data={"username": "nobody", "password": "irrelevant"}
    )
    assert denied.status_code == 400


def test_login_discards_pre_authentication_session_state(client, app):
    with app.app_context():
        make_user()
        db.session.commit()

    with client.session_transaction() as browser_session:
        browser_session["untrusted_marker"] = "keep-me-out"
        browser_session["active_department_id"] = 999

    login(client)
    with client.session_transaction() as browser_session:
        assert "untrusted_marker" not in browser_session
        assert "active_department_id" not in browser_session
        assert "_user_id" in browser_session


def test_master_admin_bootstrap_prompts_and_creates_no_default_password(app):
    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["create-master-admin"],
        input="firstadmin\nFirst Admin\nlong-training-password\nlong-training-password\n",
    )
    assert result.exit_code == 0, result.output
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == "firstadmin"))
        assert user is not None
        assert user.is_master_admin
        assert user.check_password("long-training-password")
