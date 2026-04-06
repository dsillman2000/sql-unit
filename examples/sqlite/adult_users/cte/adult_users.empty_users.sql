with testdb_testschema_users as (
    select
        null as id,
        null as name,
        null as age
    where false
)
select
    id,
    name,
    age
from testdb_testschema_users
where age >= 18
