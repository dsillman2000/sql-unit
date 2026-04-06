## Context

Building on Phase 1 Complete (all three Phase 1 changes), this phase adds temp_table input type. Temporary tables require more complex database operations than CTEs: actual table creation, population, and cleanup. This phase handles database-specific syntax and provides strong test isolation.

Key constraints:
- Depends on Phase 1 Complete
- Must support multiple database syntaxes (PostgreSQL, MySQL, SQLite)
- Tables must be cleaned up after test completion
- Must handle concurrent/parallel test execution safely

## Goals / Non-Goals

**Goals:**
- Implement temp_table input type
- Support schema-qualified table names
- Auto-create and auto-cleanup tables
- Handle database-specific DDL/DML
- Support all data formats (sql, csv, rows)

**Non-Goals:**
- Persistent table creation (temporary only)
- Table schema inference (structures via data only)

## Decisions

### Decision 1: Database-Specific Implementations

**Choice**: Support temp_table with database-specific implementations

**Rationale**:
- Different databases have different temp table syntax
- PostgreSQL: `CREATE TEMPORARY TABLE`
- MySQL: `CREATE TEMPORARY TABLE`
- SQLite: Regular tables with cleanup
- Necessary for true multi-database support

**Alternatives considered**:
- Abstraction layer → Adds complexity
- Single syntax → Limits database support

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Parallel test execution conflicts** → Multiple tests creating same table name | Use unique table names per test or database connection isolation |
| **Database-specific syntax errors** → DDL differs across databases | Test thoroughly on each database; clear error messages |

## Migration Plan

Phase 2 Temp Tables:
1. Design temp table abstraction
2. Implement PostgreSQL support
3. Implement MySQL support
4. Implement SQLite support
5. Create comprehensive tests
6. Add database-specific documentation

## Open Questions

- Should temp table names be prefixed with test name for debugging?
- Should schema be inferred from data or explicitly specified?
