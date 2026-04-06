"""Data structures for test definitions."""

from dataclasses import dataclass, field
from typing import Any


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
        parts = [
            f"Error in {self.test_id} ({self.error_type}): {self.message}"
        ]
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
