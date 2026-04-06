## Why

SQL testing is typically fragmented across multiple files and tools, disconnected from the actual SQL code. This phase establishes the core foundation: YAML doc-comment syntax for embedding tests directly in SQL files, binding tests to SQL statements, Jinja2 template support, and the core test execution engine. This enables SQL-first testing as the foundation for all subsequent features.

## What Changes

- **YAML doc-comment syntax** - Tests are embedded in `/* #! sql-unit ... */` blocks directly above SQL statements
- **Test binding mechanism** - Tests are bound to their SQL statement via doc comment proximity and `name:` identifier
- **Jinja2 template support** - SQL files can use Jinja variables and template syntax
- **Test execution engine** - Core runner that parses tests, renders SQL, executes queries, and validates results
- **Project setup with uv** - Initialize project using uv as the modern Python package manager

## Capabilities

### New Capabilities

- `doc-comment-format`: YAML structure for test specification embedded in SQL block comments, including the `#! sql-unit` marker, `name`, `description`, `given`, and `expect` keys
- `statement-identification`: Binding mechanism for tests to SQL statements; rules for which statements are testable (SELECT-only) and how to define multiple tests per statement
- `jinja-templating`: Support for Jinja template variables in SQL files, with context injection via `jinja_context` in tests

### Modified Capabilities

(None - this is a new specification phase with no existing capabilities being changed)

## Impact

- **SQL files** - Test infrastructure added directly to SQL source files (no new file types required, backward compatible)
- **Python package** - New uv-based project structure with pyproject.toml, dependencies (SQLAlchemy, pandas, Jinja2), and test runner
- **Jinja2** - Dependency required for SQL template rendering
- **Core execution model** - Foundation for all downstream features (inputs, expectations, CLI)
