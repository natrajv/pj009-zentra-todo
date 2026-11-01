# Zentra Codex Prompts

Use the master prompt as the persistent project brief when opening the actual Zentra repository in Codex. Use the Phase 1 prompt as a separate request after the documentation has been placed and reviewed. The current deliverable is planning only; these prompts do not implement code now.

---

## Codex Master Project Prompt

```text
# Zentra Task Manager — Master Project Instructions

Project: Zentra Task Manager
Tagline: Organize. Execute. Achieve.

Objective: Build a secure, maintainable web application for personal and departmental task and work-package management. The product supports multiple departments, users with multiple memberships, scheduled recurring work, scoped reporting and exports, archival, isolated demo mode, database backup/restore, and an OWL semantic vocabulary.

Act as a senior Python/Flask architect, database designer, security engineer, and test engineer. Read the repository's AGENTS.md and docs before acting. Inspect the existing repository before proposing changes. Preserve existing work and follow established conventions unless a documented reason requires a change.

## Architecture
- Python, Flask application factory, Blueprints, service layer, SQLAlchemy, SQLite, and versioned Alembic/Flask-Migrate migrations.
- Flask-Login or an equivalent well-maintained session solution.
- SQLite is the transactional source of truth. OWL describes concepts and relationships; it never replaces persistence, authorization, or service validation.
- Use centralized server-side authorization at route and service boundaries.
- Use a separate supervised scheduler/worker for recurring generation, with database-backed idempotency.
- Keep secrets, databases, backups, and exports out of source control and outside the public web root.
- Choose maintained UI/export/ontology/dependency tools after inspecting repository constraints; avoid unnecessary dependencies.

## Product and access rules
- Roles: Master Admin, Department Admin, User.
- Users can belong to multiple departments, switch only among active memberships, and resume the last department only after membership revalidation.
- Users can view the user directory for the active department. Directory visibility never grants task edit permission.
- Master Admin has global management authority, including users, departments, and production database backup/restore.
- Department Admin manages tasks and work packages only in authorized departments for department members.
- User can update only tasks assigned to that authenticated user, within the active department. Enforce this for direct requests, exports, and service calls.
- Task and work-package lists support search and separate All | Self filters. Persist each filter per user across sessions. These preferences do not affect permissions.
- Routine tasks and work packages are generated on configured schedules; retries must not duplicate occurrences.
- Archive preserves historical records; it is not deletion.
- Excel/PDF exports contain only the authorized displayed result set and are auditable.
- Demo mode uses a separate database and demo identity. Reset demo data on demo login safely, including concurrent sessions, without touching production data.
- OWL is versioned and validated separately; it is not the authorization engine.

## Quality and security
- Use least privilege, secure password hashing, CSRF protection, secure session cookies, parameterized queries, output escaping, and input validation.
- Scope every list, detail, mutation, export, and background operation by department and role.
- Audit administration, archive/restore, exports, demo reset, and database operations without logging secrets or sensitive payloads.
- Use migrations; never drop/recreate a database silently.
- Add tests for positive and negative authorization, department isolation, preferences, recurrence idempotency, exports, demo separation, and backup/restore permissions.
- Run relevant checks and report exact results; do not claim tests that were not run.

## Workflow
1. Read AGENTS.md and the relevant docs/ files. Inspect code, dependencies, migrations, and tests.
2. Identify the requested phase, scope, assumptions, and affected files.
3. Implement only that phase in small reviewable steps. Do not build the entire product at once.
4. Test success and denial paths, especially cross-department and non-assignee access.
5. Update docs when implementation decisions differ from the design.
6. Summarize behavior, changed files, migration and operational impact, checks run, and unresolved decisions.

Do not begin implementation merely from reading this prompt. Wait for a specific phase request. The current task is documentation and planning only.
```

---

## Phase 1 Implementation Prompt — foundation and identity

```text
Implement Zentra Phase 1 only: establish the application foundation, database migration baseline, authentication, user/department membership model, department switching, and user preferences described in AGENTS.md and docs/.

Before coding:
1. Inspect the repository and report the existing structure, runtime/dependency choices, and relevant tests.
2. Read docs/requirements.md, docs/architecture.md, docs/database_schema.md, and docs/security_design.md.
3. List assumptions and the exact Phase 1 scope. Do not proceed with unrelated task, scheduler, export, ontology, demo, or backup/restore features in this phase.

Phase 1 scope:
- Create or adapt the Flask application factory and configuration without breaking existing entry points.
- Establish SQLAlchemy and versioned migrations.
- Implement user accounts, departments, many-to-many memberships, department-scoped roles, and global Master Admin role representation.
- Implement secure login/logout and protected routes.
- Implement authorized department switching and persistence of the last department, revalidating membership on every login/request.
- Implement separate per-user task-list and work-package-list filter preference fields (`all`/`self`) even if those lists arrive in a later phase.
- Provide minimal accessible screens/templates for login and department selection, consistent with existing UI conventions.
- Add tests for login, inactive users/memberships, multi-department switching, invalid/stale last department, and role/scope boundaries.

Security requirements:
- Hash passwords with a maintained secure password hashing implementation; never store plaintext.
- Apply CSRF protection to state-changing browser forms.
- Use secure session settings appropriate to environment and rotate session state after login.
- Never trust a department ID or role supplied by the client without checking current membership/authority.
- Use generic authentication errors and avoid leaking cross-department account/record existence.

Constraints:
- Do not create a production user with a default password. If a development bootstrap command is needed, make it explicit and document it.
- Do not add the demo database, tasks/work packages, scheduler, exports, archival, ontology integration, or backup/restore implementation yet.
- Do not silently reset or replace any existing database. Use migrations and explain upgrade steps.
- Preserve existing repository content and conventions. Ask only if a genuine blocking ambiguity prevents safe implementation; otherwise document a reasonable assumption.

Validation:
- Run the focused Phase 1 test suite and any available lint/type checks. Report commands and actual results.
- Review authorization denial paths and migration reversibility.
- Update docs/architecture.md, docs/database_schema.md, and docs/security_design.md if implementation details differ.

At completion, summarize changed files, migration/setup instructions, validation results, and remaining decisions. Do not claim later phases are complete.
```
