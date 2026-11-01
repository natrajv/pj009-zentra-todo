from app.extensions import db
from app.models import Department, DepartmentMembership, GlobalRole, User, UserPreference


def make_user(username="ava", password="correct horse battery staple", active=True):
    user = User(username=username, display_name=username.title(), is_active=active)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(UserPreference(user=user))
    return user


def make_department(name="Operations", active=True):
    department = Department(name=name, is_active=active)
    db.session.add(department)
    db.session.flush()
    return department


def add_membership(user, department, role="user", active=True):
    membership = DepartmentMembership(
        user=user, department=department, role=role, is_active=active
    )
    db.session.add(membership)
    return membership


def make_master_admin(username="root"):
    user = make_user(username=username)
    role = GlobalRole(name=GlobalRole.MASTER_ADMIN)
    db.session.add(role)
    user.global_roles.append(role)
    return user
