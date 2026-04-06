"""rows_equal expectation for validating query result sets."""

import json
from typing import Optional

import pandas as pd

from sql_unit.core.models import DataSourceConverter, DataSource
from sql_unit.core.exceptions import SetupError
from sql_unit.expectations.expectations import Expectation, ResultSetDataFrame
from sql_unit.expectations.normalizer import DataFrameNormalizer


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
            database_manager: DatabaseManager instance (required for SQL and dialect info)
            float_precision: Tolerance for float comparisons (10^-N).
                            If None, uses default (1e-10) or value from sql-unit.yaml config

        Raises:
            SetupError: If specification is invalid or no data source provided
        """
        self.database_manager = database_manager
        self.float_precision = float_precision
        self.expected_df = None

        # Extract the data source from the spec
        data_source = self._extract_data_source(expected_spec)

        # Convert to DataFrame using the shared abstraction
        self.expected_df = DataSourceConverter.to_dataframe(data_source, database_manager)

    def _extract_data_source(self, expected_spec: dict):
        """
        Extract and validate a single data source from the specification.

        Args:
            expected_spec: Dict that should contain exactly one of: rows, csv, sql

        Returns:
            DataSource object

        Raises:
            SetupError: If no data source, multiple sources, or references provided
        """
        # Check for references (not supported at this stage)
        if "reference" in expected_spec or "reference-all" in expected_spec:
            raise SetupError(
                "External references handled by parser. Pass resolved data as rows/csv/sql instead."
            )

        # Find which data source is provided
        data_sources = ["rows", "csv", "sql"]
        provided_sources = [source for source in data_sources if source in expected_spec]

        if len(provided_sources) == 0:
            raise SetupError("rows_equal must have one data source: rows, csv, sql, or reference")
        elif len(provided_sources) > 1:
            raise SetupError(
                f"rows_equal must have exactly one data source, got {len(provided_sources)}: {', '.join(provided_sources)}"
            )

        source_format = provided_sources[0]
        source_content = expected_spec[source_format]

        # Handle each format with proper validation for expectations (allow empty data)
        if source_format == "rows":
            if not isinstance(source_content, list):
                raise SetupError(f"rows must be a list, got {type(source_content).__name__}")

            # Validate all items are dicts (even for empty list)
            for i, item in enumerate(source_content):
                if not isinstance(item, dict):
                    raise SetupError(f"Row {i} must be dict, got {type(item).__name__}")

            # Empty rows list is valid for expectations
            content = json.dumps(source_content)
            return DataSource(format="rows", content=content)

        elif source_format == "csv":
            if not isinstance(source_content, str):
                raise SetupError(f"csv must be a string, got {type(source_content).__name__}")

            # Empty CSV string is valid (becomes empty DataFrame)
            # CSV with headers only is also valid (becomes empty DataFrame)
            return DataSource(format="csv", content=source_content)

        elif source_format == "sql":
            if not isinstance(source_content, str):
                raise SetupError(f"sql must be a string, got {type(source_content).__name__}")

            validated_sql = source_content.strip()
            if not validated_sql:
                raise SetupError("sql data source cannot be empty")

            # Check that it looks like a SELECT statement
            if not validated_sql.upper().startswith(("SELECT", "WITH")):
                raise SetupError("SQL data source must start with SELECT or WITH")

            return DataSource(format="sql", content=validated_sql)

        else:
            raise SetupError(f"Unknown data source format: {source_format}")

    def evaluate(self, actual_rows: list) -> tuple[bool, str | None]:
        """
        Evaluate rows_equal expectation against actual query results.

        Args:
            actual_rows: List of row dicts from query result

        Returns:
            Tuple of (passed: bool, failure_message: str | None)
        """
        try:
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
