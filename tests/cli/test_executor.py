"""Tests for CLI executor module."""

import pytest

from sql_unit.cli.executor import (
    TestExecutionResult,
    TestStatus,
    ExecutionSummary,
    execute_tests,
)


class TestExecutionSummary:
    """Tests for ExecutionSummary."""

    def test_default_summary(self):
        """Test default summary values."""
        summary = ExecutionSummary()
        assert summary.passed == 0
        assert summary.failed == 0
        assert summary.errors == 0
        assert summary.skipped == 0
        assert summary.total_time_ms == 0.0

    def test_summary_totals(self):
        """Test summary totals."""
        summary = ExecutionSummary(passed=5, failed=2, errors=1, skipped=0, total_time_ms=100.5)
        assert summary.passed == 5
        assert summary.failed == 2
        assert summary.errors == 1
        assert sum([summary.passed, summary.failed, summary.errors, summary.skipped]) == 8


class TestTestExecutionResult:
    """Tests for TestExecutionResult."""

    def test_result_pass(self):
        """Test passing result."""
        result = TestExecutionResult(
            name="test_login",
            file_path="tests/auth_test.sql",
            status=TestStatus.PASS,
            duration_ms=50.5,
        )
        assert result.status == TestStatus.PASS
        assert result.error_message is None

    def test_result_fail(self):
        """Test failing result."""
        result = TestExecutionResult(
            name="test_login",
            file_path="tests/auth_test.sql",
            status=TestStatus.FAIL,
            duration_ms=50.5,
            error_message="Expected 5 rows, got 3",
        )
        assert result.status == TestStatus.FAIL
        assert result.error_message == "Expected 5 rows, got 3"

    def test_result_error(self):
        """Test error result."""
        result = TestExecutionResult(
            name="test_login",
            file_path="tests/auth_test.sql",
            status=TestStatus.ERROR,
            duration_ms=10.5,
            error_message="Connection refused",
        )
        assert result.status == TestStatus.ERROR
        assert "Connection refused" in result.error_message
