with testdb_testschema_transactions as (
    select
        1 as id,
        '2024-01-10' as transaction_date,
        150.00 as transaction_price,
        null as category
    union all
    select
        2 as id,
        '2024-01-25' as transaction_date,
        250.00 as transaction_price,
        null as category
    union all
    select
        3 as id,
        '2024-02-01' as transaction_date,
        350.00 as transaction_price,
        null as category
)
select avg(transaction_price) as avg_price
from testdb_testschema_transactions
where julianday(transaction_date) between
    julianday('2024-01-01') and julianday('2024-01-31')
