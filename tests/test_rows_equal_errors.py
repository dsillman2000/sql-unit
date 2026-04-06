"""Tests for rows_equal error handling and edge cases."""

import pytest

from sql_unit.core.exceptions import SetupError
from sql_unit.expectations.rows_equal import RowsEqualExpectation

try:
    import pandas as pd
except ImportError:
    pd = None


class MockDatabaseManager:
    """Mock database manager for testing SQL data source."""

    def __init__(self, results=None, raise_error=False):
        """Initialize mock with optional results or error flag."""
        self.results = results or []
        self.raise_error = raise_error
        self.executed_queries = []

    def execute_query(self, query):
        """Execute query and return results or raise error."""
        self.executed_queries.append(query)
        if self.raise_error:
            raise Exception("Database connection failed")
        return self.results


@pytest.mark.skipif(pd is None, reason="pandas not installed")
class TestRowsEqualErrorHandling:
    """Test error handling in RowsEqualExpectation."""

    def test_init_with_non_dict_rows_raises_error(self):
        """Test that non-dict rows raise SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"rows": "not a list"})
        assert "rows must be a list" in str(exc_info.value)

    def test_init_with_non_dict_row_item_raises_error(self):
        """Test that non-dict items in rows raise SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"rows": [{"id": 1}, "not a dict", {"id": 3}]})
        assert "must be dict" in str(exc_info.value)

    def test_init_with_empty_rows_list(self):
        """Test initialization with empty rows list (expects no rows)."""
        expectation = RowsEqualExpectation({"rows": []})
        assert expectation.expected_df is not None
        assert len(expectation.expected_df) == 0

    def test_init_with_csv_empty_string(self):
        """Test initialization with empty CSV string (expects no rows)."""
        expectation = RowsEqualExpectation({"csv": ""})
        assert expectation.expected_df is not None
        assert len(expectation.expected_df) == 0

    def test_init_with_csv_headers_only(self):
        """Test initialization with CSV containing only headers (no data rows)."""
        expectation = RowsEqualExpectation({"csv": "id,name,email"})
        assert expectation.expected_df is not None
        assert len(expectation.expected_df) == 0

    def test_init_with_csv_valid_content(self):
        """Test that CSV parsing with valid content succeeds."""
        expectation = RowsEqualExpectation({"csv": "id,name\n1,Alice\n2,Bob"})
        assert len(expectation.expected_df) == 2

    def test_init_with_sql_without_database_manager_raises_error(self):
        """Test that SQL data source without database_manager raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation(
                {"sql": "SELECT id, name FROM users"},
                database_manager=None,
            )
        assert "database_manager required" in str(exc_info.value)

    def test_init_with_sql_and_database_manager(self):
        """Test SQL data source with database manager succeeds."""
        mock_db = MockDatabaseManager(results=[{"id": 1, "name": "Alice"}])
        expectation = RowsEqualExpectation(
            {"sql": "SELECT id, name FROM users"},
            database_manager=mock_db,
        )
        assert len(expectation.expected_df) == 1
        assert mock_db.executed_queries[0] == "SELECT id, name FROM users"

    def test_init_with_sql_empty_result(self):
        """Test SQL data source that returns no rows."""
        mock_db = MockDatabaseManager(results=[])
        expectation = RowsEqualExpectation(
            {"sql": "SELECT id, name FROM users WHERE id > 1000"},
            database_manager=mock_db,
        )
        assert len(expectation.expected_df) == 0

    def test_init_with_sql_execution_error_raises_error(self):
        """Test that SQL execution errors are caught and wrapped."""
        mock_db = MockDatabaseManager(raise_error=True)
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation(
                {"sql": "SELECT * FROM nonexistent_table"},
                database_manager=mock_db,
            )
        assert "Failed to execute SQL query" in str(exc_info.value)

    def test_init_with_reference_raises_error(self):
        """Test that reference data source raises SetupError with helpful message."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"reference": "fixtures.yaml"})
        assert "External references handled by parser" in str(exc_info.value)

    def test_init_with_reference_all_raises_error(self):
        """Test that reference-all data source raises SetupError with helpful message."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"reference-all": "fixtures/*.yaml"})
        assert "External references handled by parser" in str(exc_info.value)

    def test_init_with_no_data_source_raises_error(self):
        """Test that no data source raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({})
        assert "rows_equal must have one data source" in str(exc_info.value)

    def test_init_with_invalid_data_source_raises_error(self):
        """Test that invalid data source key raises SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"invalid_source": "data"})
        assert "rows_equal must have one data source" in str(exc_info.value)

    def test_init_with_multiple_data_sources_raises_error(self):
        """Test that multiple data sources raise SetupError."""
        with pytest.raises(SetupError) as exc_info:
            RowsEqualExpectation({"rows": [{"id": 1}], "csv": "id\n1"})
        assert "exactly one data source" in str(exc_info.value)

    def test_parse_csv_with_whitespace_handling(self):
        """Test that CSV parsing handles leading/trailing whitespace."""
        expectation = RowsEqualExpectation({"csv": "  id,name\n  1,Alice\n  2,Bob  \n"})
        assert len(expectation.expected_df) == 2
        assert list(expectation.expected_df.columns) == ["id", "name"]

    def test_parse_csv_with_multiline_values(self):
        """Test CSV parsing with values containing commas or quotes."""
        expectation = RowsEqualExpectation(
            {"csv": 'id,name,address\n1,"Alice","123 Main St, Apt 4"\n2,Bob,"456 Oak Ave"'}
        )
        assert len(expectation.expected_df) == 2

    def test_evaluate_with_empty_actual_rows(self):
        """Test evaluate() with empty actual rows."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1}]})
        passed, msg = expectation.evaluate([])
        assert passed is False
        assert msg is not None

    def test_evaluate_success_with_matching_rows(self):
        """Test evaluate() succeeds when rows match."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": "Alice"}]})
        passed, msg = expectation.evaluate([{"id": 1, "name": "Alice"}])
        assert passed is True
        assert msg is None

    def test_evaluate_failure_with_different_rows(self):
        """Test evaluate() fails when rows don't match."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": "Alice"}]})
        passed, msg = expectation.evaluate([{"id": 2, "name": "Bob"}])
        assert passed is False
        assert msg is not None
        assert "rows_equal expectation failed" in msg

    def test_evaluate_returns_tuple(self):
        """Test that evaluate() returns (bool, str|None) tuple."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1}]})
        result = expectation.evaluate([{"id": 1}])
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert result[1] is None or isinstance(result[1], str)

    def test_evaluate_with_mismatched_columns(self):
        """Test evaluate() when expected has different columns than actual."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": "Alice"}]})
        # Actual has extra column 'email' (should be ignored)
        passed, msg = expectation.evaluate(
            [{"id": 1, "name": "Alice", "email": "alice@example.com"}]
        )
        assert passed is True

    def test_evaluate_with_missing_expected_column_in_actual(self):
        """Test evaluate() when actual is missing a column from expected."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": "Alice"}]})
        # Actual only has 'id', missing 'name'
        passed, msg = expectation.evaluate([{"id": 1}])
        assert passed is False
        assert msg is not None

    def test_evaluate_with_null_values_matching(self):
        """Test evaluate() with NULL values that match."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": None}]})
        passed, msg = expectation.evaluate([{"id": 1, "name": None}])
        assert passed is True

    def test_evaluate_with_null_mismatch(self):
        """Test evaluate() when one has NULL and other doesn't."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": None}]})
        passed, msg = expectation.evaluate([{"id": 1, "name": "Alice"}])
        assert passed is False

    def test_evaluate_with_case_insensitive_columns(self):
        """Test evaluate() with different case in column names."""
        expectation = RowsEqualExpectation({"rows": [{"ID": 1, "NAME": "Alice"}]})
        passed, msg = expectation.evaluate([{"id": 1, "name": "Alice"}])
        assert passed is True

    def test_evaluate_with_reordered_columns(self):
        """Test evaluate() with columns in different order."""
        expectation = RowsEqualExpectation({"rows": [{"name": "Alice", "id": 1}]})
        passed, msg = expectation.evaluate([{"id": 1, "name": "Alice"}])
        assert passed is True

    def test_evaluate_with_reordered_rows(self):
        """Test evaluate() with rows in different order."""
        expectation = RowsEqualExpectation(
            {"rows": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        )
        passed, msg = expectation.evaluate([{"id": 2, "name": "Bob"}, {"id": 1, "name": "Alice"}])
        assert passed is True

    def test_format_failure_message_includes_row_counts(self):
        """Test that failure message includes expected and actual row counts."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1}]})
        passed, msg = expectation.evaluate([{"id": 1}, {"id": 2}])
        assert passed is False
        assert "Expected 1 rows" in msg
        assert "got 2 rows" in msg

    def test_format_failure_message_includes_dataframes(self):
        """Test that failure message includes both DataFrames."""
        expectation = RowsEqualExpectation({"rows": [{"id": 1, "name": "Alice"}]})
        passed, msg = expectation.evaluate([{"id": 2, "name": "Bob"}])
        assert passed is False
        assert "Expected DataFrame" in msg
        assert "Actual DataFrame" in msg
