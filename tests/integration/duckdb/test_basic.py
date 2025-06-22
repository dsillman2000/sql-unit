import duckdb


def test_basic(duckdb_connection: duckdb.DuckDBPyConnection) -> None:
    result = duckdb_connection.execute("SELECT 1 + 1").fetchone()
    assert result is not None
    assert result[0] == 2
