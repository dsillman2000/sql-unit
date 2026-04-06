"""Integration tests for the complete sql-unit pipeline."""

import pytest

from sql_unit import (
    ConnectionConfig,
    ParserError,
    SqlBlockCommentParser,
    StatementValidator,
    TemplateRenderer,
    TestDefinition,
    TestRunner,
)


class TestCompleteExecutionPipeline:
    """Integration tests for parse → render → execute → validate pipeline."""
    
    def test_simple_test_execution(self, tmp_path):
        """Test end-to-end execution: parse → render → execute."""
        # Create a SQL file with a test
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("""/* #! sql-unit
name: test_select_literal
given: {}
expect:
  rows_equal:
    - result: 42
*/
SELECT 42 as result;
        """)
        
        # Parse the file
        with open(sql_file) as f:
            sql_content = f.read()
        
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql_content)
        assert len(blocks) == 1
        
        # Parse YAML
        parsed = SqlBlockCommentParser.parse_yaml_content(blocks[0][0], blocks[0][1])
        assert len(parsed) == 1
        assert parsed[0]["name"] == "test_select_literal"
        
        # Build test definition
        test = TestDefinition(
            name=parsed[0]["name"],
            given=parsed[0].get("given", {}),
            expect=parsed[0].get("expect", {}),
            filepath=str(sql_file),
            line_number=blocks[0][1]
        )
        
        # Create runner
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        runner = TestRunner(manager)
        
        # Run the test
        result = runner.run_test(test, "SELECT 42 as result;")
        assert result.passed
        assert result.test_id == f"{sql_file}::test_select_literal"
    
    def test_jinja_template_execution(self):
        """Test execution with Jinja2 template rendering."""
        test = TestDefinition(
            name="test_with_jinja",
            given={"jinja_context": {"limit": 10}},
            expect={},
            filepath="test.sql",
            line_number=1
        )
        
        config = ConnectionConfig.sqlite(":memory:")
        runner = TestRunner(config.create_connection_manager())
        
        # SQL with Jinja template
        sql = "SELECT {{ limit }} as limit_value;"
        result = runner.run_test(test, sql)
        
        # Should execute without error
        assert result.error is None or not result.error.message.startswith("Template")
    
    def test_error_handling_in_pipeline(self):
        """Test error handling in execution pipeline."""
        test = TestDefinition(
            name="test_bad_statement",
            given={},
            expect={},
            filepath="test.sql",
            line_number=1
        )
        
        config = ConnectionConfig.sqlite(":memory:")
        runner = TestRunner(config.create_connection_manager())
        
        # Invalid SQL
        result = runner.run_test(test, "SELECT * FROM nonexistent_table;")
        assert not result.passed
        assert result.error is not None
        assert "no such table" in result.error.message.lower()


class TestStatementValidationInContext:
    """Test statement validation as part of the pipeline."""
    
    def test_reject_insert_with_test(self):
        """Test that INSERT statements cannot have tests."""
        test = TestDefinition(
            name="test_insert",
            filepath="test.sql",
            line_number=1
        )
        statement = "INSERT INTO users VALUES (1, 'John');"
        
        with pytest.raises(ParserError):
            StatementValidator.validate_test_binding(test, statement, "test.sql")
    
    def test_accept_select_with_test(self):
        """Test that SELECT statements can have tests."""
        test = TestDefinition(
            name="test_select",
            filepath="test.sql",
            line_number=1
        )
        statement = "SELECT * FROM users;"
        
        # Should not raise
        StatementValidator.validate_test_binding(test, statement, "test.sql")


class TestRendererInContext:
    """Test template rendering within execution context."""
    
    def test_render_with_jinja_context(self):
        """Test rendering SQL with Jinja context from test definition."""
        test = TestDefinition(
            name="test_render",
            given={"jinja_context": {"table_name": "users", "status": "active"}},
            filepath="test.sql",
            line_number=1
        )
        
        renderer = TemplateRenderer(jinja_context=test.given["jinja_context"])
        sql = "SELECT * FROM {{ table_name }} WHERE status = '{{ status }}';"
        result = renderer.render(sql)
        
        assert "users" in result
        assert "active" in result
    
    def test_error_undefined_variable_in_context(self):
        """Test error when Jinja variable is undefined."""
        from sql_unit import RendererError
        
        test = TestDefinition(
            name="test_missing_var",
            given={},
            filepath="test.sql",
            line_number=1
        )
        
        renderer = TemplateRenderer(jinja_context=test.given)
        sql = "SELECT * FROM {{ undefined_var }};"
        
        with pytest.raises(RendererError):
            renderer.render(sql)
