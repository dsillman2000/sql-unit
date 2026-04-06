"""Unit tests for SQL statement identification."""

import pytest

from sql_unit.exceptions import ParserError
from sql_unit.models import TestDefinition
from sql_unit.statement import StatementValidator


class TestStatementTypeIdentification:
    """Tests for identifying SQL statement types."""

    def test_identify_select_statement(self):
        """Test identifying SELECT statement."""
        sql = "SELECT * FROM users;"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "SELECT"

    def test_identify_with_select_statement(self):
        """Test identifying WITH...SELECT statement."""
        sql = """
        WITH cte AS (SELECT 1 as id)
        SELECT * FROM cte;
        """
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "WITH"

    def test_identify_insert_statement(self):
        """Test identifying INSERT statement."""
        sql = "INSERT INTO users (id) VALUES (1);"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "INSERT"

    def test_identify_update_statement(self):
        """Test identifying UPDATE statement."""
        sql = "UPDATE users SET name = 'John' WHERE id = 1;"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "UPDATE"

    def test_identify_delete_statement(self):
        """Test identifying DELETE statement."""
        sql = "DELETE FROM users WHERE id = 1;"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "DELETE"

    def test_case_insensitive_identification(self):
        """Test case-insensitive statement type identification."""
        sql = "select * from users;"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "SELECT"

    def test_whitespace_before_statement(self):
        """Test handling whitespace before statement."""
        sql = "\n\n  SELECT * FROM users;"
        stmt_type = StatementValidator.get_statement_type(sql)
        assert stmt_type == "SELECT"

    def test_invalid_statement(self):
        """Test error for invalid statement."""
        sql = "INVALID SYNTAX HERE;"
        with pytest.raises(ParserError):
            StatementValidator.get_statement_type(sql)


class TestSelectStatementDetection:
    """Tests for detecting SELECT statements."""

    def test_detect_select(self):
        """Test detecting SELECT statement."""
        assert StatementValidator.is_select_statement("SELECT * FROM users;")

    def test_detect_with_select(self):
        """Test detecting WITH...SELECT statement."""
        sql = """
        WITH cte AS (SELECT 1)
        SELECT * FROM cte;
        """
        assert StatementValidator.is_select_statement(sql)

    def test_reject_insert(self):
        """Test rejecting INSERT statement."""
        assert not StatementValidator.is_select_statement("INSERT INTO users VALUES (1);")

    def test_reject_update(self):
        """Test rejecting UPDATE statement."""
        assert not StatementValidator.is_select_statement("UPDATE users SET x = 1;")

    def test_reject_delete(self):
        """Test rejecting DELETE statement."""
        assert not StatementValidator.is_select_statement("DELETE FROM users;")

    def test_reject_with_without_select(self):
        """Test rejecting WITH without SELECT."""
        # This is actually invalid SQL, but test the logic
        sql = "WITH cte AS (INSERT INTO users VALUES (1))"
        assert not StatementValidator.is_select_statement(sql)


class TestTestBinding:
    """Tests for validating test-to-statement binding."""

    def test_valid_test_binding_select(self):
        """Test valid binding to SELECT statement."""
        test = TestDefinition(name="test1", filepath="test.sql", line_number=1)
        statement = "SELECT * FROM users;"
        # Should not raise
        StatementValidator.validate_test_binding(test, statement, "test.sql")

    def test_valid_test_binding_with_select(self):
        """Test valid binding to WITH...SELECT statement."""
        test = TestDefinition(name="test1", filepath="test.sql", line_number=1)
        statement = "WITH cte AS (SELECT 1) SELECT * FROM cte;"
        # Should not raise
        StatementValidator.validate_test_binding(test, statement, "test.sql")

    def test_invalid_binding_insert(self):
        """Test error when binding to INSERT."""
        test = TestDefinition(name="test1", filepath="test.sql", line_number=1)
        statement = "INSERT INTO users VALUES (1);"
        with pytest.raises(ParserError) as exc_info:
            StatementValidator.validate_test_binding(test, statement, "test.sql")
        assert "INSERT" in str(exc_info.value)

    def test_invalid_binding_update(self):
        """Test error when binding to UPDATE."""
        test = TestDefinition(name="test1", filepath="test.sql", line_number=1)
        statement = "UPDATE users SET x = 1;"
        with pytest.raises(ParserError):
            StatementValidator.validate_test_binding(test, statement, "test.sql")

    def test_invalid_binding_no_statement(self):
        """Test error when no statement follows test."""
        test = TestDefinition(name="test1", filepath="test.sql", line_number=1)
        with pytest.raises(ParserError) as exc_info:
            StatementValidator.validate_test_binding(test, None, "test.sql")
        assert "no following" in str(exc_info.value).lower()

    def test_error_includes_test_name(self):
        """Test that error messages include test name."""
        test = TestDefinition(name="my_test", filepath="test.sql", line_number=5)
        with pytest.raises(ParserError) as exc_info:
            StatementValidator.validate_test_binding(test, None, "test.sql")
        assert "my_test" in str(exc_info.value)
