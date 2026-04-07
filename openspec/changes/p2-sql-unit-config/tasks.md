# Tasks for p2-sql-unit-config

## Prerequisite: Phase 1 and Phase 2's CLI Complete
- All Phase 1 changes must be complete
- p2-sql-unit-cli must be complete

## Capability 1: Configuration File Support

### Configuration Schema Design
- [x] Define sql-unit.yaml schema
  - databases section (connections)
  - test_paths section (where tests are located)
  - execution section (defaults like timeout, parallelism)
  - environment section (environment-specific overrides)
- [x] Document schema in code and user guide
- [x] Create example config files
  - Basic config with single database
  - Multi-database config
  - Environment-specific configs
- [x] Install PyYAML dependency
- [x] Create config module
  - ConfigLoader class
  - Configuration data structure/dataclass
- [x] Implement config file discovery
  - Check current directory for sql-unit.yaml
  - Check parent directories up to project root
  - Allow explicit --config-file flag override
- [x] Implement config file loading
  - Parse YAML
  - Handle missing file gracefully
  - Return None if not found (allow fallback)
- [x] Implement config caching
  - Load once per execution
  - Avoid repeated file I/O
- [x] Implement variable substitution (${VAR} syntax)
  - Support in database URIs
  - Support in paths
  - Support in any string values
- [x] Implement variable validation
  - Check all referenced variables exist
  - Clear error if variable not found
  - Show variable name in error message
- [x] Implement escape syntax
  - Allow escaping ${VAR} as $${VAR}
  - Document escape mechanism
- [x] Implement schema validation
  - Check required fields present
  - Check value types correct
  - Check no unknown fields
- [x] Implement database URI validation
  - Valid connection string format
  - Supported database driver
  - Resolvable after variable substitution
- [x] Implement test path validation
  - Paths exist or error with helpful message
  - Paths are readable
- [x] Implement error reporting
  - Clear error messages
  - Include config file location
  - Include line numbers if possible

## Capability 2: Database Connection Management

### Connection Definition Parsing
- [x] Implement database connection specification
  - Single connection via `connection:` block
  - Support block syntax (driver-specific parameters) and URL syntax
  - timeout (connection timeout, optional)
- [x] Support connection URI parsing
  - Standard database URIs (postgresql://user:pass@host/db)
  - Variable substitution in URIs
  - Derive dialect from connection definition

### Connection Factory Integration
- [x] Integrate config with connection factory
  - Load connections from config
  - Create connection based on config definition
  - Pass config to existing connection setup code
- [x] Implement connection selection
  - Use config connection if available
  - Override via --connection CLI flag

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
- [x] Implement command-line overrides
  - CLI flags override config values
  - Document precedence: CLI > config > built-in defaults
- [x] Implement --config flag
  - Allow explicit config file specification
  - Path relative to CWD
- [x] Implement --connection flag (config-free execution)

### Config-Based Defaults
- [ ] Use config default database for tests
- [ ] Use config timeout for test execution
- [ ] Use config parallelism (threads) default
- [ ] Use config test paths for discovery
- [x] Implement --connection CLI flag (config-free execution)

### Testing for CLI Integration
- [ ] Test config loading before CLI execution
- [ ] Test CLI flag overrides config
- [ ] Test missing config fallback (with --connection provided)
- [ ] Test invalid config error handling
- [ ] Test config values propagate to execution

## Documentation & Examples

### Configuration File Examples
- [x] Create example sql-unit.yaml (single database)
- [x] Create example sql-unit.yaml (with env vars)

### Configuration Documentation
- [x] Document full configuration schema
- [x] Document environment variable substitution
- [x] Document database connection specification
- [x] Document test path specification
- [x] Document --connection flag override behavior
- [x] Document best practices
  - Don't commit credentials
  - Use environment variables for secrets
- [x] Add troubleshooting section

### Testing
- [ ] End-to-end tests with various config files
- [ ] Test error scenarios
  - Missing config file (should error with guidance)
  - Invalid YAML
  - Missing database connection
  - Invalid database URI
  - Missing environment variables
  - Invalid test paths (warning)
- [ ] Test --connection flag behavior (config-free execution)
- [ ] Test --config flag behavior (explicit config file)

## Performance & Optimization
- [ ] Implement config caching
  - Load once per process
  - Avoid repeated file I/O
- [ ] Optimize variable substitution
  - Single pass through config
- [ ] Profile config loading time
  - Measure overhead
  - Document in performance section
