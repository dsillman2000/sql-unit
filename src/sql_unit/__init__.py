"""SQL Unit - SQL Testing Framework (Phase 1 Core)."""

from .database import (
    ConnectionConfig,
    ConnectionManager,
)
from .exceptions import (
    ExecutionError,
    ParserError,
    RendererError,
    SqlUnitError,
)
from .models import (
    ErrorReport,
    ResultSet,
    TestDefinition,
    TestFile,
    TestResult,
)
from .parser import SqlBlockCommentParser, TestDiscoveryParser
from .renderer import ParameterizedSqlBuilder, TemplateRenderer
from .runner import BatchTestRunner, TestRunner
from .statement import StatementValidator, TestBindingEngine

__version__ = "0.1.0"

__all__ = [
    # Exceptions
    "SqlUnitError",
    "ParserError",
    "RendererError",
    "ExecutionError",
    # Models
    "TestDefinition",
    "TestFile",
    "ResultSet",
    "ErrorReport",
    "TestResult",
    # Parser
    "SqlBlockCommentParser",
    "TestDiscoveryParser",
    # Statement handling
    "StatementValidator",
    "TestBindingEngine",
    # Rendering
    "TemplateRenderer",
    "ParameterizedSqlBuilder",
    # Database
    "ConnectionManager",
    "ConnectionConfig",
    # Execution
    "TestRunner",
    "BatchTestRunner",
]
