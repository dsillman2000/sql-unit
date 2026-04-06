/* #! sql-unit

    # Multi-doc syntax

    <test 1>
    ---
    <test 2>
    ---
    <test 3>

*/
/* #! sql-unit

    # Sequence syntax

    - <test 1>
    - <test 2>
    - <test 3>

*/
select
    id,
    name,
    age
from db.schema.users
where age >= 18;

select avg(transaction_price) as avg_price
from testdb.testschema.transactions
where julianday(transaction_date) between
    julianday('{{ start_date }}') and julianday('{{ end_date }}');
