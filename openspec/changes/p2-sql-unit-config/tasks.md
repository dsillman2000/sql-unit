# Tasks for p2-sql-unit-config

## Prerequisite: Phase 1, Phase 2's temp_table, and Phase 2's CLI Complete
- All Phase 1 changes must be complete
- p2-sql-unit-temp-tables must be complete
- p2-sql-unit-cli must be complete

## Capability 1: Configuration File Support

### Configuration Schema Design
- [ ] Define sql-unit.yaml schema
  - databases section (connections)
  - test_paths section (where tests are located)
  - execution section (defaults like timeout, parallelism)
  - environment section (environment-specific overrides)
- [ ] Document schema in code and user guide
- [ ] Create example config files
  - Basic config with single database
  - Multi-database config
  - Environment-specific configs

### Configuration File Loading
- [ ] Install PyYAML dependency
- [ ] Create config module
  - ConfigLoader class
  - Configuration data structure/dataclass
- [ ] Implement config file discovery
  - Check current directory for sql-unit.yaml
  - Check parent directories up to project root
  - Allow explicit --config-file flag override
- [ ] Implement config file loading
  - Parse YAML
  - Handle missing file gracefully
  - Return None if not found (allow fallback)
- [ ] Implement config caching
  - Load once per execution
  - Avoid repeated file I/O

### Environment Variable Substitution
- [ ] Implement variable substitution (${VAR} syntax)
  - Support in database URIs
  - Support in paths
  - Support in any string values
- [ ] Implement variable validation
  - Check all referenced variables exist
  - Clear error if variable not found
  - Show variable name in error message
- [ ] Implement escape syntax
  - Allow escaping ${VAR} as $${VAR}
  - Document escape mechanism

### Configuration Validation
- [ ] Implement schema validation
  - Check required fields present
  - Check value types correct
  - Check no unknown fields
- [ ] Implement database URI validation
  - Valid connection string format
  - Supported database driver
  - Resolvable after variable substitution
- [ ] Implement test path validation
  - Paths exist or error with helpful message
  - Paths are readable
- [ ] Implement error reporting
  - Clear error messages
  - Include config file location
  - Include line numbers if possible

## Capability 2: Database Connection Management

### Connection Definition Parsing
- [ ] Implement database connection specification
  - driver (postgresql, mysql, sqlite, etc.)
  - uri or connection components (host, port, user, password, database)
  - pool_size (connection pool size)
  - timeout (connection timeout)
  - options (driver-specific options)
- [ ] Support multiple named connections
  - Default connection
  - Named connections by reference
- [ ] Support connection URI parsing
  - Standard database URIs (postgresql://user:pass@host/db)
  - Variable substitution in URIs

### Connection Factory Integration
- [ ] Integrate config with connection factory
  - Load connections from config
  - Create connection based on config definition
  - Pass config to existing connection setup code
- [ ] Implement connection selection
  - Default connection if specified
  - Connection lookup by name
  - Override via CLI flag

### Testing for Connection Management
- [ ] Unit tests for connection parsing
- [ ] Unit tests for connection factory integration
- [ ] Integration tests with real databases
  - Create connection from config
  - Verify connection works
  - Test multiple named connections

## Capability 3: CLI Integration

### Config Integration with CLI
- [ ] Integrate config values into CLI execution
  - Load config before command processing
  - Use config database as default
  - Use config execution defaults (timeout, parallelism)
  - Use config test paths for discovery
- [ ] Implement command-line overrides
  - CLI flags override config values
  - Document precedence: CLI > config > built-in defaults
- [ ] Implement --config flag
  - Allow explicit config file specification
  - Path relative to CWD

### Config-Based Defaults
- [ ] Use config default database for tests
- [ ] Use config timeout for test execution
- [ ] Use config parallelism default
- [ ] Use config output format default
- [ ] Use config test paths for discovery

### Testing for CLI Integration
- [ ] Test config loading before CLI execution
- [ ] Test CLI flag overrides config
- [ ] Test missing config fallback
- [ ] Test invalid config error handling
- [ ] Test config values propagate to execution

## Capability 4: Environment-Specific Configuration

### Environment Override Support
- [ ] Support environment-specific config sections
  - development, staging, production sections
  - Environment auto-detection or explicit flag
- [ ] Implement environment selection
  - --environment/-e CLI flag
  - SQLUNIT_ENV environment variable
  - Default to development if not specified
- [ ] Implement section merging
  - Base configuration + environment overrides
  - Environment values override base

### Testing for Environment Support
- [ ] Test environment section loading
- [ ] Test environment selection via CLI
- [ ] Test environment selection via env var
- [ ] Test configuration merging
- [ ] Test precedence: CLI > env-specific > base

## Documentation & Examples

### Configuration File Examples
- [ ] Create example sql-unit.yaml (single database)
- [ ] Create example sql-unit.yaml (multi-database)
- [ ] Create example sql-unit.yaml (with env vars)
- [ ] Create example sql-unit.yaml (environment-specific)

### Configuration Documentation
- [ ] Document full configuration schema
- [ ] Document environment variable substitution
- [ ] Document database connection specification
- [ ] Document test path specification
- [ ] Document execution defaults
- [ ] Document best practices
  - Don't commit credentials
  - Use environment variables for secrets
  - Use environment-specific configs
- [ ] Add troubleshooting section

### Testing
- [ ] End-to-end tests with various config files
- [ ] Test error scenarios
  - Missing config file
  - Invalid YAML
  - Missing database connection
  - Invalid database URI
  - Missing environment variables
  - Invalid test paths

## Performance & Optimization
- [ ] Implement config caching
  - Load once per process
  - Avoid repeated file I/O
- [ ] Optimize variable substitution
  - Single pass through config
- [ ] Profile config loading time
  - Measure overhead
  - Document in performance section
