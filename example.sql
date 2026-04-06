/* #! sql-unit

  name: filter_users_by_age
  description: Shall filter users by age, returning only those 18 or older
  given:
    - cte:
        targets: ["db.schema.users"]
        rows:
          - {id: 1, name: 'Alice', age: 20}
          - {id: 2, name: 'Bob', age: 15}
          - {id: 3, name: 'Charlie', age: 35}
  expect:
    - rows_equal:
        rows:
          - {id: 1, name: 'Alice', age: 20}
          - {id: 3, name: 'Charlie', age: 35}

*/
SELECT id, name, age
FROM db.schema.users
WHERE age >= 18;
