# Project Structure

## Root Layout

```
lf-automator/           # Main package directory
├── automator/          # Core automation modules
├── db-automator/       # Database migrations and schema
└── tests/              # Test suite
```

## Module Organization

### `lf-automator/automator/`

Core business logic organized by domain:

- `automation.py`: Main `Automator` class with token counting and threshold logic
- `database/db.py`: `Database` class for PostgreSQL connections and queries
- `mailer/send.py`: `Mailer` class for SendGrid email delivery
- `tokenpools/pools.py`: `TokenPool` class for token pool management

Each module has its own `__init__.py` for package structure.

### `lf-automator/db-automator/`

Database migration management:

- `migrations/`: Flyway SQL migration files (format: `V###_YYYYMMDDHHMMSS__description.sql`)
- `flyway.toml`: Flyway configuration
- `schema-model/`: Database schema documentation

### `lf-automator/tests/`

Test organization mirrors source structure:

- `conftest.py`: Shared pytest fixtures (testcontainers setup, db connections)
- `test_*.py`: Test modules matching source modules
- `db-automator/migrations/`: Test migration copies for integration tests

## Conventions

- **Module Structure**: Each submodule has `__init__.py` and `__pycache__/` for compiled bytecode
- **Test Markers**: Use `@pytest.mark.integration` for tests requiring database/external services
- **Database Schema**: All tables use `lfautomator` schema prefix
- **Naming**: Snake_case for Python files, camelCase for database columns (with UUID suffix)
