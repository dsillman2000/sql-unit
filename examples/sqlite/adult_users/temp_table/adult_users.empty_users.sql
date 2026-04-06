create or replace temp table testdb_testschema_users__12ef as
select
    null as id,
    null as name,
    null as age
where false;

select
    id,
    name,
    age
from temp.testdb_testschema_users__12ef
where age >= 18
