/* #! sql-unit

    name: filters_child_users
    given:
      - cte:
          targets: ["testdb.testschema.users"]
          rows:
            - {id: 1, name: "Alice", age: 30}
            - {id: 2, name: "Bob", age: 15}
            - {id: 3, name: "Charlie", age: 25}
    expect:
      - rows_equal:
          rows:
            - {id: 1, name: "Alice", age: 30}
            - {id: 3, name: "Charlie", age: 25}

    ---

    name: empty_users
    given:
      - cte:
          targets: ["testdb.testschema.users"]
          rows: []
    expect:
      - row_count:
          eq: 0

    ---

    name: all_children
    given:
      - cte:
          targets: ["testdb.testschema.users"]
          csv: |
            id,name,age
            1,Alice,10
            2,Bob,15
            3,Charlie,17
    expect:
      - row_count:
          eq: 0

*/
select
    id,
    name,
    age
from testdb.testschema.users
where age >= 18
