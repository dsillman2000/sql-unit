"""SQL compilation and rendering for CLI."""

import json
from dataclasses import dataclass

import click

from sql_unit.cli.discovery import TestDiscovery, TestInfo
from sql_unit.parser import SqlBlockCommentParser
from sql_unit.renderer import TemplateRenderer


@dataclass
class CompiledTest:
    """A compiled test with rendered SQL."""

    name: str
    file_path: str
    sql: str


def compile_tests(
    tests: list[TestInfo], verbose: bool = False
) -> list[CompiledTest]:
    """Compile tests to SQL.
    
    Args:
        tests: List of tests to compile
        verbose: If True, include extra details
        
    Returns:
        List of compiled tests with SQL
    """
    compiled = []

    for test in tests:
        try:
            # Parse the test file
            test_file = SqlBlockCommentParser.parse(test.file_path)

            # Find the test definition for this test
            test_def = None
            for td in test_file.test_definitions:
                if td.name == test.name:
                    test_def = td
                    break

            if not test_def:
                click.echo(
                    f"Warning: Test {test.name} not found in {test.file_path}",
                    err=True,
                )
                continue

            # Render the SQL
            renderer = TemplateRenderer()
            sql = renderer.render_test(test_def)

            compiled.append(
                CompiledTest(
                    name=test.name,
                    file_path=test.file_path,
                    sql=sql,
                )
            )
        except Exception as e:
            click.echo(
                f"Error compiling {test.name}: {e}",
                err=True,
            )

    return compiled
