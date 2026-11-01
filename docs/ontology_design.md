# Zentra OWL Ontology Design

## 1. Purpose and boundary

The ontology supplies a stable semantic vocabulary for Zentra and supports validation, documentation, and future semantic queries. SQLite remains the operational source of truth. OWL does not enforce application authorization, transactions, or all business constraints.

## 2. Namespace and serialization

Use a project-controlled namespace after selecting a stable domain (for example, `https://example.org/zentra/ontology#` as a temporary placeholder). Store the ontology at `app/ontology/zentra.owl`, use OWL 2, and select RDF/XML or Turtle based on project tooling. Record ontology version IRI, version info, license, and change history. Replace placeholder namespace before a public release.

## 3. Core classes

- `Person` / `User`
- `Department`
- `DepartmentMembership`
- `Task`
- `WorkPackage`
- `RoutineTemplate`
- `RoutineOccurrence`
- `TaskStatus` and `WorkPackageStatus` (or controlled value individuals)
- `Role` with `MasterAdmin`, `DepartmentAdmin`, and `UserRole` values
- `AuditEvent`

Use clear distinction between a person/account, their department membership, and the role granted within a department.

## 4. Object properties

- `hasMembership` (User → DepartmentMembership)
- `membershipInDepartment` (DepartmentMembership → Department)
- `membershipRole` (DepartmentMembership → Role)
- `taskInDepartment` (Task → Department)
- `assignedTo` (Task → User)
- `partOfWorkPackage` (Task → WorkPackage)
- `workPackageInDepartment` (WorkPackage → Department)
- `ownedBy` (WorkPackage → User)
- `generatedFromTemplate` (Task/WorkPackage → RoutineTemplate)
- `generatedAsOccurrence` (Task/WorkPackage → RoutineOccurrence)
- `performedBy` (AuditEvent → User)

Declare domains/ranges where they improve consistency, but avoid axioms that accidentally infer stronger access rights than intended.

## 5. Data properties

Use only necessary descriptive fields, such as stable identifier, title, description, status, priority, due date, created timestamp, and archive state. Do not place password hashes, session data, secrets, or unnecessary personal information in the graph. Avoid duplicating mutable relational data unless synchronization ownership and refresh behavior are specified.

## 6. Constraints and reasoning

OWL’s open-world semantics mean absence of a fact is not proof of its negation. Enforce required fields, uniqueness, department consistency, and authorization through SQLite constraints and service logic; use SHACL or explicit validation for closed-world shape checks when needed. A reasoner must not be used as the permission engine.

Potential validation rules include: every task has one department; every routine occurrence points to one template; task/work-package department associations agree; membership roles are drawn from the approved role vocabulary. Validate uniqueness and exact cardinality operationally where OWL semantics alone are insufficient.

## 7. Relational mapping

Map ontology individuals to relational records using opaque stable public IDs, not row numbers. Document the direction of synchronization. Initial recommendation: SQLite is authoritative; ontology exports are derived snapshots with timestamps and ontology version. If graph writes are introduced, define transactional consistency and conflict recovery before implementation.

## 8. Validation workflow

1. Parse and load the ontology in a standalone check.
2. Validate namespace, ontology/version metadata, expected classes/properties, and imports.
3. Run optional SHACL validation against representative non-sensitive fixtures.
4. Verify an invalid ontology cannot prevent core CRUD from starting unless ontology functionality is explicitly required for that operation.
5. Do not include production personal data in committed fixtures.
