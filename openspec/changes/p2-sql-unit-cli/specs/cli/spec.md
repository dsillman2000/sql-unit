## ADDED Requirements

### Requirement: list command for test discovery
The system SHALL provide a `sql-unit list` command to discover and display available tests.

#### Scenario: List all tests
- **WHEN** user runs `sql-unit list`
- **THEN** system displays all discovered tests with names and paths

#### Scenario: Test discovery in current directory
- **WHEN** user runs `sql-unit list` from project root
- **THEN** system recursively finds all .sql files with @unit tests

#### Scenario: List output format
- **WHEN** tests are discovered
- **THEN** output includes test name, file path, and test count

#### Scenario: Filter by directory
- **WHEN** user runs `sql-unit list --directory tests/`
- **THEN** system lists only tests in that directory

#### Scenario: Filter by test name pattern
- **WHEN** user runs `sql-unit list --name "user*"`
- **THEN** system lists only tests matching the pattern

#### Scenario: Filter by tags
- **WHEN** user runs `sql-unit list --tags "integration,slow"`
- **THEN** system lists only tests with matching tags

#### Scenario: JSON output format
- **WHEN** user runs `sql-unit list --format=json`
- **THEN** system outputs valid JSON with test metadata

#### Scenario: No tests found
- **WHEN** user runs list with filter that matches no tests
- **THEN** system reports "No tests found" clearly

### Requirement: run command for test execution
The system SHALL provide a `sql-unit run` command to execute tests.

#### Scenario: Run all tests
- **WHEN** user runs `sql-unit run`
- **THEN** system discovers and executes all tests

#### Scenario: Run specific test
- **WHEN** user runs `sql-unit run --name "test_user_login"`
- **THEN** system runs only that test

#### Scenario: Run tests in directory
- **WHEN** user runs `sql-unit run --directory tests/users/`
- **THEN** system runs all tests in that directory

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
- **WHEN** user runs `sql-unit run` without parallel flag
- **THEN** tests execute sequentially

#### Scenario: Parallel execution
- **WHEN** user runs `sql-unit run --parallel`
- **THEN** tests execute using multiple workers (default: CPU count)

#### Scenario: Parallel worker count
- **WHEN** user runs `sql-unit run --parallel 4`
- **THEN** system uses exactly 4 worker processes

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
