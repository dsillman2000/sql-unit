## Context

Building on Phase 1 Core and Phase 1 Inputs, this phase adds sophisticated result validation via `rows_equal` expectation and external data reference support. Tests must validate that queries return expected result sets, not just row counts. This requires DataFrame comparison, ordering normalization, and integration with yaml-reference for external fixture files.

Key constraints:
- Depends on Phase 1 Core (execution engine) and Phase 1 Inputs (data parsing)
- Comparison must be order-independent (SQL has no guaranteed row order)
- Column order should not affect comparison
- Data types must be handled correctly (NULL vs empty string)
- yaml-reference provides external file loading mechanism

## Goals / Non-Goals

**Goals:**
- Implement `rows_equal` expectation with pandas-based comparison
- Support order-independent row comparison
- Support order-independent column comparison
- Handle multiple data types correctly
- Implement yaml-reference integration (`!reference`, `!reference-all`)
- Provide clear diffs on expectation failure
- Support external fixture files (YAML, CSV, SQL)

**Non-Goals:**
- Custom comparison logic (use pandas)
- Test data generation (external fixtures only)
- Row-level assertion details (aggregate comparison)

## Decisions

### Decision 1: Pandas for Row Comparison

**Choice**: Use pandas DataFrames for result comparison and diff output

**Rationale**:
- Order-independent comparison (sort then compare)
- Built-in type handling (strings, numbers, NULLs)
- `.assert_frame_equal()` provides friendly diffs
- Well-tested, stable library
- Familiar to data engineers

**Alternatives considered**:
- Custom comparison logic → Duplicates pandas, harder to debug
- SQL-based comparison → Complex, database-specific

### Decision 2: Column and Row Normalization

**Choice**: Sort columns alphabetically, then sort rows by all columns before comparing

**Rationale**:
- Matches user expectation: "I expect these rows, regardless of order"
- SQL has no guaranteed row order without ORDER BY
- Column order in SELECT is implementation detail
- Deterministic and reproducible

**Alternatives considered**:
- Exact positional match → Brittle, breaks on SQL refactoring
- Custom sort order → Requires user specification

### Decision 3: yaml-reference Integration (COMPLETED)

**Choice**: Support `!reference` and `!reference-all` YAML tags from yaml-reference library

**Rationale**:
- Enables DRY fixture reuse
- Standard YAML extension mechanism
- Supports multiple file formats (YAML, CSV, SQL)
- Optional feature (inline data always works)
- `!reference-all` can return sequences of tests for use with multi-test doc syntax (p1-sql-unit-core)
- Path resolution: relative to test file, governed by yaml-reference

**Alternatives considered**:
- No external references → Encourages duplication
- Custom include syntax → Duplicates yaml-reference

### Decision 4: Column Name Case Insensitivity

**Choice**: Column names in expected data are case-insensitive (lowercase can refer to uppercase)

**Rationale**:
- SQL column names vary by database (PostgreSQL preserves case, SQLite uppercases)
- User convenience: write `name` to match `NAME`, `Name`, or `name`
- Normalize all column names to lowercase for comparison

**Alternatives considered**:
- Case-sensitive matching → Brittle, breaks across databases
- User-configurable case sensitivity → Adds complexity

### Decision 5: NULL and Omitted Column Handling

**Choice**: 
- Explicit NULL in expected data must match NULL in query result
- Omitted columns in expected data are ignored (not compared)

**Rationale**:
- Explicit NULL: User explicitly expects NULL value, must match
- Omitted column: "I don't care about this column" semantics
- Aligns with practical testing: validate important columns, ignore noise

**Alternatives considered**:
- Omitted = NULL → Confusing semantics
- Omitted = error → Too restrictive

### Decision 6: Data Type Translation

**Choice**: SQL types from database are parsed into Python native types for comparison

**Rationale**:
- Database drivers return Python types already (int, str, float, bool, None)
- Compare native Python types in expectations
- No coercion between string "42" and int 42—database driver handles this

**Alternatives considered**:
- Type coercion → Adds complexity, hidden bugs
- String-only comparison → Loses type validation

### Decision 7: Float and Numeric Precision

**Choice**: Float precision is configurable via sql-unit.yaml (e.g., `float_precision: 8`)

**Rationale**:
- Makes precision behavior deterministic and explicit
- Consistent behavior regardless of database backend
- Users can tune tolerance per-project in config
- If not specified, use reasonable default (e.g., 1e-10)

**Configuration**:
```yaml
# sql-unit.yaml
float_precision: 8  # Optional - defaults to system default
```

**Alternatives considered**:
- Database manager owns → Inconsistent across backends
- Hard-coded tolerance → No user control

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Order-independent hiding bugs** → Tests pass despite wrong result order | Document semantics; recommend explicit ORDER BY in spec when order matters |
| **Large result set performance** → DataFrame conversion slow for huge datasets | Acceptable trade-off for clarity; document limitation |
| **NULL handling edge cases** → NULL comparison behavior varies by database | Test thoroughly; document NULL semantics |
| **File reference path resolution** → Relative paths can be fragile | Document path resolution rules (relative to test file or project root) |

## Migration Plan

Phase 1 Expectations builds on Phase 1 Core and Phase 1 Inputs:
1. ~~Integrate pandas library~~ Integrate pandas library
2. ~~Integrate yaml-reference library~~ (implemented in parser)
3. Implement DataFrame comparison logic
4. Implement normalization (column/row sorting)
5. Implement rows_equal expectation
6. ~~Implement external file reference loading~~ (implemented in parser)
7. Create comprehensive tests

## Open Questions

(None currently - all decisions captured above)
