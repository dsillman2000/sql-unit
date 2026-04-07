## ADDED Requirements

### Requirement: SQL backend support
The system SHALL support four major SQL backends via optional feature flags.

#### Scenario: SQLite backend via feature flag
- **WHEN** user installs `sql-unit[sqlite]`
- **THEN** system includes SQLite driver and can connect to SQLite databases

#### Scenario: MySQL backend via feature flag
- **WHEN** user installs `sql-unit[mysql]`
- **THEN** system includes MySQL driver and can connect to MySQL databases

#### Scenario: PostgreSQL backend via feature flag
- **WHEN** user installs `sql-unit[postgresql]`
- **THEN** system includes PostgreSQL driver and can connect to PostgreSQL databases

#### Scenario: DuckDB backend via feature flag
- **WHEN** user installs `sql-unit[duckdb]`
- **THEN** system includes DuckDB driver and can connect to DuckDB databases

#### Scenario: Base package without backends
- **WHEN** user installs `sql-unit` without any feature flags
- **THEN** system includes only core dependencies (yaml, pandas, sqlalchemy, sqlparse)

#### Scenario: Missing backend driver
- **WHEN** config specifies a connection to a backend driver not installed
- **THEN** system reports error indicating which feature flag to install

#### Scenario: Connection validation for backend type
- **WHEN** system loads configuration
- **THEN** system validates that the specified backend driver is available

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
The system SHALL define a single database connection in the configuration file using a `connection:` block.

#### Scenario: Single connection block
- **WHEN** config specifies `connection:` with database parameters or URL
- **THEN** system uses this connection for test execution

#### Scenario: Connection block syntax (driver-specific parameters)
- **WHEN** config specifies connection with block syntax (e.g., `sqlite: {path: ...}` or `mysql: {host: ..., port: ..., username: ..., password: ..., database: ...}`)
- **THEN** system constructs connection string from parameters

#### Scenario: Connection URL syntax
- **WHEN** config specifies `connection: {url: postgresql://user:pass@localhost/testdb}`
- **THEN** system parses URI and creates connection

#### Scenario: Environment variable substitution
- **WHEN** config contains `${DB_PASSWORD}` syntax in connection details
- **THEN** system replaces with environment variable value

#### Scenario: Missing environment variable
- **WHEN** config references undefined environment variable in connection
- **THEN** system reports error with variable name

#### Scenario: Connection timeout
- **WHEN** config specifies `timeout: 30` in the connection block
- **THEN** system applies timeout to database operations

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

#### Scenario: Default thread count
- **WHEN** config specifies `threads: 8`
- **THEN** system uses 8 worker threads (can be overridden by CLI flag)

#### Scenario: Default thread count with system auto-detect
- **WHEN** config specifies `threads: -1`
- **THEN** system uses as many threads as the host system can support

#### Scenario: Invalid thread count
- **WHEN** config specifies `threads: 0` or negative value other than -1
- **THEN** system reports error (must be >= 1 or -1)

#### Scenario: Default thread count (implicit)
- **WHEN** config does not specify `threads`
- **THEN** system defaults to 4 worker threads

#### Scenario: CLI flag overrides config
- **WHEN** config specifies `threads: 4` and user runs with `--threads 8`
- **THEN** CLI value takes precedence

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

#### Scenario: Thread validation
- **WHEN** config specifies `threads` value
- **THEN** system validates value is >= 1 or exactly -1

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

### Requirement: Config-free execution with --connection
The system SHALL support test execution without a configuration file when connection details are provided via CLI.

#### Scenario: CLI connection without config
- **WHEN** no sql-unit.yaml exists and `--connection` is provided
- **THEN** system uses CLI connection and discovers all .sql files recursively in CWD

#### Scenario: Connection precedence
- **WHEN** both config connection and `--connection` CLI flag are provided
- **THEN** CLI connection takes precedence over config connection

#### Scenario: Missing connection
- **WHEN** no sql-unit.yaml exists and no `--connection` provided
- **THEN** system reports error with guidance on creating config or providing CLI connection

#### Scenario: Config discovery with explicit --config
- **WHEN** user provides `--config /path/to/file.yaml`
- **THEN** system uses specified file; no fallback discovery
