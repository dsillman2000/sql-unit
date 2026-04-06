## Why

Phase 1 and Phase 2's capabilities (core, inputs, expectations, temp_table, CLI) work well for basic usage, but real-world projects need configuration management. The config file support allows teams to:
- Define database connections once instead of hardcoding
- Set test execution defaults (database, timeout, logging)
- Organize tests in multiple directories
- Configure environment-specific settings (dev, staging, prod)

## What Changes

- **Configuration file** - sql-unit.yaml support
- **Database connections** - Define connections in config
- **Test paths** - Specify where tests are located
- **Execution defaults** - Set timeout, parallelism, output format defaults
- **Environment variables** - Support variable substitution in config

## Capabilities

### New Capabilities

- `config-file-support`: sql-unit.yaml configuration file with database connections, test paths, and execution defaults

## Impact

- **Team coordination** - Shared configuration across team members
- **Environment management** - Different settings for dev/staging/prod
- **Simpler test execution** - No need to specify database on every run
- **CI/CD integration** - Config-driven test execution in pipelines
