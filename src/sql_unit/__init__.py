"""SQL Unit - SQL Testing Framework (Phase 1 Core)."""

from .database import (
    ConnectionConfig,
    DatabaseManager,
)
from .core.exceptions import (
    ExecutionError,
    ParserError,
    RendererError,
    SqlUnitError,
)
from .core.models import (
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
from .inputs import (
    GivenClauseParser,
    GivenClauseValidator,
    DataSourceParser,
    AliasDeriver,
    CTEInput,
    CTEInjector,
    RelationInput,
    RelationSubstitutor,
    JinjaContextInput,
    JinjaContextCollisionDetector,
    InputSetup,
    InputExecutor,
    InputValidator,
)

try:
    from .inputs.expectations import RowCountExpectation, RowCountValidator
except ImportError:
    RowCountExpectation = None
    RowCountValidator = None

__version__ = "0.1.0"

__all__ = [
    # Core
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
    "DatabaseManager",
    "ConnectionConfig",
    # Execution
    "TestRunner",
    "BatchTestRunner",
    # Inputs
    "GivenClauseParser",
    "GivenClauseValidator",
    "DataSourceParser",
    "AliasDeriver",
    "CTEInput",
    "CTEInjector",
    "RelationInput",
    "RelationSubstitutor",
    "JinjaContextInput",
    "JinjaContextCollisionDetector",
    "InputSetup",
    "InputExecutor",
    "InputValidator",
]
