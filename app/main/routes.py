from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import UserPreference
from . import bp

FILTER_FIELDS = {
    "task_list_filter": "Task list",
    "work_package_list_filter": "Work-package list",
}


@bp.get("/preferences")
@login_required
def preferences():
    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(task_list_filter="all", work_package_list_filter="all")
    return render_template("main/preferences.html", preference=preference)


@bp.post("/preferences")
@login_required
def update_preferences():
    updates = {field: request.form.get(field, "") for field in FILTER_FIELDS}
    if any(value not in {"all", "self"} for value in updates.values()):
        flash("Choose All or Self for each list.", "error")
        return redirect(url_for("main.preferences")), 400

    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)
    for field, value in updates.items():
        setattr(preference, field, value)
    db.session.commit()
    flash("Preferences saved.", "success")
    return redirect(url_for("main.preferences"))
