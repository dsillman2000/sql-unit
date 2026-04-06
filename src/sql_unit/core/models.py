"""Data structures for test definitions."""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum


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
