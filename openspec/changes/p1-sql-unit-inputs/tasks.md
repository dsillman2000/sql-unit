## 1. Given Clause Parsing

- [ ] 1.1 Create data structures for input specifications (InputSpec, InputType)
- [ ] 1.2 Parse `given:` clause from test YAML
- [ ] 1.3 Validate `given:` structure (required/optional fields per input type)
- [ ] 1.4 Implement error handling for malformed `given:` clauses

## 2. Data Format Parsers

- [ ] 2.1 Implement SQL data format parser (SELECT statement validation)
- [ ] 2.2 Implement CSV data format parser (header row, data rows)
- [ ] 2.3 Implement rows data format parser (YAML list of dicts)
- [ ] 2.4 Create DataSource abstraction covering all three formats
- [ ] 2.5 Add error handling for invalid data in each format

## 3. CTE Input Type Implementation

- [ ] 3.1 Create CTEInput class
- [ ] 3.2 Implement CTE query generation from data source
- [ ] 3.3 Implement CTE injection into test SQL (WITH ... SELECT composition)
- [ ] 3.4 Handle schema-qualified CTE targets (e.g., `db.schema.table`)
- [ ] 3.5 Support multiple CTEs in single test
- [ ] 3.6 Add tests for CTE scenarios

## 4. Relation Input Type Implementation

- [ ] 4.1 Create RelationInput class
- [ ] 4.2 Implement text-based relation name substitution in SQL
- [ ] 4.3 Handle schema-qualified table names (e.g., `prod.users` → `test.users`)
- [ ] 4.4 Support multiple relation substitutions in single test
- [ ] 4.5 Add safety checks to prevent accidental pattern matches
- [ ] 4.6 Add tests for relation substitution scenarios

## 5. Jinja Context Nested Data Sources Implementation

- [ ] 5.1 Create nested jinja_context data structure (variable name → data source binding)
- [ ] 5.2 Implement nested CTE processing in jinja_context
- [ ] 5.3 Implement nested temp_table processing in jinja_context (deferred from Phase 2)
- [ ] 5.4 Implement auto-generated alias derivation using stable content hash
- [ ] 5.5 Support explicit `alias:` override for nested data sources
- [ ] 5.6 Support scalar values in jinja_context (non-data-source variables)
- [ ] 5.7 Implement collision detection between Jinja variables and top-level target aliases
- [ ] 5.8 Implement duplicate Jinja variable name detection in same jinja_context block
- [ ] 5.9 Implement rendering order: Jinja templates first, then relation substitution
- [ ] 5.10 Validate that relation.targets cannot contain Jinja syntax (error)
- [ ] 5.11 Integrate with Phase 1 Jinja renderer for nested data source execution
- [ ] 5.12 Add tests for nested jinja_context scenarios

## 6. Row Count Expectation Implementation

- [ ] 6.1 Create RowCountExpectation class
- [ ] 6.2 Implement `eq` operator (exact match)
- [ ] 6.3 Implement `min` operator (inclusive minimum)
- [ ] 6.4 Implement `max` operator (inclusive maximum)
- [ ] 6.5 Implement expectation evaluation against result set
- [ ] 6.6 Create expectation failure reporting
- [ ] 6.7 Add tests for row_count scenarios

## 7. Input Composition and Execution

- [ ] 7.1 Implement InputSetup orchestrator (combine multiple inputs)
- [ ] 7.2 Implement execution order: data parsing → CTE injection → relation substitution → jinja context injection
- [ ] 7.3 Add error handling for input conflicts
- [ ] 7.4 Create integration tests combining multiple input types

## 8. Specs Implementation

- [ ] 8.1 Implement `given-inputs` spec requirements
- [ ] 8.2 Implement `row-count-expectations` spec requirements

## 9. Unit and Integration Tests

- [ ] 9.1 Create unit tests for input parsing
- [ ] 9.2 Create unit tests for each data format parser
- [ ] 9.3 Create tests for CTE injection
- [ ] 9.4 Create tests for relation substitution
- [ ] 9.5 Create tests for jinja_context
- [ ] 9.6 Create integration tests combining inputs and expectations
- [ ] 9.7 Achieve >80% code coverage
