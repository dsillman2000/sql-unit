## 1. Given Clause Parsing

- [x] 1.1 Create data structures for input specifications (InputSpec, InputType)
- [x] 1.2 Parse `given:` clause from test YAML
- [x] 1.3 Validate `given:` structure (required/optional fields per input type)
- [x] 1.4 Implement error handling for malformed `given:` clauses


## 2. Data Format Parsers

- [x] 2.1 Implement SQL data format parser (SELECT statement validation)
- [x] 2.2 Implement CSV data format parser (header row, data rows)
- [x] 2.3 Implement rows data format parser (YAML list of dicts)
- [x] 2.4 Create DataSource abstraction covering all three formats
- [x] 2.5 Add error handling for invalid data in each format

## 3. CTE Input Type Implementation

- [x] 3.1 Create CTEInput class
- [x] 3.2 Implement CTE query generation from data source
- [x] 3.3 Implement CTE injection into test SQL (WITH ... SELECT composition)
- [x] 3.4 Handle schema-qualified CTE targets (e.g., `db.schema.table`)
- [x] 3.5 Support multiple CTEs in single test
- [x] 3.6 Add tests for CTE scenarios

## 4. Relation Input Type Implementation

- [x] 4.1 Create RelationInput class
- [x] 4.2 Implement text-based relation name substitution in SQL
- [x] 4.3 Handle schema-qualified table names (e.g., `prod.users` → `test.users`)
- [x] 4.4 Support multiple relation substitutions in single test
- [x] 4.5 Add safety checks to prevent accidental pattern matches
- [x] 4.6 Add tests for relation substitution scenarios

## 5. Jinja Context Nested Data Sources Implementation

- [x] 5.1 Create nested jinja_context data structure (variable name → data source binding)
- [x] 5.2 Implement nested CTE processing in jinja_context
- [x] 5.3 Implement nested temp_table processing in jinja_context (deferred from Phase 2)
- [x] 5.4 Implement auto-generated alias derivation using stable content hash
- [x] 5.5 Support explicit `alias:` override for nested data sources
- [x] 5.6 Support scalar values in jinja_context (non-data-source variables)
- [x] 5.7 Implement collision detection between Jinja variables and top-level target aliases
- [x] 5.8 Implement duplicate Jinja variable name detection in same jinja_context block
- [x] 5.9 Implement rendering order: Jinja templates first, then relation substitution
- [x] 5.10 Validate that relation.targets cannot contain Jinja syntax (error)
- [x] 5.11 Integrate with Phase 1 Jinja renderer for nested data source execution
- [x] 5.12 Add tests for nested jinja_context scenarios

## 6. Row Count Expectation Implementation

- [x] 6.1 Create RowCountExpectation class
- [x] 6.2 Implement `eq` operator (exact match)
- [x] 6.3 Implement `min` operator (inclusive minimum)
- [x] 6.4 Implement `max` operator (inclusive maximum)
- [x] 6.5 Implement expectation evaluation against result set
- [x] 6.6 Create expectation failure reporting
- [x] 6.7 Add tests for row_count scenarios

## 7. Input Composition and Execution

- [x] 7.1 Implement InputSetup orchestrator (combine multiple inputs)
- [x] 7.2 Implement execution order: data parsing → CTE injection → relation substitution → jinja context injection
- [x] 7.3 Add error handling for input conflicts
- [x] 7.4 Create integration tests combining multiple input types

## 8. Specs Implementation

- [x] 8.1 Implement `given-inputs` spec requirements (28 comprehensive spec validation tests)
- [n/a] 8.2 Implement `row-count-expectations` spec requirements (moved to p1-sql-unit-expectations - row_count is an "expect", not "given")

## 9. Unit and Integration Tests

- [x] 9.1 Create unit tests for input parsing
- [x] 9.2 Create unit tests for each data format parser
- [x] 9.3 Create tests for CTE injection
- [x] 9.4 Create tests for relation substitution
- [x] 9.5 Create tests for jinja_context
- [x] 9.6 Create integration tests combining inputs and expectations
- [x] 9.7 Achieve >80% code coverage
