from pathlib import Path
from typing import Generator

import duckdb
import pytest


@pytest.fixture(scope="session")
def sql_dir() -> Path:
    return Path(__file__).parent / "sql"


@pytest.fixture(scope="session")
def duckdb_database() -> Path:
    database_file = Path(__file__).parent / "data" / "duckdb.db"
    if not database_file.parent.exists():
        database_file.parent.mkdir(parents=True)
    if database_file.exists():
        database_file.unlink()
    duckdb.connect(database=str(database_file.absolute())).close()
    return database_file


def init_tpc_h(duckdb_connection: duckdb.DuckDBPyConnection, sql_dir: Path) -> None:
    tpch_script = sql_dir / "init.sql"
    duckdb_connection.execute(tpch_script.read_text())


@pytest.fixture(scope="session")
def duckdb_connection(duckdb_database: Path, sql_dir: Path) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    # Connect to duckdb service at localhost
    conn = duckdb.connect(database=duckdb_database.as_posix())

    def init_tpc_h(connection) -> None:
        tpch_script = sql_dir / "init.sql"
        connection.execute(tpch_script.read_text())

    init_tpc_h(conn)

    yield conn
    conn.close()
