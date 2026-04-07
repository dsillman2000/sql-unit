"""Main CLI entry point for sql-unit."""

import click
from sql_unit import __version__
from sql_unit.cli.commands import list_cmd, compile_cmd, run_cmd


@click.group()
@click.version_option(version=__version__, prog_name="sql-unit")
def main():
    """SQL Unit - SQL Testing Framework CLI.
    
    Run SQL unit tests with filtering, compilation, and flexible output options.
    """
    pass


main.add_command(list_cmd, name="list")
main.add_command(compile_cmd, name="compile")
main.add_command(run_cmd, name="run")

if __name__ == "__main__":
    main()
