# Zentra Task Manager Requirements

**Status:** Planning baseline  
**Product:** Zentra Task Manager  
**Tagline:** Organize. Execute. Achieve.

## 1. Purpose and scope

Zentra is a web application for managing tasks and work packages across departments. Users may belong to more than one department. The system supports controlled administration, scheduled recurring work, personal work views, exports, archival, training in isolated demo mode, and database backup and restore.

This document is a product baseline. It does not define the implementation or authorize application coding.

## 2. Roles

| Role | Scope |
|---|---|
| Master Admin | Global user, department, task, work-package, configuration, backup, and restore administration. |
| Department Admin | Manage tasks and work packages in authorized departments for their members; read department users. |
| User | Read department user directory and department work views; update only tasks assigned to self. |

All access is limited to active department membership except Master Admin operations. Cross-department access must not be inferred from a user’s membership in another department.

## 3. Functional requirements

### Identity and department context

- **FR-001** Users can authenticate and log out.
- **FR-002** Master Admin can create, update, deactivate, and manage user accounts and departments.
- **FR-003** A user can belong to multiple departments through explicit memberships.
- **FR-004** A user can switch to any currently authorized department.
- **FR-005** The last selected department is remembered and restored on a later login only if membership remains active.
- **FR-006** Users can view the directory of users in the active department. They cannot enumerate unrelated departments.
- **FR-007** Directory visibility does not grant permission to modify another user’s tasks or account.

### Tasks and work packages

- **FR-008** Authorized users can create and view tasks and work packages within their department scope.
- **FR-009** Department Admin can create, assign, update, and archive department tasks and work packages.
- **FR-010** A User can update only tasks assigned to that authenticated user. The server checks ownership on every update.
- **FR-011** Task and work-package lists provide text search over relevant displayed fields.
- **FR-012** Task lists and work-package lists each provide **All | Self** filters. “Self” limits results to records assigned to or owned by the current user, as applicable.
- **FR-013** The task filter and work-package filter are remembered separately per user across sessions.
- **FR-014** Tasks and work packages can be archived and viewed in historical/archive views. Archive is reversible only through an authorized action and does not erase history.
- **FR-015** Status, priority, due date, assignee, work package, and department are available where appropriate for a task. A work package has a title, description, status, owner, department, and planned dates.

### Routine work

- **FR-016** Authorized administrators can define routine task and work-package templates with a schedule, effective dates, and generation rules.
- **FR-017** A scheduler creates due instances from active templates.
- **FR-018** Repeated scheduler execution must not create duplicate instances for the same template and scheduled occurrence.
- **FR-019** Generated records retain provenance to the template and scheduled occurrence that created them.

### Exports and reports

- **FR-020** Users can export the currently displayed, filtered task list to Excel and PDF.
- **FR-021** Exports apply the same department and row-level authorization as the screen and include the selected filters and generation time.
- **FR-022** Export actions are auditable. Exports must not expose hidden rows through formulas, metadata, or alternate sheets.

### Demo mode

- **FR-023** The system provides a designated demo user and a demo database suitable for training.
- **FR-024** Demo data is isolated from all production data and credentials.
- **FR-025** Demo state is reset on each demo login, using a concurrency-safe process. Active demo sessions must not overwrite one another or production state.
- **FR-026** Demo accounts cannot perform production backup or restore and cannot access production databases.

### Backup and restore

- **FR-027** Only Master Admin can request database backup or restore.
- **FR-028** Backup creates a consistent, integrity-checked database copy with a timestamp and audit record.
- **FR-029** Restore validates the backup and application schema version, requires an explicit administrative operation, and prevents writes against a database while it is being replaced.
- **FR-030** Backup files are protected from web access and are covered by documented retention and recovery procedures.

### Ontology

- **FR-031** The project includes a versioned OWL ontology defining the domain vocabulary and selected constraints/relationships.
- **FR-032** Ontology integration does not replace SQLite, service-layer validation, or application authorization.
- **FR-033** Ontology individuals, if materialized, use stable identifiers that can map to relational records without storing sensitive personal data in the graph.

## 4. Non-functional requirements

- **NFR-001 Security:** Apply least privilege, secure password storage, CSRF protection, output escaping, parameterized database access, and secure session handling.
- **NFR-002 Privacy:** Collect only data needed for the product. Limit directory information to the active department and intended fields.
- **NFR-003 Integrity:** Use foreign keys, uniqueness constraints, transactions, and migrations. Enforce business invariants in services and database constraints where possible.
- **NFR-004 Reliability:** Scheduler jobs and restore workflows must be repeatable, observable, and recoverable.
- **NFR-005 Auditability:** Record actor, action, target, scope, timestamp, and outcome for administrative and security-sensitive operations.
- **NFR-006 Accessibility:** Provide keyboard-operable controls, labels, visible focus, and readable contrast.
- **NFR-007 Maintainability:** Use modular Flask structure, documented configuration, migrations, and automated tests.
- **NFR-008 Portability:** Keep deployment configuration external to source code; support a documented production WSGI deployment.
- **NFR-009 Performance:** Paginate large lists and apply search/filtering in the database. Establish measurable response targets during deployment planning.
- **NFR-010 Time handling:** Store timestamps consistently (UTC recommended) and evaluate schedules in a configured IANA timezone.

## 5. Acceptance criteria for first usable release

1. A user in two departments can switch between them and sees no data from a non-selected department.
2. A User can view active department members but cannot update a task assigned to another person, including by direct request.
3. Department Admin can manage all scoped tasks/work packages for department members but cannot manage another department.
4. Search and All/Self filtering work for both lists, and each selection persists after logout/login.
5. Re-running a routine generator for the same occurrence creates no duplicates.
6. Excel and PDF exports contain exactly the authorized displayed result set.
7. Archive preserves records and history; normal lists exclude archived items unless requested.
8. Demo login resets only isolated demo data, including when two demo sessions overlap.
9. Only Master Admin can complete tested backup and restore workflows, with integrity and audit checks.
10. The OWL ontology loads and validates independently of the operational database.
