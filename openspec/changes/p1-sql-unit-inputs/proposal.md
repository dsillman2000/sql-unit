## Why

With the core testing framework in place, this phase adds input specification capabilities: the `given:` clause and its input types (`cte`, `relation`, `jinja_context`). This enables tests to set up data via CTEs, substitute table names for environment switching, and inject context variables—all essential for practical test scenarios.

## What Changes

- **Input specification (`given:` clause)** - Specify test input setup via four input types
- **CTE injection** - Create common table expressions with test data
- **Relation substitution** - Replace table names in queries (e.g., prod → test schema)
- **Data formats** - Support `sql`, `csv`, and `rows` data sources for all inputs
- **Multiple inputs** - Combine multiple input types in single test
- **Row count expectations** - Basic assertion: validate number of rows returned

## Capabilities

### New Capabilities

- `given-inputs`: Input specification using `cte` and `relation` types (temp_table deferred to Phase 2) with `sql`, `csv`, or `rows` data sources
- `row-count-expectations`: `row_count` expectation type with `eq`, `min`, and `max` operators

### Modified Capabilities

(None - additions only)

## Impact

- **Test expressiveness** - Tests can now set up data dynamically without pre-seeding database
- **Code organization** - Tests encapsulate their own data setup
- **Environment flexibility** - Tests can reference test databases via relation substitution
- **Data formats** - Support multiple ways to specify test data (inline or structured)
