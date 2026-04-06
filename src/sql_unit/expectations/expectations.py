"""Row count expectation evaluation."""

from ..core.exceptions import SetupError


class RowCountExpectation:
    """Represents and evaluates row_count expectations."""

    def __init__(self, row_count_spec: dict | int) -> None:
        """
        Initialize row count expectation.

        Args:
            row_count_spec: Dict with 'eq'|'min'|'max' key or int value for 'eq'

        Raises:
            SetupError: If specification is invalid
        """
        if isinstance(row_count_spec, int):
            # Shorthand: row_count: 5 means eq: 5
            self.operator = "eq"
            self.value = row_count_spec

        elif isinstance(row_count_spec, dict):
            operators = list(row_count_spec.keys())

            if not operators:
                raise SetupError("row_count expectation must have operator (eq, min, or max)")

            if len(operators) > 1:
                raise SetupError(f"row_count can only have one operator, got {operators}")

            self.operator = operators[0]
            self.value = row_count_spec[self.operator]

            if self.operator not in ("eq", "min", "max"):
                raise SetupError(
                    f"Unknown row_count operator: '{self.operator}'. Expected eq, min, or max"
                )

            if not isinstance(self.value, int) or self.value < 0:
                raise SetupError(f"row_count value must be non-negative integer, got {self.value}")

        else:
            raise SetupError(f"row_count must be int or dict, got {type(row_count_spec).__name__}")

    def evaluate(self, actual_count: int) -> bool:
        """
        Evaluate the expectation against actual row count.

        Args:
            actual_count: Actual number of rows returned

        Returns:
            True if expectation is met, False otherwise
        """
        if self.operator == "eq":
            return actual_count == self.value
        elif self.operator == "min":
            return actual_count >= self.value
        elif self.operator == "max":
            return actual_count <= self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")

    def get_failure_message(self, actual_count: int) -> str:
        """
        Generate failure message for expectation.

        Args:
            actual_count: Actual number of rows returned

        Returns:
            Human-readable failure message
        """
        if self.operator == "eq":
            return f"Expected exactly {self.value} rows, got {actual_count}"
        elif self.operator == "min":
            return f"Expected at least {self.value} rows, got {actual_count}"
        elif self.operator == "max":
            return f"Expected at most {self.value} rows, got {actual_count}"
        else:
            return "Row count expectation failed"


class RowCountValidator:
    """Validator for row count expectations in test results."""

    @staticmethod
    def validate_row_count(rows: list, expectation: RowCountExpectation) -> tuple[bool, str | None]:
        """
        Validate row count against expectation.

        Args:
            rows: List of result rows (dicts)
            expectation: RowCountExpectation to validate against

        Returns:
            Tuple of (passed: bool, failure_message: str | None)
        """
        actual_count = len(rows)
        passed = expectation.evaluate(actual_count)

        if passed:
            return True, None
        else:
            failure_msg = expectation.get_failure_message(actual_count)
            return False, failure_msg
