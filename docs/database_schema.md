# Zentra Database Schema Design

This is a logical SQLite schema proposal, not executable migration SQL. Use migrations to implement it and adapt names/types to the selected ORM conventions.

## 1. Conventions

- Integer primary keys are suitable for local SQLite operations; public-facing identifiers should be non-sequential UUIDs or opaque tokens where enumeration matters.
- Store timestamps in UTC using a consistent ISO-8601 representation or integer epoch convention.
- Enable `PRAGMA foreign_keys=ON` on every connection.
- Use explicit indexes for common scope, assignment, status, date, and search queries.
- Prefer deactivation and archival over destructive deletion where historical references exist.

## 2. Core tables

### `users`

`id` PK; `public_id` UUID unique; `username` unique and normalized to lowercase; `display_name`; `password_hash`; `is_active`; `created_at`; `updated_at`; `last_login_at`.

Do not store plaintext passwords. Define username/email normalization and account recovery separately.

### `departments`

`id` PK; `public_id` UUID unique; `name` unique; `description`; `is_active`; `created_at`; `updated_at`.

### `department_memberships`

`id` PK; `user_id` FK; `department_id` FK; `role` enum/check (`department_admin`, `user`); `is_active`; `joined_at`; `created_at`; `updated_at`; unique (`user_id`, `department_id`).

Master Admin is a global role, stored in a separate global role assignment or user authorization model; do not grant it accidentally through a department membership.

The Phase 1 implementation uses `global_roles` and the `user_global_roles` association table. The supported global role is `master_admin`. Department membership roles are restricted to `department_admin` and `user`.

### `user_preferences`

`user_id` PK/FK; `last_department_id` nullable FK; `task_list_filter` check (`all`, `self`); `work_package_list_filter` check (`all`, `self`); `updated_at`.

Revalidate `last_department_id` against active membership whenever restored.

The Phase 1 implementation also stores independent `task_list_filter` and `work_package_list_filter` values, each constrained to `all` or `self`.

### `work_packages`

`id` PK; `public_id` unique; `department_id` FK; `title`; `description`; `status`; `owner_user_id` FK nullable; `start_date`; `due_date`; `is_archived`; `archived_at`; `archived_by_user_id` FK nullable; `created_by_user_id` FK; `created_at`; `updated_at`.

### `tasks`

`id` PK; `public_id` UUID unique; `department_id` FK; `work_package_id` FK nullable (to be added with Work Packages); `title`; `description`; `status`; `priority`; `assignee_user_id` FK; `created_by_user_id` FK; `due_date`; `is_archived`; `archived_at`; `created_at`; `updated_at`.

Enforce that task and work package departments agree in service logic and, if practical, with composite keys/triggers. Every query must independently scope by department.

The initial task implementation uses `open`, `in_progress`, and `completed` statuses, and `low`, `normal`, `high`, and `urgent` priorities. Start dates, work-package links, archive actor/history, and optimistic concurrency are not yet implemented.

### `routine_templates`

`id` PK; `department_id` FK; `kind` (`task` or `work_package`); `title`; `description`; schedule definition; `timezone`; `effective_from`; `effective_until`; assignment/owner defaults; `is_active`; `created_by_user_id` FK; timestamps.

Validate recurrence expressions on write and version the schedule format if it changes.

### `routine_occurrences`

`id` PK; `template_id` FK; `occurrence_key`; `scheduled_for`; `generated_task_id` nullable FK; `generated_work_package_id` nullable FK; `status`; `created_at`; unique (`template_id`, `occurrence_key`).

The unique key is the core idempotency guard. Ensure exactly one generated target matches `kind`.

### `audit_events`

`id` PK; `occurred_at`; `actor_user_id` nullable FK; `action`; `target_type`; `target_public_id` nullable; `department_id` nullable FK; `outcome`; `details` JSON restricted to non-secret metadata. A request ID can be added when request correlation is introduced.

Audit records should be append-only through application permissions. The Phase 1 implementation records successful department, user, and membership creation/reactivation. Define retention and privacy policy.

### `system_operations`

`id` PK; `operation_type` (`backup`, `restore`, `demo_reset`); `requested_by_user_id` nullable FK; `started_at`; `completed_at`; `status`; `artifact_reference` nullable; `details_json` without secrets.

## 3. Optional extensions

- `task_status_history`: actor, task, previous/new status, timestamp.
- `work_package_status_history`.
- `attachments`: store file metadata and controlled path/object key; do not store uploaded executable content in the web root.
- `export_events`: filters/scope and outcome without retaining exported content.
- `global_roles`: user-to-global-role mapping if more than one global role is anticipated.

## 4. Key indexes and constraints

- `department_memberships(user_id, is_active)` and `(department_id, is_active, user_id)`.
- `tasks(department_id, is_archived, status, due_date)` and `(department_id, assignee_user_id, is_archived)`.
- `work_packages(department_id, is_archived, status, due_date)` and `(department_id, owner_user_id, is_archived)`.
- `routine_templates(is_active, effective_from)`.
- Unique `(template_id, occurrence_key)` on `routine_occurrences`.
- Check constraints for enumerated role, status, priority, and filter values.
- Use `ON DELETE RESTRICT` for referenced users/departments and retain history through deactivation/archive.

## 5. Database separation

Production and demo databases use separate files, configuration bindings, credentials/process permissions, and backup paths. Never select a database from a client-provided path. A demo reset restores a known versioned seed and never touches production connection state.
