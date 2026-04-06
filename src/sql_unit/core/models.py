"""Data structures for test definitions."""

import json
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    import pandas as pd


class InputType(Enum):
    """Types of input specifications in the given section."""

    CTE = "cte"
    RELATION = "relation"
    JINJA_CONTEXT = "jinja_context"
    TEMP_TABLE = "temp_table"


@dataclass
class DataSource:
    """Represents a data source (SQL, CSV, or rows) used in input specifications."""

    format: str  # 'sql', 'csv', or 'rows'
    content: str  # SQL query, CSV string, or serialized rows

    def is_valid(self) -> bool:
        """Check if data source content is valid for its format."""
        if self.format == "sql":
            # Will be validated during parsing
            return bool(self.content.strip())
        elif self.format == "csv":
            return bool(self.content.strip())
        elif self.format == "rows":
            return bool(self.content)
        return False


@dataclass
class InputSpec:
    """Represents a single input specification in the given section."""

    input_type: InputType
    targets: list[str] = field(default_factory=list)  # For CTE/Relation
    replacement: str | None = None  # For Relation
    data_source: DataSource | None = None  # For CTE/Relation
    alias: str | None = None  # For CTE/Relation/NestedDataSource
    jinja_context: dict[str, Any] = field(default_factory=dict)  # For Jinja context block


@dataclass
class TestDefinition:
    """Represents a single SQL unit test."""

    name: str
    given: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    description: str | None = None
    filepath: str | None = None
    line_number: int | None = None

    def test_id(self) -> str:
        """Return formatted test identifier: filepath::name"""
        if self.filepath:
            return f"{self.filepath}::{self.name}"
        return self.name


@dataclass
class TestFile:
    """Represents a SQL file with embedded tests."""

    filepath: str
    tests: list[TestDefinition] = field(default_factory=list)

    def has_test(self, name: str) -> bool:
        """Check if test name exists in file."""
        return any(t.name == name for t in self.tests)


@dataclass
class ResultSet:
    """Represents query execution results."""

    rows: list[dict[str, Any]] = field(default_factory=list)

    def as_list(self) -> list[dict[str, Any]]:
        """Return rows as list of dicts."""
        return self.rows


@dataclass
class ErrorReport:
    """Represents an error during test execution."""

    test_id: str
    error_type: str
    message: str
    filepath: str | None = None
    line_number: int | None = None
    executed_sql: str | None = None

    def __str__(self) -> str:
        parts = [f"Error in {self.test_id} ({self.error_type}): {self.message}"]
        if self.filepath:
            parts.append(f"File: {self.filepath}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        if self.executed_sql:
            parts.append(f"SQL: {self.executed_sql}")
        return "\n".join(parts)


@dataclass
class TestResult:
    """Represents the result of a test execution."""

    test_id: str
    passed: bool
    duration: float = 0.0
    error: ErrorReport | None = None

    def is_success(self) -> bool:
        """Return True if test passed."""
        return self.passed


class DataSourceConverter:
    """Converts DataSource objects to rows or DataFrames for use in inputs and expectations."""

    @staticmethod
    def to_rows(data_source: DataSource, database_manager: Any) -> list[dict[str, Any]]:
        """
        Convert a data source to a list of dicts (rows).

        Handles all three data source formats (sql, csv, rows) and requires a
        database manager for dialect information and SQL execution.

        Args:
            data_source: DataSource object with format and content
            database_manager: DatabaseManager instance (required for SQL execution and dialect info)

        Returns:
            List of dicts representing rows

        Raises:
            SetupError: If data source format is invalid or conversion fails
        """
        from sql_unit.core.exceptions import SetupError
        import csv
        import io

        if data_source.format == "sql":
            # Execute SQL query and return results
            try:
                results = database_manager.execute_query(data_source.content)
                return results if results else []
            except Exception as e:
                raise SetupError(f"Failed to execute SQL query: {str(e)}") from e

        elif data_source.format == "csv":
            # Parse CSV string to rows
            # Handle empty CSV gracefully (valid for expectations)
            try:
                lines = [line.strip() for line in data_source.content.strip().split("\n") if line.strip()]

                if not lines:
                    # Empty CSV - valid, just no data
                    return []

                # Parse CSV using csv.DictReader
                from sql_unit.inputs.inputs import CSVDialectDetector
                delimiter = CSVDialectDetector.detect_delimiter(data_source.content)

                # Use StringIO with properly formatted lines to avoid header whitespace issues
                csv_text = "\n".join(lines)
                reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
                rows = []
                for row in reader:
                    # Convert empty strings to None
                    converted_row = {k: None if v == "" else v for k, v in row.items()}
                    rows.append(converted_row)

                return rows
            except Exception as e:
                from sql_unit.core.exceptions import SetupError as OrigSetupError
                if isinstance(e, OrigSetupError):
                    raise
                raise SetupError(f"Failed to parse CSV: {str(e)}") from e

        elif data_source.format == "rows":
            # Deserialize rows from JSON
            try:
                rows = json.loads(data_source.content)
                if not isinstance(rows, list):
                    raise SetupError("rows format must deserialize to a list")
                # Empty list is valid
                return rows
            except json.JSONDecodeError as e:
                raise SetupError(f"Failed to parse rows JSON: {str(e)}") from e
            except Exception as e:
                from sql_unit.core.exceptions import SetupError as OrigSetupError
                if isinstance(e, OrigSetupError):
                    raise
                raise SetupError(f"Failed to deserialize rows: {str(e)}") from e

        else:
            raise SetupError(f"Unknown data source format: {data_source.format}")

    @staticmethod
    def to_dataframe(data_source: DataSource, database_manager: Any) -> "pd.DataFrame":
        """
        Convert a data source to a pandas DataFrame.

        Convenience wrapper around to_rows() that creates a DataFrame from the
        resulting rows. Returns an empty DataFrame for empty result sets.

        Args:
            data_source: DataSource object with format and content
            database_manager: DatabaseManager instance (required for SQL execution and dialect info)

        Returns:
            pandas DataFrame with normalized column names (lowercase)

        Raises:
            SetupError: If data source format is invalid or conversion fails
        """
        import pandas as pd
        from sql_unit.expectations.expectations import ResultSetDataFrame

        rows = DataSourceConverter.to_rows(data_source, database_manager)

        if not rows:
            return pd.DataFrame()

        return ResultSetDataFrame.from_rows(rows)
