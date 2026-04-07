# sql-unit.yaml Schema

## Overview

The `sql-unit.yaml` configuration file defines project-level settings for SQL Unit testing, including database connections, test paths, and execution defaults.

## Top-Level Structure

```yaml
# Database connection (required)
connection: {...}

# Test discovery paths (optional, default: all .sql files)
test_paths:
  - tests/
  - integration/

# Execution defaults (optional)
threads: 4
timeout: 30
```

## Connection Block

### Block Syntax (Driver-Specific Parameters)

Specify connection using driver-specific parameters:

```yaml
connection:
  sqlite:
    path: tests.db

connection:
  postgresql:
    host: localhost
    port: 5432
    user: postgres
    password: ${DB_PASSWORD}  # Environment variable substitution
    database: test_db
    timeout: 30

connection:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: ${DB_PASSWORD}
    database: test_db

connection:
  duckdb:
    path: tests.duckdb
```

### URL Syntax

Specify connection using database URL:

```yaml
connection:
  url: "sqlite:///tests.db"
  
connection:
  url: "postgresql://${DB_USER}:${DB_PASSWORD}@localhost/test_db"
  
connection:
  url: "mysql://root:${DB_PASSWORD}@localhost/test_db"
```

## Test Paths

Specify directories where SQL test files are located. Supports glob patterns.

```yaml
test_paths:
  - tests/
  - integration/tests/
  - "**/*_test.sql"
```

**Defaults:** If not specified, all .sql files in the current directory and subdirectories are discovered.

## Execution Defaults

### Threads

Number of worker threads for parallel test execution.

```yaml
threads: 4  # Use 4 threads
threads: -1 # Use system maximum (auto-detect)
```

**Constraints:**
- Must be >= 1 or exactly -1
- Default: 4

### Timeout

Query timeout in seconds for database operations.

```yaml
timeout: 30  # 30 second timeout
```

**Default:** No timeout (queries run until completion)

## Environment Variable Substitution

Support `${VAR_NAME}` syntax to reference environment variables:

```yaml
connection:
  postgresql:
    host: ${DB_HOST}
    port: ${DB_PORT}
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}
```

### Escaping

To use a literal `${`, escape it as `$${`:

```yaml
note: "This is $${literal} text"  # Results in: This is ${literal} text
```

## Complete Example

```yaml
# Database connection
connection:
  postgresql:
    host: localhost
    port: 5432
    user: postgres
    password: ${DB_PASSWORD}
    database: test_db
    timeout: 30

# Test discovery
test_paths:
  - tests/unit/
  - tests/integration/

# Execution defaults
threads: 8
```

## Validation Rules

1. **Required:** `connection` block must be present
2. **Connection:** Either block syntax or URL syntax (not both)
3. **Test Paths:** All paths must exist and be readable (warning if not)
4. **Threads:** Must be integer >= 1 or exactly -1
5. **Timeout:** Must be positive integer if specified
6. **Variables:** All `${VAR}` references must resolve to existing environment variables

## Discovery

The system searches for `sql-unit.yaml` in:
1. Current working directory
2. Parent directories (walking up the tree)
3. Stops at first match

Error if multiple `sql-unit.yaml` files found in the tree.

## CLI Overrides

Command-line arguments take precedence over config file values:

```bash
# Override config connection with CLI flag
sql-unit run --connection "sqlite:///override.db"

# Use explicit config file
sql-unit run --config /path/to/custom.yaml

# Override thread count
sql-unit run --threads 16
```
