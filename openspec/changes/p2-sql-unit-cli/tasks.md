# Tasks for p2-sql-unit-cli

## Prerequisite: Phase 1 Complete
- All p1-sql-unit-core, p1-sql-unit-inputs, p1-sql-unit-expectations changes must be complete

## Capability 1: cli-list - Test Discovery

### CLI Framework Setup
- [ ] Install Click dependency
- [ ] Create cli module/package
- [ ] Implement main entry point (sql-unit command)
- [ ] Add --help and --version flags

### list Command Implementation
- [ ] Implement list command structure
- [ ] Implement test discovery
  - Scan for .sql unit files
  - Parse unit metadata (title, tags, etc.)
  - Build test registry
- [ ] Implement filtering options
  - --directory/-d filter (single directory)
  - --name/-n filter (test name pattern)
  - --tags/-t filter (comma-separated tags)
  - Support combining filters (AND logic)
- [ ] Implement output formatting
  - Human-readable (one line per test with name and path)
  - JSON output (--format=json)
- [ ] Implement sorting
  - Sort by test name
  - Sort by directory
  - Support --sort-by flag

### Testing for list Command
- [ ] Unit tests for test discovery
- [ ] Unit tests for filtering logic
- [ ] Unit tests for output formatting
- [ ] Integration tests with sample test files
- [ ] Test edge cases (no tests found, invalid filters, etc.)

## Capability 2: cli-run - Test Execution

### run Command Implementation
- [ ] Implement run command structure
- [ ] Implement filtering options (same as list)
  - --directory/-d
  - --name/-n
  - --tags/-t
- [ ] Implement execution modes
  - Default: run all discovered tests
  - Filtered: run matching tests
  - Single test: run specific test
- [ ] Implement output options
  - Human-readable format (test name, pass/fail, time)
  - JSON format (--format=json)
  - Verbose output (--verbose/-v)
    - Show SQL statements executed
    - Show input setup details
    - Show expectation details
- [ ] Implement result aggregation
  - Count passed/failed/skipped tests
  - Total execution time
  - Summary report

### Parallel Execution Support
- [ ] Implement --threads/-j flag
  - Default: sequential execution
  - Value: number of workers (optional, defaults to CPU count)
- [ ] Implement test queue and worker pool
  - Use multiprocessing.Pool or concurrent.futures
  - Distribute tests to workers
  - Collect results from workers
- [ ] Implement output synchronization
  - Queue-based result collection
  - Write results atomically per test
  - Prevent output garbling
- [ ] Implement resource management
  - Limit concurrent database connections
  - Document connection pool configuration
  - Add warnings for high worker counts

### Exit Codes
- [ ] Implement exit code handling
  - 0: All tests passed
  - 1: One or more tests failed
  - 2: Invalid arguments or configuration error
- [ ] Implement error handling for:
  - Missing test files
  - Invalid configuration
  - Database connection failures
  - Test execution exceptions

### Testing for run Command
- [ ] Unit tests for command parsing
- [ ] Unit tests for filtering logic
- [ ] Unit tests for output formatting
- [ ] Integration tests with sample tests
  - Run and verify results
  - Test filter combinations
  - Test parallel execution
- [ ] Integration tests for exit codes
  - All pass → exit 0
  - Some fail → exit 1
  - Invalid args → exit 2
- [ ] Test edge cases
  - No matching tests
  - Database connection failures
  - Malformed test files

## Capability 3: Output Formatting

### Human-Readable Output
- [ ] Implement formatted table output
  - Column headers: Test Name | Status | Time | Location
  - Status symbols: ✓ (pass), ✗ (fail), ⊘ (skip)
  - Color output (green/red) if terminal supports it
- [ ] Implement summary output
  - Line: "X passed, Y failed, Z skipped in T seconds"
- [ ] Implement detailed output (--verbose)
  - Show SQL statements
  - Show input setup
  - Show expectation details
  - Show assertion failures

### JSON Output
- [ ] Implement JSON schema for results
  - test_name (string)
  - status (pass|fail|skip)
  - duration_ms (integer)
  - path (string)
  - error_message (string, if failed)
  - details (object with sql, inputs, expectations for verbose)
- [ ] Implement JSON aggregation
  - List of test results
  - Summary object
  - Metadata (tool version, timestamp, etc.)
- [ ] Validate JSON output with test
  - Parse output as JSON
  - Verify schema

### Testing for Output Formatting
- [ ] Test human-readable formatting
  - Verify column alignment
  - Verify symbols
  - Test color codes (if applicable)
- [ ] Test JSON formatting
  - Parse output as valid JSON
  - Verify schema compliance
  - Test with various test outcomes
- [ ] Test verbose output
  - Verify SQL display
  - Verify input details
  - Verify expectation details

## CLI Integration & Documentation

### Error Handling & Messages
- [ ] Implement user-friendly error messages
  - Configuration errors
  - Database connection errors
  - Test execution errors
- [ ] Implement help text for all commands
- [ ] Implement example usage in help

### Testing
- [ ] End-to-end CLI tests
  - Run list command and verify output
  - Run tests and verify results
  - Run with filters and verify
  - Run with parallel and verify
- [ ] Test all command flags
- [ ] Test error scenarios

### Documentation
- [ ] Add CLI usage documentation
  - list command with examples
  - run command with examples
  - Filtering examples
  - Output format examples
  - Parallel execution examples
- [ ] Add troubleshooting section
- [ ] Add CI/CD integration examples
