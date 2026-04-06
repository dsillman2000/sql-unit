"""Statement identification and validation for SQL unit tests."""

import re
from typing import NamedTuple

from .exceptions import ParserError
from .models import TestDefinition, TestFile


class StatementInfo(NamedTuple):
    """Information about a SQL statement."""
    type: str  # SELECT, INSERT, UPDATE, DELETE, WITH
    content: str
    line_number: int


class StatementValidator:
    """Validates SQL statements against test requirements."""
    
    # Pattern to identify statement type
    STATEMENT_TYPE_PATTERN = re.compile(
        r'^\s*(WITH|SELECT|INSERT|UPDATE|DELETE)\b',
        re.IGNORECASE | re.MULTILINE
    )
    
    @classmethod
    def get_statement_type(cls, statement: str) -> str:
        """
        Extract statement type from SQL statement.
        
        Args:
            statement: SQL statement text
            
        Returns:
            Statement type: SELECT, INSERT, UPDATE, DELETE, WITH
        """
        match = cls.STATEMENT_TYPE_PATTERN.search(statement)
        if not match:
            raise ParserError(f"Cannot identify statement type: {statement[:50]}")
        return match.group(1).upper()
    
    @classmethod
    def is_select_statement(cls, statement: str) -> bool:
        """
        Check if statement is a SELECT (or WITH...SELECT).
        
        Args:
            statement: SQL statement text
            
        Returns:
            True if statement is a SELECT query, False otherwise
        """
        stmt_type = cls.get_statement_type(statement)
        # WITH...SELECT is also queryable
        if stmt_type == 'WITH':
            # Check if it ends with SELECT
            return 'select' in statement.lower()
        return stmt_type == 'SELECT'
    
    @classmethod
    def validate_test_binding(
        cls,
        test: TestDefinition,
        statement: str | None,
        filepath: str
    ) -> None:
        """
        Validate that test is bound to a valid SELECT statement.
        
        Args:
            test: Test definition
            statement: Following SQL statement or None if not found
            filepath: Source filepath for error reporting
            
        Raises:
            ParserError: If statement is not SELECT or is missing
        """
        if not statement:
            raise ParserError(
                f"Test '{test.name}' has no following SQL statement",
                filepath=filepath,
                line_number=test.line_number
            )
        
        if not cls.is_select_statement(statement):
            stmt_type = cls.get_statement_type(statement)
            raise ParserError(
                f"Test '{test.name}' is bound to {stmt_type} statement, only SELECT statements can have tests",
                filepath=filepath,
                line_number=test.line_number
            )


class TestBindingEngine:
    """Binds tests to their SQL statements."""
    
    @classmethod
    def bind_tests_to_file(
        cls,
        filepath: str,
        tests: list[TestDefinition],
        sql_content: str
    ) -> TestFile:
        """
        Bind tests to statements in a SQL file.
        
        Args:
            filepath: Source file path
            tests: List of test definitions extracted from file
            sql_content: Full SQL file content
            
        Returns:
            TestFile with bound tests
            
        Raises:
            ParserError: If test binding validation fails
        """
        test_file = TestFile(filepath=filepath)
        
        # For each test, validate it's bound to a SELECT statement
        # Tests are bound by proximity - we need to find the next statement after each test
        # This is done during parsing, so here we just validate
        
        for test in tests:
            # Validate test has proper structure
            if not test.given:
                test.given = {}
            if not test.expect:
                test.expect = {}
            
            # Note: Full statement validation happens during execution
            # Here we just ensure the test structure is valid
            test_file.tests.append(test)
        
        return test_file
