# Zentra ToDo Manager (v0.1.0)  
Daily tasks manager for office and personal   
Version: v0.1.0, Build: +20261101.1419

## Phase 1: foundation and identity

The foundation is a Flask application with SQLite, SQLAlchemy, versioned Alembic migrations, login, department memberships/switching, and persistent list preferences. Department-scoped task lists, search, status updates, and task details are available. Work-package management remains a later phase.

### Local setup

1. Install Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).
2. Run `uv sync --group dev`.
3. Copy `.env.example` to `.env` and set `SECRET_KEY` to a long random value. Keep `.env` private.
4. Initialize the database with `uv run flask --app wsgi db upgrade`.
5. Create the first administrator interactively with `uv run flask --app wsgi create-master-admin`. The command prompts for credentials and rejects passwords shorter than 12 characters; it creates no default account.
6. Start the local server with `uv run flask --app wsgi run`, sign in as the Master Admin, then use **Administration** to create departments and user memberships.

Production deployments must set `APP_ENV=production`, use HTTPS, and keep database and secret files private. See [docs/deployment.md](docs/deployment.md).

Run the focused test suite with `uv run pytest`.
