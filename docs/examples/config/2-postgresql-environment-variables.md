# Example 2: PostgreSQL with Environment Variables

Use environment variables for sensitive credentials.

```yaml
connection:
  postgresql:
    host: ${DB_HOST}
    port: ${DB_PORT}
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}
    timeout: 30

test_paths:
  - tests/

threads: 4
```

## Setup

Create a `.env` file (don't commit to git):

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your-secret-password
DB_NAME=test_db
```

Load before running tests:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your-secret-password
export DB_NAME=test_db

sql-unit run
```

## Alternative: Using URL Syntax

```yaml
connection:
  url: "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

test_paths:
  - tests/

threads: 4
```
