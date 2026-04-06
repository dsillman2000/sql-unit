## 1. Project Setup with uv

- [ ] 1.1 Initialize uv project with `uv init`
- [ ] 1.2 Create pyproject.toml with project metadata and uv configuration
- [ ] 1.3 Create project structure: src/sql_unit/, tests/, docs/
- [ ] 1.4 Add core dependencies: SQLAlchemy, pandas, Jinja2, PyYAML
- [ ] 1.5 Add development dependencies: pytest, pytest-cov
- [ ] 1.6 Configure uv.lock file for reproducible builds
- [ ] 1.7 Set up virtual environment via uv

## 2. YAML Parser and Test Discovery

- [ ] 2.1 Implement SQL block comment parser (extract `/* #! sql-unit ... */` blocks)
- [ ] 2.2 Implement YAML parsing of comment content with error handling
- [ ] 2.3 Implement test binding to immediately following SQL statement
- [ ] 2.4 Validate that only SELECT statements have tests
- [ ] 2.5 Support multiple tests per statement (via `---` separator)
- [ ] 2.6 Validate test name uniqueness within a file
- [ ] 2.7 Implement file/directory traversal for test discovery
- [ ] 2.8 Create TestDefinition and TestFile data structures

## 3. Jinja2 Template Rendering

- [ ] 3.1 Integrate Jinja2 template engine
- [ ] 3.2 Implement SQL rendering with basic variable substitution
- [ ] 3.3 Implement error handling for undefined variables
- [ ] 3.4 Implement error handling for syntax errors in templates
- [ ] 3.5 Add SQL injection protection for context variables (parameterization)
- [ ] 3.6 Create TemplateRenderer class with test context support

## 4. Database Connection Management

- [ ] 4.1 Create database connection manager using SQLAlchemy
- [ ] 4.2 Implement connection factory supporting multiple database types
- [ ] 4.3 Implement SQLite support (including :memory:)
- [ ] 4.4 Implement connection pooling
- [ ] 4.5 Add transaction management for test isolation

## 5. Test Execution Engine

- [ ] 5.1 Create TestRunner class for orchestrating test execution
- [ ] 5.2 Implement test execution pipeline: parse → render → execute → validate
- [ ] 5.3 Implement query execution via SQLAlchemy
- [ ] 5.4 Implement result set retrieval as rows (dicts)
- [ ] 5.5 Create ResultSet data structure
- [ ] 5.6 Implement transaction handling: begin → execute → rollback/commit
- [ ] 5.7 Implement test result tracking (pass/fail/error)

## 6. Error Handling and Reporting

- [ ] 6.1 Create custom exception hierarchy (ParserError, RendererError, ExecutionError)
- [ ] 6.2 Implement error messages with file location and line numbers
- [ ] 6.3 Include test identification (`<filepath>::<test_name>`) in all errors
- [ ] 6.4 Include executed SQL (with resolved Jinja) in error output
- [ ] 6.5 Create ErrorReport data structure

## 7. Unit Tests for Phase 1

- [ ] 7.1 Create unit tests for YAML parser
- [ ] 7.2 Create unit tests for SQL statement identification
- [ ] 7.3 Create unit tests for Jinja2 renderer
- [ ] 7.4 Create unit tests for TemplateRenderer error handling
- [ ] 7.5 Create integration tests with SQLite (parser → render → execute)
- [ ] 7.6 Create tests for error cases and edge cases
- [ ] 7.7 Achieve >80% code coverage for Phase 1 code

## 8. Basic Specs Implementation

- [ ] 8.1 Implement `doc-comment-format` spec requirements
- [ ] 8.2 Implement `statement-identification` spec requirements
- [ ] 8.3 Implement `jinja-templating` spec requirements (basic context injection)
