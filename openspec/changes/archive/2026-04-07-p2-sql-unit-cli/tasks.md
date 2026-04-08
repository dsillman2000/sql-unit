# Tasks for p2-sql-unit-cli

## Prerequisite: Phase 1 Complete
- All p1-sql-unit-core, p1-sql-unit-inputs, p1-sql-unit-expectations changes must be complete

## Project Setup

### Dependencies
- [x] Add Click to pyproject.toml dependencies
  - Update `dependencies` array to include "click>=8.0.0"
  - This is required for all CLI commands below

### CLI Framework Setup
- [x] Install Click dependency
- [x] Create cli module/package (src/sql_unit/cli/)
- [x] Implement main entry point (sql-unit command)
- [x] Add --help and --version flags
- [x] Create entry point in pyproject.toml for the sql-unit command

### list Command Implementation
- [x] Implement list command structure
- [x] Implement test discovery
  - Scan for .sql unit files
  - Parse unit metadata (title, tags, etc.)
  - Build test registry
- [x] Implement -s/--select filtering with four selector types
  - Name: exact test name (e.g., `-s test_user_login`)
  - Glob: pattern matching (e.g., `-s "user_*"`)
  - File: specific SQL file path (e.g., `-s tests/users/auth_test.sql`)
  - Folder: directory path (e.g., `-s tests/integration/`)
  - Support multiple selectors for union results
- [x] Implement output formatting
  - Human-readable (one line per test with name and path)
  - JSON output (--format=json)
- [x] Implement sorting
  - Sort by test name
  - Sort by directory
  - Support --sort-by flag
- [x] Implement parallel discovery via --threads flag (optional)
  - Default: sequential discovery
  - -1: use CPU count
  - N: use specific thread count

### Testing for list Command
- [x] Unit tests for test discovery
- [x] Unit tests for filtering logic (all four selector types)
- [x] Unit tests for output formatting (human-readable and JSON)
- [x] Unit tests for parallel discovery
- [x] Integration tests with sample test files
- [x] Test edge cases (no tests found, invalid filters, etc.)

## Capability 1.5: cli-compile - SQL Output

### compile Command Implementation
- [x] Implement compile command structure
- [x] Implement test discovery (same discovery as list)
- [x] Implement -s/--select filtering (same four selector types as list)
  - Name: exact test name
  - Glob: pattern matching
  - File: specific SQL file path
  - Folder: directory path
  - Support multiple selectors for union results
- [x] Implement SQL compilation
  - Render Jinja templates with context
  - Output plaintext SQL statements
  - No database connection required
- [x] Implement output formatting
  - Human-readable SQL output to stdout (default)
  - JSON format (--format=json) with test name and compiled SQL
- [x] Implement parallel discovery with sequential output
  - Discover tests in parallel via --threads flag
  - Buffer results for sequential output (no interleaving)
  - Output SQL in discovery order

### Testing for compile Command
- [x] Unit tests for SQL compilation
- [x] Unit tests for Jinja template rendering
- [x] Unit tests for filtering logic
- [x] Unit tests for output formatting (plaintext and JSON)
- [x] Integration tests with sample test files
- [x] Test edge cases (Jinja errors, no matching tests, etc.)

## Capability 2: cli-run - Test Execution

### run Command Implementation
- [x] Implement run command structure
- [x] Implement -s/--select filtering (same four selector types as list)
  - Name: exact test name
  - Glob: pattern matching
  - File: specific SQL file path
  - Folder: directory path
  - Support multiple selectors for union results
- [x] Implement execution modes
  - Default: run all discovered tests
  - Filtered: run matching tests
  - Single test: run specific test
- [x] Implement output options
  - Human-readable format (test name, pass/fail, time)
  - JSON format (--format=json)
  - Verbose output (--verbose/-v)
    - Show SQL statements executed
    - Show input setup details
    - Show expectation details
- [x] Implement result aggregation
  - Count passed/failed/skipped tests
  - Total execution time
  - Summary report

### Parallel Execution Support
- [x] Implement --threads/-j flag with ThreadPoolExecutor
  - Default: sequential execution (1 thread)
  - -1: use CPU count
  - N: use specific thread count
- [x] Implement thread pool and test queue
  - Use concurrent.futures.ThreadPoolExecutor
  - Distribute tests to worker threads
  - Collect results from workers
- [x] Implement output synchronization
  - Queue-based result collection
  - Write results atomically per test
  - Prevent output garbling with locks
- [x] Implement resource management
  - SQLAlchemy connection pool is thread-safe by design
  - Document --threads behavior and defaults
  - Each worker thread shares the connection pool
  - Add guidance on connection pool tuning for large thread counts

### Exit Codes
- [x] Implement exit code handling
  - 0: All tests passed
  - 1: One or more tests failed
  - 2: Invalid arguments or configuration error
- [x] Implement error handling for:
  - Missing test files
  - Invalid configuration
  - Database connection failures
  - Test execution exceptions

### Testing for run Command
- [x] Unit tests for command parsing and -s/--select filtering
- [x] Unit tests for filtering logic (all four selector types)
- [x] Unit tests for output formatting (human-readable and JSON)
- [x] Unit tests for exit code handling
- [x] Integration tests with sample tests
  - Run and verify results
  - Test filter combinations (union of multiple selectors)
  - Test parallel execution with various thread counts
  - Test thread safety with concurrent database operations
- [x] Integration tests for exit codes
  - All pass → exit 0
  - Some fail → exit 1
  - Invalid args or connection error → exit 2
- [x] Test edge cases
  - No matching tests
  - Database connection failures
  - Malformed test files
  - Thread pool exception handling

## Capability 3: Output Formatting

### Human-Readable Output
- [x] Implement formatted table output
  - Column headers: Test Name | Status | Time | Location
  - Status symbols: ✓ (pass), ✗ (fail), ⊘ (skip)
  - Color output (green/red) if terminal supports it
- [x] Implement summary output
  - Line: "X passed, Y failed, Z skipped in T seconds"
- [x] Implement detailed output (--verbose)
  - Show SQL statements
  - Show input setup
  - Show expectation details
  - Show assertion failures

### JSON Output
- [x] Implement JSON schema for results
  - test_name (string)
  - status (pass|fail|skip)
  - duration_ms (integer)
  - path (string)
  - error_message (string, if failed)
  - details (object with sql, inputs, expectations for verbose)
- [x] Implement JSON aggregation
  - List of test results
  - Summary object
  - Metadata (tool version, timestamp, etc.)
- [x] Validate JSON output with test
  - Parse output as JSON
  - Verify schema

### Testing for Output Formatting
- [x] Test human-readable formatting
  - Verify column alignment
  - Verify symbols
  - Test color codes (if applicable)
- [x] Test JSON formatting
  - Parse output as valid JSON
  - Verify schema compliance
  - Test with various test outcomes
- [x] Test verbose output
  - Verify SQL display
  - Verify input details
  - Verify expectation details

## CLI Integration & Documentation

### Configuration & Connection Handling
- [x] Implement config file loading (sql-unit.yaml)
  - Read test_paths from config
  - Read connection settings from config
- [x] Implement --connection CLI override
  - Take precedence over config connection
  - Support environment variable substitution (${VAR})
- [x] Implement config-free mode
  - When --connection provided without config, discover all .sql files in CWD
  - Use -s/--select for filtering to avoid surprise execution
- [x] Implement connection error handling
  - Clear error message when no connection configured
  - Suggest creating config or using --connection flag

### Error Handling & Messages
- [x] Implement user-friendly error messages
  - Configuration errors (missing config, invalid format)
  - Database connection errors (connection refused, auth failed)
  - Test execution errors (syntax errors, runtime errors)
  - Missing connection guidance (actionable suggestions)
- [x] Implement help text for all commands (list, compile, run)
  - Usage syntax
  - All available flags and options
  - Example usage
- [x] Implement -s/--select help with examples
  - Document four selector types (name, glob, file, folder)
  - Show how to combine multiple selectors

### Testing
- [x] End-to-end CLI tests
  - Run list command and verify output formats
  - Run compile command and verify SQL output
  - Run tests and verify results
  - Run with -s/--select filters and verify
  - Run with --threads and verify parallel execution
- [x] Test all command flags
  - -s/--select with all four selector types
  - --threads with various values (-1, 1, 4, etc.)
  - --format (human-readable, json)
  - --verbose for run command
- [x] Test error scenarios
  - No connection configured
  - Invalid selector patterns
  - Database connection failures
  - Malformed test files
  - Thread pool exhaustion

### Documentation
- [x] Add CLI usage documentation
   - list command with examples (-s/--select, --format, --threads)
   - compile command with examples
   - run command with examples (-s/--select, --threads, --verbose, --format)
   - Detailed -s/--select filtering guide with all four selector types
   - Output format examples (human-readable and JSON)
   - Parallel execution guide and thread tuning
- [x] Add connection configuration documentation
  - Creating sql-unit.yaml with connection settings
  - Using --connection CLI flag
  - Config vs CLI precedence
  - Environment variable substitution
- [x] Add troubleshooting section
  - Common errors and solutions
  - Thread pool tuning for large test suites
  - Connection pool configuration
- [x] Add CI/CD integration examples
  - GitHub Actions workflow
  - Exit code handling in CI
  - Parallel execution in CI environments
