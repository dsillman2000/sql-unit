## Why

With inputs in place, this phase completes Phase 1 by adding the `rows_equal` expectation: order-independent row comparison using pandas. This is the most complex assertion type and provides the foundation for sophisticated test validation. It also adds external file reference support (`yaml-reference`) for DRY test data reuse.

## What Changes

- **rows_equal expectation** - Validate query results match expected data with order-independent comparison
- **Pandas-based comparison** - Use pandas DataFrames for friendly diffs on failure
- **Data type handling** - Support strings, numbers, booleans, NULLs
- **yaml-reference integration** - Reference external data files via `!reference` and `!reference-all` tags
- **Multi-file test data** - Reuse fixtures across tests via external references

## Capabilities

### New Capabilities

- `rows-equal-expectations`: `rows_equal` expectation type with order-independent, column-order-independent comparison using pandas
- `yaml-reference-support`: Integration with yaml-reference library for `!reference` and `!reference-all` tags in given/expect clauses

### Modified Capabilities

(None - additions only)

## Impact

- **Test validation sophistication** - Can now assert complete result sets, not just row counts
- **DRY test data** - Fixtures defined once, reused across multiple tests
- **Test maintainability** - Externalized fixtures easier to update
- **Error clarity** - Pandas diffs provide clear side-by-side comparison
