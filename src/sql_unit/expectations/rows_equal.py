"""rows_equal expectation for validating query result sets."""

import csv
import io
from typing import Optional

import pandas as pd

from ..core.exceptions import SetupError
from .expectations import Expectation
from .normalizer import DataFrameNormalizer


class RowsEqualExpectation(Expectation):
    """Represents and evaluates rows_equal expectations."""

    def __init__(
        self,
        expected_spec: dict,
        database_manager=None,
        float_precision: Optional[float] = None,
    ) -> None:
        """
        Initialize rows_equal expectation.

        Args:
            expected_spec: Dict with one of: rows, csv, sql, or reference
                Example: {rows: [{id: 1, name: "Alice"}]}
                Example: {csv: "id,name\\n1,Alice"}
                Example: {sql: "SELECT id, name FROM ..."}
                Example: {reference: "tests.yaml"}
            database_manager: DatabaseManager instance for executing SQL queries
            float_precision: Tolerance for float comparisons (10^-N).
                            If None, uses default (1e-10) or value from sql-unit.yaml config

        Raises:
            SetupError: If specification is invalid or no data source provided
        """
        self.database_manager = database_manager
        self.float_precision = float_precision
        self.expected_df = None

        # Validate exactly one data source is provided
        data_sources = ["rows", "csv", "sql", "reference", "reference-all"]
        provided_sources = [source for source in data_sources if source in expected_spec]

        if len(provided_sources) == 0:
            raise SetupError("rows_equal must have one data source: rows, csv, sql, or reference")
        elif len(provided_sources) > 1:
            raise SetupError(
                f"rows_equal must have exactly one data source, got {len(provided_sources)}: {', '.join(provided_sources)}"
            )

        # Parse data source
        if "rows" in expected_spec:
            self._parse_rows(expected_spec["rows"])
        elif "csv" in expected_spec:
            self._parse_csv(expected_spec["csv"])
        elif "sql" in expected_spec:
            if not database_manager:
                raise SetupError("database_manager required for sql: data source")
            self._parse_sql(expected_spec["sql"])
        elif "reference" in expected_spec or "reference-all" in expected_spec:
            raise SetupError(
                "External references handled by parser. Pass resolved data as rows/csv/sql instead."
            )

    def _parse_rows(self, rows_data: list) -> None:
        """
        Parse expected data from YAML list of dicts.

        Args:
            rows_data: List of row dicts

        Raises:
            SetupError: If data is invalid
        """
        if not isinstance(rows_data, list):
            raise SetupError(f"rows must be a list, got {type(rows_data).__name__}")

        if not rows_data:
            # Empty list is valid - expects no rows
            self.expected_df = pd.DataFrame()
            return

        # Validate all items are dicts
        for i, row in enumerate(rows_data):
            if not isinstance(row, dict):
                raise SetupError(f"rows[{i}] must be dict, got {type(row).__name__}")

        # Convert to DataFrame and normalize column names to lowercase
        from .expectations import ResultSetDataFrame

        self.expected_df = ResultSetDataFrame.from_rows(rows_data)

    def _parse_csv(self, csv_data: str) -> None:
        """
        Parse expected data from CSV string.

        Args:
            csv_data: CSV string (first row = headers, rest = data)

        Raises:
            SetupError: If CSV is invalid
        """
        try:
            lines = [line.strip() for line in csv_data.strip().split("\n") if line.strip()]

            if not lines:
                # Empty CSV is valid - expects no rows
                self.expected_df = pd.DataFrame()
                return

            # Use StringIO for csv.DictReader
            reader = csv.DictReader(io.StringIO("\n".join(lines)))
            rows = list(reader)

            if not rows:
                # Headers only, no data
                self.expected_df = pd.DataFrame()
                return

            from .expectations import ResultSetDataFrame

            self.expected_df = ResultSetDataFrame.from_rows(rows)
        except Exception as e:
            raise SetupError(f"Failed to parse CSV: {str(e)}") from e

    def _parse_sql(self, sql_query: str) -> None:
        """
        Parse expected data from SQL query.

        Executes query against database and uses result as expected data.

        Args:
            sql_query: SQL SELECT statement

        Raises:
            SetupError: If query execution fails
        """
        try:
            results = self.database_manager.execute_query(sql_query)
            if not results:
                self.expected_df = pd.DataFrame()
                return

            from .expectations import ResultSetDataFrame

            self.expected_df = ResultSetDataFrame.from_rows(results)
        except Exception as e:
            raise SetupError(f"Failed to execute SQL query: {str(e)}") from e

    def evaluate(self, actual_rows: list) -> tuple[bool, str | None]:
        """
        Evaluate rows_equal expectation against actual query results.

        Args:
            actual_rows: List of row dicts from query result

        Returns:
            Tuple of (passed: bool, failure_message: str | None)
        """
        try:
            from .expectations import ResultSetDataFrame

            actual_df = ResultSetDataFrame.from_rows(actual_rows)

            # Normalize both DataFrames for comparison
            # Get expected columns list
            expected_cols = list(self.expected_df.columns)

            # Normalize actual to only include expected columns
            actual_normalized = DataFrameNormalizer.normalize_columns(actual_df, expected_cols)
            expected_normalized = DataFrameNormalizer.normalize(self.expected_df)

            # Both should be sorted identically
            actual_normalized = DataFrameNormalizer.normalize(actual_normalized)

            # Calculate tolerance for float comparison from float_precision
            # float_precision is 10^-N, so we use it as atol for absolute tolerance
            # rtol is set to 0 since we want absolute precision control, not relative
            atol = self.float_precision if self.float_precision is not None else 1e-10
            rtol = 0  # Disable relative tolerance, use only absolute tolerance

            # Compare DataFrames using pandas.testing.assert_frame_equal
            try:
                pd.testing.assert_frame_equal(
                    expected_normalized,
                    actual_normalized,
                    check_dtype=True,
                    check_exact=False,
                    atol=atol,
                    rtol=rtol,
                )
                return True, None
            except AssertionError as pandas_error:
                # Format detailed diff message
                failure_msg = self._format_failure_message(
                    expected_normalized,
                    actual_normalized,
                    str(pandas_error),
                )
                return False, failure_msg

        except Exception as e:
            return False, f"Comparison error: {str(e)}"

    def _format_failure_message(
        self,
        expected_df: "pd.DataFrame",
        actual_df: "pd.DataFrame",
        pandas_error: str,
    ) -> str:
        """
        Format detailed failure message with side-by-side comparison.

        Args:
            expected_df: Expected DataFrame (normalized)
            actual_df: Actual DataFrame (normalized)
            pandas_error: Error message from pandas.testing.assert_frame_equal

        Returns:
            Human-readable failure message with diffs
        """
        lines = [
            "rows_equal expectation failed:",
            f"Expected {len(expected_df)} rows, got {len(actual_df)} rows",
            "",
            "Pandas assertion output:",
            pandas_error,
            "",
            "Expected DataFrame:",
            str(expected_df),
            "",
            "Actual DataFrame:",
            str(actual_df),
        ]

        return "\n".join(lines)
