"""rows_equal expectation for validating query result sets."""

from typing import Optional

import pandas as pd

from sql_unit.core.models import DataSource, DataSourceConverter
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
            self._parse_from_spec("rows", expected_spec["rows"])
        elif "csv" in expected_spec:
            self._parse_from_spec("csv", expected_spec["csv"])
        elif "sql" in expected_spec:
            if not database_manager:
                raise SetupError("database_manager required for sql: data source")
            self._parse_from_spec("sql", expected_spec["sql"])
        elif "reference" in expected_spec or "reference-all" in expected_spec:
            raise SetupError(
                "External references handled by parser. Pass resolved data as rows/csv/sql instead."
            )

    def _parse_from_spec(self, format_type: str, content: any) -> None:
        """
        Parse expected data from raw YAML specification.

        Converts raw YAML values (rows list, csv string, or sql string) into a
        DataSource object, then uses DataSourceConverter to create a DataFrame.

        Args:
            format_type: One of 'rows', 'csv', or 'sql'
            content: The raw content for that format type

        Raises:
            SetupError: If specification is invalid or conversion fails
        """
        try:
            # Create DataSource directly for rows/csv (bypass parser validation for empty data)
            if format_type == "rows":
                if not isinstance(content, list):
                    raise SetupError(f"rows must be a list, got {type(content).__name__}")
                # Validate all items are dicts
                for i, row in enumerate(content):
                    if not isinstance(row, dict):
                        raise SetupError(f"rows[{i}] must be dict, got {type(row).__name__}")
                # Serialize to JSON for storage in DataSource
                import json as json_lib
                data_source = DataSource(format="rows", content=json_lib.dumps(content))

            elif format_type == "csv":
                if not isinstance(content, str):
                    raise SetupError(f"csv must be a string, got {type(content).__name__}")
                # CSV content is stored as-is
                data_source = DataSource(format="csv", content=content)

            elif format_type == "sql":
                if not isinstance(content, str):
                    raise SetupError(f"sql must be a string, got {type(content).__name__}")
                from sql_unit.inputs.inputs import SQLValidator
                # Validate SQL content
                validated_sql = SQLValidator.validate_sql(content)
                data_source = DataSource(format="sql", content=validated_sql)

            else:
                raise SetupError(f"Unknown format: {format_type}")

            # Use DataSourceConverter to create DataFrame
            self.expected_df = DataSourceConverter.to_dataframe(
                data_source, self.database_manager
            )
        except SetupError:
            raise
        except Exception as e:
            raise SetupError(f"Failed to parse {format_type} data source: {str(e)}") from e

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
