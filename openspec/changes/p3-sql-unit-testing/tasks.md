# Tasks for p3-sql-unit-testing

## Prerequisite: Phase 1 and Phase 2 Complete
- All p1-sql-unit-core, p1-sql-unit-inputs, p1-sql-unit-expectations changes must be complete
- All p2-sql-unit-temp-tables, p2-sql-unit-cli, p2-sql-unit-config changes must be complete

## Test Infrastructure Setup

### Testing Framework & Dependencies
- [ ] Install pytest, pytest-cov, pytest-xdist
- [ ] Install testcontainers library
- [ ] Install pytest plugins
  - pytest-timeout (prevent hanging tests)
  - pytest-mock (mocking support)
- [ ] Create tests/ directory structure
  - tests/unit/
  - tests/integration/
  - tests/performance/
  - tests/fixtures/
  - conftest.py (root fixtures)

### Test Database Fixtures
- [ ] Create PostgreSQL test container fixture
  - Image: postgres:15 (or latest stable)
  - Auto-cleanup after test
  - Customizable database name/user/password
  - Wait for readiness
- [ ] Create MySQL test container fixture
  - Image: mysql:8 (or latest stable)
  - Auto-cleanup after test
  - Customizable database name/user/password
  - Wait for readiness
- [ ] Create SQLite test container fixture
  - In-memory database per test
  - Auto-cleanup
- [ ] Create multi-database fixture
  - Parametrize tests to run on all three databases
  - Single test code, multiple executions

### Test Utilities & Helpers
- [ ] Create SQL statement builders (for test data setup)
- [ ] Create assertion helpers
  - compare_result_sets (ignore row order)
  - assert_sql_syntax (validate SQL)
- [ ] Create temporary file helpers
- [ ] Create mock factories
  - Mock database connections
  - Mock configurations
- [ ] Create sample data generators

## Unit Tests

### Parser & Renderer Tests
- [ ] Test SQL Unit doc comment parsing
  - Valid syntax parsing
  - Invalid syntax error handling
  - Multiple tests in one file
  - Edge cases (empty sections, whitespace)
- [ ] Test statement binding
  - Variable substitution
  - Complex expressions
  - Error handling
- [ ] Test Jinja2 rendering
  - Template rendering
  - Variable substitution
  - Conditional blocks
  - Loops
- [ ] Test SQL parsing
  - Query structure extraction
  - Error handling for malformed SQL

### Input Type Tests (CTE, Relation, Temp Table)
- [ ] Test CTE input setup
  - CTE generation
  - Multiple CTEs
  - Nested CTEs
  - Error handling
- [ ] Test relation input setup
  - Schema-qualified names
  - Table name validation
  - Error handling
- [ ] Test temp_table input setup
  - Database-specific DDL generation
  - PostgreSQL specific
  - MySQL specific
  - SQLite specific
  - Schema qualification
  - Cleanup behavior
- [ ] Test input data loading
  - SQL data source parsing
  - CSV data loading
  - Row data conversion
  - Data type inference

### Expectation Tests
- [ ] Test rows_equal expectation
  - Exact row matching
  - Order-independent comparison
  - NULL handling
  - Data type coercion
  - Column name matching
- [ ] Test expectation failure messaging
  - Clear difference reporting
  - Row count mismatch messages
  - Column value mismatch messages

### Configuration Tests
- [ ] Test YAML loading
  - Valid config parsing
  - Invalid YAML error handling
  - Missing file handling
- [ ] Test environment variable substitution
  - ${VAR} syntax parsing
  - Variable validation
  - Missing variable errors
- [ ] Test database connection parsing
  - URI validation
  - Connection parameter extraction
- [ ] Test configuration validation
  - Required fields
  - Type validation
  - Path validation

### CLI Tests
- [ ] Test list command
  - Test discovery
  - Filtering by name
  - Filtering by directory
  - Filtering by tags
  - Output formatting
  - JSON output parsing
- [ ] Test run command
  - Test execution
  - Result collection
  - Exit codes (pass, fail, error)
  - Output formatting
- [ ] Test parallel execution
  - Multiple tests run concurrently
  - Result aggregation
  - Output doesn't garble
- [ ] Test CLI flags
  - --help displays help
  - --version displays version
  - --verbose shows details
  - --format selects output format
  - --threads enables parallel execution

## Integration Tests

### Full Workflow Tests
- [ ] Test complete flow: parse → setup → execute → validate
  - With CTE inputs
  - With relation inputs
  - With temp_table inputs
  - With rows_equal expectations
- [ ] Test multiple test execution
  - Run multiple tests in sequence
  - Run multiple tests in parallel
  - Verify isolation
- [ ] Test error scenarios
  - Setup failures
  - SQL execution failures
  - Expectation validation failures

### Multi-Database Tests
- [ ] Test on PostgreSQL
  - Run complete workflow
  - Test database-specific features
- [ ] Test on MySQL
  - Run complete workflow
  - Test database-specific features
- [ ] Test on SQLite
  - Run complete workflow
  - Test database-specific features

### CLI Integration Tests
- [ ] Test full CLI workflow
  - Discover tests
  - Run tests
  - Display results
  - Verify exit codes
- [ ] Test with config file
  - Load config
  - Use config database
  - Use config defaults
- [ ] Test environment variable handling
  - Substitution in config
  - Override via CLI

### End-to-End Tests
- [ ] Test with realistic SQL Unit files
  - Multiple tests per file
  - Complex setup (multiple inputs)
  - Complex validation (multiple expectations)
  - Error cases

## Performance Benchmarks

### Execution Benchmarks
- [ ] Benchmark test parsing time
  - Single file with many tests
  - Many files with single test
- [ ] Benchmark test setup time
  - CTE setup
  - Relation setup
  - Temp_table setup
- [ ] Benchmark test execution time
  - Simple queries
  - Complex queries with joins
- [ ] Benchmark test validation time
  - Small result sets
  - Large result sets

### Scalability Benchmarks
- [ ] Benchmark parallel execution
  - Measure speedup with parallel workers
  - Identify bottlenecks
- [ ] Benchmark memory usage
  - Single test memory
  - Parallel test memory
- [ ] Benchmark with large datasets
  - Large temp_table setup
  - Large expectation result sets

### Performance Documentation
- [ ] Document baseline performance metrics
- [ ] Document performance per database
- [ ] Document scalability characteristics
- [ ] Identify performance optimization opportunities

## Coverage & Quality

### Coverage Measurement
- [ ] Run coverage analysis
  - Measure line coverage
  - Measure branch coverage
  - Generate coverage reports
- [ ] Identify uncovered code paths
  - Document why (if intentional)
  - Write tests (if needed)
- [ ] Target 90%+ coverage
  - Exclude generated code
  - Exclude test utilities
- [ ] Publish coverage reports
  - Text output
  - HTML output
  - Optional: external service (Codecov)

### Test Quality
- [ ] Review test assertions
  - Each test asserts something meaningful
  - Assertions are specific
- [ ] Review test independence
  - Tests don't depend on execution order
  - Tests clean up after themselves
- [ ] Review test maintainability
  - Use fixtures to avoid duplication
  - Use parametrization for variants
  - Clear test names describing what's tested

## CI/CD Integration

### Test Execution in CI
- [ ] Configure test execution in CI pipeline
  - Run on every commit
  - Run on pull requests
  - Run on release candidates
- [ ] Setup test database containers in CI
  - Docker-in-Docker or equivalent
  - Network configuration
  - Resource limits
- [ ] Configure coverage reports in CI
  - Generate reports
  - Publish to external service (optional)
  - Fail if coverage drops below threshold

### Test Documentation
- [ ] Document how to run tests locally
  - Install test dependencies
  - Run all tests
  - Run specific test modules
  - Run with coverage
- [ ] Document test structure
  - Where to add new tests
  - Test naming conventions
  - Fixture usage patterns
- [ ] Document CI test execution
  - How tests run in CI
  - How to debug CI test failures

## Test Execution & Maintenance

### Local Test Execution
- [ ] Create test execution scripts/Makefile targets
  - make test (run all)
  - make test-unit (unit only)
  - make test-integration (integration only)
  - make test-coverage (with coverage)
- [ ] Document test environment setup
  - Python version requirements
  - Docker requirements
  - Database/external service requirements

### Test Maintenance
- [ ] Monitor test flakiness
  - Identify intermittent failures
  - Document and fix root causes
- [ ] Keep test dependencies updated
  - pytest updates
  - testcontainers updates
  - Other library updates
- [ ] Review and refactor tests periodically
  - Consolidate duplicated test code
  - Update obsolete tests
  - Improve clarity
