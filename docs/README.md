# Zentra project documentation

These documents define the planning baseline for the Zentra Task Manager. They describe requirements and design; they do not implement the application.

## Documents

- [Requirements](requirements.md) — functional scope, roles, and acceptance criteria.
- [Architecture](architecture.md) — application layers, proposed structure, and operational boundaries.
- [Database schema](database_schema.md) — logical SQLite model to implement through versioned migrations.
- [Security design](security_design.md) — authentication, authorization, isolation, and operational controls.
- [Ontology design](ontology_design.md) — OWL vocabulary and its relationship to relational data.
- [Deployment](deployment.md) — environment, release, backup, and operations guidance.
- [Codex prompts](codex_prompts.md) — master project prompt and implementation prompts for Phases 1 and Sprint 2.
- [Module and function catalog](module_catalog.md) — implemented module responsibilities and planned product functions.

Persistent repository instructions are in the root [AGENTS.md](../AGENTS.md).

## Current scope

Sprint 2 v0.1.1 is implemented for the shared presentation shell, product metadata, About/Features, task/search grids, and per-user grid width preferences. Work-package records and task associations remain future work; current task detail explicitly reports the missing association. The backlog and implementation prompt remain in [requirements](requirements.md) and [Codex prompts](codex_prompts.md) for traceability.
