# Technology Stack

## Language & Runtime

- **Python**: 3.12+
- **Package Manager**: uv (modern Python package manager)

## Core Dependencies

- **psycopg2-binary**: PostgreSQL database adapter
- **sendgrid**: Email delivery service client
- **requests**: HTTP library for API calls
- **python-dotenv**: Environment variable management
- **foreninglet-data**: Foreninglet API integration (>=0.4.0)

## Development Tools

- **pytest**: Testing framework with integration test markers
- **testcontainers**: Docker-based test containers (PostgreSQL 16-alpine)
- **ruff**: Fast Python linter and formatter
- **pre-commit**: Git hook management for code quality

## Database

- **PostgreSQL**: Primary database (tested with version 16)
- **Flyway**: Database migration management (see `db-automator/`) uses version 11
- **Schema**: `lfautomator` with tables for token pools and history

## Logging
- **Loguru**: Used to write all logs

## Common Commands

```bash
# Install dependencies
uv sync

# Run tests
pytest

# Run integration tests only
pytest -m integration

# Run linter
ruff check .

# Format code
ruff format .

# Run pre-commit hooks
pre-commit run --all-files
```

## Environment Configuration

Environment variables are loaded from `.env` files. Required variables:
- `SENDGRID_API_KEY`: SendGrid API authentication
- `POSTGRESQL_ADDON_HOST`, `POSTGRESQL_ADDON_PORT`, `POSTGRESQL_ADDON_DB`, `POSTGRESQL_ADDON_USER`, `POSTGRESQL_ADDON_PASSWORD`: Database connection
- `API_PASSWORD`, `API_BASE_URL`: Foreninglet API credentials

## Development Script prerequisites
Always load .env file for any files built for development tasks

# Rules
## Tests
All tests should ALWAYS run successfully before and after implementing a feature

## Linting and formatting
Ruff has to pass after each feature - both for formatting and linting

