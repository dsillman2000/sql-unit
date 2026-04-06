## Context

Building on Phase 1, Phase 2's temp_table, and CLI support, this phase adds configuration file support. The sql-unit.yaml file allows projects to define database connections, test locations, and execution defaults in one place. This reduces setup overhead and enables environment-specific configuration.

Key constraints:
- Depends on Phase 1, Phase 2's temp_table, and Phase 2's CLI to be complete
- Must support multiple database connection definitions
- Must allow environment variable substitution
- Must be optional (fallback to CLI args when config missing)
- Must validate configuration on load

## Goals / Non-Goals

**Goals:**
- Load and parse sql-unit.yaml configuration
- Support multiple named database connections
- Support test path specifications
- Support execution defaults (timeout, parallelism, output format)
- Environment variable substitution (${VAR} syntax)
- Configuration validation and error reporting
- Fallback to CLI arguments when config missing

**Non-Goals:**
- Dynamic configuration reloading
- Configuration schema evolution/versioning
- Configuration file generation/scaffolding
- Encrypted credentials storage

## Decisions

### Decision 1: Configuration Format

**Choice**: YAML format for sql-unit.yaml

**Rationale**:
- Human-readable and easy to write
- Hierarchical structure natural for nested config
- Good Python support (PyYAML)
- Common in developer tools (Docker, Kubernetes, etc.)

**Alternatives considered**:
- TOML → Equally good but less hierarchical
- JSON → Less readable
- INI → Less expressive for nested structures

### Decision 2: Database Connection Definitions

**Choice**: Named connections with flexible URI support

**Rationale**:
- Support multiple databases/environments
- Named references easy to use in tests
- Flexible URI format supports all databases

**Alternatives considered**:
- Single default database → Inflexible
- Inline per-test config → Repetitive

### Decision 3: Environment Variable Substitution

**Choice**: Support ${VAR} syntax for environment variables

**Rationale**:
- Secrets don't need to be in config file
- Standard syntax familiar to developers
- Can reference any environment variable

**Alternatives considered**:
- .env file loading → More complex
- Credential manager integration → Overkill for MVP

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Credentials in config file** → Sensitive data exposure | Document .gitignore best practices; support env vars; clear warnings |
| **Config not found** → Tests fail mysteriously | Provide clear error message; check multiple locations; fallback to CLI args |
| **Environment variable not set** → Substitution fails | Validate all variables exist; clear error messages |
| **Config format errors** → Parse failures | Comprehensive validation; helpful error messages with line numbers |

## Migration Plan

Phase 2 Config:
1. Design configuration schema
2. Implement YAML loading and parsing
3. Implement configuration validation
4. Implement environment variable substitution
5. Integrate config with CLI (use config values as defaults)
6. Integrate config with database connection setup
7. Create configuration examples
8. Add configuration documentation
9. Create comprehensive tests

## Open Questions

- Should config support multiple files (base + environment-specific)?
- Should config support command-line override of values (--set key=value)?
- Should failed config validation be an error or warning?
- Should sql-unit.yaml be searched for in parent directories (like .git)?
