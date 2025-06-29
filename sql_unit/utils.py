from typing import Any, Type


def native_to_sql(obj: Any) -> str:
    """Convert a native Python object to its SQL representation."""
    if isinstance(obj, str):
        return f"'{obj}'"
    elif isinstance(obj, (int, float)):
        return str(obj)
    elif obj is None:
        return "null"
    elif isinstance(obj, list):
        return f"[{', '.join(native_to_sql(item) for item in obj)}]"
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    else:
        raise TypeError(f"Unsupported type for SQL conversion: {type(obj)}")


def native_to_sql_typedef(typ: Type) -> str:
    """Convert a native Python type to its SQL type definition."""
    if typ is str:
        return "string"
    elif typ is int:
        return "int"
    elif typ is float:
        return "float"
    elif typ is list:
        return "array"
    elif typ is bool:
        return "boolean"
    elif typ is type(None):
        return "null"
    else:
        raise TypeError(f"Unsupported type for SQL type definition: {typ}")
