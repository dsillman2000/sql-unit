## ADDED Requirements

### Requirement: sql-unit.yaml configuration file
The system SHALL support a `sql-unit.yaml` configuration file to define project-level settings.

#### Scenario: Configuration file discovery
- **WHEN** sql-unit is run from project directory
- **THEN** system automatically discovers sql-unit.yaml in current or parent directories

#### Scenario: Explicit configuration file
- **WHEN** user runs `sql-unit --config /path/to/config.yaml`
- **THEN** system uses specified configuration file

#### Scenario: Configuration file not found
- **WHEN** configuration file is not found
- **THEN** system gracefully continues with defaults (no error if optional)

#### Scenario: Configuration parsing
- **WHEN** sql-unit.yaml contains valid YAML
- **THEN** system correctly parses all configuration sections

#### Scenario: Invalid YAML syntax
- **WHEN** sql-unit.yaml contains invalid YAML
- **THEN** system reports ParseError with line number

### Requirement: Database connection configuration
The system SHALL define database connections in configuration file.

#### Scenario: Single database connection
- **WHEN** config specifies `databases.default` connection
- **THEN** system uses this connection for test execution

#### Scenario: Named database connections
- **WHEN** config specifies multiple named connections (default, staging, prod)
- **THEN** system can select which database to use

#### Scenario: Database URI format
- **WHEN** config specifies `uri: postgresql://user:pass@localhost/testdb`
- **THEN** system parses URI and creates connection

#### Scenario: Connection parameters
- **WHEN** config specifies individual parameters (driver, host, port, user, password, database)
- **THEN** system constructs connection string from parameters

#### Scenario: Environment variable substitution
- **WHEN** config contains `${DB_PASSWORD}` syntax
- **THEN** system replaces with environment variable value

#### Scenario: Missing environment variable
- **WHEN** config references undefined environment variable
- **THEN** system reports error with variable name

#### Scenario: Connection timeout
- **WHEN** config specifies `timeout: 30` seconds
- **THEN** system applies timeout to database operations

#### Scenario: Connection pool size
- **WHEN** config specifies `pool_size: 10`
- **THEN** system creates connection pool with specified size

### Requirement: Test path configuration
The system SHALL specify where test files are located.

#### Scenario: Single test directory
- **WHEN** config specifies `test_paths: ["tests/"]`
- **THEN** system discovers tests only in that directory

#### Scenario: Multiple test directories
- **WHEN** config specifies multiple paths
- **THEN** system discovers tests in all specified directories

#### Scenario: Glob patterns in test paths
- **WHEN** config uses `tests/**/*_test.sql` pattern
- **THEN** system discovers files matching the pattern

#### Scenario: Non-existent test directory
- **WHEN** config specifies path that doesn't exist
- **THEN** system reports warning and continues with other paths

### Requirement: Execution defaults configuration
The system SHALL allow setting execution defaults in configuration.

#### Scenario: Default parallelism
- **WHEN** config specifies `parallel: 4`
- **THEN** system defaults to 4 workers (can be overridden by CLI flag)

#### Scenario: Default output format
- **WHEN** config specifies `output_format: json`
- **THEN** system defaults to JSON output

#### Scenario: Default timeout
- **WHEN** config specifies `test_timeout: 60` seconds
- **THEN** system applies timeout to each test

#### Scenario: Default database selection
- **WHEN** config specifies `default_database: staging`
- **THEN** system uses staging database unless CLI overrides

#### Scenario: CLI flag overrides config
- **WHEN** config specifies `parallel: 4` and user runs with `--parallel 8`
- **THEN** CLI value takes precedence

### Requirement: Environment-specific configuration
The system SHALL support environment-specific configuration overrides.

#### Scenario: Base configuration with environment override
- **WHEN** config has base settings and `dev:` section
- **THEN** dev values override base values when environment is dev

#### Scenario: Environment auto-detection
- **WHEN** user runs `sql-unit run --environment staging`
- **THEN** system loads staging-specific configuration

#### Scenario: Environment variable selection
- **WHEN** SQLUNIT_ENV environment variable is set
- **THEN** system auto-selects matching environment section

#### Scenario: Missing environment section
- **WHEN** user specifies environment that doesn't exist in config
- **THEN** system reports error with available environments

### Requirement: Configuration validation
The system SHALL validate configuration on load.

#### Scenario: Required fields validation
- **WHEN** config is missing required fields
- **THEN** system reports which fields are required

#### Scenario: Type validation
- **WHEN** config field has wrong type (e.g., string instead of number)
- **THEN** system reports type error with field name

#### Scenario: Connection validation
- **WHEN** config specifies database connection
- **THEN** system validates URI format or required parameters

#### Scenario: Path validation
- **WHEN** config specifies test paths
- **THEN** system checks paths exist (with warnings if not)

### Requirement: Example configurations
The system SHALL provide clear examples in documentation.

#### Scenario: Example with single database
- **WHEN** user reads documentation
- **THEN** clear example shows basic config for one database

#### Scenario: Example with multiple environments
- **WHEN** user reads documentation
- **THEN** example shows how to configure dev, staging, prod

#### Scenario: Example with environment variables
- **WHEN** user reads documentation
- **THEN** example shows password substitution via ${DB_PASSWORD}
