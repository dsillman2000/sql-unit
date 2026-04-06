/* #! sql-unit

    name: using_otherschema_users
    given:
      - relation:
          targets: ["testdb.testschema.users"]
          replacement: "testdb.otherschema.users"
    expect:
      - rows_equal:
          rows:
            - {id: 1, name: "Alice", age: 30}
            - {id: 3, name: "Charlie", age: 25}

*/
select
    id,
    name,
    age
from testdb.testschema.users
where age >= 18
