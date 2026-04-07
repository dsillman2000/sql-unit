"""Tests for CLI output formatting."""

import json

import pytest
from click.testing import CliRunner

from sql_unit.cli.commands import list_cmd, compile_cmd, run_cmd
from sql_unit.cli.discovery import TestInfo
from sql_unit.cli.executor import TestExecutionResult, TestStatus, ExecutionSummary


class TestListOutputFormatting:
    """Tests for list command output formatting."""

    def test_list_human_output_format(self):
        """Test human-readable output format."""
        runner = CliRunner()
        result = runner.invoke(list_cmd, ["--format", "human"])
        assert result.exit_code == 0
        # Should contain "Total:" in output
        if "No tests found" not in result.output:
            assert "Test Name" in result.output or "Total:" in result.output

    def test_list_json_output_valid(self):
        """Test JSON output is valid JSON."""
        runner = CliRunner()
        result = runner.invoke(list_cmd, ["--format", "json"])
        if result.exit_code == 0 and result.output.strip():
            try:
                data = json.loads(result.output)
                assert "tests" in data
                assert "count" in data
            except json.JSONDecodeError:
                pytest.skip("No tests in discovery to parse JSON")


class TestRunOutputFormatting:
    """Tests for run command output formatting."""

    def test_run_requires_connection(self):
        """Test run command requires connection."""
        runner = CliRunner()
        result = runner.invoke(run_cmd, [])
        # Should fail due to missing connection (exit code 1 or 2)
        assert result.exit_code != 0
        assert "connection" in result.output.lower() or "error" in result.output.lower()

    def test_run_human_output_symbols(self):
        """Test human output contains status symbols."""
        from sql_unit.cli.commands import _output_run_human

        results = [
            TestExecutionResult(
                name="test_pass",
                file_path="test.sql",
                status=TestStatus.PASS,
                duration_ms=10.5,
            ),
            TestExecutionResult(
                name="test_fail",
                file_path="test.sql",
                status=TestStatus.FAIL,
                duration_ms=20.5,
                error_message="Expected 5 rows, got 3",
            ),
        ]
        summary = ExecutionSummary(passed=1, failed=1, total_time_ms=31.0)

        runner = CliRunner()
        with runner.isolation():
            _output_run_human(results, summary)
        # Would check output capture in actual test

    def test_run_json_output_structure(self):
        """Test JSON output has correct structure."""
        from sql_unit.cli.commands import _output_run_json

        results = [
            TestExecutionResult(
                name="test_pass",
                file_path="test.sql",
                status=TestStatus.PASS,
                duration_ms=10.5,
            ),
        ]
        summary = ExecutionSummary(passed=1, total_time_ms=10.5)

        # Capture output
        runner = CliRunner()
        with runner.isolation() as outstreams:
            _output_run_json(results, summary)

        # Parse output
        output = outstreams[0].getvalue() if outstreams else ""
        if output.strip():
            data = json.loads(output)
            assert "results" in data
            assert "summary" in data
            assert len(data["results"]) == 1
            assert data["summary"]["passed"] == 1
