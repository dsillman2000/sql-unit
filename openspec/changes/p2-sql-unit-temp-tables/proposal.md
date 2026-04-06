## Why

Phase 1 established the foundation with CTEs and relation substitution for input setup. This phase adds `temp_table` input type, enabling tests to create temporary tables with test data. Temporary tables provide stronger isolation than CTEs and enable testing complex schemas with multiple related tables.

## What Changes

- **Temporary table creation** - Create and populate temporary tables per test
- **Schema-qualified tables** - Support schema.table naming
- **Auto-cleanup** - Temporary tables dropped after test completion
- **Per-database syntax** - Handle database-specific temp table creation

## Capabilities

### New Capabilities

- `given-inputs` (temp_table extension): temp_table input type supporting SQL, CSV, and rows data sources with schema qualification

### Modified Capabilities

(None - extends given-inputs from Phase 1)

## Impact

- **Test isolation** - Temporary tables isolate test data from permanent schema
- **Complex schema testing** - Enable tests involving multiple related tables
- **Transaction safety** - Temporary tables with transaction rollback
