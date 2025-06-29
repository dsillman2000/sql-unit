import ast
import re
from functools import cached_property
from pathlib import Path
from typing import Any

import yaml
from daff import PythonTableView
from jinja2 import Environment
from pydantic import BaseModel, Field, RootModel, computed_field, model_validator

from sql_unit import annotations, types, utils

SQLUnitRow = RootModel[dict[str, Any]]


SQLUNIT_IDENTIFIER_PATTERN = re.compile(
    r"^sql\-unit\.(?P<type>.+?) \"(?P<identifier>[A-Za-z0-9_.-]+)\"$"
)
SQLUNIT_GIVEN_PATTERN = re.compile(r"^given \"(?P<name>[A-Za-z0-9_.-]+)\"$")


class SQLUnitMock(BaseModel):
    """SQL Unit Mock Model, representing a mock with its name and type."""

    name: str = Field(..., description="Name of the mock.")
    typ: types.SQLUnitMockType = Field(
        ..., description="Type of the mock.", alias="type"
    )
    default: Any | None = Field(None, description="Default value for the mock, if any.")
    columns: dict[str, str] | None = Field(
        None,
        description="Schema (name -> type lookup) of columns for the mock, if applicable.",
    )

    @model_validator(mode="after")
    def validate_type(self) -> "SQLUnitMock":
        """Ensure that the type is valid and set default values if not provided."""
        if self.typ == types.SQLUnitMockType.table and self.columns is None:
            raise ValueError("Table mocks must have a defined schema (columns).")
        return self

    @classmethod
    def from_yaml_item(cls, key: str, value: Any) -> "SQLUnitMock":
        """Create an SQLUnitMock instance from a YAML item."""
        match = SQLUNIT_IDENTIFIER_PATTERN.match(key)
        if not match:
            raise ValueError(f"Invalid mock identifier: {key}")
        assert (
            match.group("type") == "mock"
        ), "Only 'mock' type is supported in this context."
        identifier = match.group("identifier")
        return cls(
            name=identifier,
            **value,  # type: ignore
        )

    @property
    def default_value(self) -> Any:
        """Get the default value for the mock, if any."""
        return ast.literal_eval(
            self.typ.default_factory(self.name)
            if self.default is None
            else self.default
        )  # type: ignore


class SQLUnitMockSchema(RootModel[dict[str, SQLUnitMock]]):
    """SQL Unit Mock Schema Model, representing a schema of mocks."""

    @classmethod
    def from_template(cls, template_str: str) -> "SQLUnitMockSchema":
        """Create an SQLUnitMockSchema instance from a Jinja2 template string."""
        comment_obj = annotations.get_comments_obj(template_str)
        mocks: dict[str, SQLUnitMock] = {}
        for key, value in comment_obj.items():
            if "sql-unit.mock" not in key:
                continue
            try:
                parsed_mock = SQLUnitMock.from_yaml_item(key, value)
                mocks[parsed_mock.name] = parsed_mock
            except ValueError:
                pass
        return cls(mocks)

    @cached_property
    def default_values(self) -> dict[str, Any]:
        """Dictionary of mock names to their default values."""
        return {name: mock.default_value for name, mock in self.root.items()}


class SQLUnitSource(BaseModel):
    """SQL Unit Source Model, representing a file containing Jinja-templated SQL source code."""

    path: Path = Field(..., description="Path to the SQL file.")

    def mock_schema(self) -> SQLUnitMockSchema:
        """Extract the mock schema from the SQL file."""
        template_str = self.path.read_text()
        return SQLUnitMockSchema.from_template(template_str)

    def test_cases(self) -> "list[SQLUnitTestCase]":
        """Extract test cases from the SQL file."""
        cases: list[SQLUnitTestCase] = []
        comments = annotations.get_comments_obj(self.code)  # type: ignore
        for key, value in comments.items():
            try:
                if "sql-unit.test" not in key:
                    continue
                case = SQLUnitTestCase.from_yaml_item(self, key, value)
                cases.append(case)
            except ValueError:
                # raise e
                continue
        return cases

    def mock(self, name: str) -> SQLUnitMock | None:
        """Get a specific mock by name."""
        return self.mock_schema().root.get(name)

    def __hash__(self) -> int:
        return hash(self.path)

    @computed_field
    def code(self) -> str:
        """SQL code content of the file."""
        return self.path.read_text()


class YAMLTable(BaseModel):
    rows: list[RootModel[dict[str, Any]]] = Field(
        default_factory=list, description="Rows of the YAML table."
    )
    columns: dict[str, str] = Field(
        default_factory=lambda: {"id": "int"}, description="Columns of the YAML table."
    )

    @model_validator(mode="after")
    def validate_columns(self) -> "YAMLTable":
        """Ensure that all rows have the same columns as defined in the table."""
        if not self.columns:
            raise ValueError("Columns must be defined for a YAMLTable.")
        for row in self.rows:
            if set(row.root.keys()) != set(self.columns):
                raise ValueError(
                    f"Row {row} does not match defined columns {self.columns}."
                )
        return self

    @classmethod
    def empty_mock_table(cls, mock_table: SQLUnitMock) -> "YAMLTable":
        """Create an empty YAML table for a mock."""
        return cls(rows=[], columns=mock_table.columns)  # type: ignore

    @classmethod
    def from_string(
        cls, table_str: str, schema: dict[str, str] | None = None
    ) -> "YAMLTable":
        """Create a YAMLTable from a string representation."""
        table_str = table_str.strip()
        lines = table_str.splitlines()
        if not lines:
            raise ValueError("Table string is empty.")
        header = lines[0].strip()
        columns = list(map(str.strip, header.split("|")[1:-1]))
        annotations = {
            col: ("" if "::" not in col else col.split("::", 1)[-1].strip())
            for col in columns
        }
        annotations = {
            k: v for k, v in annotations.items() if v
        }  # remove empty annotations
        if not all(c in "|- " for c in lines[1].strip()):
            raise ValueError(
                "Invalid table format, expected a header and separator line."
            )
        rows = []
        for line in lines[2:]:
            if not line.strip():
                continue
            values = map(yaml.safe_load, map(str.strip, line.split("|")[1:-1]))
            row = {col: val for col, val in zip(columns, values)}
            rows.append(row)
        if schema is None:
            if rows:
                # infer from first row
                schema = {
                    col: utils.native_to_sql_typedef(type(val))
                    for col, val in rows[0].items()
                }
            else:
                schema = {col: "string" for col in columns}
        schema |= annotations
        return cls(rows=rows, columns=schema)

    def as_unioned_selects(self) -> str:
        """Convert the YAML table to a set of unioned SQL SELECT statements."""
        if self.rows:
            selects = []
            for row in self.rows:
                sql_values = {
                    key: utils.native_to_sql(value) for key, value in row.root.items()
                }
                aliases = [
                    f"cast({val} as {typ}) as {key}"
                    for (key, val), typ in zip(
                        sql_values.items(), self.columns.values()
                    )
                ]
                select = f"select {', '.join(aliases)}"
                selects.append(select)
            return "\nunion all\n".join(selects)
        return (
            "select "
            + ", ".join(
                f"cast({utils.native_to_sql(None)} as {typ}) as {col}"
                for col, typ in self.columns.items()
            )
            + "\nwhere false"
        )

    def as_python_table(self) -> PythonTableView:
        """Convert the YAML table to a PythonTableView."""
        return PythonTableView([row.root for row in self.rows])


class SQLUnitTestCase(BaseModel):
    """SQL Unit Test Case Model, representing a test case with given conditions and expected results."""

    source: SQLUnitSource = Field(..., description="Source SQL file for the test case.")
    name: str = Field(..., description="Name of the test case.")
    expected: YAMLTable = Field(
        ..., description="Expected result table for the test case."
    )
    given: dict[str, Any] = Field(
        ..., description="Given conditions for the test case."
    )

    @staticmethod
    def parse_given(source: SQLUnitSource, key: str, value: Any) -> Any:
        """Parse the 'given' conditions from a YAML item."""
        match = SQLUNIT_GIVEN_PATTERN.match(key)
        if not match:
            raise ValueError(f"Invalid given condition identifier: {key}")
        name = match.group("name")
        mock_type = source.mock(name)
        if not mock_type:
            raise ValueError(f"Mock '{name}' not found in source mocks.")
        if mock_type.typ == types.SQLUnitMockType.table:
            return YAMLTable.from_string(value, schema=mock_type.columns)
        return value

    @classmethod
    def from_yaml_item(
        cls, source: SQLUnitSource, key: str, value: Any
    ) -> "SQLUnitTestCase":
        """Create an SQLUnitTestCase instance from a YAML item."""
        match = SQLUNIT_IDENTIFIER_PATTERN.match(key)
        if not match:
            raise ValueError(f"Invalid test case identifier: {key}")
        if match.group("type") != "test":
            raise ValueError("Only 'test' type is supported in this context.")
        name = match.group("identifier")
        assert "expected" in value, "Test case must have an 'expected' field."
        expected = YAMLTable.from_string(value["expected"])
        given_keys = {k: v for k, v in value.items() if SQLUNIT_GIVEN_PATTERN.match(k)}
        given = {k: cls.parse_given(source, k, v) for k, v in given_keys.items()}
        for k in source.mock_schema().root.keys():
            if k not in given:
                given[k] = YAMLTable.empty_mock_table(source.mock(k))  # type: ignore
        return cls(
            source=source,
            name=name,
            expected=expected,
            given=given,
        )

    def compile(self) -> str:
        """Compile the test case into a SQL query."""
        leading_with_pattern = re.compile(
            r"^\s*(with)\s+.+?\s+as\s+\(.+?\)", re.IGNORECASE | re.DOTALL
        )
        source_code: str = self.source.code  # type: ignore
        leading_with_match = leading_with_pattern.match(source_code)
        if leading_with_match:
            source_code = leading_with_pattern.sub("", source_code)
        given_withs = []
        with_clause = ""
        for name, value in self.given.items():
            if isinstance(value, YAMLTable):
                given_withs.append(f"{name}_table as ({value.as_unioned_selects()})")
            else:
                continue
        if given_withs:
            with_clause = f"with {', '.join(given_withs)}"
            if leading_with_match:
                trailing_comma = "," if leading_with_match else ""
                with_clause = f"{with_clause}{trailing_comma}\n"

        injected_source_code = with_clause + "\n" + source_code
        env = Environment()
        template = env.from_string(injected_source_code)
        context = self.given.copy()
        for mock in self.source.mock_schema().root.values():
            if mock.typ == types.SQLUnitMockType.table:
                context[mock.name] = f"{mock.name}_table"
        rendered_code = template.render(**context)
        return rendered_code.strip()
