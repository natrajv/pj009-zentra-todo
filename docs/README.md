# Zentra project documentation

These documents define the planning baseline for the Zentra Task Manager. They describe requirements and design; they do not implement the application.

## Documents

- [Requirements](requirements.md) — functional scope, roles, and acceptance criteria.
- [Architecture](architecture.md) — application layers, proposed structure, and operational boundaries.
- [Database schema](database_schema.md) — logical SQLite model to implement through versioned migrations.
- [Security design](security_design.md) — authentication, authorization, isolation, and operational controls.
- [Ontology design](ontology_design.md) — OWL vocabulary and its relationship to relational data.
- [Deployment](deployment.md) — environment, release, backup, and operations guidance.
- [Codex prompts](codex_prompts.md) — master project prompt and Phase 1 implementation prompt.

Persistent repository instructions are in the root [AGENTS.md](../AGENTS.md).

## Current scope

The current deliverable is documentation and prompts only. Do not implement the application until a specific implementation phase is requested. Resolve the open operational choices in these documents during the relevant implementation phase, and record any decisions that change the design.
