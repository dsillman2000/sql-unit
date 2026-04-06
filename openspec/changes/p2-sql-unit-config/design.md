## Context

Building on Phase 1, Phase 2's temp_table, and CLI support, this phase adds configuration file support. The sql-unit.yaml file allows projects to define database connections, test locations, and execution defaults in one place. This reduces setup overhead and enables flexible test execution.

The MVP must support four major SQL backends (SQLite, MySQL, PostgreSQL, DuckDB) via optional feature flags, allowing users to install only the dependencies they need. The base `sql-unit` package includes core dependencies (YAML parsing, data handling, SQL parsing) without database drivers.

Key constraints:
- Depends on Phase 1, Phase 2's temp_table, and Phase 2's CLI to be complete
- Must support a single database connection definition using `connection:` block
- Connection can use block syntax (with driver-specific parameters) or URL syntax
- Must support four backends: SQLite, MySQL, PostgreSQL, DuckDB (tested in MVP)
- Backend support via optional feature flags: `sql-unit[sqlite]`, `sql-unit[mysql]`, `sql-unit[postgresql]`, `sql-unit[duckdb]`
- Base package includes only core dependencies: yaml, pandas, sqlalchemy, sqlparse
- Optional `timeout` parameter in connection block for query timeout
- Optional `threads` parameter at config root level (default 4, min 1, -1 for system max)
- Must allow environment variable substitution
- Must be optional (fallback to CLI args when config missing)
- Must validate configuration on load
- No environment-specific configuration sections

## Goals / Non-Goals

**Goals:**
- Load and parse sql-unit.yaml configuration
- Support single database connection via `connection:` block
- Support block syntax (driver-specific parameters) and URL syntax for connections
- Support four SQL backends: SQLite, MySQL, PostgreSQL, DuckDB
- Implement optional feature flags for backend dependencies
- Base package with core dependencies (yaml, pandas, sqlalchemy, sqlparse)
- Support optional `timeout` parameter in connection block
- Support optional `threads` parameter at root level (default 4, min 1, -1 for system max)
- Support test path specifications
- Environment variable substitution (${VAR} syntax)
- Configuration validation and error reporting
- Fallback to CLI arguments when config missing

**Non-Goals:**
- Dynamic configuration reloading
- Configuration schema evolution/versioning
- Configuration file generation/scaffolding
- Encrypted credentials storage
- Environment-specific configuration sections (all config is static)
- Output format defaults (only execution-related: threads, timeout)
- Multiple database connections
- Additional SQL backends beyond SQLite, MySQL, PostgreSQL, DuckDB (can add later)

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

**Choice**: Single connection via `connection:` block with flexible URI support

**Rationale**:
- Simpler configuration and fewer sources of confusion
- Supports flexible connection definition (block syntax or URL syntax)
- Handles all database types (SQLite, MySQL, PostgreSQL, DuckDB)
- Environment variables can be used for secrets in connection details

**Alternatives considered**:
- Multiple named connections → More complex, not needed for MVP
- Inline per-test config → Repetitive
- Single default database only → Would need to extend later

### Decision 3: Environment Variable Substitution

**Choice**: Support ${VAR} syntax for environment variables

**Rationale**:
- Secrets don't need to be in config file
- Standard syntax familiar to developers
- Can reference any environment variable

**Alternatives considered**:
- .env file loading → More complex
- Credential manager integration → Overkill for MVP

### Decision 4: Threads Configuration

**Choice**: Optional `threads` parameter at root level with sensible defaults

**Rationale**:
- Allows users to control parallelism without CLI flags
- Default of 4 is reasonable for most systems
- Sentinel value -1 enables automatic detection for flexible deployments
- Minimum of 1 prevents invalid configurations

**Alternatives considered**:
- Fixed parallelism → Not flexible
- No threading config → Less control for users
- Environment variable only → Less discoverable

### Decision 5: No Environment-Specific Sections

**Choice**: Single static configuration file without environment sections

**Rationale**:
- Simpler configuration model
- Environment management deferred to external tooling
- CLI can accept database/connection args for environment selection
- Reduces config complexity for MVP

**Alternatives considered**:
- Base + environment overrides → More complex, can add later
- Multiple config files → Users manage externally

### Decision 6: Backend Support via Optional Feature Flags

**Choice**: Four backends (SQLite, MySQL, PostgreSQL, DuckDB) with optional feature flag installation

**Rationale**:
- Reduces dependency bloat for users who only need one backend
- Allows users to install only what they need: `sql-unit[sqlite]`, `sql-unit[mysql]`, `sql-unit[postgresql]`, `sql-unit[duckdb]`
- Base package stays lightweight with only core dependencies
- Core dependencies: yaml, pandas, sqlalchemy, sqlparse
- Backends tested in MVP to ensure quality, but optional for users

**Alternatives considered**:
- Single package with all drivers → Bloated for most users
- Single driver support → Not flexible enough
- Multiple separate packages → Complicated installation
- All backends required → Unnecessary dependencies

### Decision 7: Dialect Exposure for CLI

**Choice**: Config connection block exposes dialect for CLI to use during execution

**Rationale**:
- Connection block defines driver (sqlite, mysql, postgresql, duckdb) - CLI reads this
- Block syntax: `connection: { sqlite: { path: ... } }` directly indicates dialect
- URL syntax: `connection: { url: "sqlite:///..." }` parses dialect from URL scheme
- CLI uses dialect for SQLAlchemy connection and any SQL syntax adjustments
- Enables test execution against configured database

**Alternatives considered**:
- Separate dialect field → Redundant, can be derived from connection
- CLI auto-detects → Adds runtime complexity, fails silently on unknown
- Hardcoded SQLite → Would break multi-backend support

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

- Should config support command-line override of values (--set key=value)?
- Should failed config validation be an error or warning?
- Should sql-unit.yaml be searched for in parent directories (like .git)?
- Should timeout be configurable at both connection and test level?
