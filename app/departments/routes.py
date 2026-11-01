from __future__ import annotations

from flask import abort, flash, g, redirect, render_template, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import select

from ..extensions import db
from ..models import Department, DepartmentMembership, UserPreference
from ..permissions import can_access_department
from . import bp


@bp.get("")
@login_required
def index():
    if current_user.is_master_admin:
        departments = db.session.scalars(
            select(Department).where(Department.is_active.is_(True)).order_by(Department.name)
        ).all()
    else:
        departments = db.session.scalars(
            select(Department)
            .join(DepartmentMembership)
            .where(
                DepartmentMembership.user_id == current_user.id,
                DepartmentMembership.is_active.is_(True),
                Department.is_active.is_(True),
            )
            .order_by(Department.name)
        ).all()
    return render_template(
        "departments/index.html", departments=departments, active_department=g.active_department
    )


@bp.post("/<int:department_id>/switch")
@login_required
def switch(department_id: int):
    department = db.session.get(Department, department_id)
    if department is None or not can_access_department(current_user, department):
        abort(404)

    preference = db.session.get(UserPreference, current_user.id)
    if preference is None:
        preference = UserPreference(user=current_user)
        db.session.add(preference)
    preference.last_department_id = department.id
    session["active_department_id"] = department.id
    db.session.commit()
    flash(f"Active department: {department.name}.", "success")
    return redirect(url_for("tasks.index"))
