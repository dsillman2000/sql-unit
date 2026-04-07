# CLI Spec

## Purpose

This specification defines the command-line interface (CLI) for SQL Unit, including test discovery via the `list` command, SQL compilation via the `compile` command, and test execution via the `run` command. The CLI supports multiple output formats, parallel execution, granular test filtering, configuration management, and database connection specification for comprehensive test lifecycle management.

## Requirements

### Requirement: list command for test discovery
The system SHALL provide a `sql-unit list` command to discover and display available tests. This command does not require a database connection.

#### Scenario: List all tests
- **WHEN** user runs `sql-unit list`
- **THEN** system displays all discovered tests with names and paths

#### Scenario: Test discovery in current directory
- **WHEN** user runs `sql-unit list` from project root
- **THEN** system recursively finds all .sql files with @unit tests

#### Scenario: List output format
- **WHEN** tests are discovered
- **THEN** output includes test name, file path, and test count

#### Scenario: Select by test name
- **WHEN** user runs `sql-unit list -s test_user_login`
- **THEN** system lists only the test with that exact name

#### Scenario: Select by glob pattern
- **WHEN** user runs `sql-unit list -s "user_*"`
- **THEN** system lists only tests matching the glob pattern

#### Scenario: Select by file
- **WHEN** user runs `sql-unit list -s tests/users/auth_test.sql`
- **THEN** system lists tests only from that specific file

#### Scenario: Select by folder
- **WHEN** user runs `sql-unit list -s tests/integration/`
- **THEN** system lists tests from all .sql files in that directory and subdirectories

#### Scenario: Multiple selectors (union)
- **WHEN** user runs `sql-unit list -s test_login -s "admin_*" -s tests/regression/`
- **THEN** system lists tests matching any of the selectors (union)

#### Scenario: JSON output format
- **WHEN** user runs `sql-unit list --format=json`
- **THEN** system outputs valid JSON with test metadata

#### Scenario: No tests found
- **WHEN** user runs list with selector that matches no tests
- **THEN** system reports "No tests found" clearly

#### Scenario: No connection required
- **WHEN** user runs `sql-unit list` without any database configured
- **THEN** system completes successfully without error

#### Scenario: List with parallel discovery
- **WHEN** user runs `sql-unit list --threads 4`
- **THEN** system discovers tests in parallel for faster collection

### Requirement: compile command for SQL output
The system SHALL provide a `sql-unit compile` command that outputs plaintext SQL to stdout. This command does not require a database connection.

#### Scenario: Compile all tests
- **WHEN** user runs `sql-unit compile`
- **THEN** system discovers all tests and outputs compiled SQL to stdout

#### Scenario: Select by test name
- **WHEN** user runs `sql-unit compile -s test_user_login`
- **THEN** system compiles only the test with that exact name

#### Scenario: Select by glob pattern
- **WHEN** user runs `sql-unit compile -s "user_*"`
- **THEN** system compiles only tests matching the glob pattern

#### Scenario: Select by file
- **WHEN** user runs `sql-unit compile -s tests/users/auth_test.sql`
- **THEN** system compiles tests only from that specific file

#### Scenario: Select by folder
- **WHEN** user runs `sql-unit compile -s tests/integration/`
- **THEN** system compiles tests from all .sql files in that directory and subdirectories

#### Scenario: Multiple selectors (union)
- **WHEN** user runs `sql-unit compile -s test_login -s "admin_*" -s tests/regression/`
- **THEN** system compiles tests matching any of the selectors (union)

#### Scenario: Compile with Jinja rendered
- **WHEN** test contains Jinja template variables
- **THEN** system renders templates before outputting SQL

#### Scenario: Compile output format
- **WHEN** compile command runs
- **THEN** output is plaintext SQL, one statement per line, in discovery order

#### Scenario: Compile JSON output format
- **WHEN** user runs `sql-unit compile --format=json`
- **THEN** system outputs JSON with test name and compiled SQL for each test

#### Scenario: Compile with parallel discovery but sequential output
- **WHEN** user runs `sql-unit compile --threads 4`
- **THEN** system discovers tests in parallel but outputs SQL sequentially (no interleaving)

#### Scenario: No connection required
- **WHEN** user runs `sql-unit compile` without any database configured
- **THEN** system completes successfully without attempting database connection

#### Scenario: Redirect compile output to file
- **WHEN** user runs `sql-unit compile > output.sql`
- **THEN** system writes all compiled SQL to the file

### Requirement: run command for test execution
The system SHALL provide a `sql-unit run` command to execute tests.

#### Scenario: Run all tests
- **WHEN** user runs `sql-unit run`
- **THEN** system discovers and executes all tests

#### Scenario: Select by test name
- **WHEN** user runs `sql-unit run -s test_user_login`
- **THEN** system runs only the test with that exact name

#### Scenario: Select by glob pattern
- **WHEN** user runs `sql-unit run -s "user_*"`
- **THEN** system runs only tests matching the glob pattern

#### Scenario: Select by file
- **WHEN** user runs `sql-unit run -s tests/users/auth_test.sql`
- **THEN** system runs tests only from that specific file

#### Scenario: Select by folder
- **WHEN** user runs `sql-unit run -s tests/integration/`
- **THEN** system runs tests from all .sql files in that directory and subdirectories

#### Scenario: Multiple selectors (union)
- **WHEN** user runs `sql-unit run -s test_login -s "admin_*" -s tests/regression/`
- **THEN** system runs tests matching any of the selectors (union)

#### Scenario: Test execution summary
- **WHEN** tests complete execution
- **THEN** system displays summary: X passed, Y failed, Z skipped, duration

#### Scenario: Verbose output
- **WHEN** user runs `sql-unit run --verbose`
- **THEN** system shows SQL statements, setup details, and assertion information

#### Scenario: Exit code on success
- **WHEN** all tests pass
- **THEN** command exits with code 0

#### Scenario: Exit code on failure
- **WHEN** one or more tests fail
- **THEN** command exits with code 1

#### Scenario: Exit code on error
- **WHEN** configuration or setup error occurs
- **THEN** command exits with code 2

### Requirement: Parallel test execution
The system SHALL support running tests in parallel for faster execution.

#### Scenario: Sequential execution (default)
- **WHEN** user runs `sql-unit run --threads 1` with explicit single threaded execution
- **THEN** tests execute sequentially

#### Scenario: Parallel execution
- **WHEN** user runs `sql-unit run --threads -1`
- **THEN** tests execute using maximum worker count

#### Scenario: Parallel worker count
- **WHEN** user runs `sql-unit run --threads 4`
- **THEN** system uses exactly 4 worker threads

#### Scenario: Output ordering in parallel mode
- **WHEN** tests run in parallel
- **THEN** output is not garbled (results are buffered and written atomically)

#### Scenario: Test isolation in parallel
- **WHEN** multiple tests with same temp table name run in parallel
- **THEN** tests don't interfere (names are unique per test)

#### Scenario: Connection pool management
- **WHEN** parallel tests execute
- **THEN** database connections are properly pooled and isolated

### Requirement: Output formatting
The system SHALL support multiple output formats for different use cases.

#### Scenario: Human-readable output
- **WHEN** user runs `sql-unit run` (default)
- **THEN** system displays formatted table with test results (✓ pass, ✗ fail)

#### Scenario: JSON output format
- **WHEN** user runs `sql-unit run --format=json`
- **THEN** system outputs valid JSON with test results, durations, and errors

#### Scenario: Color output for terminal
- **WHEN** output is to a terminal
- **THEN** system uses colors (green for pass, red for fail)

#### Scenario: No color output for piped output
- **WHEN** output is piped to a file or another command
- **THEN** system disables colors automatically

#### Scenario: Result details in JSON
- **WHEN** test fails
- **THEN** JSON output includes full error message and assertion details

### Requirement: CLI usability
The system SHALL provide clear help and error messages.

#### Scenario: Help command
- **WHEN** user runs `sql-unit --help`
- **THEN** system displays usage information and available commands

#### Scenario: Help for specific command
- **WHEN** user runs `sql-unit run --help`
- **THEN** system displays command-specific options and examples

#### Scenario: Version display
- **WHEN** user runs `sql-unit --version`
- **THEN** system displays current version

#### Scenario: Invalid arguments
- **WHEN** user provides invalid command line arguments
- **THEN** system displays error message and suggests correct usage

#### Scenario: Missing required database
- **WHEN** test execution requires database but none configured
- **THEN** system displays clear error: "Database connection required"

### Requirement: Connection specification via CLI
The system SHALL support specifying database connections via `--connection` flag.

#### Scenario: CLI connection without config file
- **WHEN** user runs `sql-unit run --connection "sqlite:///test.db"` (no sql-unit.yaml)
- **THEN** system discovers all .sql files recursively in CWD and uses provided connection

#### Scenario: CLI connection overrides config
- **WHEN** user runs `sql-unit run --connection "postgres://prod"` (sql-unit.yaml exists)
- **THEN** system uses CLI connection, ignoring any connection in config file

#### Scenario: Connection precedence
- **WHEN** both config connection and `--connection` flag are provided
- **THEN** CLI `--connection` takes precedence

#### Scenario: No connection provided
- **WHEN** no sql-unit.yaml exists and no `--connection` flag provided
- **THEN** system reports error with guidance on creating config or providing CLI connection

#### Scenario: Connection with environment variables
- **WHEN** `--connection` contains `${VAR}` syntax
- **THEN** system substitutes with environment variable values (via config system)

### Requirement: Test selection with --select
The system SHALL support granular test filtering via `-s/--select` flag.

#### Scenario: Select without config paths restriction
- **WHEN** user runs `sql-unit run --connection "..." -s "tests/auth/*"`
- **THEN** system filters from all discovered .sql files in CWD using glob pattern

#### Scenario: Default test discovery scope
- **WHEN** user runs with `--connection` and no `--select`
- **THEN** system discovers all .sql files recursively in CWD (implicit `**/*`)

#### Scenario: Select patterns with config paths
- **WHEN** config specifies `test_paths: ["tests/"]` and user provides `-s "auth/*"`
- **THEN** system discovers tests only in test_paths, then filters by pattern

#### Scenario: Multiple select filters (union)
- **WHEN** user runs `sql-unit run -s "tests/auth/*" -s "*_integration_*" -s tests/db/`
- **THEN** system unifies results from all selectors
