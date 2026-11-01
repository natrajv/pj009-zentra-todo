from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from flask_login import UserMixin
from sqlalchemy import JSON, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

user_global_roles = db.Table(
    "user_global_roles",
    db.Column(
        "user_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    db.Column(
        "global_role_id",
        db.Integer,
        db.ForeignKey("global_roles.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class TimestampMixin:
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid4()))
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime(timezone=True))

    memberships = db.relationship(
        "DepartmentMembership", back_populates="user", cascade="all, delete-orphan"
    )
    global_roles = db.relationship(
        "GlobalRole", secondary=user_global_roles, back_populates="users"
    )
    preferences = db.relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    @validates("username")
    def normalize_username(self, _key: str, value: str) -> str:
        return value.strip().lower()

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_master_admin(self) -> bool:
        return any(role.name == GlobalRole.MASTER_ADMIN for role in self.global_roles)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class GlobalRole(db.Model):
    __tablename__ = "global_roles"

    MASTER_ADMIN = "master_admin"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)
    users = db.relationship("User", secondary=user_global_roles, back_populates="global_roles")


class Department(TimestampMixin, db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    memberships = db.relationship("DepartmentMembership", back_populates="department")


class DepartmentMembership(TimestampMixin, db.Model):
    __tablename__ = "department_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "department_id", name="uq_membership_user_department"),
        CheckConstraint("role IN ('department_admin', 'user')", name="ck_membership_role"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    role = db.Column(db.String(30), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    joined_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    user = db.relationship("User", back_populates="memberships")
    department = db.relationship("Department", back_populates="memberships")


class UserPreference(db.Model):
    __tablename__ = "user_preferences"
    __table_args__ = (
        CheckConstraint("task_list_filter IN ('all', 'self')", name="ck_task_list_filter"),
        CheckConstraint(
            "work_package_list_filter IN ('all', 'self')", name="ck_work_package_list_filter"
        ),
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    task_list_filter = db.Column(db.String(10), nullable=False, default="all", server_default="all")
    work_package_list_filter = db.Column(
        db.String(10), nullable=False, default="all", server_default="all"
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=func.now(),
    )

    user = db.relationship("User", back_populates="preferences")
    last_department = db.relationship("Department")


class AuditEvent(db.Model):
    __tablename__ = "audit_events"

    id = db.Column(db.Integer, primary_key=True)
    occurred_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True
    )
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    action = db.Column(db.String(80), nullable=False)
    target_type = db.Column(db.String(40), nullable=False)
    target_public_id = db.Column(db.String(36))
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"))
    outcome = db.Column(db.String(20), nullable=False, default="success")
    details = db.Column(JSON, nullable=False, default=dict)

    actor = db.relationship("User")
    department = db.relationship("Department")


class Task(TimestampMixin, db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'completed')", name="ck_task_status"
        ),
        CheckConstraint(
            "priority IN ('low', 'normal', 'high', 'urgent')", name="ck_task_priority"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), nullable=False, unique=True, default=lambda: str(uuid4()))
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="open", server_default="open")
    priority = db.Column(db.String(20), nullable=False, default="normal", server_default="normal")
    assignee_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    due_date = db.Column(db.Date)
    is_archived = db.Column(db.Boolean, nullable=False, default=False, server_default="0")
    archived_at = db.Column(db.DateTime(timezone=True))

    department = db.relationship("Department")
    assignee = db.relationship("User", foreign_keys=[assignee_user_id])
    created_by = db.relationship("User", foreign_keys=[created_by_user_id])
