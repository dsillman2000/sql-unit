# SQL Unit CLI - Usage Guide

The `sql-unit` command-line interface provides three main commands for discovering, compiling, and executing SQL unit tests.

## Commands

### list - Discover and Display Tests

List all available SQL unit tests with optional filtering and sorting.

**No database connection required.**

```bash
sql-unit list [OPTIONS]
```

#### Options

- `-s, --select TEXT` - Filter tests (can be used multiple times for union)
  - Test name: `-s test_user_login`
  - Glob pattern: `-s "user_*"` or `-s "test_*"`
  - File path: `-s tests/auth_test.sql`
  - Directory: `-s tests/auth/`
- `--format [human|json]` - Output format (default: human)
- `--sort-by [name|directory|path]` - Sort results (default: name)
- `--threads N` - Parallel discovery threads (1=sequential, -1=CPU count)

#### Examples

```bash
# List all tests
sql-unit list

# List with human-readable output
sql-unit list --format human

# List matching pattern
sql-unit list -s "user_*"

# List from specific file
sql-unit list -s tests/auth_test.sql

# List from directory
sql-unit list -s tests/integration/

# Combine multiple selectors (union)
sql-unit list -s test_login -s "admin_*" -s tests/regression/

# JSON output
sql-unit list --format json

# Sort by directory
sql-unit list --sort-by directory
```

### compile - Render SQL Templates

Compile tests to SQL by rendering Jinja2 templates. Output compiled SQL without executing against a database.

**No database connection required.**

```bash
sql-unit compile [OPTIONS]
```

#### Options

- `-s, --select TEXT` - Filter tests (can be used multiple times)
- `--format [sql|json]` - Output format (default: sql)
- `--threads N` - Parallel discovery threads (1=sequential, -1=CPU count)

#### Examples

```bash
# Compile all tests to plain SQL
sql-unit compile

# Compile specific test
sql-unit compile -s test_user_login

# Compile with glob pattern
sql-unit compile -s "user_*"

# JSON output (includes test names and SQL)
sql-unit compile --format json

# Compile from directory
sql-unit compile -s tests/integration/
```

### run - Execute Tests

Execute SQL unit tests against a database and report results.

**Requires database connection (via config or --connection flag).**

```bash
sql-unit run [OPTIONS]
```

#### Options

- `-s, --select TEXT` - Filter tests (can be used multiple times)
- `--connection URL` - Database connection URL (overrides config)
- `--format [human|json]` - Output format (default: human)
- `-j, --threads N` - Parallel execution threads (1=sequential, -1=CPU count)
- `-v, --verbose` - Show detailed output

#### Examples

```bash
# Run all tests
sql-unit run --connection "sqlite:///tests.db"

# Run specific test
sql-unit run -s test_user_login --connection "sqlite:///tests.db"

# Run with pattern matching
sql-unit run -s "user_*" --connection "sqlite:///tests.db"

# Parallel execution (4 threads)
sql-unit run -j 4 --connection "sqlite:///tests.db"

# Parallel with CPU count
sql-unit run -j -1 --connection "sqlite:///tests.db"

# JSON output
sql-unit run --format json --connection "sqlite:///tests.db"

# Verbose output with details
sql-unit run -v --connection "sqlite:///tests.db"

# Combine selectors (union)
sql-unit run -s test_login -s "admin_*" -s tests/regression/ \
  --connection "postgresql://user:pass@localhost/testdb"
```

## Filter Syntax: -s/--select

The `-s` or `--select` flag provides flexible test filtering. You can use multiple selectors to create a union of results.

### Selector Types

1. **Test Name** - Exact match
   ```bash
   sql-unit list -s test_user_login
   ```

2. **Glob Pattern** - Use wildcards (* and ?)
   ```bash
   sql-unit list -s "user_*"       # All tests starting with user_
   sql-unit list -s "test_*"       # All tests starting with test_
   sql-unit list -s "*_integration"  # All tests ending with _integration
   ```

3. **File Path** - Specific SQL file
   ```bash
   sql-unit list -s tests/auth_test.sql
   sql-unit list -s "tests/auth/user_test.sql"
   ```

4. **Directory** - All tests in a folder (ends with /)
   ```bash
   sql-unit list -s tests/
   sql-unit list -s tests/integration/
   sql-unit list -s tests/auth/
   ```

### Combining Selectors (Union)

Multiple selectors combine with union (OR) logic:

```bash
# Tests from list.sql OR matches pattern user_*
sql-unit run -s tests/list.sql -s "user_*" --connection "sqlite:///test.db"

# Tests matching pattern OR from directory
sql-unit run -s "admin_*" -s tests/admin/ --connection "sqlite:///test.db"

# All three types combined
sql-unit run -s test_login -s "user_*" -s tests/regression/ \
  --connection "sqlite:///test.db"
```

## Output Formats

### Human-Readable (Default)

Tests are displayed in a formatted table:

```
Test Name                Status    Time (ms)  Path
─────────────────────────────────────────────────────────
test_user_login          ✓ pass         12.5  tests/auth_test.sql
test_user_logout         ✗ fail         25.3  tests/auth_test.sql
test_admin_setup         ✓ pass          8.1  tests/admin_test.sql

3 passed, 1 failed, 0 errors, 0 skipped in 46.0ms
```

Status symbols:
- `✓ pass` - Test passed
- `✗ fail` - Test failed (assertion error)
- `⊘ error` - Test error (exception during execution)
- `⊗ skip` - Test skipped

### JSON Output

Structured output suitable for CI/CD pipelines:

```json
{
  "results": [
    {
      "name": "test_user_login",
      "file_path": "tests/auth_test.sql",
      "status": "pass",
      "duration_ms": 12.5,
      "error_message": null,
      "details": {}
    },
    {
      "name": "test_user_logout",
      "file_path": "tests/auth_test.sql",
      "status": "fail",
      "duration_ms": 25.3,
      "error_message": "Expected 5 rows, got 3",
      "details": {}
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "errors": 0,
    "skipped": 0,
    "total_time_ms": 46.0
  }
}
```

## Exit Codes

The `run` command returns specific exit codes for CI/CD integration:

- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Error or invalid configuration

## Database Connection

The `run` command requires a database connection. Specify it via:

### Option 1: Command Line Flag

```bash
sql-unit run --connection "sqlite:///tests.db"
sql-unit run --connection "postgresql://user:password@localhost:5432/testdb"
sql-unit run --connection "mysql://user:password@localhost:3306/testdb"
```

### Option 2: Config File (sql-unit.yaml)

```yaml
connection:
  url: "sqlite:///tests.db"
  # OR with environment variable:
  # url: "${DATABASE_URL}"

test_paths:
  - "tests/"
  - "src/test_definitions/"
```

Then run:
```bash
sql-unit run
```

### Precedence

`--connection` flag always takes precedence over config file connection.

## Parallel Execution

Use `-j` or `--threads` to run tests in parallel:

```bash
# Sequential (default)
sql-unit run --connection "sqlite:///test.db"

# 4 parallel threads
sql-unit run -j 4 --connection "sqlite:///test.db"

# Auto-detect CPU count
sql-unit run -j -1 --connection "sqlite:///test.db"
```

**Note**: Test execution is I/O-bound (waiting on database), so threading is safe. SQLAlchemy connection pools are thread-safe and shared across worker threads.

## Troubleshooting

### No database connection configured

**Error**: "No database connection configured"

**Solution**: Provide connection via CLI:
```bash
sql-unit run --connection "sqlite:///tests.db"
```

Or create `sql-unit.yaml`:
```yaml
connection:
  url: "sqlite:///tests.db"
```

### No tests found

**Error**: "No tests found"

**Cause**: No .sql files exist in discovery paths, or selectors are too restrictive

**Solution**:
```bash
# Verify tests exist
sql-unit list

# Check selector syntax
sql-unit list -s "test_*"

# Broaden search
sql-unit list --sort-by path
```

### Connection refused

**Error**: "Error executing tests: Connection refused"

**Cause**: Database not running or wrong connection URL

**Solution**:
```bash
# Verify database is running
# Check connection URL syntax

# Test with SQLite (no setup required)
sql-unit run --connection "sqlite:///tests.db"
```

### Thread pool exhaustion

**Issue**: Many parallel tests but connection pool exhausted

**Solution**: Reduce thread count or tune connection pool:
```bash
# Use fewer threads
sql-unit run -j 2 --connection "postgresql://..."

# Or increase pool size in connection URL
sql-unit run -j -1 \
  --connection "postgresql://user:pass@host/db?pool_size=20"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: SQL Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: pip install sql-unit
      
      - name: Run SQL tests
        run: |
          sql-unit run \
            --connection "postgresql://postgres:password@localhost/testdb" \
            --format json \
            -j 4 > test-results.json
      
      - name: Parse results
        run: |
          # Parse test-results.json and fail if needed
          python -c "
            import json
            with open('test-results.json') as f:
              data = json.load(f)
              print(f\"Tests: {data['summary']['passed']} passed, {data['summary']['failed']} failed\")
              exit(0 if data['summary']['failed'] == 0 else 1)
          "
```

### Exit Code Usage

```bash
sql-unit run --connection "postgresql://..." --format json

if [ $? -eq 0 ]; then
  echo "All tests passed"
elif [ $? -eq 1 ]; then
  echo "Tests failed"
  exit 1
else
  echo "Error running tests"
  exit 2
fi
```

## Configuration File: sql-unit.yaml

Full example:

```yaml
# Database connection (can be overridden with --connection)
connection:
  url: "sqlite:///tests.db"
  # Or use environment variable:
  # url: "${DATABASE_URL}"

# Test discovery paths
test_paths:
  - "tests/unit/"
  - "tests/integration/"
  - "src/tests/"

# Default thread count for parallel execution
threads: 4

# Default output format
output_format: "human"
```

Environment variable substitution is supported:
```yaml
connection:
  url: "${DATABASE_URL}"  # Will expand $DATABASE_URL
```
