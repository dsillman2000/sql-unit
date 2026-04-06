## ADDED Requirements

### Requirement: Temporary table input type
The system SHALL support `temp_table` input type to create temporary tables for test data isolation.

#### Scenario: Temp table creation and cleanup
- **WHEN** test specifies `temp_table:` input
- **THEN** table is created before test execution and dropped after

#### Scenario: Temp table populated with SQL
- **WHEN** temp_table uses `sql:` data source with SELECT statement
- **THEN** table is created with schema from SELECT and populated with results

#### Scenario: Temp table populated with CSV
- **WHEN** temp_table uses `csv:` data source
- **THEN** schema is inferred from CSV headers and data is loaded

#### Scenario: Temp table populated with rows
- **WHEN** temp_table uses `rows:` data source
- **THEN** table is created from row structure and populated with data

#### Scenario: Schema-qualified table name
- **WHEN** temp_table specifies name like `myschema.mytable`
- **THEN** table is created in the specified schema

#### Scenario: Multiple temp tables in single test
- **WHEN** test specifies multiple `temp_table:` inputs
- **THEN** all tables are created and cleaned up properly

#### Scenario: Temp table in concurrent execution
- **WHEN** multiple tests use same temp table name in parallel
- **THEN** table names are uniquely prefixed to prevent conflicts

#### Scenario: Cleanup on test failure
- **WHEN** test fails during execution
- **THEN** temp table is still cleaned up before next test

#### Scenario: Cleanup on setup failure
- **WHEN** temp table creation fails (e.g., syntax error)
- **THEN** system rolls back and reports setup error

### Requirement: Database-specific DDL support
The system SHALL support temp table creation on PostgreSQL, MySQL, and SQLite.

#### Scenario: PostgreSQL temporary table
- **WHEN** using PostgreSQL database
- **THEN** system uses `CREATE TEMPORARY TABLE` syntax

#### Scenario: MySQL temporary table
- **WHEN** using MySQL database
- **THEN** system uses `CREATE TEMPORARY TABLE` syntax

#### Scenario: SQLite temporary table
- **WHEN** using SQLite database
- **THEN** system creates regular table with cleanup via DROP TABLE

#### Scenario: Data type mapping per database
- **WHEN** creating temp table on specific database
- **THEN** column data types are mapped correctly to database dialect

#### Scenario: Database error handling
- **WHEN** temp table creation fails on database (e.g., invalid column type)
- **THEN** system reports error with database-specific message

### Requirement: Temp table isolation
The system SHALL ensure temp tables provide proper test isolation.

#### Scenario: Temp table not visible to other tests
- **WHEN** test A creates temp table and test B runs
- **THEN** test B cannot access test A's temp table

#### Scenario: No data persistence
- **WHEN** temp table is created and populated in test
- **THEN** data is not visible in permanent schema after cleanup

#### Scenario: Transaction isolation
- **WHEN** test creates temp table within transaction
- **THEN** transaction rollback also removes temp table

#### Scenario: Connection isolation
- **WHEN** temp tables are created per-connection
- **THEN** different test connections don't see each other's temp tables

### Requirement: Temp table performance considerations
The system SHALL document and manage temp table performance characteristics.

#### Scenario: Large dataset temp table
- **WHEN** temp table is created with 100k+ rows
- **THEN** creation completes in reasonable time and test executes

#### Scenario: Multiple temp table creation
- **WHEN** test creates many temp tables sequentially
- **THEN** cumulative creation time is acceptable for typical tests

#### Scenario: Index creation on temp table
- **WHEN** temp table is created with indexes
- **THEN** indexes are created and used for query performance

#### Scenario: Cleanup performance
- **WHEN** temp table is dropped after test
- **THEN** cleanup completes quickly regardless of table size
