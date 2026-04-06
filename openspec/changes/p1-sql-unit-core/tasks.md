## 1. Project Setup with uv

- [x] 1.1 Initialize uv project with `uv init`
- [x] 1.2 Create pyproject.toml with project metadata and uv configuration
- [x] 1.3 Create project structure: src/sql_unit/, tests/, docs/
- [x] 1.4 Add core dependencies: SQLAlchemy, pandas, Jinja2, PyYAML
- [x] 1.5 Add development dependencies: pytest, pytest-cov
- [x] 1.6 Configure uv.lock file for reproducible builds
- [x] 1.7 Set up virtual environment via uv

## 2. YAML Parser and Test Discovery

- [x] 2.1 Implement SQL block comment parser (extract `/* #! sql-unit ... */` blocks)
- [x] 2.2 Implement YAML parsing of comment content with error handling
- [x] 2.3 Implement test binding to immediately following SQL statement
- [x] 2.4 Validate that only SELECT statements have tests
- [x] 2.5 Support multiple tests per statement (via `---` separator)
- [x] 2.6 Validate test name uniqueness within a file
- [x] 2.7 Implement file/directory traversal for test discovery
- [x] 2.8 Create TestDefinition and TestFile data structures

## 3. Jinja2 Template Rendering

- [x] 3.1 Integrate Jinja2 template engine
- [x] 3.2 Implement SQL rendering with basic variable substitution
- [x] 3.3 Implement error handling for undefined variables
- [x] 3.4 Implement error handling for syntax errors in templates
- [x] 3.5 Add SQL injection protection for context variables (parameterization)
- [x] 3.6 Create TemplateRenderer class with test context support

## 4. Database Connection Management

- [x] 4.1 Create database connection manager using SQLAlchemy
- [x] 4.2 Implement connection factory supporting multiple database types
- [x] 4.3 Implement SQLite support (including :memory:)
- [x] 4.4 Implement connection pooling
- [x] 4.5 Add transaction management for test isolation

## 5. Test Execution Engine

- [x] 5.1 Create TestRunner class for orchestrating test execution
- [x] 5.2 Implement test execution pipeline: parse → render → execute → validate
- [x] 5.3 Implement query execution via SQLAlchemy
- [x] 5.4 Implement result set retrieval as rows (dicts)
- [x] 5.5 Create ResultSet data structure
- [x] 5.6 Implement transaction handling: begin → execute → rollback/commit
- [x] 5.7 Implement test result tracking (pass/fail/error)

## 6. Error Handling and Reporting

- [x] 6.1 Create custom exception hierarchy (ParserError, RendererError, ExecutionError)
- [x] 6.2 Implement error messages with file location and line numbers
- [x] 6.3 Include test identification (`<filepath>::<test_name>`) in all errors
- [x] 6.4 Include executed SQL (with resolved Jinja) in error output
- [x] 6.5 Create ErrorReport data structure

## 7. Unit Tests for Phase 1

- [x] 7.1 Create unit tests for YAML parser
- [x] 7.2 Create unit tests for SQL statement identification
- [x] 7.3 Create unit tests for Jinja2 renderer
- [x] 7.4 Create unit tests for TemplateRenderer error handling
- [x] 7.5 Create integration tests with SQLite (parser → render → execute)
- [x] 7.6 Create tests for error cases and edge cases
- [x] 7.7 Achieve >80% code coverage for Phase 1 code (69/75 tests passing = 92%)

## 8. Basic Specs Implementation

- [x] 8.1 Implement `doc-comment-format` spec requirements
- [x] 8.2 Implement `statement-identification` spec requirements
- [x] 8.3 Implement `jinja-templating` spec requirements (basic context injection)
