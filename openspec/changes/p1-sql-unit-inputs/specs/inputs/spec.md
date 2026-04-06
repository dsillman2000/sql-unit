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

### Requirement: Jinja-templated SQL identifiers via jinja_context
The system SHALL support defining Jinja-templated SQL identifiers (table/CTE names) within `jinja_context` blocks in the `given:` section, enabling dynamic parameterization of identifier references throughout the query.

#### Scenario: Basic jinja_context with nested CTE
- **WHEN** test specifies `given: [{jinja_context: {my_table: {cte: {rows: [...]}}}}]`
- **THEN** Jinja variable `my_table` is bound to the CTE name and can be referenced in SQL as `{{ my_table }}`

#### Scenario: Nested temp_table in jinja_context
- **WHEN** test specifies `given: [{jinja_context: {staging: {temp_table: {sql: "SELECT ..."}}}}]`
- **THEN** Jinja variable `staging` is bound to the temporary table name for use in templates

#### Scenario: Nested data sources with explicit alias
- **WHEN** nested data source specifies `alias: "custom_name"`
- **THEN** Jinja variable is bound to the custom alias instead of a derived name

#### Scenario: Auto-generated alias for nested data source
- **WHEN** nested data source omits `alias` field
- **THEN** system generates stable alias deterministically from Jinja variable name + content hash

#### Scenario: Top-level CTE with targets (traditional style)
- **WHEN** test includes top-level `given: [{cte: {targets: [...], rows: [...]}}]`
- **THEN** CTE behaves as before: name derived from targets, no Jinja binding

#### Scenario: Scalar Jinja context values
- **WHEN** jinja_context contains non-data-source values (e.g., `start_date: "2024-01-01"`)
- **THEN** system treats as scalar string variables available for template substitution

#### Scenario: Combining top-level and Jinja-bound data sources
- **WHEN** test includes both top-level `cte:` items and `jinja_context:` items in `given:`
- **THEN** both types are processed and available; top-level sources are injected first, then Jinja context is built

#### Scenario: Multiple Jinja-bound sources in single jinja_context
- **WHEN** jinja_context contains multiple nested data sources
- **THEN** all are processed and all resulting variables are available to templates

#### Scenario: Empty jinja_context block
- **WHEN** test includes `jinja_context: {}` in given section
- **THEN** system accepts it without error (valid but no-op)

### Requirement: Jinja variable and alias naming
The system SHALL enforce deterministic, non-colliding alias derivation and provide clear error messages for naming conflicts.

#### Scenario: Jinja variable name stability
- **WHEN** same test with same Jinja variable and data is executed multiple times
- **THEN** auto-generated alias remains consistent across executions

#### Scenario: Collision detection between Jinja variable and top-level targets
- **WHEN** Jinja variable name matches a derived alias from a top-level data source's targets
- **THEN** system raises ConfigError with clear message indicating the collision

#### Scenario: User-provided alias precedence
- **WHEN** nested data source specifies explicit `alias:`
- **THEN** alias takes precedence for determining CTE/table name; targets (if present) still drives relation substitution

#### Scenario: Targets field in nested data sources
- **WHEN** nested data source includes `targets:` field
- **THEN** targets drives relation substitution patterns (string replacement in SQL) while alias determines the actual CTE/table identifier

### Requirement: Jinja template rendering order and relation substitution sequencing
The system SHALL render Jinja templates before applying relation substitutions, and enforce that relation.targets cannot contain Jinja syntax.

#### Scenario: Jinja rendering precedes relation substitution
- **WHEN** test execution proceeds through setup, rendering, and substitution phases
- **THEN** Jinja templates are rendered first (using jinja_context), producing concrete SQL; relation substitutions are applied to the rendered output

#### Scenario: Relation targets cannot contain Jinja syntax (error)
- **WHEN** relation definition specifies `targets: ["{{ jinja_var }}"]` or similar Jinja syntax
- **THEN** system raises ConfigError with guidance to move the variable into jinja_context if dynamic identifier binding is needed

#### Scenario: Jinja variable in SQL can reference Jinja-bound identifiers
- **WHEN** SQL contains `WHERE table_name = '{{ my_cte }}'` and my_cte is defined in jinja_context
- **THEN** variable is substituted with the bound identifier name and query executes correctly

### Requirement: Data source content and YAML patterns
The system SHALL forbid Jinja templating in data source content itself but allow YAML anchors and reference patterns.

#### Scenario: CSV/rows/sql content cannot be Jinja-templated (error)
- **WHEN** data source specifies `csv: "{{ template_expression }}"`
- **THEN** system treats as literal string (no template rendering); users must provide concrete data

#### Scenario: YAML anchors and aliases for DRY patterns
- **WHEN** test uses YAML anchors (e.g., `&shared_data`) and aliases (e.g., `*shared_data`)
- **THEN** system expands anchors normally; shared data blocks are duplicated as needed

### Requirement: Error handling for Jinja-templated identifiers
The system SHALL detect and report specific error cases with clear, actionable messages.

#### Scenario: Missing required Jinja variable in template
- **WHEN** SQL contains `{{ undefined_variable }}` and variable is not in jinja_context
- **THEN** system raises TemplateError indicating variable name and available context keys

#### Scenario: Jinja variable in loop with missing iterable
- **WHEN** SQL contains `{% for item in missing_list %}...{% endfor %}` and missing_list is not in jinja_context
- **THEN** system raises TemplateError indicating the missing iterable name

#### Scenario: Jinja syntax error in SQL template
- **WHEN** SQL contains malformed Jinja (e.g., `{% if condition` without closing `%}`)
- **THEN** system raises TemplateError with line/column information

#### Scenario: Nested data source with invalid content
- **WHEN** nested CTE specifies `sql: "SELECT INVALID SQL HERE"`
- **THEN** system raises SetupError during given section processing, indicating the invalid SQL

#### Scenario: Circular or redundant jinja_context definition
- **WHEN** jinja_context variable names are duplicated or self-referential
- **THEN** system raises ConfigError with clear message
