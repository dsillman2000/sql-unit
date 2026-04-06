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

### Decision 4: Alias Generation Strategy for All Data Sources

**Choice**: Auto-generate stable aliases using deterministic hash of (targets/variable_name + data content) for both top-level and nested data sources; allow user-provided `alias:` to override

**Derivation algorithm**:
1. If data source includes explicit `alias:` field → use that value
2. Else:
   - For top-level CTEs: compute `<sanitized_targets>_<content_hash>` (e.g., `db_schema_users_abc123`)
   - For nested (Jinja-bound) sources: compute `<variable_name>_<content_hash>` (e.g., `my_users_xyz789`)

**Critical consequence**: Queries must reference generated alias names, not the original sanitized target names. The `targets` field on top-level CTEs is used only for relation substitution patterns (see Decision 5), not for naming the CTE itself.

**Example**:
```yaml
given:
  - cte:
      targets: ["users"]
      rows: [...]  # hash derives as abc123

# Query must use the generated alias:
then: |
  SELECT * FROM users_abc123  # NOT FROM users
```

**Rationale**:
- **Deterministic**: Same test data produces same alias across execution runs (critical for reproducibility)
- **Automatic**: Users don't have to manually name every alias
- **Content-aware**: Alias changes if data changes, reducing risk of stale references
- **Override capability**: Users can provide explicit alias when defaults are inadequate
- **Unified collision detection**: All sources (top-level and Jinja) use same hashing scheme
- **Not test-scoped**: Hash is not salted by test name (each test has its own isolation)

**Alternatives considered**:
- Sequential numbering (jinja_cte_1, jinja_cte_2, ...) → Non-deterministic, hard to debug
- Variable name only → Risk of collision if same variable used with different data
- User must always specify alias → Boilerplate burden
- Sanitized target names for top-level CTEs (original design) → Loses collision detection benefits, requires separate hashing for Jinja variables

### Decision 5: Role of targets Field in CTE Definition

**Choice**: The `targets` field on a CTE (whether top-level or nested) serves **only** for relation substitution patterns, not for CTE naming.

**Clarification**:
- `alias` (when provided) or generated hash determines the CTE identifier name (what you write in SQL)
- `targets` specifies which original table names should be replaced when `relation` substitution is applied
- This allows tests to define a CTE from production schema and substitute references to that production table name in the query

**Example**:
```yaml
given:
  - cte:
      targets: ["prod.users"]      # Original table name
      rows: [...]                  # Data for the CTE
      # Generated alias: prod_users_abc123

  - relation:
      targets: ["prod.users"]      # Find references to this
      replacement: "prod_users_abc123"  # Replace with the CTE name

then: |
  SELECT * FROM prod.users  # Will be substituted to reference the CTE
```

**Rationale**:
- **Clarity**: `targets` is explicitly about substitution patterns
- **Flexibility**: Users can have generated CTE names while controlling what gets replaced
- **Orthogonal concerns**: Identifier naming and substitution patterns are separate decisions

**Alternatives considered**:
- `targets` takes precedence over `alias` → Confusing, breaks user intent for custom naming
- `alias` disables `targets` → Loses substitution flexibility
- Forbid both together → Unnecessarily restrictive

### Decision 6: Relation Substitution via SQL AST

**Choice**: Use SQL AST parsing (sqlparse library) to identify and replace identifier nodes matching the target name, rather than text-based regex replacement.

**Implementation strategy**:
1. Parse the SQL query using sqlparse to build an AST
2. Traverse AST to find identifier nodes (table/CTE names)
3. Match identifiers against `targets` (case-insensitive by default)
4. For schema-qualified targets (e.g., `prod.users`), match only schema-qualified identifiers in the query; bare `users` will not match
5. Replace matched identifier nodes with the replacement value

**Rationale**:
- **Safety**: Avoids substring matches (e.g., `targets: ["users"]` won't match `users_archive` or `user_id`)
- **Correctness**: Identifier semantics handled by parser, not regex heuristics
- **Robustness**: Handles quoted identifiers, schema qualification, and edge cases naturally
- **Maintainability**: Clear separation between parsing and replacement logic

**Alternatives considered**:
- Text-based regex replacement → Brittle, susceptible to false matches
- Manual string parsing → Duplicates parser logic, error-prone

### Decision 8: Collision Detection and Validation

**Choice**: At test setup time, detect and error if:
1. A Jinja variable name matches an auto-derived or user-provided alias from any data source (top-level or nested)
2. A Jinja variable name is duplicated within the same jinja_context block

**Error message format**:
```
ConfigError: Jinja variable 'users_abc123' collides with auto-derived alias from CTE data source. 
Rename the Jinja variable or provide explicit `alias:` on the conflicting data source.
```

**Rationale**:
- **Early detection**: Prevents silent shadowing or unexpected behavior at query time
- **Explicit naming**: Forces user awareness of alias derivation
- **Guidance**: Error messages suggest remediation steps
- **Unified scheme**: All data sources use hashed aliases, so collision detection applies uniformly

**Alternatives considered**:
- Silent shadowing (highest precedence wins) → Hard to debug, leads to surprises
- No collision checking → Users discover issues at query execution
- Forbid top-level sources if jinja_context present → Unnecessarily restrictive

### Decision 9: Jinja Filters and Environment Configuration

**Choice**: Enable all Jinja2 built-in filters (e.g., `upper`, `lower`, `default`, `length`, etc.) in SQL templates. Additionally, SQLUnitEnvironment will provide a custom `default` filter for robustness.

**Usage examples**:
```yaml
given:
  - jinja_context:
      table_name: "users"
      start_date: "2024-01-01"

then: |
  SELECT * FROM {{ table_name | upper }}
  WHERE created_at >= '{{ start_date | default("2020-01-01") }}'
```

**Rationale**:
- **Flexibility**: Filters enable common transformations (case conversion, defaults, formatting) without needing separate context values
- **Robustness**: `default` filter handles missing variables gracefully
- **Familiarity**: Leverages standard Jinja2 idioms

**Scope**:
- All Jinja2 built-in filters available
- Custom filters must be registered explicitly (not in Phase 1 scope)

**Alternatives considered**:
- No filters (minimal implementation) → Limits expressiveness
- Custom filters only → Loses Jinja2 built-in benefits

## Execution Order and Test Lifecycle

The following execution sequence ensures proper interaction between Jinja rendering, CTE injection, and relation substitution:

1. **Parse YAML test definition** → Extract `given:` inputs, SQL query, expectations
2. **Build jinja_context dict** → Collect nested data sources and scalar values from `jinja_context:` blocks
3. **Render Jinja templates in SQL query** → Use jinja_context to resolve all `{{ ... }}` expressions, producing concrete SQL with identifier names
4. **Parse rendered SQL** → Identify query structure and statement boundaries
5. **Inject CTEs** → Build WITH clause from all CTE inputs and prepend to rendered SQL
6. **Apply relation substitutions** → Use AST-based replacement to substitute table names in the fully-rendered SQL (no Jinja syntax can be present)
7. **Execute SQL batch** → Run against database
8. **Validate expectations** → Check row count, etc.

**Critical constraints**:
- Jinja rendering happens first, so all `{{ ... }}` must resolve to concrete values before CTE/relation logic sees the SQL
- `relation.targets` cannot contain Jinja syntax; dynamic identifiers must be parameterized through jinja_context
- Unused Jinja variables are allowed (no warning or error)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Hash collisions** → Different data produces same alias | Use cryptographic hash (e.g., SHA256); collisions statistically negligible |
| **Generated aliases are opaque** → `users_abc123` less readable than `users` | Document alias generation scheme; provide clear error messages that show generated names |
| **CTE name collision if AST parser missed identifiers** → CTE shadows actual table unexpectedly | Comprehensive testing of sqlparse; document sqlparse limitations; require fully-qualified names when ambiguity exists |
| **Relation substitution fragility** → AST parsing edge cases (complex CTEs, subqueries) | Use sqlparse library (mature, well-tested); add extensive tests for edge cases |
| **CSV parsing issues** → Dialect differences, special characters | Auto-detect common delimiters; use Python's csv library; document format requirements |
| **Jinja rendering errors** → Template syntax errors hard to debug | Provide detailed error messages with line/column info; validate templates early |
| **Ordering assumption violations** → User tries Jinja syntax in relation.targets | Validate that targets has no Jinja syntax at setup time; error with guidance |


## Implementation Approach

Phase 1 Inputs builds on Phase 1 Core:

1. **Parse and validate `given:` structure** (including jinja_context blocks)
2. **Implement data format parsers** (SQL, CSV, rows) with auto-detection of CSV dialects
3. **Implement alias derivation** (stable hash-based for all data sources) with collision detection
4. **Implement CTE input type** 
   - Parse CTE definitions
   - Generate stable aliases
   - Inject CTEs into rendered SQL as WITH clause
5. **Implement relation input type**
   - Parse relation definitions
   - Use sqlparse to build AST
   - Perform case-insensitive identifier matching and substitution
6. **Implement jinja_context nested sources**
   - Parse nested CTE and temp_table definitions
   - Build jinja_context dict with variable bindings
   - Apply alias generation and collision detection
7. **Implement test execution lifecycle**
   - Build jinja_context
   - Render Jinja templates in SQL (all filters enabled)
   - Parse rendered SQL
   - Inject CTEs
   - Apply relation substitutions
   - Execute SQL batch
8. **Implement row_count expectation**
   - Parse row_count expectations
   - Evaluate eq, min, max operators
9. **Create comprehensive tests** covering all scenarios, edge cases, and error conditions

## Open Questions

The following decisions have been clarified through user feedback and are no longer open:

- ~~Should relation substitution be case-insensitive?~~ **Yes, case-insensitive by default.**
- ~~How should CSV dialect be specified?~~ **Auto-detect common delimiters (comma, tab, pipe, semicolon).**
- ~~Should unused CTEs/variables be warned about?~~ **Unused variables allowed silently; no warnings.**
- ~~Should we allow Jinja filters?~~ **Yes, all Jinja2 built-in filters enabled, plus custom `default` filter in SQLUnitEnvironment.**
- ~~Should top-level CTEs get hashed aliases?~~ **Yes, all data sources use stable hashed aliases deterministically.**

Remaining open questions for future phases:

- Should we provide a way to audit/inspect generated aliases (e.g., via a `--show-aliases` flag in CLI)?
- Should unused CTEs be logged as debug information?
- How granular should the content hash be for alias stability? (byte-level, row-level, column-level?)
- Should schema-qualified relation targets (e.g., `prod.users`) match only schema-qualified references, or also bare names?
