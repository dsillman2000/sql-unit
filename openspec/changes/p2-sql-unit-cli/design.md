## Context

Building on Phase 1 (core execution engine) and Phase 2's temp_table support, this phase adds a command-line interface (CLI) for test discovery and execution. The CLI must integrate with the existing test loader and executor, enabling developers to run tests locally and CI/CD systems to automate test execution.

Key constraints:
- Depends on Phase 1 and Phase 2 Complete
- Must support test filtering by name, directory, tags
- Must provide machine-readable (JSON) and human-readable output
- Must integrate with CI/CD systems via exit codes
- Must support parallel test execution
- Must work with configured databases (Phase 2's config)

## Goals / Non-Goals

**Goals:**
- Implement `list` command for test discovery
- Implement `run` command for test execution
- Support filtering by test name, directory, tags
- Provide JSON output mode for tooling
- Provide human-readable output mode for developers
- Proper exit codes (0 = all pass, 1 = failures)
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

**Choice**: Support optional parallel execution via --parallel flag

**Rationale**:
- Large test suites benefit from parallelization
- Optional flag allows users to choose
- Can use multiprocessing for CPU-bound tasks

**Alternatives considered**:
- Always parallel → May cause issues with shared resources
- No parallel support → Slower test execution for large suites

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Test isolation in parallel mode** → Concurrent tests interfere with each other | Phase 2's temp_table unique naming ensures isolation; document requirements |
| **Database connection limits** → Too many parallel tests exhaust connections | Document max parallel workers; default to CPU count; allow user override |
| **Output garbling in parallel mode** → Multiple tests writing simultaneously | Use queue-based output collection; write atomically per test |

## Migration Plan

Phase 2 CLI:
1. Design CLI architecture
2. Implement Click integration
3. Implement list command with filtering
4. Implement run command with basic execution
5. Add output formatting (human-readable, JSON)
6. Add parallel execution support
7. Add exit code handling
8. Create comprehensive CLI tests
9. Add CLI documentation

## Open Questions

- Should test filtering support regex patterns or simple glob/string matching?
- Should parallel mode default to number of CPUs or require explicit flag?
- Should --verbose show full SQL statement execution details?
- Should test results be cached or always re-executed?
