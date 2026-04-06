"""Tests for ResultSetDataFrame converter."""

import pytest

from sql_unit.expectations import ResultSetDataFrame

try:
    import pandas as pd
except ImportError:
    pd = None


@pytest.mark.skipif(pd is None, reason="pandas not installed")
class TestResultSetDataFrame:
    """Test ResultSetDataFrame converter."""

    def test_empty_rows(self):
        """Test conversion of empty result set."""
        rows = []
        df = ResultSetDataFrame.from_rows(rows)
        assert df.empty
        assert len(df) == 0

    def test_single_row(self):
        """Test conversion of single row."""
        rows = [{"id": 1, "name": "Alice"}]
        df = ResultSetDataFrame.from_rows(rows)
        assert len(df) == 1
        assert list(df.columns) == ["id", "name"]
        assert df.loc[0, "id"] == 1
        assert df.loc[0, "name"] == "Alice"

    def test_multiple_rows(self):
        """Test conversion of multiple rows."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]
        df = ResultSetDataFrame.from_rows(rows)
        assert len(df) == 3
        assert list(df.columns) == ["id", "name"]

    def test_integer_column_type(self):
        """Test integer column type preservation."""
        rows = [{"id": 1}, {"id": 2}]
        df = ResultSetDataFrame.from_rows(rows)
        # pandas may use int64 or Int64 depending on NaN presence
        assert df["id"].dtype in (int, "int64", "Int64")

    def test_string_column_type(self):
        """Test string column type preservation."""
        rows = [{"name": "Alice"}, {"name": "Bob"}]
        df = ResultSetDataFrame.from_rows(rows)
        # pandas may use object or string dtype for strings
        assert df["name"].dtype in ("object", "string")  # Accept both

    def test_float_column_type(self):
        """Test float column type preservation."""
        rows = [{"score": 3.14}, {"score": 2.71}]
        df = ResultSetDataFrame.from_rows(rows)
        assert df["score"].dtype == "float64"

    def test_boolean_column_type(self):
        """Test boolean column type preservation."""
        rows = [{"active": True}, {"active": False}]
        df = ResultSetDataFrame.from_rows(rows)
        assert df["active"].dtype == "bool"

    def test_null_values(self):
        """Test NULL/None value handling."""
        rows = [{"id": 1, "name": None}, {"id": None, "name": "Bob"}]
        df = ResultSetDataFrame.from_rows(rows)
        assert pd.isna(df.loc[0, "name"])
        assert pd.isna(df.loc[1, "id"])

    def test_mixed_types_with_null(self):
        """Test mixed column types with NULL values."""
        rows = [
            {"id": 1, "name": "Alice", "score": 95.5, "active": True},
            {"id": 2, "name": "Bob", "score": None, "active": False},
            {"id": None, "name": "Charlie", "score": 87.0, "active": None},
        ]
        df = ResultSetDataFrame.from_rows(rows)
        assert len(df) == 3
        assert set(df.columns) == {"id", "name", "score", "active"}
        assert pd.isna(df.loc[1, "score"])
        assert pd.isna(df.loc[2, "id"])
        assert pd.isna(df.loc[2, "active"])

    def test_column_name_lowercase(self):
        """Test column name normalization to lowercase."""
        rows = [{"ID": 1, "Name": "Alice", "SCORE": 95}]
        df = ResultSetDataFrame.from_rows(rows)
        assert list(df.columns) == ["id", "name", "score"]

    def test_case_insensitive_column_access(self):
        """Test that column names are case-insensitive."""
        rows = [{"ID": 1, "Name": "Alice"}]
        df = ResultSetDataFrame.from_rows(rows)
        # Access via lowercase
        assert df.loc[0, "id"] == 1
        assert df.loc[0, "name"] == "Alice"

    def test_complex_data_types(self):
        """Test handling of various data types together."""
        rows = [
            {
                "int_col": 42,
                "float_col": 3.14,
                "str_col": "hello",
                "bool_col": True,
                "null_col": None,
            },
        ]
        df = ResultSetDataFrame.from_rows(rows)
        assert df.loc[0, "int_col"] == 42
        assert df.loc[0, "float_col"] == 3.14
        assert df.loc[0, "str_col"] == "hello"
        assert df.loc[0, "bool_col"] == True  # Use == instead of is
        assert pd.isna(df.loc[0, "null_col"])
