"""Tests for RowsEqualExpectation."""

import pytest

try:
    import pandas as pd
except ImportError:
    pd = None

from sql_unit.expectations import RowsEqualExpectation
from sql_unit.core.exceptions import SetupError


@pytest.mark.skipif(pd is None, reason="pandas not installed")
class TestRowsEqualExpectation:
    """Test RowsEqualExpectation."""

    def test_rows_exact_match(self):
        """Test rows_equal with exact match."""
        spec = {"rows": [{"id": 1, "name": "Alice"}]}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 1, "name": "Alice"}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_mismatch(self):
        """Test rows_equal with mismatch."""
        spec = {"rows": [{"id": 1, "name": "Alice"}]}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 2, "name": "Bob"}]
        passed, msg = expectation.evaluate(actual)
        assert not passed
        assert msg is not None

    def test_rows_order_independent(self):
        """Test order-independent row comparison."""
        spec = {
            "rows": [
                {"id": 2, "name": "Bob"},
                {"id": 1, "name": "Alice"},
            ]
        }
        expectation = RowsEqualExpectation(spec)

        # Actual rows in different order
        actual = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_column_order_independent(self):
        """Test column order independence."""
        spec = {"rows": [{"id": 1, "name": "Alice"}]}
        expectation = RowsEqualExpectation(spec)

        # Actual rows with columns in different order
        actual = [{"name": "Alice", "id": 1}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_case_insensitive_columns(self):
        """Test case-insensitive column names."""
        spec = {"rows": [{"id": 1, "name": "Alice"}]}
        expectation = RowsEqualExpectation(spec)

        # Actual with uppercase columns
        actual = [{"ID": 1, "NAME": "Alice"}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_empty(self):
        """Test empty result set expectation."""
        spec = {"rows": []}
        expectation = RowsEqualExpectation(spec)

        actual = []
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_row_count_mismatch(self):
        """Test row count mismatch detection."""
        spec = {"rows": [{"id": 1}]}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 1}, {"id": 2}]
        passed, msg = expectation.evaluate(actual)
        assert not passed
        assert "Expected 1 rows, got 2 rows" in msg

    def test_rows_with_null_values(self):
        """Test NULL value comparison."""
        spec = {"rows": [{"id": 1, "name": None}]}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 1, "name": None}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_null_mismatch(self):
        """Test NULL vs non-NULL mismatch."""
        spec = {"rows": [{"id": 1, "name": None}]}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 1, "name": "Alice"}]
        passed, msg = expectation.evaluate(actual)
        assert not passed

    def test_csv_parse_valid(self):
        """Test CSV parsing with valid data."""
        csv_data = "id,name\n1,Alice\n2,Bob"
        spec = {"csv": csv_data}
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_csv_parse_invalid(self):
        """Test CSV parsing with invalid data."""
        csv_data = "id,name\n1,Alice\n2"  # Missing column
        spec = {"csv": csv_data}

        # This should work (csv module handles this)
        expectation = RowsEqualExpectation(spec)
        assert expectation.expected_df is not None

    def test_csv_empty(self):
        """Test empty CSV."""
        csv_data = "id,name"  # Headers only, no data
        spec = {"csv": csv_data}
        expectation = RowsEqualExpectation(spec)

        actual = []
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_multiple_rows(self):
        """Test multiple rows comparison."""
        spec = {
            "rows": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"},
            ]
        }
        expectation = RowsEqualExpectation(spec)

        actual = [
            {"id": 3, "name": "Charlie"},
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_rows_mixed_types(self):
        """Test mixed column types."""
        spec = {
            "rows": [
                {"id": 1, "name": "Alice", "score": 95.5, "active": True},
            ]
        }
        expectation = RowsEqualExpectation(spec)

        actual = [{"id": 1, "name": "Alice", "score": 95.5, "active": True}]
        passed, msg = expectation.evaluate(actual)
        assert passed, msg

    def test_no_data_source(self):
        """Test error when no data source provided."""
        spec = {}  # No rows, csv, sql, or reference
        with pytest.raises(SetupError, match="must have one data source"):
            RowsEqualExpectation(spec)

    def test_sql_not_supported_without_manager(self):
        """Test error when sql specified without database_manager."""
        spec = {"sql": "SELECT * FROM test"}
        with pytest.raises(SetupError, match="database_manager required"):
            RowsEqualExpectation(spec)

    def test_reference_error_message(self):
        """Test that reference is handled by parser."""
        spec = {"reference": "tests.yaml"}
        with pytest.raises(
            SetupError, match="External references handled by parser"
        ):
            RowsEqualExpectation(spec)
