## Context

Building on Phases 1 and 2 (complete implementation of sql-unit), Phase 3 creates a comprehensive test suite for the library itself. This ensures sql-unit works correctly across different databases, use cases, and edge cases. The test suite includes unit tests, integration tests, and performance benchmarks.

Key constraints:
- Depends on Phases 1 and 2 Complete
- Must test against PostgreSQL, MySQL, SQLite
- Must use Docker containers for test databases
- Must achieve 90%+ code coverage
- Must be maintainable and extensible
- Must run in CI/CD pipelines

## Goals / Non-Goals

**Goals:**
- Comprehensive unit test coverage (90%+)
- Integration tests for full workflows
- Multi-database testing (PostgreSQL, MySQL, SQLite)
- Performance benchmarks
- Test fixtures and helpers for reusability
- CI/CD-ready test execution
- Clear test documentation

**Non-Goals:**
- Stress testing or load testing
- Security testing
- Accessibility testing
- GUI/UI testing

## Decisions

### Decision 1: Test Framework

**Choice**: Use pytest as test framework

**Rationale**:
- Industry standard for Python
- Good fixture/plugin support
- Easy parametrization for multi-database testing
- Rich assertions
- Great CI/CD integration

**Alternatives considered**:
- unittest → More verbose
- nose2 → Older, less popular

### Decision 2: Database Test Environment

**Choice**: Use Docker containers (testcontainers) for test databases

**Rationale**:
- Isolated test environment per test run
- No pre-configured databases required
- Reproducible across machines/CI
- Automatic cleanup
- Test-specific database setup

**Alternatives considered**:
- Pre-configured test databases → Manual setup required
- SQLite only → Can't test multi-database compatibility
- Mocking databases → Doesn't test real database interactions

### Decision 3: Test Organization

**Choice**: Organize by module/feature with separate unit/integration/performance directories

**Rationale**:
- Clear separation of concerns
- Easy to run subset of tests
- Follows common patterns
- Supports different execution profiles

**Alternatives considered**:
- Monolithic test file → Unwieldy
- Test file per source file → Fine-grained but scattered

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Slow test suite** → Docker startup overhead | Cache containers; use parallel execution; separate fast/slow tests |
| **Flaky tests** → Database state issues | Proper cleanup; transaction isolation; idempotent tests |
| **Test maintenance burden** → Large test suite | Focus on critical paths; parametrize common patterns |
| **Coverage gaps** → Edge cases untested | Regular coverage analysis; target 90%+ coverage |

## Migration Plan

Phase 3 Testing:
1. Setup test infrastructure (pytest, testcontainers, fixtures)
2. Create test database fixtures (PostgreSQL, MySQL, SQLite)
3. Write unit tests for parser/renderer
4. Write unit tests for input types (CTE, relation, temp_table)
5. Write unit tests for expectations (rows_equal)
6. Write integration tests for full workflows
7. Write CLI tests
8. Write configuration tests
9. Add performance benchmarks
10. Measure and report coverage
11. Add test documentation

## Open Questions

- Should test databases run in containers or use pre-configured instances?
- Should performance benchmarks track results over time?
- Should coverage reports be published (e.g., Codecov)?
- How many concurrent tests should run? (trade-off: speed vs. resource usage)
