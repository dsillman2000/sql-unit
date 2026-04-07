# Example 4: DuckDB for Analytical Testing

DuckDB is optimized for analytical queries and can work with file-based or in-memory databases.

## File-Based Database

### String Syntax (Simple)

```yaml
connection:
  duckdb: "test.duckdb"
```

This connects to a DuckDB database file `test.duckdb` in the project directory.

### Dictionary Syntax (Explicit)

```yaml
connection:
  duckdb:
    path: "test.duckdb"
```

Both syntaxes are equivalent. Use whichever you prefer.

## In-Memory Database

For testing without persistent storage:

```yaml
connection:
  duckdb: ":memory:"
```

Or with dictionary syntax:

```yaml
connection:
  duckdb:
    path: ":memory:"
```

## With Test Paths

Specify where tests are located:

```yaml
connection:
  duckdb: "test.duckdb"

test_paths:
  - tests/analytics/
  - tests/sql/
```

## With Execution Defaults

Control parallelism and timeout:

```yaml
connection:
  duckdb: "test.duckdb"

test_paths:
  - tests/

threads: 4      # Use 4 worker threads
timeout: 30     # 30 second timeout per query
```

## URL Syntax

```yaml
connection:
  url: "duckdb:///test.duckdb"

test_paths:
  - tests/

threads: 4
```

Or for in-memory:

```yaml
connection:
  url: "duckdb:///:memory:"

test_paths:
  - tests/

threads: 4
```

## Analytical Use Case

DuckDB excels at analytical queries. Example configuration for data warehouse testing:

```yaml
connection:
  duckdb: "warehouse.duckdb"

test_paths:
  - tests/queries/

threads: 8      # Leverage parallelism for analytical workloads
timeout: 60     # Longer timeout for complex queries
```
