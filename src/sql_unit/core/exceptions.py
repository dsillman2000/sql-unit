"""Custom exception hierarchy for sql-unit."""


class SqlUnitError(Exception):
    """Base exception for all sql-unit errors."""
    pass


class ParserError(SqlUnitError):
    """Raised when parsing SQL or YAML fails."""
    
    def __init__(self, message: str, filepath: str | None = None, line_number: int | None = None):
        self.message = message
        self.filepath = filepath
        self.line_number = line_number
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.filepath:
            parts.append(f"File: {self.filepath}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        return " | ".join(parts)


class RendererError(SqlUnitError):
    """Raised when template rendering fails."""
    
    def __init__(self, message: str, test_id: str | None = None, sql: str | None = None):
        self.message = message
        self.test_id = test_id
        self.sql = sql
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.test_id:
            parts.append(f"Test: {self.test_id}")
        if self.sql:
            parts.append(f"SQL: {self.sql[:100]}...")
        return " | ".join(parts)


class ExecutionError(SqlUnitError):
    """Raised when test execution fails."""
    
    def __init__(self, message: str, test_id: str | None = None, sql: str | None = None):
        self.message = message
        self.test_id = test_id
        self.sql = sql
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.test_id:
            parts.append(f"Test: {self.test_id}")
        if self.sql:
            parts.append(f"SQL: {self.sql[:100]}...")
        return " | ".join(parts)


class ConfigError(SqlUnitError):
    """Raised when configuration or test definition is invalid."""
    
    def __init__(self, message: str, test_id: str | None = None):
        self.message = message
        self.test_id = test_id
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.test_id:
            parts.append(f"Test: {self.test_id}")
        return " | ".join(parts)


class SetupError(SqlUnitError):
    """Raised when test setup (given clause processing) fails."""
    
    def __init__(self, message: str, test_id: str | None = None):
        self.message = message
        self.test_id = test_id
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.test_id:
            parts.append(f"Test: {self.test_id}")
        return " | ".join(parts)


class TemplateError(SqlUnitError):
    """Raised when Jinja template rendering fails."""
    
    def __init__(self, message: str, test_id: str | None = None):
        self.message = message
        self.test_id = test_id
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        parts = [self.message]
        if self.test_id:
            parts.append(f"Test: {self.test_id}")
        return " | ".join(parts)
