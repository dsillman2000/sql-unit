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

### Decision 5: YAML Reference Resolution Architecture

**Choice**: Use `sql-unit.yaml` file location as the project root; resolve all `!reference` tag paths relative to this project root via yaml_reference library with configurable `allow_paths`.

**Rationale**:
- `sql-unit.yaml` naturally defines a project boundary (config location = project scope)
- Enables cross-subdirectory references without fragile `../../../` relative paths
- Project root becomes semantic anchor: `!reference-all "fixtures/tests.yaml"` works from any subdirectory
- yaml_reference library handles path resolution safely; `allow_paths` prevents escape attacks
- User-configurable `allow_paths` in sql-unit.yaml allows fine-grained control
- Paths always resolve consistently regardless of current working directory

**Implementation details**:
1. Test discovery requires finding `sql-unit.yaml` (refuse discovery without it)
2. Project root = directory containing `sql-unit.yaml`
3. `allow_paths` configured in sql-unit.yaml YAML block; defaults to `[<project_root>]`
4. yaml_reference resolves all `!reference` and `!reference-all` paths relative to project root
5. Errors from yaml-reference (e.g., path outside allow_paths, circular references) propagate as ParserError

**Path resolution example:**
```
Project structure:
  adult_users/
    ├── sql-unit.yaml
    ├── references/
    │   ├── adult_users.sql      (contains: !reference-all "tests.yaml")
    │   └── tests.yaml
    ├── cte/
    │   └── adult_users.sql      (can reference: !reference-all "references/tests.yaml")
    └── fixtures/
        └── common_tests.yaml    (can be referenced from anywhere)

sql-unit.yaml config:
  allow_paths:
    - references/
    - fixtures/

From any SQL file, these paths resolve correctly:
  !reference-all "references/tests.yaml"    ✓ Works
  !reference-all "fixtures/common_tests.yaml" ✓ Works
  !reference-all "../../../secret.yaml"     ✗ Error (outside allow_paths)
```

**Alternatives considered**:
- Relative paths from SQL file → Fragile with nested directories, inconsistent
- Absolute paths required → Breaks portability, yaml_reference forbids this
- No sql-unit.yaml requirement → Can't define consistent project boundary
- Hard-coded allow_paths → Inflexible for large projects with multiple fixture directories

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **YAML parsing errors** → Test file becomes unparseable | Provide clear error messages with line numbers |
| **Database dependency** → Tests require live connection | Provide SQLite `:memory:` option for development |
| **Jinja variable collision** → User variables conflict with SQL identifiers | Document variable naming conventions |
| **Missing sql-unit.yaml** → Discovery fails, user confused | Clear error message: "sql-unit.yaml not found. Create one to define project scope" |
| **Path escape attempts** → User accidentally references files outside project | yaml_reference enforces allow_paths; provide clear error on violation |
| **Circular references** → YAML A references B which references A | yaml_reference detects and reports; propagate as ParserError |
| **Misconfigured allow_paths** → Too restrictive prevents valid references | Document configuration with examples; error messages show allowed paths |

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
- ~~Should sql-unit.yaml be required?~~ **DECIDED**: Yes, required for discovery. (Decision 5)
- ~~Should allow_paths be configurable?~~ **DECIDED**: Yes, via sql-unit.yaml config block. (Decision 5)
- ~~How should path resolution work for references?~~ **DECIDED**: Relative to project root (sql-unit.yaml directory) with yaml_reference + allow_paths. (Decision 5)
