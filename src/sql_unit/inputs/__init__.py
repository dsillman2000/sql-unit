import importlib.util

from sql_unit.inputs.inputs import (
    GivenClauseParser,
    GivenClauseValidator,
    DataSourceParser,
    AliasDeriver,
    CSVParser,
    CSVDialectDetector,
    RowsParser,
)
from sql_unit.inputs.cte import CTEInput, CTEInjector
from sql_unit.inputs.relation import RelationInput, RelationSubstitutor
from sql_unit.inputs.jinja_context import (
    JinjaContextInput,
    JinjaContextCollisionDetector,
    JinjaContextDataSource,
)
from sql_unit.inputs.setup import InputSetup, InputExecutor, InputValidator

HAS_EXPECTATIONS = importlib.util.find_spec("sql_unit.expectations.expectations") is not None
if HAS_EXPECTATIONS:
    from sql_unit.expectations.expectations import RowCountExpectation, RowCountValidator  # noqa: F401

__all__ = [
    "GivenClauseParser",
    "GivenClauseValidator",
    "DataSourceParser",
    "AliasDeriver",
    "CSVParser",
    "CSVDialectDetector",
    "RowsParser",
    "CTEInput",
    "CTEInjector",
    "RelationInput",
    "RelationSubstitutor",
    "JinjaContextInput",
    "JinjaContextCollisionDetector",
    "JinjaContextDataSource",
    "InputSetup",
    "InputExecutor",
    "InputValidator",
]
if HAS_EXPECTATIONS:
    __all__.extend(["RowCountExpectation", "RowCountValidator"])
