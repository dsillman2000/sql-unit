## Context

The sql-unit framework foundation must support YAML doc-comment syntax for embedding tests in SQL files, binding tests to SQL statements, rendering Jinja templates, and executing tests against databases. This phase establishes the core infrastructure: project structure, YAML parser, Jinja2 integration, and basic test execution engine.

Key constraints:
- Tests must be colocated with SQL code via doc comments
- Only SELECT statements are testable
- Jinja2 rendering must happen before SQL execution
- Project must use uv as package manager
- SQLAlchemy provides database abstraction

## Goals / Non-Goals

**Goals:**
- Establish project structure using uv
- Parse YAML doc comments from SQL files
- Bind tests to SQL statements
- Support Jinja2 template rendering in SQL
- Create basic test execution engine
- Support database connections via SQLAlchemy
- Provide foundation for downstream features

**Non-Goals:**
- CLI commands (Phase 2)
- Configuration files (Phase 2)
- Advanced input types like temp_table (Phase 2)
- Documentation site (Phase 4)
- Expectations beyond structure (Phase 1 inputs/expectations)

## Decisions

### Decision 1: uv as Package Manager

**Choice**: Use uv for project setup, dependency management, and virtual environments

**Rationale**:
- Fast, modern, Rust-based tool
- Reproducible builds with lock files
- Unified tool for virtual environment and dependency management
- Growing adoption in Python ecosystem

**Alternatives considered**:
- Poetry → More opinionated, heavier tool
- pip + virtualenv → Slower, fragmented

### Decision 2: Doc-comment binding pattern

**Choice**: Bind tests via `/* #! sql-unit ... */` block comments immediately preceding SQL statements

**Rationale**:
- Tests colocated with code they validate
- Standard SQL comment syntax
- Clear marker (`#! sql-unit`) distinguishes from documentation
- Immediate binding avoids disambiguation

**Alternatives considered**:
- Separate `.test.yaml` files → Scattered, harder to maintain
- Python test files → Duplicates SQL code

### Decision 3: Jinja2 for template rendering

**Choice**: Integrate Jinja2 template engine for SQL variable substitution

**Rationale**:
- Standard Python templating engine
- Supports variable injection and conditional logic
- Familiar to data engineers
- Rendering happens before SQL execution

**Alternatives considered**:
- No templating → Less flexible for parameterized tests
- String formatting → Unsafe, no template logic

### Decision 4: Multi-Test Syntax Support

**Choice**: Support two syntaxes for stacking multiple tests in a single doc comment

**Rationale**:
- Multi-doc syntax (`---` separators): Easier to read and draft manually
- Sequence syntax (YAML list): Enables combining tests from multiple files via `!reference-all`
- Both produce same internal representation - parser normalizes to list
- User choice based on use case

**Multi-doc syntax:**
```sql
/* #! sql-unit
name: test_login
given:
  sql: SELECT 'john' as username
expect:
  rows_equal:
    - username: john
---
name: test_register
given:
  sql: SELECT 'jane' as username
expect:
  rows_equal:
    - username: jane
*/
```

**Sequence syntax:**
```sql
/* #! sql-unit
- name: test_login
  given:
    sql: SELECT 'john' as username
  expect:
    rows_equal:
      - username: john
- name: test_register
  given:
    sql: SELECT 'jane' as username
  expect:
    rows_equal:
      - username: jane
*/
```

**Usage with !reference-all:**
```sql
/* #! sql-unit
!reference-all "test_fixtures/users.yml"
*/
```

**Alternatives considered**:
- Single syntax only → Less flexibility for different workflows
- Auto-detection only → Harder to debug edge cases
- Require explicit syntax marker → Adds complexity

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **YAML parsing errors** → Test file becomes unparseable | Provide clear error messages with line numbers |
| **Database dependency** → Tests require live connection | Provide SQLite `:memory:` option for development |
| **Jinja variable collision** → User variables conflict with SQL identifiers | Document variable naming conventions |

## Migration Plan

This is a new specification phase. Phase 1 establishes the foundation:
1. Initialize uv project structure
2. Create YAML parser and test discovery
3. Integrate Jinja2 rendering
4. Build basic test execution engine
5. Create unit tests for parser and renderer

Subsequent phases depend on this foundation.

## Open Questions

- Should test names be unique globally (across files) or only within a file?
- What default Jinja context variables should be available (test name, file path, etc.)?
- How should undefined Jinja variables be handled (error vs. empty)?
