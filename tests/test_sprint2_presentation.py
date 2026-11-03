from __future__ import annotations

import json

import pytest

from app.config import load_product_config
from app.extensions import db
from app.models import Department, Task, UserPreference
from tests.factories import add_membership, make_department, make_user


def login(client, username="ava"):
    return client.post(
        "/auth/login", data={"username": username, "password": "correct horse battery staple"}
    )


def test_product_config_is_required_and_validated(tmp_path):
    with pytest.raises(RuntimeError, match="Unable to load"):
        load_product_config(tmp_path / "missing.json")
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps({"app_name": "Only a name"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="must define"):
        load_product_config(invalid)


def test_header_about_features_and_home_route(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        db.session.commit()
    response = login(client)
    assert response.location.endswith("/tasks")
    with app.app_context():
        department_id = db.session.scalar(db.select(Department.id))
    client.post(f"/departments/{department_id}/switch")
    assert client.get("/").location.endswith("/tasks")
    task_page = client.get("/tasks")
    assert b"Zentra Task Hub" in task_page.data and b"v0.1.1" in task_page.data
    assert b"Departments</a>" not in task_page.data and b"Features</a>" in task_page.data
    about = client.get("/about")
    assert b"Build" in about.data and b"+20261102.0001" in about.data
    assert b"Department-scoped task lists" in client.get("/features").data


def test_search_result_opens_scoped_detail(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        task = Task(department=department, title="Searchable task", assignee=user, created_by=user)
        db.session.add(task)
        db.session.commit()
        department_id, task_id = department.id, task.id
    login(client)
    client.post(f"/departments/{department_id}/switch")
    search_page = client.get("/tasks/search?q=Searchable")
    assert f"/tasks?selected={task_id}".encode() in search_page.data
    assert b"q=Searchable" in search_page.data
    detail = client.get(f"/tasks?selected={task_id}")
    assert b"<h3>Searchable task</h3>" in detail.data
    assert b"Work-package associations are not available" in detail.data
    assert client.get("/tasks?sort=invalid").status_code == 400


def test_grid_widths_persist_and_validate(client, app):
    with app.app_context():
        user = make_user()
        department = make_department()
        add_membership(user, department)
        db.session.commit()
        user_id, department_id = user.id, department.id
    login(client)
    client.post(f"/departments/{department_id}/switch")
    assert (
        client.post(
            "/preferences/grid-widths/task", data={"column": "task", "width": "310"}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/preferences/grid-widths/task", data={"column": "unknown", "width": "310"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/preferences/grid-widths/task", data={"column": "task", "width": "900"}
        ).status_code
        == 400
    )
    with app.app_context():
        preference = db.session.get(UserPreference, user_id)
        assert preference.grid_widths["task"]["task"] == 310
    assert b'value="310"' in client.get("/preferences").data
    client.post(
        "/preferences",
        data={"task_list_filter": "self", "work_package_list_filter": "all"},
    )
    with app.app_context():
        assert db.session.get(UserPreference, user_id).grid_widths["task"]["task"] == 310
    restored = client.post(
        "/preferences",
        data={
            "task_list_filter": "all",
            "work_package_list_filter": "all",
            "restore_grid_defaults": "1",
        },
    )
    assert restored.status_code == 302
    with app.app_context():
        assert db.session.get(UserPreference, user_id).grid_widths == {}


def test_detail_lookup_does_not_cross_department(client, app):
    with app.app_context():
        user = make_user()
        own, outside = make_department("Own"), make_department("Outside")
        add_membership(user, own)
        outside_task = Task(department=outside, title="Secret", assignee=user, created_by=user)
        db.session.add(outside_task)
        db.session.commit()
        own_id, outside_id = own.id, outside_task.id
    login(client)
    client.post(f"/departments/{own_id}/switch")
    response = client.get(f"/tasks?selected={outside_id}")
    assert b"Secret" not in response.data and b"Task details" not in response.data
