# Tasks for p2-sql-unit-temp-tables

## Prerequisite: Phase 1 Complete
- All p1-sql-unit-core, p1-sql-unit-inputs, and p1-sql-unit-expectations changes must be complete

## Capability 1: temp_table Input Type

### Database Abstraction Layer
- [ ] Create database adapter interface (DbAdapter) with methods for:
  - Creating temporary tables (with database-specific syntax)
  - Dropping temporary tables
  - Checking table existence
  - Getting database dialect information
- [ ] Implement PostgreSQL adapter
  - CREATE TEMPORARY TABLE support
  - Schema-qualified naming
  - Session-level table lifecycle
- [ ] Implement MySQL adapter
  - CREATE TEMPORARY TABLE support
  - Schema qualification if supported
  - Connection-scoped lifecycle
- [ ] Implement SQLite adapter
  - Regular table creation with cleanup
  - Database-specific temporary table semantics
  - Cleanup via DROP TABLE

### temp_table Input Type Implementation
- [ ] Extend InputConfig to support temp_table type
- [ ] Implement TempTableInput class
  - name field (required)
  - schema field (optional, defaults to public/default schema)
  - data field (SQL, CSV, or rows)
  - database_type field (determined from connection)
- [ ] Add temp_table parsing to given-inputs section handler
- [ ] Add temp_table validation
  - Name format validation (alphanumeric, underscores)
  - Schema name validation
  - Data format validation

### Data Loading
- [ ] Implement temp table creation from SQL data
  - Parse SQL CREATE TABLE or INSERT statements
  - Execute with database-specific adapter
- [ ] Implement temp table creation from CSV data
  - Infer schema from CSV headers
  - Handle data type inference
  - Load via CSV import or row-by-row inserts
- [ ] Implement temp table creation from rows data
  - Convert rows list to INSERT statements
  - Batch inserts efficiently
  - Handle various data types

### Cleanup and Lifecycle
- [ ] Implement automatic table cleanup after test execution
  - Track created temp tables
  - Drop tables in reverse creation order
  - Handle cleanup errors gracefully
- [ ] Implement transaction-safe cleanup
  - Cleanup in test transaction context
  - Rollback on cleanup failures
- [ ] Implement concurrent test safety
  - Generate unique table names for concurrent execution
  - Prefix table names with test ID (e.g., test_12345_tablename)
  - Document isolation guarantees

## Testing

### Unit Tests for Database Adapters
- [ ] Test PostgreSQL adapter
  - CREATE TEMPORARY TABLE execution
  - Schema-qualified table names
  - Proper cleanup
- [ ] Test MySQL adapter
  - CREATE TEMPORARY TABLE execution
  - Cleanup behavior
- [ ] Test SQLite adapter
  - Table creation
  - Cleanup behavior

### Integration Tests for temp_table Input Type
- [ ] Test temp_table with SQL data source
  - Single table creation
  - Multiple tables in single test
  - Schema-qualified names
- [ ] Test temp_table with CSV data source
  - CSV parsing and loading
  - Data type inference
  - Large datasets
- [ ] Test temp_table with rows data source
  - Row list loading
  - Multiple data types
  - NULL handling
- [ ] Test cleanup and lifecycle
  - Tables exist during test execution
  - Tables properly dropped after test
  - No orphaned tables on failures
- [ ] Test concurrent execution
  - Multiple tests with same table name execute safely
  - Unique naming prevents conflicts
- [ ] Test error handling
  - Invalid table names
  - Invalid schema names
  - Database connection failures
  - DDL/DML execution errors

### End-to-End Tests
- [ ] Test complete workflow with temp_table inputs
  - Setup, execute, cleanup cycle
  - Multiple temp tables per test
  - Complex schemas with relationships

## Documentation Updates
- [ ] Update input types documentation
  - Add temp_table input type specification
  - Show examples for SQL, CSV, rows data
  - Document schema qualification
- [ ] Add database compatibility notes
  - PostgreSQL-specific notes
  - MySQL-specific notes
  - SQLite-specific notes
- [ ] Add examples to user guide
  - Simple temp_table example
  - Complex multi-table example
  - Concurrent execution example

## Performance & Optimization
- [ ] Benchmark temp_table creation performance
  - Measure single table creation
  - Measure multi-table creation
  - Measure cleanup overhead
- [ ] Optimize batch operations
  - Batch INSERT statements when possible
  - Use connection pooling for setup/cleanup
- [ ] Document performance characteristics
  - Expected time for typical temp_table setup
  - Scalability notes
