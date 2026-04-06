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
- Support jinja_context variable injection
- Support `sql`, `csv`, and `rows` data formats
- Implement row_count expectation with `eq`, `min`, `max`
- Enable combining multiple input types
- Provide clear error messages for input errors

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

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **CTE name collision** → CTE shadows actual tables in unexpected ways | Require fully-qualified table names; document best practices |
| **Relation substitution fragility** → Text substitution could match unintended patterns | Use careful regex or AST-based replacement |
| **CSV parsing issues** → Dialect differences, special characters | Use Python's csv library; document format requirements |

## Migration Plan

Phase 1 Inputs builds on Phase 1 Core:
1. Parse and validate `given:` structure
2. Implement each input type handler
3. Implement data format parsers (SQL, CSV, rows)
4. Implement CTE query composition
5. Implement relation substitution
6. Implement row_count expectation evaluation
7. Create comprehensive tests

## Open Questions

- Should relation substitution be case-insensitive?
- How should CSV dialect be specified (auto-detect, explicit parameter)?
- Should unused CTEs be validated (warn if CTE defined but not used)?
