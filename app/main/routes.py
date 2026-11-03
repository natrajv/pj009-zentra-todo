from __future__ import annotations

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import UserPreference
from . import bp

FILTER_FIELDS = {
    "task_list_filter": "Task list",
    "work_package_list_filter": "Work-package list",
}


@bp.get("/about")
@login_required
def about():
    return render_template("main/about.html")


@bp.get("/features")
@login_required
def features():
    return render_template("main/features.html")


@bp.get("/preferences")
@login_required
def preferences():
    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(
            task_list_filter="all", work_package_list_filter="all", grid_widths={}
        )
    defaults = current_app.config["PRODUCT_CONFIG"]["grid_defaults"]
    widths = {
        grid: {**columns, **(preference.grid_widths or {}).get(grid, {})}
        for grid, columns in defaults.items()
    }
    return render_template(
        "main/preferences.html", preference=preference, grid_widths=widths, grid_defaults=defaults
    )


@bp.post("/preferences")
@login_required
def update_preferences():
    updates = {field: request.form.get(field, "") for field in FILTER_FIELDS}
    if any(value not in {"all", "self"} for value in updates.values()):
        flash("Choose All or Self for each list.", "error")
        return redirect(url_for("main.preferences")), 400

    defaults = current_app.config["PRODUCT_CONFIG"]["grid_defaults"]
    existing_preference = db.session.get(UserPreference, current_user.id)
    widths = (
        {grid: dict(columns) for grid, columns in (existing_preference.grid_widths or {}).items()}
        if existing_preference
        else {}
    )
    for grid, columns in defaults.items():
        widths.setdefault(grid, {})
        for column in columns:
            key = f"width_{grid}_{column}"
            raw = request.form.get(key)
            if raw in (None, ""):
                continue
            try:
                width = int(raw)
            except ValueError:
                abort(400)
            if not 60 <= width <= 800:
                abort(400)
            widths[grid][column] = width
    if request.form.get("restore_grid_defaults") == "1":
        widths = {}

    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)
    for field, value in updates.items():
        setattr(preference, field, value)
    preference.grid_widths = widths
    db.session.commit()
    flash("Preferences saved.", "success")
    return redirect(url_for("main.preferences"))


@bp.post("/preferences/grid-widths/<grid>")
@login_required
def save_grid_width(grid):
    defaults = current_app.config["PRODUCT_CONFIG"]["grid_defaults"]
    if grid not in defaults:
        abort(404)
    column = request.form.get("column", "")
    if column not in defaults[grid]:
        abort(400)
    try:
        width = int(request.form.get("width", ""))
    except ValueError:
        abort(400)
    if not 60 <= width <= 800:
        abort(400)
    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)
    stored = dict(preference.grid_widths or {})
    stored.setdefault(grid, {})[column] = width
    preference.grid_widths = stored
    db.session.commit()
    return {"ok": True}
