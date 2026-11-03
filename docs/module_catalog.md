# Zentra Module and Function Catalog

This catalog maps the product areas to their responsibilities and functions. It distinguishes the current Phase 1 implementation from planned modules so the list does not imply that later features already exist.

## Implemented modules

| Module | Current functions |
|---|---|
| `app` | `create_app` configures the Flask application, extensions, Blueprints, active department context, and the interactive Master Admin bootstrap command. SQLite connections enable foreign keys. |
| `app.config` | Supplies development/default and production configuration, database location, secret key, CSRF, and session-cookie settings. |
| `app.extensions` | Owns shared SQLAlchemy and Flask-Login extensions and loads active users from the session ID. |
| `app.models` | Defines users, global roles, departments, department memberships, user preferences, audit events, and tasks. Handles password hashing/checking and username normalization. |
| `app.permissions` | Centralizes active membership lookup and policies for department access, department management, and task updates. |
| `app.auth` | Signs users in and out, checks active accounts and credentials, initializes session state, and restores a still-authorized last department. |
| `app.departments` | Lists departments available to the signed-in user and switches the active department after authorization. |
| `app.admin` | Provides Master Admin identity screens and operations to create departments, create users with an initial membership, and add/reactivate memberships. Records audit events for these operations. |
| `app.main` | Displays and saves the separate per-user task and work-package list filter preferences (`all` or `self`). |
| `app.tasks` | Provides a department-scoped task workspace, search, task creation and editing, status updates, deletion, task list filtering, and pagination. Also provides the work-package navigation placeholder. |
| `migrations` | Stores versioned Alembic schema changes, including identity/preferences, audit events, and department-scoped tasks. |
| `wsgi.py` | Creates the application instance for the local Flask command and WSGI server. |

## Planned product modules

These are product responsibilities from the requirements and architecture. Add them only in their requested implementation phases.

### Sprint 2 v0.1.1 presentation/configuration work

The following work is planned and not yet implemented. It extends the existing `app.main`, `app.tasks`, templates, and static assets; it does not authorize building unrelated product modules.

| Area | Intended functions |
|---|---|
| Configuration and product metadata | Load `config.json` safely and expose product name, version, build, About summary, Features content, and default grid widths to templates/services. Keep secrets and environment-specific database settings out of this public product metadata file. |
| Shared shell/navigation | Compact branded header, Task/WP icons and labels, account and Preferences links in the rail, About and Features links, authenticated Tasks home/logo destination, and breadcrumbs. |
| Data grids/preferences | Format specified dates, support sorting and column resizing, persist per-user widths for Task/WP/Search Result grids, and restore configured defaults. Validate submitted preference keys/widths server-side. |
| Task details/search | Open task details from search rows and show associated WP summary where a relationship exists, while respecting current department and row-level authorization. |
| Delete confirmation | Keep the existing confirmation interaction fully visible and operable with keyboard and small viewports. |

| Module | Intended functions |
|---|---|
| `work_packages` | Create, view, update, assign/own, search, filter, archive, and restore department work packages; associate tasks while enforcing same-department scope. |
| `routines` | Manage recurring task and work-package templates; calculate due occurrences; generate records with provenance and idempotency protection; report generation outcomes. |
| `exports` | Produce Excel and PDF files from the same authorized and filtered result set shown to the requester; neutralize spreadsheet formulas and audit export requests. |
| `archive` | Archive and restore tasks/work packages with permission checks and history/audit records; expose authorized historical views. |
| `demo` | Authenticate the designated training identity against isolated demo storage and reset demo state safely without connecting to or modifying production data. |
| `backup_restore` (administrative service) | Allow only Master Admin to request controlled backup/restore; validate integrity and schema compatibility, protect files, quiesce writes for restore, and audit outcomes. |
| `ontology` | Store and validate the versioned OWL vocabulary and map stable public identifiers to relational records when a derived ontology export is needed. SQLite remains authoritative. |
| `services` | Host reusable application operations and authorization-aware business rules called by routes, workers, and exports. Keep request handling thin and pass actor and department context explicitly. |
| `worker` / scheduler | Run routine generation as a separately supervised process, with retries and idempotent occurrence handling. |

## Shared responsibilities

- **Authorization:** Every route and future service, worker, export, and administrative operation must enforce role, active membership, department scope, and row-level rules on the server.
- **Persistence:** SQLite and versioned migrations own transactional state. OWL is descriptive and does not grant access or replace validation.
- **Audit:** Record sensitive administrative and operational actions without storing secrets or unnecessary personal/task content.
- **Presentation:** Templates and static assets render accessible, responsive screens; they do not enforce permissions.
- **Verification:** Tests cover success and denial paths, especially cross-department access, non-assignee updates, and operational isolation.

## Current limitations

Work-package persistence and operations, recurring work, exports, archival, demo mode, backup/restore, and ontology integration are not implemented in the current phase. The Work Package navigation destination is a placeholder. The current task delete operation removes the task record and writes an audit event; product-wide archival behavior remains a later requirement and should be implemented as archival rather than deletion in its phase.
