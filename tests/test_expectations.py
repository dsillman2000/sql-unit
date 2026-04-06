"""Tests for expectation classes (RowCountExpectation, RowCountValidator)."""

import pytest

from sql_unit.core.exceptions import SetupError
from sql_unit.expectations.expectations import (
    RowCountExpectation,
    RowCountValidator,
    ResultSetDataFrame,
)

try:
    import pandas as pd
except ImportError:
    pd = None


class TestRowCountExpectation:
    """Test RowCountExpectation class."""

    def test_init_with_int_shorthand(self):
        """Test initialization with int shorthand (row_count: 5)."""
        expectation = RowCountExpectation(5)
        assert expectation.operator == "eq"
        assert expectation.value == 5

    def test_init_with_dict_eq(self):
        """Test initialization with dict eq operator."""
        expectation = RowCountExpectation({"eq": 10})
        assert expectation.operator == "eq"
        assert expectation.value == 10

    def test_init_with_dict_min(self):
        """Test initialization with dict min operator."""
        expectation = RowCountExpectation({"min": 3})
        assert expectation.operator == "min"
        assert expectation.value == 3

    def test_init_with_dict_max(self):
        """Test initialization with dict max operator."""
        expectation = RowCountExpectation({"max": 100})
        assert expectation.operator == "max"
        assert expectation.value == 100

    def test_init_with_empty_dict_raises_error(self):
        """Test that empty dict raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation({})
        assert "row_count expectation must have operator" in str(exc_info.value)

    def test_init_with_multiple_operators_raises_error(self):
        """Test that multiple operators in dict raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation({"eq": 5, "min": 3})
        assert "row_count can only have one operator" in str(exc_info.value)

    def test_init_with_invalid_operator_raises_error(self):
        """Test that invalid operator raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation({"invalid": 5})
        assert "Unknown row_count operator: 'invalid'" in str(exc_info.value)

    def test_init_with_float_value_raises_error(self):
        """Test that non-integer value raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation({"eq": 5.5})
        assert "row_count value must be non-negative integer" in str(exc_info.value)

    def test_init_with_negative_value_raises_error(self):
        """Test that negative value raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation({"eq": -1})
        assert "row_count value must be non-negative integer" in str(exc_info.value)

    def test_init_with_invalid_type_raises_error(self):
        """Test that invalid type (not int or dict) raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowCountExpectation("invalid")
        assert "row_count must be int or dict" in str(exc_info.value)

    def test_evaluate_eq_passes(self):
        """Test evaluate() with eq operator when count matches."""
        expectation = RowCountExpectation({"eq": 5})
        assert expectation.evaluate(5) is True

    def test_evaluate_eq_fails(self):
        """Test evaluate() with eq operator when count doesn't match."""
        expectation = RowCountExpectation({"eq": 5})
        assert expectation.evaluate(3) is False

    def test_evaluate_min_passes(self):
        """Test evaluate() with min operator when count is sufficient."""
        expectation = RowCountExpectation({"min": 5})
        assert expectation.evaluate(5) is True
        assert expectation.evaluate(10) is True

    def test_evaluate_min_fails(self):
        """Test evaluate() with min operator when count is insufficient."""
        expectation = RowCountExpectation({"min": 5})
        assert expectation.evaluate(3) is False

    def test_evaluate_max_passes(self):
        """Test evaluate() with max operator when count is within limit."""
        expectation = RowCountExpectation({"max": 5})
        assert expectation.evaluate(5) is True
        assert expectation.evaluate(2) is True

    def test_evaluate_max_fails(self):
        """Test evaluate() with max operator when count exceeds limit."""
        expectation = RowCountExpectation({"max": 5})
        assert expectation.evaluate(10) is False

    def test_get_failure_message_eq(self):
        """Test failure message for eq operator."""
        expectation = RowCountExpectation({"eq": 5})
        msg = expectation.get_failure_message(3)
        assert "Expected exactly 5 rows" in msg
        assert "got 3" in msg

    def test_get_failure_message_min(self):
        """Test failure message for min operator."""
        expectation = RowCountExpectation({"min": 5})
        msg = expectation.get_failure_message(2)
        assert "Expected at least 5 rows" in msg
        assert "got 2" in msg

    def test_get_failure_message_max(self):
        """Test failure message for max operator."""
        expectation = RowCountExpectation({"max": 5})
        msg = expectation.get_failure_message(10)
        assert "Expected at most 5 rows" in msg
        assert "got 10" in msg


class TestRowCountValidator:
    """Test RowCountValidator class."""

    def test_validate_row_count_passes(self):
        """Test validate_row_count when expectation passes."""
        expectation = RowCountExpectation({"eq": 2})
        rows = [{"id": 1}, {"id": 2}]
        passed, msg = RowCountValidator.validate_row_count(rows, expectation)
        assert passed is True
        assert msg is None

    def test_validate_row_count_fails(self):
        """Test validate_row_count when expectation fails."""
        expectation = RowCountExpectation({"eq": 5})
        rows = [{"id": 1}, {"id": 2}]
        passed, msg = RowCountValidator.validate_row_count(rows, expectation)
        assert passed is False
        assert msg is not None
        assert "Expected exactly 5 rows" in msg
        assert "got 2" in msg

    def test_validate_row_count_empty_rows_eq_zero(self):
        """Test validate_row_count with empty rows expecting 0."""
        expectation = RowCountExpectation({"eq": 0})
        rows = []
        passed, msg = RowCountValidator.validate_row_count(rows, expectation)
        assert passed is True
        assert msg is None

    def test_validate_row_count_empty_rows_eq_nonzero(self):
        """Test validate_row_count with empty rows expecting non-zero."""
        expectation = RowCountExpectation({"eq": 5})
        rows = []
        passed, msg = RowCountValidator.validate_row_count(rows, expectation)
        assert passed is False
        assert msg is not None


@pytest.mark.skipif(pd is None, reason="pandas not installed")
class TestResultSetDataFrameEdgeCases:
    """Test edge cases for ResultSetDataFrame."""

    def test_from_rows_with_no_columns(self):
        """Test from_rows with completely empty rows (no columns at all)."""
        rows = []
        df = ResultSetDataFrame.from_rows(rows)
        assert df.empty
        assert len(df.columns) == 0

    def test_from_rows_with_mixed_column_presence(self):
        """Test from_rows where rows have different keys (sparse data)."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "age": 30},  # Missing 'name', has 'age' not in first row
        ]
        df = ResultSetDataFrame.from_rows(rows)
        assert len(df) == 2
        # pandas fills missing values with NaN
        assert "id" in df.columns
        assert "name" in df.columns
        assert "age" in df.columns

    def test_from_rows_column_names_mixed_case(self):
        """Test that column names are converted to lowercase."""
        rows = [{"ID": 1, "Name": "Alice", "EMAIL": "alice@example.com"}]
        df = ResultSetDataFrame.from_rows(rows)
        assert list(df.columns) == ["id", "name", "email"]

    def test_from_rows_with_special_characters_in_names(self):
        """Test column names with special characters and spaces."""
        rows = [{"user id": 1, "first_name": "Alice", "account@type": "premium"}]
        df = ResultSetDataFrame.from_rows(rows)
        # Column names should be lowercase but preserve special characters
        assert all(col.islower() or col in ["_", "@", " "] for col in df.columns)

    def test_from_rows_preserves_int_type(self):
        """Test that integer types are preserved."""
        rows = [{"count": 42}, {"count": 100}]
        df = ResultSetDataFrame.from_rows(rows)
        assert df["count"].dtype in [int, "int64", "Int64"]

    def test_from_rows_preserves_float_type(self):
        """Test that float types are preserved."""
        rows = [{"price": 19.99}, {"price": 29.99}]
        df = ResultSetDataFrame.from_rows(rows)
        assert df["price"].dtype in [float, "float64"]

    def test_from_rows_handles_none_values(self):
        """Test that None values are converted to NaN."""
        rows = [{"id": 1, "name": None}, {"id": 2, "name": "Bob"}]
        df = ResultSetDataFrame.from_rows(rows)
        assert pd.isna(df.loc[0, "name"])
        assert df.loc[1, "name"] == "Bob"

    def test_from_rows_with_boolean_values(self):
        """Test that boolean values are preserved."""
        rows = [{"active": True, "verified": False}]
        df = ResultSetDataFrame.from_rows(rows)
        # pandas converts Python bools to numpy bools, use truthiness checks
        assert df.loc[0, "active"]
        assert not df.loc[0, "verified"]

    def test_from_rows_with_string_values(self):
        """Test that string values are preserved."""
        rows = [{"email": "alice@example.com", "status": "active"}]
        df = ResultSetDataFrame.from_rows(rows)
        assert df.loc[0, "email"] == "alice@example.com"
        assert df.loc[0, "status"] == "active"
