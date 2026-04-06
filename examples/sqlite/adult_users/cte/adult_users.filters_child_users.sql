with testdb_testschema_users as (
    select
        1 as id,
        'Alice' as name,
        30 as age
    union all
    select
        2 as id,
        'Bob' as name,
        15 as age
    union all
    select
        3 as id,
        'Charlie' as name,
        25 as age
)
select
    id,
    name,
    age
from testdb_testschema_users
where age >= 18
