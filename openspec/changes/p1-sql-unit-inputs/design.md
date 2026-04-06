## Context

Building on the core Phase 1 foundation, this phase adds input setup (`given:` clause) and row count expectations. Tests must be able to define input data and assertions. This requires parsing the `given:` structure, implementing input types (CTE injection, relation substitution, jinja_context), supporting multiple data formats, and implementing row count validation.

Key constraints:
- Depends on Phase 1: parser, Jinja rendering, execution engine
- Inputs are optional (tests can have no `given:` clause)
- Temp_table input deferred to Phase 2 (more complex database operations)
- Data formats must support SQL queries, CSV, and inline YAML rows

## Goals / Non-Goals

**Goals:**
- Parse and validate `given:` clause structure
- Implement CTE injection into SQL statements
- Implement relation (table name) substitution
- Support jinja_context variable injection with nested data sources
- Support auto-generated and user-provided aliases for Jinja-bound sources
- Support `sql`, `csv`, and `rows` data formats
- Implement row_count expectation with `eq`, `min`, `max`
- Enable combining multiple input types (top-level and Jinja-bound)
- Detect and error on alias collisions between Jinja variables and top-level sources
- Enforce Jinja rendering before relation substitution (no Jinja syntax in relation.targets)
- Provide clear error messages for input errors and Jinja rendering failures

**Non-Goals:**
- temp_table input (Phase 2 - requires table creation/cleanup)
- yaml-reference support (Phase 2)
- rows_equal expectations (Phase 1 expectations)
- CLI integration (Phase 2)

## Decisions

### Decision 1: Input Types and Deferral of temp_table

**Choice**: Implement cte, relation, jinja_context in Phase 1; defer temp_table to Phase 2

**Rationale**:
- CTE and relation are query composition (no database changes)
- jinja_context is simple variable injection
- temp_table requires table creation/cleanup infrastructure (deferred)
- Cleaner separation of concerns

**Alternatives considered**:
- Implement all input types together → Coupling temp_table to simpler types
- Implement no inputs in Phase 1 → Delays functionality

### Decision 2: Jinja-templated Identifiers via jinja_context Block

**Choice**: Define Jinja-bound data sources by nesting them inside `jinja_context:` blocks in the `given:` section

**Structure**:
```yaml
given:
  - jinja_context:
      my_variable_name:
        cte:
          rows: [...]  # or csv/sql
      another_variable:
        temp_table:
          sql: SELECT ...
      scalar_param: "2024-01-01"
```

**Rationale**:
- **Locality**: Variable definition and its data source are co-located, making intent clear
- **Separation of concerns**: Jinja-bound sources are visually distinct from traditional top-level sources
- **Ergonomics**: Eliminates boilerplate like "reference via alias" indirection
- **Clarity**: Variable name is explicit; no need for inference from targets

**Alternatives considered**:
- Separate indirection layer (top-level source with alias reference) → Boilerplate and multi-step lookup
- Global `variables:` block → Decouples variable from data, harder to reason about scope
- Inline Jinja in targets → Conflates identifier binding with string replacement mechanics

### Decision 2: Data Format Support

**Choice**: Support `sql`, `csv`, and `rows` for all input types

**Rationale**:
- SQL: Natural for data engineers, re-uses existing queries
- CSV: Portable, human-readable
- Rows: Inline YAML, no file dependencies
- Flexibility in test authoring

**Alternatives considered**:
- Single format only → Restrictive
- Format per input type → Complex

### Decision 3: Row Count Validation

**Choice**: Implement `row_count` expectation with `eq`, `min`, `max` operators

**Rationale**:
- Simplest assertion (just a number)
- Foundation for more complex assertions
- Fast to evaluate
- Common use case

**Alternatives considered**:
- Only rows_equal → Skips simple validation
- Add complex assertions in Phase 1 → Scope creep

### Decision 4: Alias Generation Strategy for Nested Data Sources

**Choice**: Auto-generate stable aliases using deterministic hash of (variable name + data content); allow user-provided `alias:` to override

**Derivation algorithm**:
1. If nested data source includes explicit `alias:` field → use that value
2. Else → compute `<variable_name>_<content_hash>` where content_hash is stable hash of serialized data

**Rationale**:
- **Deterministic**: Same test data produces same alias across execution runs (critical for reproducibility)
- **Automatic**: Users don't have to manually name every alias
- **Content-aware**: Alias changes if data changes, reducing risk of stale references
- **Override capability**: Users can provide explicit alias when defaults are inadequate
- **Not test-scoped**: Hash is not salted by test name (each test has its own isolation)

**Alternatives considered**:
- Sequential numbering (jinja_cte_1, jinja_cte_2, ...) → Non-deterministic, hard to debug
- Variable name only → Risk of collision if same variable used with different data
- User must always specify alias → Boilerplate burden

### Decision 5: Dual Role of targets Field and Alias Interaction

**Choice**: When both `alias` and `targets` are present on a nested data source:
- `alias` determines the actual CTE/table identifier name
- `targets` still drives relation substitution (string replacement patterns in SQL)

**Rationale**:
- **Flexibility**: Users can have clean identifier names while still controlling string replacement behavior
- **Orthogonal concerns**: Identifier naming and substitution patterns are separate decisions
- **Backward compatibility**: Existing relation/targets logic unchanged for top-level sources

**Alternatives considered**:
- `targets` takes precedence over `alias` → Confusing, breaks user intent for custom naming
- `alias` disables `targets` → Loses substitution flexibility
- Forbid both together → Unnecessarily restrictive

### Decision 6: Rendering Order: Jinja Templates Before Relation Substitution

**Choice**: Execute test phases in this order:
1. Parse YAML test definition
2. Parse SQL query structure and statement boundaries
3. Build full SQL batch (float temp_tables to top, CTEs below, main query last)
4. Build jinja_context dict from nested sources and scalar values
5. **Render Jinja templates** using jinja_context
6. **Apply relation substitutions** to the rendered output
7. Execute full SQL batch
8. Validate expectations

**Rationale**:
- **Jinja first**: Templates resolve to concrete identifiers before substitution patterns are applied
- **Substitution second**: Can reference both original table names and Jinja-resolved identifiers
- **No circularity**: Jinja variables cannot themselves depend on substitutions
- **Clear separation**: Two distinct transformation phases

**Consequence**: `relation.targets` cannot contain Jinja syntax (e.g., `targets: ["{{ my_table }}"]` is an error). Users should parameterize identifiers via jinja_context instead.

**Alternatives considered**:
- Simultaneous rendering and substitution → Circular dependencies, ambiguous semantics
- Substitution first → Can't reference Jinja-bound identifiers in relation patterns
- Separate passes per query section → Unnecessary complexity

### Decision 7: Collision Detection and Validation

**Choice**: At test setup time, detect and error if:
1. A Jinja variable name matches an auto-derived alias from a top-level data source's targets
2. A Jinja variable name is duplicated within the same jinja_context block

**Error message format**:
```
ConfigError: Jinja variable 'users_abc123' collides with auto-derived alias from top-level CTE targets. 
Rename the Jinja variable or provide explicit `alias:` on the conflicting data source.
```

**Rationale**:
- **Early detection**: Prevents silent shadowing or unexpected behavior at query time
- **Explicit naming**: Forces user awareness of alias derivation
- **Guidance**: Error messages suggest remediation steps

**Alternatives considered**:
- Silent shadowing (highest precedence wins) → Hard to debug, leads to surprises
- No collision checking → Users discover issues at query execution
- Forbid top-level sources if jinja_context present → Unnecessarily restrictive

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **CTE name collision** → CTE shadows actual tables in unexpected ways | Require fully-qualified table names; document best practices |
| **Relation substitution fragility** → Text substitution could match unintended patterns | Use careful regex or AST-based replacement |
| **CSV parsing issues** → Dialect differences, special characters | Use Python's csv library; document format requirements |
| **Alias collision between Jinja and top-level sources** → Silent shadowing leads to bugs | Implement early collision detection with clear error messages |
| **Jinja rendering complexity** → Template syntax errors hard to debug | Provide detailed error messages with line/column info; validate templates early |
| **Ordering assumption violations** → User assumes Jinja works in relation.targets | Document rendering order explicitly; error if Jinja syntax detected in targets |

## Migration Plan

Phase 1 Inputs builds on Phase 1 Core:
1. Parse and validate `given:` structure (including jinja_context blocks)
2. Implement jinja_context variable binding logic
3. Implement auto-generated alias derivation with collision detection
4. Implement each input type handler (CTE, relation, jinja_context)
5. Implement data format parsers (SQL, CSV, rows)
6. Implement CTE query composition
7. Implement relation substitution (with validation that targets has no Jinja syntax)
8. Implement test execution with rendering order: Jinja → relation substitution
9. Implement row_count expectation evaluation
10. Create comprehensive tests covering all Jinja scenarios and error cases

## Open Questions

- Should relation substitution be case-insensitive?
- How should CSV dialect be specified (auto-detect, explicit parameter)?
- Should unused CTEs be validated (warn if CTE defined but not used)?
- How granular should the content hash be for alias stability? (byte-level, row-level, column-level?)
- Should we allow Jinja filters or custom filters in templates? (e.g., `{{ table_name | upper }}`)
- What is the expected behavior if a Jinja-bound variable is defined but never used in the query?
