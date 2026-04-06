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

### Decision 7: Config-Based Dialect Awareness

**Choice**: CLI reads connection config to determine database dialect for SQL execution

**Rationale**:
- Config defines connection (SQLite, MySQL, PostgreSQL, DuckDB) - CLI uses this to know dialect
- Dialect needed for SQL manipulation (adjusting syntax if needed) and test execution
- Enables SQLAlchemy to use correct driver when executing tests
- Follows "config drives execution" principle from p2-sql-unit-config

**Alternatives considered**:
- CLI accepts dialect as flag → Redundant with config, adds user error
- Hardcode SQLite → Would break other backends
- Detect at runtime by connecting → Adds latency, fails before user sees options

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Database connection limits** → Too many parallel tests exhaust connections | Document max parallel workers; default to CPU count; allow user override |
| **Output garbling in parallel mode** → Multiple tests writing simultaneously | Use queue-based output collection; write atomically per test |

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

## Open Questions

- Should parallel mode default to number of CPUs or require explicit flag?
- Should --verbose show full SQL statement execution details?
- Should test results be cached or always re-executed?
