# Zentra Security Design

## 1. Security objectives

Protect department data from cross-department access, prevent users from changing other users’ tasks, isolate demo state, and restrict sensitive administrative operations. Treat UI visibility as convenience only; all controls are enforced server-side.

## 2. Authentication and sessions

- Store passwords using a current, slow password hashing function through a maintained framework/library. Never log or return password hashes.
- Use generic login failures, rate limits or throttling, and secure password reset procedures.
- Set session cookies `HttpOnly`, `Secure` in HTTPS deployments, and an appropriate `SameSite` policy. Rotate the session after authentication and privilege changes.
- Protect state-changing browser requests with CSRF tokens. Set session lifetime and idle timeout explicitly.
- Deactivated users and revoked memberships must lose access on the next authorization check; do not trust stale session role data.

Phase 1 uses Werkzeug's scrypt password hashing, generic login failures, a session clear before login, and a fresh Flask-Login session. Flask-WTF CSRF protection is enabled for forms. Sessions use HTTP-only and SameSite=Lax cookies; production config marks session and remember cookies Secure and refuses to start without `SECRET_KEY`.

## 3. Authorization model

First resolve the authenticated actor, active department, active membership, and global role. Then enforce the action matrix:

| Action | Master Admin | Department Admin | User |
|---|---|---|---|
| Manage global users/departments | All | No | No |
| View active department user directory | All | Active department | Active department |
| Manage department tasks/work packages | All | Authorized department | No |
| Update a task | All | Authorized department | Only if assigned to self and in active department |
| View/export tasks | Authorized scope | Authorized department | Authorized department and allowed view |
| Backup/restore production database | Yes | No | No |

Apply the same checks to HTML routes, JSON endpoints, background jobs, exports, and direct service calls. Reject unauthorized IDs without revealing whether an out-of-scope record exists. Validate that an assignee belongs to the task department.

## 4. Department switching and preferences

Accept a department switch only if the user has current active membership or is Master Admin. Validate the stored last department at every login. Treat filter preferences as presentation state and never as permission grants.

The request hook reloads the active department and membership from SQLite for every authenticated request. It removes an invalid session selection immediately. A stale saved department is cleared at login; the user can still access other active memberships. Identity setup routes return not-found to non-Master Admin users, validate department IDs and role values server-side, and record successful provisioning actions in the audit table.

Task reads and search are constrained to the active department and the stored All/Self preference. Task updates are checked against the task department and assignee on every request. Permanent deletion is restricted to Department Admin and Master Admin within the active department. Department Admin and Master Admin can assign tasks only to active members of the selected department. Task create, update, status, and deletion actions are audited.

## 5. Search, exports, and data leakage

- Use parameterized queries and database-side pagination.
- Search only authorized results; escape user input for display and use safe query construction.
- Build exports from the same authorized query/service used by the displayed list. Recheck permission immediately before generation.
- Neutralize spreadsheet formula injection for values beginning with formula-triggering characters.
- Avoid sensitive data in export metadata and temporary files. Clean temporary outputs and audit export requests.

## 6. Demo mode

- Use physically separate database files and strict configuration selection controlled by server-side authentication flow.
- Never accept a database filename, path, or mode selector from the browser.
- Use least-privilege process permissions. Demo login must never reset production storage.
- Make resets concurrency-safe. Prefer per-session demo copies if sessions overlap; otherwise serialize access and clearly limit concurrent training sessions.
- Prevent demo credentials from reaching production and block production backup/restore from demo context.

## 7. Routine generation and archival

The scheduler uses a service identity with only required rights. Enforce idempotency with a unique occurrence constraint and transaction. Archive/restore actions require scoped permission and create audit/history records. Avoid hard deletion of referenced business records.

## 8. Backup and restore controls

- Require authenticated Master Admin and recent reauthentication for restore.
- Store backups outside the web root with restrictive permissions and a documented retention policy.
- Verify backup integrity and schema compatibility before restore. Create a pre-restore backup, quiesce writes, use an atomic replacement strategy when supported, and confirm integrity afterward.
- Record operator, artifact identifier, timestamps, and result; never expose filesystem paths or secrets in client responses.

## 9. Application and deployment controls

- Keep secrets outside source control and use environment or secret-store configuration.
- Set production debug off; use HTTPS; configure trusted hosts and secure headers.
- Keep dependencies pinned/locked and review updates. Apply database file and backup permissions at the OS level.
- Do not log passwords, session identifiers, CSRF tokens, full exported rows, or secret configuration.
- Establish vulnerability reporting, incident response, and backup recovery exercises before production use.

## 10. Verification cases

Tests should cover direct-object reference attempts across departments, task updates by a non-assignee, department admin scope, stale membership, invalid last-department preference, export scope, demo reset isolation under concurrent logins, scheduler retries, and backup/restore role checks.
