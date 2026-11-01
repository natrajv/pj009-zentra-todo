from __future__ import annotations

from datetime import UTC, datetime

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from ..extensions import db
from ..models import Department, User, UserPreference
from ..permissions import can_access_department
from . import bp


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = db.session.scalar(select(User).where(User.username == username))
        if user is None or not user.is_active or not user.check_password(password):
            flash("The username or password is incorrect.", "error")
            return render_template("auth/login.html"), 401

        session.clear()
        login_user(user, remember=False, fresh=True)
        session.permanent = True
        user.last_login_at = datetime.now(UTC)
        preference = db.session.get(UserPreference, user.id)
        if preference is None:
            preference = UserPreference(user=user)
            db.session.add(preference)
        preferred = (
            db.session.get(Department, preference.last_department_id)
            if preference.last_department_id
            else None
        )
        if preferred is not None and can_access_department(user, preferred):
            session["active_department_id"] = preferred.id
        else:
            if preference.last_department_id is not None:
                preference.last_department_id = None
            session.pop("active_department_id", None)
        db.session.commit()
        return redirect(url_for("tasks.index"))

    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))
