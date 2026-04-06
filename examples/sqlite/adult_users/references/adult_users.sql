/* #! sql-unit

    !reference-all "tests.yaml"

*/
select
    id,
    name,
    age
from testdb.testschema.users
where age >= 18
