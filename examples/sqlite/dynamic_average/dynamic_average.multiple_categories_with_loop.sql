with testdb_testschema_transactions as (
    select
        1 as id,
        '2024-01-10' as transaction_date,
        100.00 as transaction_price,
        'electronics' as category
    union all
    select
        2 as id,
        '2024-01-15' as transaction_date,
        200.00 as transaction_price,
        'books' as category
    union all
    select
        3 as id,
        '2024-01-20' as transaction_date,
        300.00 as transaction_price,
        'clothing' as category
    union all
    select
        4 as id,
        '2024-01-25' as transaction_date,
        400.00 as transaction_price,
        'electronics' as category
)
select avg(transaction_price) as avg_price
from testdb_testschema_transactions
where julianday(transaction_date) between
    julianday('2024-01-01') and julianday('2024-01-31')
    and category in ('electronics', 'books')