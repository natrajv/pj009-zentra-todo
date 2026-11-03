# Zentra Task Manager Requirements

**Status:** Planning baseline  
**Product:** Zentra Task Manager  
**Current release baseline:** v0.1.0
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

## 6. Sprint 2 backlog — v0.1.1

This is the requested next implementation scope. It is a backlog, not a statement that the functionality is implemented. Preserve the existing Flask/SQLite architecture, authorization rules, accessible UI, and migration policy. Do not pull unrelated planned modules into Sprint 2.

| ID | Area | Requirement | Type |
|---|---|---|---|
| SBL-0008 | Left navigation | Rename “Work Package” to “WP”. | Enhancement |
| SBL-0009 | Left navigation | Use distinct, recognizable Task and WP icons/logos with accessible names. | Enhancement |
| SBL-0010 | App header | Add the Zentra ToDo Manager brand logo. | Enhancement |
| SBL-0011 | App header/navigation | Move the user account and Preferences entry points from the header into the left navigation rail. Keep account details and sign-out reachable. | Enhancement |
| SBL-0012 | App header | Remove Departments and Tasks links from the app header. | Enhancement |
| SBL-0013 | App header | Display the app name on one line with compact spacing. | Enhancement |
| SBL-0014 | App header | Use the configured product name “Zentra Task Hub”, followed by the version number. | Enhancement |
| SBL-0015 | App header | Add About and Features destinations. | Feature |
| SBL-0016 | About | Show a short functionality summary, version, and build number sourced from configuration. | Feature |
| SBL-0017 | Features | Show the detailed product feature list sourced from configuration. | Feature |
| SBL-0018 | Home | Make the Task page the authenticated landing page. | Enhancement |
| SBL-0019 | Home | Clicking the app logo navigates to the Task page for authenticated users. | Enhancement |
| SBL-0020 | Data grid | Format Due Date and Created dates as `dd-mm-yy`. | Enhancement |
| SBL-0021 | Data grid | Allow column resizing and persist each user's widths across sessions. | Enhancement |
| SBL-0022 | Data grid | Make data-grid columns sortable. | Enhancement |
| SBL-0023 | Data grid | Fix the task delete confirmation so it is fully visible and usable in the viewport. | Bug |
| SBL-0024 | Task details | Include the associated Work Package details when a task belongs to a work package. | Enhancement |
| SBL-0025 | Search | Make search result rows open the corresponding task details. | Enhancement |
| SBL-0026 | Main content | Add breadcrumb navigation reflecting the current page/context. | Feature |
| SBL-0027 | Configuration | Use a `config.json` file for product metadata, feature descriptions, and default grid settings. | Feature |
| SBL-0028 | Configuration | Read the app name from configuration rather than hardcoding it. | Enhancement |
| SBL-0029 | Configuration | Read the app version from configuration. | Enhancement |
| SBL-0030 | Configuration | Store the detailed feature list in configuration for display on the Features page. | Enhancement |
| SBL-0031 | Configuration | Store the build number in configuration. | Enhancement |
| SBL-0032 | Configuration | Store the version number in configuration. | Enhancement |
| SBL-0033 | Preferences | Let users configure Task, Work Package, and Search Result grid column widths in Preferences. Supply defaults in `config.json` and provide a restore-defaults action. | Feature |

### Sprint 2 acceptance criteria

1. Authenticated navigation uses the WP label, distinct Task/WP icons, and places account and Preferences access on the left rail; the header contains no Departments or Tasks links.
2. The compact header displays the configured “Zentra Task Hub” name and version on one line. The brand logo returns an authenticated user to Tasks.
3. About and Features pages render their content from `config.json`, including version and build metadata. Missing or invalid configuration fails safely with a clear operational error rather than silently displaying stale hardcoded metadata.
4. Tasks is the authenticated home page. Breadcrumbs identify the current page and preserve useful navigation context.
5. Task grid date values use `dd-mm-yy`. Columns can be sorted and resized; widths remain per-user and persist across sessions. Preferences exposes widths for Task, WP, and Search Result grids and can restore the configured defaults.
6. Opening a task detail shows its linked WP summary when one exists. Search result rows open the matching task detail.
7. Delete confirmation remains fully visible at supported viewport sizes and is keyboard accessible.
8. Grid sorting, resizing, and preference updates do not broaden record visibility or alter server-side authorization. Persist user-owned grid preferences through the existing persistence approach or a versioned migration, as appropriate; never recreate the database.
9. Add focused tests for config loading/rendering, authenticated navigation/home routing, date formatting, task-detail/search navigation, grid preference persistence/default restoration, and the relevant access boundaries. Update docs to record implementation decisions.

## 7. GUI presentation standards

The following standards adapt the compact data-workspace presentation in [the Zentra example](example-gui-zentra.html) to Zentra's authenticated task-management workflows. They define visual and interaction conventions; they do not add database-viewer features such as opening arbitrary database files or running SQL.

- **GUI-001 — Application header:** Use a compact, single-line header with the Zentra mark and configured product name/version at the left. Show useful workspace context, such as the active department, beneath or beside the product identity when space permits. Place secondary product destinations and page-level actions at the right.
- **GUI-002 — Workspace navigation:** Use a narrow vertical navigation rail with recognizable icons and visible text labels. Clearly mark the active destination, provide accessible names for icon controls, and keep authorized account, preferences, and administration entry points reachable from the rail.
- **GUI-003 — Content workspace:** Let the main content occupy the available viewport width. Use a clear page heading and context line, followed by compact toolbars and the data grid. Keep normal page scrolling available; use internal scrolling for wide or long grids where it improves navigation.
- **GUI-004 — Contextual controls:** Group controls near the content they affect. Use compact, single-row search fields with adjacent Search and Clear actions; place list filters and grid actions in the same toolbar when space allows. Search and filtering must operate on the current authorized dataset.
- **GUI-005 — Data grids:** Present records in a dense, readable table with a distinct header row, sortable headings where supported, clear hover and selected-row states, and pagination for large result sets. Preserve usable column sizing and horizontal scrolling on narrow viewports. Row actions must have accessible labels, remain visually distinct from row selection, and be keyboard operable.
- **GUI-006 — Details and forms:** Present record details and focused create/edit forms in bounded dialogs or panels. Keep dialog content scrollable within the viewport, provide a clear title and close/cancel action, and distinguish destructive actions. Closing details opened from Search returns to the same Search results and preserves its query and page. Do not imply that unavailable relationships or operations are supported.
- **GUI-007 — Feedback and help:** Show concise status and error feedback close to the relevant workflow. Use consistent headings and grouped sections for longer help, product information, and preferences.
- **GUI-008 — Responsive behavior:** At narrower widths, allow toolbar controls to wrap without overlap, keep navigation usable, and let grids scroll horizontally. Dialogs and account panels must remain within the viewport.
- **GUI-009 — Accessibility and consistency:** Use semantic headings, labels, landmarks, keyboard-operable controls, visible focus, and readable contrast. Reuse spacing, color, control, grid, and dialog styles across Tasks, Search, Work Packages, and administration pages.
- **GUI-010 — Full-page grid mode:** Provide a Full Page control in the Content Search region. Full-page mode shows the Content Search controls and current data grid while hiding the workspace navigation and other page chrome. Keep a compact branded application header with a Back control. Preserve the current query, filters, sort order, page, and selected result when actions reload the grid in full-page mode; Back restores the prior normal page view.
- **GUI-011 — Left sidebars:** Distinguish the compact application navigation rail from a contextual left sidebar. Use the contextual sidebar for page-specific sections, give it a title matching its destination, show its sections as labeled list items, identify the active item, and provide an accessible collapse/expand control. Selecting an item displays its corresponding content in the main area without mixing the sections. On Preferences, the sidebar is titled “Preferences” and contains “List filters” and “Grid column widths (pixels)”; each selection opens its own editable form with a section-specific save action.
