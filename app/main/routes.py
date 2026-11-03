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
PREFERENCE_SECTIONS = {"list_filters", "grid_widths"}


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
    section = request.args.get("section", "list_filters")
    if section not in PREFERENCE_SECTIONS:
        abort(404)
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
        "main/preferences.html",
        preference=preference,
        grid_widths=widths,
        grid_defaults=defaults,
        selected_section=section,
    )


@bp.post("/preferences")
@login_required
def update_preferences():
    section = request.form.get("section")
    legacy_submission = section is None
    section = section or "list_filters"
    if section not in PREFERENCE_SECTIONS:
        abort(400)
    defaults = current_app.config["PRODUCT_CONFIG"]["grid_defaults"]
    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)

    if section == "list_filters" or legacy_submission:
        updates = {field: request.form.get(field, "") for field in FILTER_FIELDS}
        provided_updates = {
            field: value for field, value in updates.items()
            if not legacy_submission or field in request.form
        }
        if any(value not in {"all", "self"} for value in provided_updates.values()):
            flash("Choose All or Self for each list.", "error")
            return redirect(url_for("main.preferences", section=section)), 400
        for field, value in provided_updates.items():
            setattr(preference, field, value)
        message = "Preferences saved." if legacy_submission else "List filters saved."
    if section == "grid_widths" or legacy_submission:
        widths = {
            grid: dict(columns)
            for grid, columns in (preference.grid_widths or {}).items()
        }
        has_width_values = False
        for grid, columns in defaults.items():
            widths.setdefault(grid, {})
            for column in columns:
                raw = request.form.get(f"width_{grid}_{column}")
                if raw in (None, ""):
                    continue
                has_width_values = True
                try:
                    width = int(raw)
                except ValueError:
                    abort(400)
                if not 60 <= width <= 800:
                    abort(400)
                widths[grid][column] = width
        if request.form.get("restore_grid_defaults") == "1":
            widths = {}
            message = "Grid column widths restored to defaults."
        elif section == "grid_widths" or has_width_values:
            message = "Grid column widths saved."
        if section == "grid_widths" or has_width_values or request.form.get("restore_grid_defaults") == "1":
            preference.grid_widths = widths

    db.session.commit()
    flash(message, "success")
    redirect_section = section if not legacy_submission else "list_filters"
    return redirect(url_for("main.preferences", section=redirect_section))


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
