## Context

Building on Phase 1 (core execution engine), this phase adds a command-line interface (CLI) for test discovery, compilation, and execution. The CLI must integrate with the existing test loader and executor, enabling developers to run tests locally and CI/CD systems to automate test execution. The CLI provides `list` for discovery, `compile` for SQL output without execution, and `run` for actual test execution.

Key constraints:
- Depends on Phase 1 and Phase 2 Complete
- Must support test selection via -s/--select (name, glob, file, folder)
- Must provide machine-readable (JSON) and human-readable output
- Must integrate with CI/CD systems via exit codes
- Must support parallel test execution
- Must read connection config from p2-sql-unit-config to determine dialect and connection
- Must use connection dialect for SQL execution against real database

## Goals / Non-Goals

**Goals:**
- Implement `list` command for test discovery (no connection required)
- Implement `run` command for test execution
- Implement `compile` command for SQL output (no connection required)
- Support test selection via -s/--select (name, glob, file, folder) with union support
- Provide JSON output mode for tooling
- Provide human-readable output mode for developers
- Proper exit codes (0 = all pass, 1 = failures, 2 = errors)
- Support parallel execution flag
- Support verbose output for debugging

**Non-Goals:**
- Interactive test debugging (breakpoints, etc.)
- Test code generation
- Test template scaffolding
- Watch/file system monitoring mode

## Decisions

### Decision 1: CLI Framework Choice

**Choice**: Use Click for CLI framework

**Rationale**:
- Lightweight and focused on CLI building
- Easy to test
- Good documentation
- Minimal dependencies
- Good for Python packaging

**Alternatives considered**:
- argparse → More verbose
- Typer → More features than needed; newer/less stable
- Poetry CLI → Overkill for this use case

### Decision 2: Output Formats

**Choice**: Support both human-readable and JSON output

**Rationale**:
- Developers need readable output for local development
- CI/CD systems need machine-readable format for parsing
- Can be toggled via --format flag

**Alternatives considered**:
- JSON only → Poor developer experience
- Human-readable only → CI/CD integration harder
- Both with separate commands → More complex

### Decision 3: Parallel Execution

**Choice**: Support optional parallel execution via --threads flag

**Rationale**:
- Large test suites benefit from parallelization
- Optional flag allows users to choose
- Can use multiprocessing for CPU-bound tasks

**Alternatives considered**:
- Always parallel → May cause issues with shared resources
- No parallel support → Slower test execution for large suites

### Decision 4: No-Connection Commands

**Choice**: `list` and `compile` commands don't require database connection

**Rationale**:
- Test discovery only reads and parses .sql files
- Compile only renders Jinja templates and outputs SQL to stdout
- Allows users to explore tests and generate SQL without database setup
- Useful for debugging and SQL inspection workflows

**Alternatives considered**:
- Always require connection → Blocks exploration without database
- Optional connection for list → Adds complexity without benefit

### Decision 5: Compile Command Output

**Choice**: Compile discovers tests in parallel but outputs SQL sequentially

**Rationale**:
- Parallel discovery speeds up test collection for large projects
- Sequential output prevents SQL statements from being interleaved
- Plaintext SQL must remain valid and readable
- Can use parallel discovery then sequential buffer flush

**Alternatives considered**:
- Sequential discovery → Slower for large codebases
- Parallel output → Garbled/interleaved SQL output

### Decision 6: Test Selection Syntax (-s/--select)

**Choice**: Unified `-s/--select` flag supporting four selector types with union via multiple flags

**Rationale**:
- Single flag for all selection modes keeps CLI simple
- Four selector types cover common use cases: exact name, glob pattern, specific file, folder
- Multiple selectors can be combined to union results
- Consistent across list, compile, and run commands

**Selector Types:**
1. **Name**: Exact test scenario name (e.g., `-s test_user_login`)
2. **Glob**: Glob pattern for test names (e.g., `-s "user_*"` or `-s "test_*"`)
3. **File**: Specific SQL file path (e.g., `-s tests/users/auth_test.sql`)
4. **Folder**: Directory path containing tests (e.g., `-s tests/integration/`)

**Usage Examples:**
```
# Single selector
sql-unit run -s test_user_login
sql-unit compile -s "user_*"
sql-unit list -s tests/users/

# Multiple selectors (union)
sql-unit run -s test_login -s "admin_*" -s tests/regression/
```

**Alternatives considered**:
- Separate flags for each type → Too many flags, confusing
- Regex patterns instead of glob → More powerful but complex
- Complex set operations (intersection, difference) → Too complex for MVP
- Config file for selectors → Adds setup overhead

### Decision 8: Connection Override via --connection

**Choice**: Support `--connection "<url>"` flag to override config connection or enable config-free execution

**Rationale**:
- Enables ad-hoc testing without project setup (no sql-unit.yaml required)
- Allows CI/CD pipelines to inject connection details dynamically
- Supports temporary environment overrides without editing config
- Makes tool accessible for quick iteration and testing

**Behavior**:
- `--connection` always takes precedence over config file connection
- When `--connection` provided without config file, discovers all .sql files recursively in CWD
- Environment variables supported in connection string (via config system)

**Example workflows**:
```bash
# Config-driven (config file provides connection)
sql-unit run

# Config-free (explicit connection, discovers all .sql in CWD)
sql-unit run --connection "sqlite:///test.db"

# Override (config for paths, CLI for connection)
sql-unit run --connection "postgres://staging" --select "tests/auth/*"
```

**Alternatives considered**:
- Config always required → Blocks quick testing, poor onboarding
- No override capability → Reduced flexibility for CI/CD
- Generic --set flag → Too complex, doesn't align with precedence model

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Database connection limits** → Too many parallel tests exhaust connections | Document max parallel workers; default to CPU count; allow user override |
| **Output garbling in parallel mode** → Multiple tests writing simultaneously | Use queue-based output collection; write atomically per test |
| **Config vs CLI precedence confusion** → Users unclear which settings win | Document precedence clearly; show warning when override applied |

## Test Discovery & Selection

### Discovery Scope

**Config-driven mode** (with sql-unit.yaml):
- Test discovery limited to `test_paths:` specified in config
- Default fallback: all .sql files recursively (`**/*`)
- `--select` filters within these paths

**Config-free mode** (with `--connection` only):
- Test discovery searches all .sql files recursively in CWD (`**/*`)
- `--select` filters these discovered tests
- No config-based path restrictions

### Selection Semantics

The `-s/--select` flag provides granular filtering:

```
Discovery phase:
  ├─ Read config (if exists) for test_paths scope
  └─ Find all .sql files matching test_paths
     (or all .sql files recursively if no config)

Selection phase:
  ├─ If --select provided:
  │  └─ Apply glob/pattern filters to discovered tests
  │     (union across multiple --select flags)
  └─ If no --select: use all discovered tests

Examples:
  sql-unit run -s "tests/auth/*"           # Glob within discovered tests
  sql-unit run -s tests/auth_test.sql      # Specific file
  sql-unit run -s "user_*"                 # Test name pattern
  sql-unit run -s tests/ -s "regression_*" # Union of folder + name pattern
```

### No Default Test Path Override via CLI

The system does NOT provide `--test-paths` or similar. Instead:
- Config defines static search scope (test_paths)
- `-s/--select` provides dynamic filtering
- This separation keeps concerns clean: config = project structure, CLI = this run's subset

## Migration Plan

Phase 2 CLI:
1. Design CLI architecture
2. Implement Click integration
3. Implement list command with filtering (no connection required)
4. Implement compile command for SQL output (no connection required)
5. Implement run command with basic execution
6. Add output formatting (human-readable, JSON)
7. Add parallel execution support
8. Add exit code handling
9. Create comprehensive CLI tests
10. Add CLI documentation

## Resolved Questions

### Q: How do config and CLI arguments interact?
**A: Clear precedence model:**
- `--connection` always overrides config connection
- `--threads` always overrides config threads
- Config provides defaults; CLI flags are explicit overrides
- Config connection is required unless `--connection` provided explicitly

### Q: What happens when no config is found and no --connection is provided?
**A: Error with actionable guidance:**
```
✗ No database connection configured

You must specify a database connection to run tests. Choose one:

Option 1: Create a sql-unit.yaml in your project:
  
  connection:
    url: "sqlite:///tests.db"

  Then run:
    sql-unit run

Option 2: Provide connection via CLI:
  
  sql-unit run --connection "sqlite:///tests.db"

See documentation for more connection examples.
```

### Q: How are tests discovered in config-free mode (--connection only)?
**A:** All .sql files recursively from CWD are discovered. User should use `--select` to filter specific tests. This prevents surprise execution of hundreds of files.

### Q: Should parallel mode default to number of CPUs or require explicit flag?
**A: Default to number of CPUs (or config threads if specified).** Allow override with `--threads` flag.

### Q: Should --verbose show full SQL statement execution details?
**A: Not in MVP.** Start with simple verbose (stack traces, more output). Can add SQL details in phase 3+.

### Q: Should test results be cached or always re-executed?
**A: Always re-execute.** No caching in MVP. Can add incremental execution later.
