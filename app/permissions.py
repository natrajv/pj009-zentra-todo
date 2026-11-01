from __future__ import annotations

from .models import Department, DepartmentMembership, User

ROLE_USER = "user"
ROLE_DEPARTMENT_ADMIN = "department_admin"


def membership_for(user: User, department_id: int) -> DepartmentMembership | None:
    return next(
        (
            membership
            for membership in user.memberships
            if membership.department_id == department_id and membership.is_active
        ),
        None,
    )


def can_access_department(user: User, department: Department) -> bool:
    return bool(
        user.is_active
        and department.is_active
        and (user.is_master_admin or membership_for(user, department.id))
    )


def can_manage_department(user: User, department: Department) -> bool:
    membership = membership_for(user, department.id)
    return bool(
        user.is_active
        and department.is_active
        and (user.is_master_admin or (membership and membership.role == ROLE_DEPARTMENT_ADMIN))
    )


def can_update_task(user: User, department: Department, assignee_user_id: int | None) -> bool:
    if not can_access_department(user, department):
        return False
    if user.is_master_admin or can_manage_department(user, department):
        return True
    return assignee_user_id == user.id
