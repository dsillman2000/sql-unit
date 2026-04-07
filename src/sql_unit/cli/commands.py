"""List command for discovering and displaying SQL unit tests."""

import json
from typing import Optional

import click

from sql_unit.cli.discovery import TestDiscovery, TestInfo
from sql_unit.cli.compiler import compile_tests, CompiledTest


@click.command()
@click.option(
    "-s",
    "--select",
    "selectors",
    multiple=True,
    help="Filter tests by name, glob pattern, file path, or directory. Can be used multiple times.",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format (human-readable or JSON).",
)
@click.option(
    "--sort-by",
    type=click.Choice(["name", "directory", "path"]),
    default="name",
    help="Sort results by name, directory, or path.",
)
@click.option(
    "--threads",
    type=int,
    default=1,
    help="Number of threads for parallel discovery (1 = sequential, -1 = CPU count).",
)
def list_cmd(
    selectors: tuple[str, ...],
    format: str,
    sort_by: str,
    threads: int,
) -> None:
    """List available SQL unit tests with optional filtering.
    
    Discovers all SQL test files and displays them with filtering options.
    No database connection required.
    
    Examples:
        sql-unit list                          # List all tests
        sql-unit list -s test_user_login       # List specific test
        sql-unit list -s "user_*"              # List with glob pattern
        sql-unit list -s tests/auth_test.sql   # List from specific file
        sql-unit list -s tests/auth/ --format json
    """
    try:
        # Initialize discovery
        discovery = TestDiscovery()

        # Filter tests if selectors provided
        if selectors:
            tests = discovery.filter_by_selectors(list(selectors))
        else:
            tests = discovery.tests

        # Sort tests
        if sort_by == "name":
            tests = sorted(tests, key=lambda t: t.name)
        elif sort_by == "directory":
            tests = sorted(tests, key=lambda t: (t.directory, t.name))
        elif sort_by == "path":
            tests = sorted(tests, key=lambda t: t.file_path)

        # Output results
        if format == "json":
            _output_json(tests)
        else:
            _output_human_readable(tests)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(code=2)


def _output_human_readable(tests: list[TestInfo]) -> None:
    """Output tests in human-readable format."""
    if not tests:
        click.echo("No tests found.")
        return

    # Calculate column widths
    max_name_width = max((len(t.name) for t in tests), default=10)
    max_path_width = max((len(t.file_path) for t in tests), default=10)

    # Print header
    click.echo(
        f"{'Test Name':<{max_name_width}}  {'Path':<{max_path_width}}"
    )
    click.echo("-" * (max_name_width + max_path_width + 2))

    # Print tests
    for test in tests:
        click.echo(f"{test.name:<{max_name_width}}  {test.file_path:<{max_path_width}}")

    click.echo(f"\nTotal: {len(tests)} tests")


def _output_json(tests: list[TestInfo]) -> None:
    """Output tests in JSON format."""
    output = [
        {"name": t.name, "file_path": t.file_path, "directory": t.directory}
        for t in tests
    ]
    click.echo(json.dumps({"tests": output, "count": len(tests)}, indent=2))


@click.command()
@click.option(
    "-s",
    "--select",
    "selectors",
    multiple=True,
    help="Filter tests by name, glob pattern, file path, or directory. Can be used multiple times.",
)
@click.option(
    "--format",
    type=click.Choice(["sql", "json"]),
    default="sql",
    help="Output format (plain SQL or JSON with test name and SQL).",
)
@click.option(
    "--threads",
    type=int,
    default=1,
    help="Number of threads for parallel discovery (1 = sequential, -1 = CPU count).",
)
def compile_cmd(
    selectors: tuple[str, ...],
    format: str,
    threads: int,
) -> None:
    """Compile SQL unit tests to SQL output.
    
    Renders Jinja templates and outputs compiled SQL for tests.
    No database connection required.
    
    Examples:
        sql-unit compile                       # Compile all tests
        sql-unit compile -s test_user_login    # Compile specific test
        sql-unit compile -s "user_*" --format json
    """
    try:
        # Initialize discovery
        discovery = TestDiscovery()

        # Filter tests if selectors provided
        if selectors:
            tests = discovery.filter_by_selectors(list(selectors))
        else:
            tests = discovery.tests

        if not tests:
            click.echo("No tests found.", err=True)
            raise click.Exit(code=2)

        # Compile tests
        compiled = compile_tests(tests)

        # Output results
        if format == "json":
            _output_compile_json(compiled)
        else:
            _output_compile_sql(compiled)

    except click.Exit:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(code=2)


def _output_compile_sql(compiled: list[CompiledTest]) -> None:
    """Output compiled tests as plain SQL."""
    for test in compiled:
        click.echo(f"-- Test: {test.name} ({test.file_path})")
        click.echo(test.sql)
        click.echo("")


def _output_compile_json(compiled: list[CompiledTest]) -> None:
    """Output compiled tests as JSON."""
    output = [
        {"name": t.name, "file_path": t.file_path, "sql": t.sql} for t in compiled
    ]
    click.echo(json.dumps({"tests": output, "count": len(output)}, indent=2))


@click.command()
@click.option(
    "-s",
    "--select",
    "selectors",
    multiple=True,
    help="Filter tests by name, glob pattern, file path, or directory. Can be used multiple times.",
)
@click.option(
    "--connection",
    type=str,
    help="Database connection URL (overrides config file).",
)
@click.option(
    "--format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Output format (human-readable or JSON).",
)
@click.option(
    "-j",
    "--threads",
    type=int,
    default=1,
    help="Number of threads for parallel execution (1 = sequential, -1 = CPU count).",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Show detailed output (SQL statements, inputs, expectations).",
)
def run_cmd(
    selectors: tuple[str, ...],
    connection: Optional[str],
    format: str,
    threads: int,
    verbose: bool,
) -> None:
    """Execute SQL unit tests.
    
    Runs tests and reports results with optional filtering and parallel execution.
    Requires database connection (via config file or --connection flag).
    
    Examples:
        sql-unit run                           # Run all tests
        sql-unit run -s test_user_login        # Run specific test
        sql-unit run -s "user_*" -j 4          # Run with pattern, parallel
        sql-unit run --connection "sqlite:///test.db"
    """
    try:
        # Initialize discovery
        discovery = TestDiscovery()

        # Filter tests if selectors provided
        if selectors:
            tests = discovery.filter_by_selectors(list(selectors))
        else:
            tests = discovery.tests

        if not tests:
            click.echo("No tests found.", err=True)
            raise click.Exit(code=2)

        # Parse connection (placeholder - would load from config or use provided)
        connection_config = None
        if connection:
            # TODO: Parse connection URL into ConnectionConfig
            pass

        # Execute tests
        from sql_unit.cli.executor import execute_tests

        results, summary = execute_tests(tests, connection_config, threads, verbose)

        # Output results
        if format == "json":
            _output_run_json(results, summary)
        else:
            _output_run_human(results, summary)

        # Return appropriate exit code
        if summary.failed > 0 or summary.errors > 0:
            raise click.Exit(code=1)

    except click.Exit:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Exit(code=2)


def _output_run_human(results, summary) -> None:
    """Output test results in human-readable format."""
    if not results:
        click.echo("No tests executed.")
        return

    # Status symbol map
    symbols = {
        "pass": "✓",
        "fail": "✗",
        "error": "⊘",
        "skip": "⊗",
    }

    # Calculate column widths
    max_name_width = max((len(r.name) for r in results), default=10)

    # Print header
    click.echo(f"{'Test Name':<{max_name_width}}  {'Status':<7}  {'Time (ms)'}  Path")
    click.echo("-" * (max_name_width + 50))

    # Print results
    for result in results:
        symbol = symbols.get(result.status.value, "?")
        status_str = f"{symbol} {result.status.value}"
        click.echo(
            f"{result.name:<{max_name_width}}  {status_str:<7}  {result.duration_ms:>8.1f}  {result.file_path}"
        )
        if result.error_message:
            click.echo(f"  Error: {result.error_message}")

    # Print summary
    click.echo("")
    summary_line = f"{summary.passed} passed, {summary.failed} failed, {summary.errors} errors, {summary.skipped} skipped in {summary.total_time_ms:.1f}ms"
    click.echo(summary_line)


def _output_run_json(results, summary) -> None:
    """Output test results as JSON."""
    output = {
        "results": [
            {
                "name": r.name,
                "file_path": r.file_path,
                "status": r.status.value,
                "duration_ms": r.duration_ms,
                "error_message": r.error_message,
                "details": r.details,
            }
            for r in results
        ],
        "summary": {
            "passed": summary.passed,
            "failed": summary.failed,
            "errors": summary.errors,
            "skipped": summary.skipped,
            "total_time_ms": summary.total_time_ms,
        },
    }
    click.echo(json.dumps(output, indent=2))

