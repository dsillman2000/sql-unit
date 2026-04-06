"""Tests for DataFrame normalization."""

import pytest

try:
    import pandas as pd
except ImportError:
    pd = None

from sql_unit.expectations.normalizer import DataFrameNormalizer


@pytest.mark.skipif(pd is None, reason="pandas not installed")
class TestDataFrameNormalizer:
    """Test DataFrame normalization."""

    def test_normalize_column_order(self):
        """Test that columns are sorted alphabetically."""
        df = pd.DataFrame({"z": [1, 2], "a": [3, 4], "m": [5, 6]})
        normalized = DataFrameNormalizer.normalize(df)
        assert list(normalized.columns) == ["a", "m", "z"]

    def test_normalize_row_order(self):
        """Test that rows are sorted by all columns."""
        df = pd.DataFrame({"id": [3, 1, 2], "name": ["Charlie", "Alice", "Bob"]})
        normalized = DataFrameNormalizer.normalize(df)
        assert list(normalized["id"]) == [1, 2, 3]
        assert list(normalized["name"]) == ["Alice", "Bob", "Charlie"]

    def test_normalize_row_order_multiple_columns(self):
        """Test row sorting with multiple columns."""
        df = pd.DataFrame(
            {
                "first": ["B", "A", "A"],
                "second": [2, 1, 2],
            }
        )
        normalized = DataFrameNormalizer.normalize(df)
        # Sort by first, then by second
        assert list(normalized["first"]) == ["A", "A", "B"]
        assert list(normalized["second"]) == [1, 2, 2]

    def test_normalize_column_name_lowercase(self):
        """Test column name normalization to lowercase."""
        df = pd.DataFrame({"ID": [1, 2], "Name": ["Alice", "Bob"]})
        normalized = DataFrameNormalizer.normalize(df)
        assert list(normalized.columns) == ["id", "name"]

    def test_normalize_empty_dataframe(self):
        """Test normalization of empty DataFrame."""
        df = pd.DataFrame()
        normalized = DataFrameNormalizer.normalize(df)
        assert len(normalized) == 0

    def test_normalize_single_row(self):
        """Test normalization of single row."""
        df = pd.DataFrame({"z": [1], "a": [2]})
        normalized = DataFrameNormalizer.normalize(df)
        assert list(normalized.columns) == ["a", "z"]
        assert len(normalized) == 1

    def test_normalize_with_null_values(self):
        """Test normalization with NULL values."""
        df = pd.DataFrame(
            {
                "id": [3, None, 1],
                "name": ["Charlie", "Alice", "Bob"],
            }
        )
        normalized = DataFrameNormalizer.normalize(df)
        # NaN should be at the end
        assert pd.isna(normalized.iloc[-1]["id"])

    def test_normalize_columns_subset(self):
        """Test selecting only expected columns."""
        df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"], "extra": [10, 20]})
        normalized = DataFrameNormalizer.normalize_columns(df, ["id", "name"])
        assert list(normalized.columns) == ["id", "name"]
        assert len(normalized) == 2

    def test_normalize_columns_omitted(self):
        """Test that omitted columns are ignored."""
        df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"], "extra": [10, 20]})
        # Expected has id and name, but not extra
        normalized = DataFrameNormalizer.normalize_columns(df, ["id", "name"])
        assert "extra" not in normalized.columns
        assert list(normalized.columns) == ["id", "name"]

    def test_normalize_columns_missing_in_df(self):
        """Test when expected column is missing in actual DataFrame."""
        df = pd.DataFrame({"id": [1, 2]})
        # Expected has id and name, but df only has id
        normalized = DataFrameNormalizer.normalize_columns(df, ["id", "name"])
        # Only columns that exist in both
        assert list(normalized.columns) == ["id"]

    def test_normalize_columns_alphabetical_order(self):
        """Test that normalized columns are in alphabetical order."""
        df = pd.DataFrame({"z": [1], "a": [2], "m": [3]})
        normalized = DataFrameNormalizer.normalize_columns(df, ["z", "a", "m"])
        assert list(normalized.columns) == ["a", "m", "z"]

    def test_normalize_columns_case_insensitive(self):
        """Test case-insensitive column name matching."""
        df = pd.DataFrame({"ID": [1], "NAME": ["Alice"]})
        normalized = DataFrameNormalizer.normalize_columns(df, ["id", "name"])
        assert list(normalized.columns) == ["id", "name"]

    def test_normalize_index_reset(self):
        """Test that index is reset to 0, 1, 2, ..."""
        df = pd.DataFrame({"id": [1, 2, 3]}, index=[10, 20, 30])
        normalized = DataFrameNormalizer.normalize(df)
        assert list(normalized.index) == [0, 1, 2]

    def test_normalize_preserves_data_types(self):
        """Test that normalization preserves column data types."""
        df = pd.DataFrame({"int": [3, 1, 2], "float": [3.5, 1.1, 2.2], "str": ["c", "a", "b"]})
        normalized = DataFrameNormalizer.normalize(df)
        assert normalized["int"].dtype == df["int"].dtype
        assert normalized["float"].dtype == df["float"].dtype
        assert normalized["str"].dtype == df["str"].dtype
