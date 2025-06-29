from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "query_name, expected_mocks",
    [
        pytest.param(
            "tpch_q1.sql", {"lineitem": "table", "delta": "int"}, id="tpch_q1"
        ),
        pytest.param("determined_for.sql", {"columns": "mapping"}, id="determined_for"),
    ],
)
def test_get_mocks(
    query_name: str, expected_mocks: set[str], duckdb_sql_dir: Path
) -> None:
    from sql_unit.model import SQLUnitSource

    sql_file = duckdb_sql_dir / query_name
    source = SQLUnitSource(path=sql_file)
    schema = source.mock_schema()
    print(f"{schema =}")

    txn = {name: typ.typ for name, typ in schema.root.items()}
    assert txn == expected_mocks


def test_parse_yaml_table():
    from sql_unit.model import YAMLTable

    str_content = """
    | one | two | three |
    |-----|-----|-------|
    | 1   | 2   | 3     |
    | 4   | 5   | 6     |
    """
    table = YAMLTable.from_string(
        str_content, schema={"one": "int", "two": "int", "three": "int"}
    )

    assert table.columns == {"one": "int", "two": "int", "three": "int"}
    assert len(table.rows) == 2
    assert table.rows[0].root == {"one": 1, "two": 2, "three": 3}
    assert table.rows[1].root == {"one": 4, "two": 5, "three": 6}

    assert (
        table.as_unioned_selects()
        == """
select cast(1 as int) as one, cast(2 as int) as two, cast(3 as int) as three
union all
select cast(4 as int) as one, cast(5 as int) as two, cast(6 as int) as three
    """.strip()
    )

    str_content = """
    | should | be | empty |
    |--------|----|-------|
    """
    table = YAMLTable.from_string(
        str_content, schema={"should": "int", "be": "int", "empty": "int"}
    )

    assert table.columns == {"should": "int", "be": "int", "empty": "int"}
    assert len(table.rows) == 0
    assert (
        table.as_unioned_selects()
        == """
select cast(null as int) as should, cast(null as int) as be, cast(null as int) as empty
where false
    """.strip()
    )


def test_parse_unit_test_case(tmp_path: Path):
    from sql_unit.model import SQLUnitSource
    from sql_unit.types import SQLUnitMockType

    sql_content = """
/*
    # sql-unit

    sql-unit.mock "mysrc":
      type: table
      columns:
        id: int
        name: string
*/
select * from {{ mysrc }} where id = 1 and name is not null
"""
    sql_file = tmp_path / "test.sql"
    sql_file.write_text(sql_content)
    source = SQLUnitSource(path=sql_file)

    mocks = source.mock_schema()
    assert mocks.model_dump() == {
        "mysrc": {
            "name": "mysrc",
            "typ": SQLUnitMockType.table,
            "default": None,
            "columns": {"id": "int", "name": "string"},
        }
    }
    assert source.test_cases() == []

    sql_content += """
/*
    # sql-unit

    sql-unit.test "test_case_1":
      expected: |-
        | id | name |
        |----|------|

    sql-unit.test "test_case_2":
      given "mysrc": |-
        | id | name |
        |----|------|
        | 1  | foo  |
        | 2  | bar  |
      expected: |-
        | id | name |
        |----|------|
        | 1  | foo  |

*/
"""
    del source
    sql_file.unlink()
    sql_file_2 = tmp_path / "test_with_cases.sql"
    sql_file_2.write_text(sql_content)
    source = SQLUnitSource(path=sql_file_2)

    assert len(source.test_cases()) == 2
    case_1, case_2 = source.test_cases()
    assert case_1.name == "test_case_1"
    assert "where false" in case_1.expected.as_unioned_selects()
    assert case_2.name == "test_case_2"
    assert "where false" not in case_2.expected.as_unioned_selects()

    assert (
        case_1.compile()
        == """with mysrc_table as (select cast(null as int) as id, cast(null as string) as name
where false)

/*
    # sql-unit

    sql-unit.mock "mysrc":
      type: table
      columns:
        id: int
        name: string
*/
select * from mysrc_table where id = 1 and name is not null

/*
    # sql-unit

    sql-unit.test "test_case_1":
      expected: |-
        | id | name |
        |----|------|

    sql-unit.test "test_case_2":
      given "mysrc": |-
        | id | name |
        |----|------|
        | 1  | foo  |
        | 2  | bar  |
      expected: |-
        | id | name |
        |----|------|
        | 1  | foo  |

*/"""
    )
