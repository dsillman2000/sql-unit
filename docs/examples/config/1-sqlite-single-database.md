# Example 1: Single SQLite Database

Simplest configuration for local testing.

```yaml
connection:
  sqlite: "tests.db"
```

This connects to a SQLite database file `tests.db` in the project directory.

For in-memory testing:

```yaml
connection:
  sqlite: ":memory:"
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
