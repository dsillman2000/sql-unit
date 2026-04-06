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

#### Scenario: Multi-doc syntax (--- separator)
- **WHEN** doc comment contains multiple YAML documents separated by `---`
- **THEN** system parses all documents and returns as ordered list of tests

#### Scenario: Multi-doc with named tests
- **WHEN** multi-doc syntax contains `name:` in each document
- **THEN** system uses specified names for each test

#### Scenario: Sequence syntax (YAML list)
- **WHEN** doc comment contains a YAML list (tests prefixed with `-`)
- **THEN** system parses list and returns as ordered list of tests

#### Scenario: Sequence syntax with !reference-all
- **WHEN** doc comment contains `!reference-all` tag returning test sequence
- **THEN** system expands reference and includes tests in output list

#### Scenario: Project boundary requirement
- **WHEN** test discovery is initiated
- **THEN** system searches for `sql-unit.yaml` file in directory tree
- **AND** if no `sql-unit.yaml` found, system raises DiscoveryError with message: "sql-unit.yaml not found. Please create one to define the sql-unit project scope."

#### Scenario: Project root from sql-unit.yaml location
- **WHEN** `sql-unit.yaml` is found in project directory
- **THEN** that directory is designated as the sql-unit project root
- **AND** all path resolutions for `!reference` tags use this project root as anchor

#### Scenario: YAML reference with relative path
- **WHEN** doc comment contains `!reference-all "fixtures/tests.yaml"`
- **AND** file `fixtures/tests.yaml` exists relative to project root
- **THEN** system resolves reference and includes tests from that file

#### Scenario: YAML reference from nested subdirectory
- **WHEN** SQL file is in subdirectory `cte/` containing `!reference-all "fixtures/tests.yaml"`
- **AND** project root is parent of `cte/` and contains `fixtures/` subdirectory
- **THEN** system resolves reference to `project_root/fixtures/tests.yaml` regardless of SQL file location

#### Scenario: YAML reference with parent directory traversal
- **WHEN** SQL file contains `!reference-all "../references/tests.yaml"`
- **AND** path resolves within project root and within allow_paths
- **THEN** system allows reference if within allowed scope

#### Scenario: YAML reference outside allow_paths
- **WHEN** SQL file contains `!reference-all "../../external/tests.yaml"`
- **AND** path would escape project root or violates allow_paths configuration
- **THEN** system raises ParserError with message indicating path is outside allowed scope

#### Scenario: Circular reference detection
- **WHEN** file A references file B and file B references file A
- **THEN** system raises ParserError indicating circular dependency

#### Scenario: Missing referenced file
- **WHEN** doc comment contains `!reference-all "missing_fixtures.yaml"`
- **AND** file does not exist at resolved path
- **THEN** system raises ParserError with message indicating file not found at expected location

#### Scenario: Invalid YAML in referenced file
- **WHEN** referenced file contains invalid YAML syntax
- **THEN** system raises ParserError with message indicating YAML syntax error in referenced file

#### Scenario: allow_paths configuration in sql-unit.yaml
- **WHEN** sql-unit.yaml contains configuration block with `allow_paths: [fixtures/, references/]`
- **THEN** only paths under those directories (relative to project root) are allowed for `!reference` tags
- **AND** defaults to project root if not specified

#### Scenario: Multiple references in single doc comment
- **WHEN** doc comment contains multiple `!reference-all` tags or `!reference` tags
- **THEN** system resolves all references and combines results into single test list

#### Scenario: Empty referenced file
- **WHEN** referenced file exists but contains no valid YAML documents
- **THEN** system returns empty list (no tests from that file)

### Requirement: Path resolution and project scope
- **WHEN** doc comment contains both `---` separators and list items
- **THEN** system raises ParseError indicating mutually exclusive syntax

#### Scenario: Auto-naming for unnamed tests
- **WHEN** test in multi-doc or sequence lacks explicit `name:`
- **THEN** system generates name based on position (e.g., `test_1`, `test_2`) or file context

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
The system SHALL support optional Jinja2 templating in SQL statements for conditional logic, loops, and filters. Jinja rendering occurs before relation substitution.

#### Scenario: Simple Jinja2 expression in SQL
- **WHEN** SQL contains `{{ variable_name }}`
- **THEN** system renders template using variables from `given` section (jinja_context and scalar values)

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

#### Scenario: Jinja rendering precedes relation substitution
- **WHEN** test execution proceeds through rendering and substitution phases
- **THEN** Jinja templates are rendered first (producing concrete SQL), followed by relation substitutions applied to the rendered output

#### Scenario: Jinja variable bound to identifier from jinja_context
- **WHEN** SQL contains `{{ table_name }}` and `table_name` is bound to a data source identifier in jinja_context
- **THEN** variable is substituted with the actual CTE or table identifier name

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
