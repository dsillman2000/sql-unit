"""Integration tests for CLI commands."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from sql_unit.cli.main import main
from sql_unit.cli.discovery import TestInfo
from sql_unit.cli.executor import TestExecutionResult, ExecutionSummary, TestStatus


class TestCliListCommand:
    """Integration tests for list command."""

    def test_list_no_tests_found(self):
        """Test list command with no tests."""
        runner = CliRunner()

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            mock_discovery.return_value.tests = []
            result = runner.invoke(main, ["list"])

            assert result.exit_code == 0
            assert "No tests found" in result.output

    def test_list_with_selector(self):
        """Test list command with selector."""
        runner = CliRunner()

        test1 = TestInfo(name="test_user", directory="tests", file_path="tests/user.sql")
        test2 = TestInfo(name="test_admin", directory="tests", file_path="tests/admin.sql")

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.tests = [test1, test2]
            mock_instance.filter_by_selectors.return_value = [test1]

            result = runner.invoke(main, ["list", "-s", "test_user"])

            assert result.exit_code == 0
            assert "test_user" in result.output

    def test_list_json_format(self):
        """Test list command with JSON output."""
        runner = CliRunner()

        test1 = TestInfo(name="test_user", directory="tests", file_path="tests/user.sql")

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.tests = [test1]
            mock_instance.filter_by_selectors.return_value = []

            result = runner.invoke(main, ["list", "--format", "json"])

            assert result.exit_code == 0
            assert '"tests":' in result.output
            assert '"count":' in result.output

    def test_list_sort_by_name(self):
        """Test list command sorting by name."""
        runner = CliRunner()

        test1 = TestInfo(name="z_test", directory="tests", file_path="tests/z.sql")
        test2 = TestInfo(name="a_test", directory="tests", file_path="tests/a.sql")

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.tests = [test1, test2]
            mock_instance.filter_by_selectors.return_value = []

            result = runner.invoke(main, ["list", "--sort-by", "name"])

            assert result.exit_code == 0
            # a_test should come before z_test in output
            assert result.output.find("a_test") < result.output.find("z_test")


class TestCliCompileCommand:
    """Integration tests for compile command."""

    def test_compile_no_tests_found(self):
        """Test compile command with no tests."""
        runner = CliRunner()

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            mock_instance = MagicMock()
            mock_discovery.return_value = mock_instance
            mock_instance.tests = []
            mock_instance.filter_by_selectors.return_value = []

            result = runner.invoke(main, ["compile"])

            assert result.exit_code == 2
            assert "No tests found" in result.output

    def test_compile_sql_output(self):
        """Test compile command with SQL output."""
        runner = CliRunner()

        test1 = TestInfo(name="test_user", directory="tests", file_path="tests/user.sql")

        with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
            with patch("sql_unit.cli.commands.compile_tests") as mock_compile:
                mock_instance = MagicMock()
                mock_discovery.return_value = mock_instance
                mock_instance.tests = [test1]
                mock_instance.filter_by_selectors.return_value = []

                from sql_unit.cli.compiler import CompiledTest

                mock_compile.return_value = [
                    CompiledTest(name="test_user", file_path="tests/user.sql", sql="SELECT 1")
                ]

                result = runner.invoke(main, ["compile"])

                assert result.exit_code == 0
                assert "SELECT 1" in result.output


class TestCliRunCommand:
    """Integration tests for run command."""

    def test_run_no_connection_configured(self):
        """Test run command without connection configured."""
        runner = CliRunner()

        with patch("sql_unit.cli.commands.ConfigLoader.load_config") as mock_config:
            mock_config.return_value = None

            with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
                mock_instance = MagicMock()
                mock_discovery.return_value = mock_instance
                test1 = TestInfo(name="test_user", directory="tests", file_path="tests/user.sql")
                mock_instance.tests = [test1]
                mock_instance.filter_by_selectors.return_value = []

                result = runner.invoke(main, ["run"])

                assert result.exit_code == 2
                assert "No database connection configured" in result.output

    def test_run_with_connection_flag(self):
        """Test run command with --connection flag."""
        runner = CliRunner()

        with patch("sql_unit.cli.commands.ConfigLoader.load_config") as mock_config:
            mock_config.return_value = None

            with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
                with patch("sql_unit.cli.commands.execute_tests") as mock_execute:
                    mock_instance = MagicMock()
                    mock_discovery.return_value = mock_instance
                    test1 = TestInfo(
                        name="test_user", directory="tests", file_path="tests/user.sql"
                    )
                    mock_instance.tests = [test1]
                    mock_instance.filter_by_selectors.return_value = []

                    mock_result = TestExecutionResult(
                        name="test_user",
                        file_path="tests/user.sql",
                        status=TestStatus.PASS,
                        duration_ms=10.5,
                    )
                    mock_summary = ExecutionSummary(passed=1, total_time_ms=10.5)
                    mock_execute.return_value = ([mock_result], mock_summary)

                    result = runner.invoke(main, ["run", "--connection", "sqlite:///:memory:"])

                    assert result.exit_code == 0


class TestCliErrorHandling:
    """Tests for error handling in CLI."""

    def test_list_invalid_config_file(self):
        """Test list command with invalid config file."""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text("invalid: yaml: content:")

            with patch("sql_unit.cli.commands.ConfigLoader.load_config") as mock_config:
                mock_config.side_effect = Exception("Invalid config")

                with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
                    mock_instance = MagicMock()
                    mock_discovery.return_value = mock_instance
                    mock_instance.tests = []
                    mock_instance.filter_by_selectors.return_value = []

                    result = runner.invoke(main, ["list"])

                    # Should show warning but not fail
                    assert "Warning: Error loading config" in result.output

    def test_run_invalid_connection_url(self):
        """Test run command with invalid connection URL."""
        runner = CliRunner()

        with patch("sql_unit.cli.commands.ConfigLoader.load_config") as mock_config:
            mock_config.return_value = None

            with patch("sql_unit.cli.commands.TestDiscovery") as mock_discovery:
                mock_instance = MagicMock()
                mock_discovery.return_value = mock_instance
                test1 = TestInfo(name="test_user", directory="tests", file_path="tests/user.sql")
                mock_instance.tests = [test1]
                mock_instance.filter_by_selectors.return_value = []

                result = runner.invoke(main, ["run", "--connection", "invalid://url"])

                assert result.exit_code == 2
                assert "Invalid connection URL" in result.output


class TestCliHelpAndVersion:
    """Tests for help and version commands."""

    def test_list_help(self):
        """Test list command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["list", "--help"])

        assert result.exit_code == 0
        assert "List available SQL unit tests" in result.output
        assert "--select" in result.output

    def test_compile_help(self):
        """Test compile command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["compile", "--help"])

        assert result.exit_code == 0
        assert "Compile SQL unit tests" in result.output

    def test_run_help(self):
        """Test run command help."""
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--help"])

        assert result.exit_code == 0
        assert "Execute SQL unit tests" in result.output

    def test_main_help(self):
        """Test main help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Commands:" in result.output or "Usage:" in result.output
