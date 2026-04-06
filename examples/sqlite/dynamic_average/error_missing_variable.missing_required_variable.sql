/* Expected to fail during compilation/rendering

Error: Jinja variable 'start_date' is undefined
Hint: Use the |default() filter or define in jinja_context block

Expected SQL (will not render due to error):
with testdb_testschema_transactions as (
    select
        1 as id,
        '2024-01-15' as transaction_date,
        100.00 as transaction_price
)
select avg(transaction_price) as avg_price
from testdb_testschema_transactions
where julianday(transaction_date) between
    julianday('{{ start_date }}') and julianday('2024-01-31')
