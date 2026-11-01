from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from flask import Flask, g, redirect, session, url_for
from flask_login import current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .config import Config
from .extensions import db, login_manager

csrf = CSRFProtect()
migrate = Migrate()


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if os.environ.get("APP_ENV", "development").lower() == "production":
        from .config import ProductionConfig

        app.config.from_object(ProductionConfig)
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = "test-only-secret-key"
        else:
            raise RuntimeError("Set SECRET_KEY in the environment before starting Zentra.")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    from . import models  # noqa: F401
    from .admin import bp as admin_bp
    from .auth import bp as auth_bp
    from .departments import bp as departments_bp
    from .main import bp as main_bp
    from .tasks import bp as tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(departments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tasks_bp)

    @app.get("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return redirect(url_for("tasks.index"))

    @app.before_request
    def refresh_department_context() -> None:
        g.active_department = None
        g.active_membership = None
        if not current_user.is_authenticated:
            session.pop("active_department_id", None)
            return

        from .models import Department, DepartmentMembership, UserPreference
        from .permissions import can_access_department

        department_id = session.get("active_department_id")
        if department_id is None:
            preference = db.session.get(UserPreference, current_user.id)
            department_id = preference.last_department_id if preference else None

        if department_id is None:
            return

        department = db.session.get(Department, department_id)
        if department is None or not department.is_active or not can_access_department(
            current_user, department
        ):
            session.pop("active_department_id", None)
            return

        membership = db.session.scalar(
            db.select(DepartmentMembership).where(
                DepartmentMembership.user_id == current_user.id,
                DepartmentMembership.department_id == department.id,
                DepartmentMembership.is_active.is_(True),
            )
        )
        g.active_department = department
        g.active_membership = membership
        session["active_department_id"] = department.id

    @app.cli.command("create-master-admin")
    def create_master_admin() -> None:
        """Interactively create a Master Admin; no default credentials are provided."""
        import click

        from .models import GlobalRole, User

        username = click.prompt("Username").strip().lower()
        display_name = click.prompt("Display name").strip()
        if not username or len(username) > 80 or not display_name or len(display_name) > 120:
            raise click.ClickException(
                "Provide a username and display name within the allowed length."
            )
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
        if len(password) < 12:
            raise click.ClickException("Password must be at least 12 characters.")
        if db.session.scalar(db.select(User).where(User.username == username)):
            raise click.ClickException("That username is already in use.")
        user = User(username=username, display_name=display_name)
        user.set_password(password)
        role = db.session.scalar(
            db.select(GlobalRole).where(GlobalRole.name == GlobalRole.MASTER_ADMIN)
        )
        if role is None:
            role = GlobalRole(name=GlobalRole.MASTER_ADMIN)
        user.global_roles.append(role)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Master Admin '{username}' created.")

    return app
