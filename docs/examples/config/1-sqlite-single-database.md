# Example 1: Single SQLite Database

Simplest configuration for local testing.

## Basic Configuration

### String Syntax (Simple)

```yaml
connection:
  sqlite: "tests.db"
```

This connects to a SQLite database file `tests.db` in the project directory.

### Dictionary Syntax (Explicit)

```yaml
connection:
  sqlite:
    path: "tests.db"
```

Both syntaxes are equivalent. Use whichever you prefer.

## In-Memory Database

For testing without persistent storage:

```yaml
connection:
  sqlite: ":memory:"
```

Or with dictionary syntax:

```yaml
connection:
  sqlite:
    path: ":memory:"
```

## With Test Paths

Specify where tests are located:

```yaml
connection:
  sqlite: "tests.db"

test_paths:
  - tests/unit/
  - tests/integration/
```

## With Execution Defaults

Control parallelism and timeout:

```yaml
connection:
  sqlite: "tests.db"

test_paths:
  - tests/

threads: 4      # Use 4 worker threads
timeout: 30     # 30 second timeout per query
```
