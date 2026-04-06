# expectations Specification

## Purpose
TBD - created by archiving change p1-sql-unit-expectations. Update Purpose after archive.
## Requirements
### Requirement: Row equality expectation in expect section
The system SHALL support `rows_equal` expectation in the `expect:` section to validate query results.

#### Scenario: rows_equal with rows data source
- **WHEN** test specifies `expect: [{rows_equal: {rows: [{id: 1, name: "Alice"}]}}]`
- **THEN** system validates query output matches the specified rows

#### Scenario: Exact row match
- **WHEN** query returns rows matching expected data exactly
- **THEN** test passes

#### Scenario: Row mismatch detected
- **WHEN** query returns different rows than expected
- **THEN** test fails with detailed diff showing differences

#### Scenario: Order-independent comparison
- **WHEN** expected and actual rows are in different order
- **THEN** test passes (rows compared by value, not position)

#### Scenario: Column order independence
- **WHEN** expected and actual rows have columns in different order
- **THEN** test passes (columns compared by name, not position)

#### Scenario: Column name case insensitivity
- **WHEN** query returns column names in different case
- **THEN** column comparison is case-insensitive

#### Scenario: Row count mismatch
- **WHEN** expected has N rows but query returns M rows (N ≠ M)
- **THEN** test fails showing actual vs expected count

#### Scenario: NULL handling in comparison
- **WHEN** expected data includes NULL and query returns NULL
- **THEN** NULL values are considered equal

#### Scenario: NULL vs non-NULL mismatch
- **WHEN** expected has NULL but query returns actual value
- **THEN** test fails indicating NULL mismatch

#### Scenario: Data type translation from SQL to Python
- **WHEN** database returns column with SQL type (e.g., INTEGER, VARCHAR, BOOLEAN, DECIMAL)
- **THEN** system parses values into Python native types (int, str, bool, float)
- **AND** Python native types are compared in unit test expectations

#### Scenario: Omitted column is ignored
- **WHEN** expected data omits a column present in query result
- **THEN** column is excluded from comparison (comparison ignores extra columns)

### Requirement: Expected data formats in rows_equal
The system SHALL support three formats for specifying expected rows: rows, CSV, and SQL.

#### Scenario: Expected rows as YAML list
- **WHEN** rows_equal specifies `rows: [{id: 1, name: "Alice"}]`
- **THEN** expected data is loaded from YAML list of dicts

#### Scenario: Expected rows as CSV
- **WHEN** rows_equal specifies `csv: | id,name\n1,Alice\n2,Bob`
- **THEN** CSV is parsed (first row = headers, remaining = data)

#### Scenario: Expected rows from SQL query
- **WHEN** rows_equal specifies `sql: | SELECT ...`
- **THEN** query is executed and result set becomes expected data

#### Scenario: Empty result validation
- **WHEN** rows_equal is specified with zero rows expected
- **THEN** test passes if query returns no rows

### Requirement: Comparison output and diagnostics
The system SHALL provide clear diff output when rows_equal fails.

#### Scenario: Diff shows missing rows
- **WHEN** expected data has rows not in query result
- **THEN** diff clearly marks these as missing

#### Scenario: Diff shows extra rows
- **WHEN** query result has rows not in expected data
- **THEN** diff clearly marks these as unexpected

#### Scenario: Diff shows column value mismatch
- **WHEN** row exists in both but column values differ
- **THEN** diff shows the expected vs actual values side-by-side

#### Scenario: Diff includes row position
- **WHEN** rows_equal fails
- **THEN** diff indicates which rows matched and which didn't for easier debugging

#### Scenario: Partial match indication
- **WHEN** some rows match and others don't
- **THEN** diff clearly shows count of matching vs non-matching rows

### Requirement: Pandas-based comparison
The system SHALL use pandas DataFrames for robust row comparison.

#### Scenario: DataFrame sorting for comparison
- **WHEN** comparing result sets
- **THEN** both expected and actual are sorted by all columns alphabetically for consistent comparison

#### Scenario: Float precision from config
- **WHEN** sql-unit.yaml specifies `float_precision: N`
- **THEN** floating-point comparison uses tolerance of 10^(-N) for equality

#### Scenario: Float precision default
- **WHEN** sql-unit.yaml does not specify float_precision
- **THEN** system applies reasonable default tolerance (e.g., 1e-10)

#### Scenario: Datetime normalization
- **WHEN** comparing datetime values
- **THEN** system normalizes to same precision before comparison

#### Scenario: Pandas assert output
- **WHEN** rows_equal assertion fails
- **THEN** error message includes pandas assertion output for clarity
