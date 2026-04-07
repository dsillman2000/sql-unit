# Example 3: MySQL with Basic Connection

Connect to a MySQL database with explicit connection parameters.

## Basic Configuration

### Dictionary Syntax (Explicit)

```yaml
connection:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: your-password
    database: test_db
```

This connects to a MySQL database on `localhost` with the specified credentials.

### URL Syntax (Compact)

```yaml
connection:
  url: "mysql://root:your-password@localhost:3306/test_db"
```

Both syntaxes are equivalent. Use whichever you prefer.

## With Test Paths

Specify where tests are located:

```yaml
connection:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: your-password
    database: test_db

test_paths:
  - tests/sql/
```

## With Execution Defaults

Control parallelism and timeout:

```yaml
connection:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: your-password
    database: test_db

test_paths:
  - tests/

threads: 4      # Use 4 worker threads
timeout: 30     # 30 second timeout per query
```

## Using Environment Variables

For sensitive credentials, use environment variables:

```yaml
connection:
  mysql:
    host: ${DB_HOST}
    port: ${DB_PORT}
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    database: ${DB_NAME}

test_paths:
  - tests/

threads: 4
```

Load environment variables before running:

```bash
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your-password
export DB_NAME=test_db

sql-unit run
```

## Alternative: URL with Environment Variables

```yaml
connection:
  url: "mysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

test_paths:
  - tests/

threads: 4
```
