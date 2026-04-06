## ADDED Requirements

### Requirement: CTE (Common Table Expression) input in given section
The system SHALL support `cte` input type in the `given:` section to inject Common Table Expressions.

#### Scenario: Single CTE definition
- **WHEN** test specifies `given: [cte: {targets: [...], rows: [...]}]`
- **THEN** CTE definition is created and injected as WITH clause before main query

#### Scenario: CTE with targets field
- **WHEN** CTE specifies `targets: ["db.schema.users"]`
- **THEN** CTE name is derived from target (sanitized: dots → underscores)

#### Scenario: CTE with rows data source
- **WHEN** CTE uses `rows: [{id: 1, name: "Alice"}]`
- **THEN** rows are converted to VALUES clause in CTE definition

#### Scenario: Multiple CTEs in single test
- **WHEN** test includes multiple `cte:` items in `given:` list
- **THEN** all CTEs are injected as a single WITH clause with proper comma separation

#### Scenario: CTE injection into query
- **WHEN** CTEs are defined in given section
- **THEN** main query can reference CTE names as if they were tables

### Requirement: Relation (table substitution) input in given section
The system SHALL support `relation` input type in `given:` section to substitute table references in the query.

#### Scenario: Simple table reference substitution
- **WHEN** test specifies `given: [{relation: {targets: ["source_table"], replacement: "test_table"}}]`
- **THEN** all occurrences of "source_table" in the query are replaced with "test_table"

#### Scenario: Multiple table substitutions
- **WHEN** test specifies multiple relation items in `given:`
- **THEN** all substitutions are applied in sequence

#### Scenario: Case-insensitive matching
- **WHEN** query references table in different case
- **THEN** system performs case-insensitive matching

### Requirement: Input data sources (sql, csv, rows)
The system SHALL support three formats for specifying test data: sql, csv, and rows.

#### Scenario: SQL as data source
- **WHEN** CTE or relation uses `sql: | SELECT ...`
- **THEN** system executes the SELECT query and uses result as data

#### Scenario: CSV as data source
- **WHEN** input uses `csv: | id,name\n1,Alice\n2,Bob`
- **THEN** first row is column headers, remaining rows are data

#### Scenario: Rows list as data source
- **WHEN** input uses `rows: [{id: 1, name: "Alice"}, {id: 2, name: "Bob"}]`
- **THEN** list of dicts becomes test data, keys are column names

#### Scenario: Data type preservation
- **WHEN** row data contains mixed types (strings, numbers, booleans, null)
- **THEN** system preserves original types

#### Scenario: NULL value handling
- **WHEN** CSV contains empty cells or rows contain null
- **THEN** empty/null values are treated as SQL NULL

### Requirement: Test data lifecycle
The system SHALL properly set up and manage test data for each test execution.

#### Scenario: Given section processing
- **WHEN** test includes `given:` section with input definitions
- **THEN** system processes all items sequentially to prepare test data

#### Scenario: Data isolation per test
- **WHEN** one test executes with given section
- **THEN** test data is isolated (doesn't affect other tests)

#### Scenario: No side effects on permanent schema
- **WHEN** test uses CTEs or temporary table substitutions
- **THEN** no permanent changes are made to database
