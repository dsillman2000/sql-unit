## ADDED Requirements

### Requirement: SQL Unit test doc comment format
The system SHALL parse SQL unit test definitions from SQL doc comments using the `#! sql-unit` pseudo-shebang format.

#### Scenario: Basic unit test parsing
- **WHEN** a SQL file contains `/* #! sql-unit ... */` doc comment
- **THEN** system parses and extracts the YAML test definition

#### Scenario: YAML structure with required fields
- **WHEN** doc comment contains `name:` and `given:` and `expect:` fields
- **THEN** system correctly parses all three required fields

#### Scenario: Optional description field
- **WHEN** doc comment includes `description:` field
- **THEN** system parses and stores the description

#### Scenario: Invalid YAML syntax detection
- **WHEN** doc comment contains invalid YAML
- **THEN** system raises ParseError with clear message indicating YAML syntax issue

#### Scenario: Multiple tests in single file
- **WHEN** SQL file contains multiple `/* #! sql-unit ... */` doc comments
- **THEN** system parses and returns all tests

### Requirement: Statement rendering with given section
The system SHALL process the `given` section to set up test data and render the SQL statement.

#### Scenario: Rendering with given section data
- **WHEN** test specifies `given:` with CTE definitions
- **THEN** system processes given section and prepares SQL with injected data

#### Scenario: Multiple given items
- **WHEN** test includes multiple items in `given:` list
- **THEN** system processes all items in sequence

#### Scenario: Query rendering after setup
- **WHEN** test setup is complete
- **THEN** system renders the SQL query (potentially with Jinja2 templating)

### Requirement: Jinja2 template rendering in SQL
The system SHALL support optional Jinja2 templating in SQL statements for conditional logic, loops, and filters.

#### Scenario: Simple Jinja2 expression in SQL
- **WHEN** SQL contains `{{ variable_name }}`
- **THEN** system renders template using variables from `given` section

#### Scenario: Conditional block in query
- **WHEN** SQL contains `{% if condition %}...{% endif %}`
- **THEN** system renders conditional block based on context

#### Scenario: Loop in query
- **WHEN** SQL contains `{% for item in items %}...{% endfor %}`
- **THEN** system renders loop and generates SQL

#### Scenario: Jinja2 filter usage
- **WHEN** SQL contains `{{ text | upper }}`
- **THEN** system applies filter and renders uppercase text

#### Scenario: Template syntax error
- **WHEN** SQL contains invalid Jinja2 syntax
- **THEN** system raises TemplateError with error location

### Requirement: Expectation validation
The system SHALL validate query results against expectations defined in the `expect:` section.

#### Scenario: Successful expectation validation
- **WHEN** query executes and results match expectations
- **THEN** test passes

#### Scenario: Expectation failure
- **WHEN** query results don't match expectations
- **THEN** test fails with detailed diff

#### Scenario: Multiple expectations
- **WHEN** test includes multiple items in `expect:` list
- **THEN** system validates all expectations (test passes only if all pass)

### Requirement: Core test execution lifecycle
The system SHALL execute SQL unit tests through complete lifecycle: parse → setup → execute → validate.

#### Scenario: Complete test execution flow
- **WHEN** test definition is well-formed
- **THEN** system: 1) parses YAML, 2) sets up test data from given, 3) renders SQL, 4) executes query, 5) validates against expect, 6) returns results

#### Scenario: Database connection requirement
- **WHEN** test execution is attempted without a database connection
- **THEN** system raises ExecutionError indicating missing connection

#### Scenario: Test result includes metadata
- **WHEN** test completes execution
- **THEN** result includes test name, status (pass/fail), duration, and any error messages

#### Scenario: Setup failure handling
- **WHEN** test data setup fails (e.g., CTE with invalid SQL)
- **THEN** system reports error and stops execution (doesn't attempt query execution)

#### Scenario: Query execution failure
- **WHEN** rendered SQL has syntax errors
- **THEN** system reports error with the attempted SQL statement
