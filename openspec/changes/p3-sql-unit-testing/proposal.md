## Why

Phases 1 and 2 implement the full SQL Unit testing framework with core execution, inputs, expectations, temp tables, CLI, and configuration. Phase 3 focuses on the sql-unit library itself - a comprehensive test suite ensuring reliability and correctness. This phase tests:
- Core parser and renderer
- Input setup (CTE, relation, temp_table)
- Expectation validation (rows_equal)
- Database integrations (PostgreSQL, MySQL, SQLite)
- CLI functionality
- Configuration management

## What Changes

- **Test suite structure** - Organized by module/capability
- **Fixture and helper setup** - Reusable test utilities
- **Database test containers** - Docker-based test databases
- **Integration tests** - Full workflow testing
- **Performance benchmarks** - Ensure acceptable performance
- **Test coverage** - Target 90%+ coverage

## Capabilities

### New Capabilities

- `sql-unit-test-suite`: Comprehensive test suite for sql-unit library with unit, integration, and performance tests

## Impact

- **Reliability** - Ensure sql-unit works correctly across databases and use cases
- **Maintainability** - Tests document expected behavior
- **Performance** - Benchmarks ensure no regressions
- **Quality assurance** - CI/CD gate for all changes
