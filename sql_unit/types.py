from enum import StrEnum
from typing import Callable


class SQLUnitMockType(StrEnum):
    """
    Enum representing different Jinja data types which can be used as mocks.
    """

    table = "table"
    mapping = "mapping"
    sequence = "sequence"
    int = "int"
    float = "float"
    str = "str"
    bool = "bool"

    @property
    def default_factory(self) -> "Callable[[str], str]":
        """Get the default value for the type, if applicable."""
        defaults = {
            SQLUnitMockType.table: lambda name: f'"{name}_table"',
            SQLUnitMockType.mapping: lambda _: "{}",
            SQLUnitMockType.sequence: lambda _: "[]",
            SQLUnitMockType.int: lambda _: "0",
            SQLUnitMockType.float: lambda _: "0.0",
            SQLUnitMockType.str: lambda name: f'"{name}"',
            SQLUnitMockType.bool: lambda _: "false",
        }
        return defaults[self]
