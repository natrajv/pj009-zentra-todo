# Zentra Deployment Plan

This document describes deployment requirements to settle and a safe initial operating model. Exact host, domain, process manager, and storage paths depend on the selected environment.

## 1. Environments

- **Development:** local instance database, debug tooling enabled only on loopback, synthetic data.
- **Test/CI:** isolated temporary database, deterministic fixtures, no production secrets.
- **Production:** supported WSGI server behind HTTPS reverse proxy; debug disabled; persistent restricted database and backup directories.
- **Demo:** separate demo database and configuration, never pointed at production storage.

Use separate secrets and databases for each environment. Keep `.env` and SQLite files out of version control.

## 2. Configuration

Provide a documented `.env.example` with names and safe placeholders only. Configuration includes secret key, environment, database locations, trusted hosts, session policy, timezone, logging level, export temp directory, backup directory, scheduler settings, and ontology validation settings. Fail startup for missing production secrets or unsafe production settings.

## 3. Application process

Run Flask through a production WSGI server; do not use the development server in production. Place a reverse proxy in front for TLS termination, request limits, and security headers. Configure worker count with SQLite’s single-writer behavior in mind. Store the database on reliable local storage with backups; avoid network filesystems unless their locking/consistency is verified.

## 4. Scheduler process

Run recurring generation as a distinct supervised process or platform scheduler, not as an uncoordinated scheduler in every web worker. Use idempotency constraints, bounded retries, a configured timezone, and observable job outcomes. Document restart and missed-run behavior.

## 5. Database lifecycle

Apply migrations as an explicit release step with a pre-migration backup. Keep a rollback/recovery plan. Enable foreign keys and configure SQLite journal mode based on deployment testing. Monitor disk space and backup completion. Run integrity checks on a schedule and after restore.

The initial Phase 1 downgrade removes all identity and preference tables. It is intended for an empty database or disposable migration verification only; do not downgrade a database containing user data. Recover production data from a verified backup instead.

## 6. Backup, restore, and retention

Define RPO/RTO, retention, encryption at rest, access controls, and off-host copy requirements with the operator. Verify backup integrity automatically and conduct restore drills. Restore must quiesce application writes and preserve a pre-restore copy. Do not expose backup files through static routes.

## 7. Logging and health

Send structured application and scheduler logs to a restricted destination with rotation/retention. Exclude secrets and personal task content. Provide liveness/readiness checks that reveal no sensitive configuration. Alert on repeated failed logins, scheduler failures, backup failures, low storage, and restore operations according to operator policy.

## 8. Release checklist

- Lock dependencies and record supported Python/runtime versions.
- Configure production secrets, allowed hosts, HTTPS, secure cookies, CSRF, and debug-off mode.
- Run migrations and focused authorization/integration checks.
- Verify demo/production database separation.
- Verify routine generation and duplicate prevention.
- Verify export scoping and temporary-file cleanup.
- Verify backup and restore in a staging environment.
- Record deployment version, migration state, operator, and recovery contact.

## 9. Decisions required before production

Select hosting and OS, domain/TLS ownership, database/backup paths, backup encryption/retention, RPO/RTO, scheduler technology, timezone and recurrence semantics, concurrent demo session policy, administrator recovery process, and monitoring destination.
