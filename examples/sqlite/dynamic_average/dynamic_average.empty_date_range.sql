with testdb_testschema_transactions as (
    select
        1 as id,
        '2024-01-15' as transaction_date,
        100.00 as transaction_price,
        null as category
    union all
    select
        2 as id,
        '2024-01-20' as transaction_date,
        200.00 as transaction_price,
        null as category
)
select avg(transaction_price) as avg_price
from testdb_testschema_transactions
where julianday(transaction_date) between
    julianday('2024-02-01') and julianday('2024-02-28')