# Zentra Task Manager — Codex project instructions

## Project objective

Build Zentra, a secure web application for personal and departmental task and work-package management. The application uses Python, Flask, SQLite, and an OWL ontology. The working tagline is **Organize. Execute. Achieve.**

## Working rules

- Inspect the repository and its existing conventions before changing files. Preserve existing work and explain any necessary migration or compatibility decisions.
- Implement only the requested phase. The planning package does not authorize building the application in one pass.
- Keep SQLite as the transactional source of truth. OWL describes domain concepts and relationships; it does not replace persistence, authorization, or validation.
- Enforce authorization on the server for every route, service operation, export, and administrative action. Hiding UI controls is not authorization.
- Use migrations for schema changes. Do not silently recreate or drop a database.
- Keep demo data isolated from production data. Never reset or seed production data as part of a demo login.
- Preserve auditability for sensitive changes, archive operations, exports, backup, and restore.
- Avoid committing secrets, real user data, database files, backups, or generated exports.
- Add or update tests for implemented behavior and run the relevant checks before reporting completion. Do not claim checks that were not run.
- Update documentation when implementation decisions change the design in `docs/`.

## Product decisions

- Roles: Master Admin, Department Admin, User.
- A user may belong to multiple departments and can switch only among those memberships. Remember the last authorized department between logins.
- A user can view the user directory for the active department, but that visibility does not grant task editing rights.
- Ordinary Users may update only tasks assigned to themselves. Department Admins manage tasks and work packages in their departments. Master Admin has global administration.
- Task and work-package lists support search and **All | Self** filters. Persist each list filter per user across sessions.
- Routine tasks and work packages are generated on schedules with idempotency protection.
- Archival retains historical records; it is not deletion.
- Excel and PDF exports contain only the rows the requesting user is currently authorized to see and may filter.
- Demo mode uses a separate database and a designated demo user. Reset demo state at demo login with concurrency-safe isolation.
- Only Master Admin may perform controlled database backup and restore.

## Preferred technical direction

Use a Flask application factory, Blueprints, service-layer business logic, centralized authorization, SQLAlchemy, and versioned Alembic/Flask-Migrate migrations. Use Flask-Login for sessions. Prefer a supported Python version already established by the repository; otherwise target Python 3.12. Use pytest. Select UI, export, scheduler, ontology, and dependency-management libraries after inspecting repository constraints and documenting the choice.

## Suggested structure

Follow `docs/architecture.md` as a starting point, adapting to existing conventions. Keep routes thin, business rules in services, authorization decisions centralized, and persistence behind models/repositories.

## Required implementation workflow

1. Read this file and all relevant `docs/` files, then inspect the repository, dependencies, and existing tests.
2. State the phase scope, assumptions, and files expected to change before making broad changes.
3. Implement in small, reviewable steps. Do not introduce unrelated features.
4. Validate authorization at the service boundary and cover negative access cases.
5. Run focused tests and applicable project checks. Report exact commands and results.
6. Summarize changed files, behavior, migration/operational impact, and known follow-up decisions.

## Scope boundary

The current deliverable is documentation and prompts only. Do not implement the application until a later implementation request.
