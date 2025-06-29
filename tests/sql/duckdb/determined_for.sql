/*

    # sql-unit

    sql-unit.mock "columns":
      type: mapping
      default: {"my_col": "my_value"}

*/
--noqa: disable=all

select
    {% for col, val in (columns | dict).items() %}
    {{ val }} as {{ col }}{% if not loop.last %},{% endif %}
    {% endfor %}

/*
    # noqa: disable=LT*
    # sql-unit

    sql-unit.test "columns":
      expect: |-
        | my_col     |
        | ---------- |
        | "my_value" |

    sql-unit.test "other_columns":
      given "columns": {"one": 1, "two": 2, "three": 3}
      expect: |-
        | one | two | three |
        | --- | --- | ----- |
        | 1   | 2   | 3     |

*/
