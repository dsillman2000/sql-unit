"""SQL Unit - SQL Testing Framework (Phase 1 Core)."""

from sql_unit.database import (
    ConnectionConfig,
    DatabaseManager,
)
from sql_unit.core.exceptions import (
    ExecutionError,
    ParserError,
    RendererError,
    SqlUnitError,
)
from sql_unit.core.models import (
    ErrorReport,
    ResultSet,
    TestDefinition,
    TestFile,
    TestResult,
)
from sql_unit.parser import SqlBlockCommentParser, TestDiscoveryParser
from sql_unit.renderer import ParameterizedSqlBuilder, TemplateRenderer
from sql_unit.runner import BatchTestRunner, TestRunner
from sql_unit.statement import StatementValidator, TestBindingEngine
from sql_unit.inputs import (
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
    from sql_unit.inputs import RowCountExpectation, RowCountValidator
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
