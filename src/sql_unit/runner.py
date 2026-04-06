"""Test execution engine orchestrating the parse → render → execute → validate pipeline."""

import time
from typing import Any

from .database import ConnectionManager
from .exceptions import ExecutionError, ParserError, RendererError
from .models import TestDefinition, TestResult, ResultSet, ErrorReport
from .renderer import TemplateRenderer


class TestRunner:
    """Orchestrates test execution: parse → render → execute → validate."""
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        Initialize test runner.
        
        Args:
            connection_manager: Database connection manager
        """
        self.connection = connection_manager
    
    def run_test(
        self,
        test: TestDefinition,
        statement_sql: str
    ) -> TestResult:
        """
        Execute a single test through complete lifecycle.
        
        Args:
            test: Test definition to execute
            statement_sql: The SQL statement being tested
            
        Returns:
            TestResult with pass/fail status and metadata
        """
        test_id = test.test_id()
        start_time = time.time()
        
        try:
            # Phase 1: Setup (execute given section if present)
            given_context = self._setup_test(test, test_id)
            
            # Phase 2: Render SQL with template substitution
            rendered_sql = self._render_sql(statement_sql, test_id, given_context)
            
            # Phase 3: Execute query
            result_rows = self._execute_query(rendered_sql, test_id)
            
            # Phase 4: Validate expectations
            self._validate_expectations(test, result_rows, test_id)
            
            # Test passed
            duration = time.time() - start_time
            return TestResult(
                test_id=test_id,
                passed=True,
                duration=duration
            )
            
        except (ParserError, RendererError, ExecutionError) as e:
            duration = time.time() - start_time
            error_report = ErrorReport(
                test_id=test_id,
                error_type=type(e).__name__,
                message=str(e),
                filepath=test.filepath,
                line_number=test.line_number
            )
            return TestResult(
                test_id=test_id,
                passed=False,
                duration=duration,
                error=error_report
            )
        except Exception as e:
            duration = time.time() - start_time
            error_report = ErrorReport(
                test_id=test_id,
                error_type="UnexpectedError",
                message=str(e),
                filepath=test.filepath,
                line_number=test.line_number
            )
            return TestResult(
                test_id=test_id,
                passed=False,
                duration=duration,
                error=error_report
            )
    
    def _setup_test(self, test: TestDefinition, test_id: str) -> dict[str, Any]:
        """
        Execute setup phase from 'given' section.
        
        Args:
            test: Test definition
            test_id: Test identifier for error reporting
            
        Returns:
            Dictionary of variables from given section (jinja_context)
            
        Raises:
            ExecutionError: If setup fails
        """
        context = {}
        
        if not test.given:
            return context
        
        # Extract jinja_context if present
        if 'jinja_context' in test.given:
            context = test.given['jinja_context'].copy()
        
        # TODO: Handle additional given section items (CTEs, temp tables, etc.)
        # This would execute SQL from given.sql or given.data
        
        return context
    
    def _render_sql(
        self,
        sql: str,
        test_id: str,
        context: dict[str, Any]
    ) -> str:
        """
        Render SQL with Jinja2 template support.
        
        Args:
            sql: SQL statement potentially with Jinja2 templates
            test_id: Test identifier for error reporting
            context: Variables for template rendering
            
        Returns:
            Rendered SQL statement
            
        Raises:
            RendererError: If rendering fails
        """
        renderer = TemplateRenderer(jinja_context=context)
        return renderer.render(sql, test_id=test_id)
    
    def _execute_query(self, sql: str, test_id: str) -> list[dict[str, Any]]:
        """
        Execute query and retrieve results.
        
        Args:
            sql: SQL query to execute
            test_id: Test identifier for error reporting
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            ExecutionError: If execution fails
        """
        try:
            return self.connection.execute_query(sql)
        except ExecutionError as e:
            # Re-raise with test context
            raise ExecutionError(
                str(e),
                test_id=test_id,
                sql=sql
            )
    
    def _validate_expectations(
        self,
        test: TestDefinition,
        result_rows: list[dict[str, Any]],
        test_id: str
    ) -> None:
        """
        Validate query results against expectations.
        
        Args:
            test: Test definition with expectations
            result_rows: Actual query result rows
            test_id: Test identifier for error reporting
            
        Raises:
            ExecutionError: If validation fails
        """
        if not test.expect:
            # No expectations defined - test passes
            return
        
        # TODO: Implement expectation validators
        # For now, basic structure support
        
        # Common expectation types:
        # - rows_equal: [list of dicts]
        # - row_count: number
        # - columns_exist: [list of column names]
        # - no_nulls: [list of column names]
        
        pass  # Placeholder for expectation validation


class BatchTestRunner:
    """Runs multiple tests and collects results."""
    
    def __init__(self, runner: TestRunner):
        """
        Initialize batch runner.
        
        Args:
            runner: TestRunner instance to use for execution
        """
        self.runner = runner
    
    def run_tests(
        self,
        tests: list[TestDefinition],
        statements: list[str]
    ) -> list[TestResult]:
        """
        Run multiple tests.
        
        Args:
            tests: List of test definitions
            statements: List of SQL statements (must match test count)
            
        Returns:
            List of TestResult objects
        """
        if len(tests) != len(statements):
            raise ExecutionError(
                f"Test count ({len(tests)}) does not match statement count ({len(statements)})"
            )
        
        results = []
        for test, statement in zip(tests, statements):
            result = self.runner.run_test(test, statement)
            results.append(result)
        
        return results
    
    def get_summary(self, results: list[TestResult]) -> dict[str, Any]:
        """
        Generate summary statistics from test results.
        
        Args:
            results: List of test results
            
        Returns:
            Dictionary with summary statistics
        """
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        total_duration = sum(r.duration for r in results)
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results) if results else 0,
            "total_duration": total_duration
        }
