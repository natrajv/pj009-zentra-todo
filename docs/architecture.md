# Zentra Architecture

## 1. Architecture goals

Keep the application understandable and testable. Use Flask for HTTP and session handling, SQLite for transactional operational data, and OWL for a small semantic model. Apply authorization in the application service layer and scope all reads and writes to the active department.

## 2. Logical layers

1. **Web layer:** Flask application factory, Blueprints, forms/API schemas, request validation, templates, and response formatting. Routes remain thin.
2. **Application services:** Authentication, membership switching, task/work-package operations, routine generation, exports, archival, audit, backup/restore orchestration, and authorization checks.
3. **Persistence:** SQLAlchemy models and repositories, SQLite, Alembic migrations, transaction boundaries, and integrity constraints.
4. **Background work:** A scheduler/worker invokes idempotent routine-generation services. The scheduler is a separate process in production; it does not run once per web worker.
5. **Semantic model:** Versioned OWL file, ontology loader/validator, and optional mapping adapter. The graph is not the source of truth for transactional state.
6. **Presentation assets:** Responsive HTML, CSS, JavaScript, and a project-owned Zentra logo asset.

## 3. Suggested repository layout

```text
zentra/
  app/
    __init__.py
    config.py
    extensions.py
    models/
    auth/
    users/
    departments/
    tasks/
    work_packages/
    routines/
    exports/
    admin/
    services/
    templates/
    static/
      css/
      js/
      img/
    ontology/
      zentra.owl
  migrations/
  docs/
  tests/
  instance/                 # local-only database and secrets; ignored by Git
  wsgi.py
  pyproject.toml
  uv.lock
  .env.example
  .gitignore
```

Adapt this layout to a repository’s existing structure instead of moving files solely to match the example.

## 4. Technology direction

- Python 3.12 or the compatible version established by the repository.
- Flask application factory and Blueprints.
- SQLAlchemy ORM and Flask-Migrate/Alembic.
- Flask-Login or an equivalent session mechanism.
- SQLite with foreign keys enabled on every connection.
- A separately supervised scheduler/worker for recurring generation.
- A maintained Excel/PDF generation library selected during implementation.
- RDFLib and/or Owlready2 for OWL loading and validation, selected based on the needed capabilities.
- pytest for tests; a lockfile-based environment manager (Astral UV is the initial recommendation).

Do not add every candidate dependency before confirming the use case and compatibility.

## 5. Request and authorization flow

For every protected action: authenticate the actor; load the actor’s active department context; confirm active membership or global Master Admin authority; validate that the target belongs to that department; apply role and row-level rules; perform the service operation in a transaction; write an audit event for sensitive actions; return only authorized fields. Service functions must accept actor/context explicitly rather than trusting department IDs supplied by the browser.

## 6. Department and preference context

Memberships are many-to-many. The active department lives in the server-side session and is selected only from the current user’s active memberships. Persist the last department and list filter preferences in the database. On login, restore the department only after membership revalidation; otherwise choose a valid default and require a deliberate switch where needed.

## 7. Routine generation

Store recurrence templates and generated occurrence keys in SQLite. The worker claims due occurrences and inserts records under a unique constraint on `(template_id, occurrence_key)` in a transaction. It can retry safely after interruption. Track next-run and last-run results. The recurrence format, timezone, daylight-saving behavior, and missed-run policy must be specified before implementation.

## 8. Demo isolation

Use a physically separate demo SQLite database. Reset from a versioned seed or pristine snapshot when demo login begins. Protect reset with a process-safe lock and avoid sharing mutable demo storage between concurrent users; use per-session demo copies if overlapping sessions are supported. Demo requests use only the demo database binding. This isolation must be tested at the connection/service boundary.

## 9. Backup and restore

Use SQLite’s supported backup mechanism to create consistent backups. Store outside the web root with restrictive filesystem permissions. Restore is an administrative maintenance operation: validate file integrity and schema compatibility, quiesce writes, create a pre-restore backup, replace atomically where supported, reopen connections, run integrity checks, and record the outcome. Define recovery steps for failure before enabling production restore.

## 10. Observability and operation

Use structured logs with request IDs; never log passwords, session tokens, database credentials, or exported personal data. Record scheduler outcomes and backup/restore events. Add health/readiness checks that do not expose secrets. Keep secrets and deployment-specific paths outside source control.

## 11. Phase 1 implementation baseline

The initial implementation uses `app/` with an application factory, `auth`, `departments`, `main`, and `admin` Blueprints, SQLAlchemy models, and a centralized permission policy module. Flask-Migrate manages Alembic migrations. Flask-Login handles authenticated sessions; Flask-WTF protects state-changing forms. The local entry point is `wsgi.py`.

The schema contains users, global roles, department memberships, departments, user preferences, audit events, and department-scoped tasks. Master Admin is represented in `global_roles`; Department Admin and User roles belong to department memberships. A Master Admin may switch to any active department. Other users may switch only to an active department with an active membership. The active department and role are reloaded from the database on each request.

The first administrator is created explicitly with the interactive `create-master-admin` Flask CLI command. There is no seeded user or default password. Master Admin can use the identity setup page to create departments, create users with an initial department role, and add users to more departments. These actions are written to `audit_events`. The task workspace scopes list, search, selection, edits, and deletion to the active department. It displays a read-only paginated task grid on the left and selected task details on the right; editing is opt-in from the detail panel. The account menu shows the signed-in user, effective role, and active department. Ordinary users can update only their own assigned tasks; only Department Admin and Master Admin can delete department tasks. Task and work-package list preferences remain separate; work-package behavior is for a later phase.

## 12. Database-viewer workspace presentation

Authenticated pages use a compact left navigation rail for Tasks, Work Package, and Search. The task page presents a paginated read-only table with row actions; selecting a row opens a view dialog, Control-click opens its edit dialog, and Create Task opens a create dialog. The Search page scopes matching across task fields to the active department, with the search panel above the result table. Master identity lists are presented as data tables. Work Package navigation currently opens an explicitly empty table because no work-package persistence or CRUD behavior is implemented yet; this is a UI destination only.
