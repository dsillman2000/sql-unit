/* #! sql-unit

    name: missing_required_variable
    description: Should fail with clear error when required variable is missing
    given:
      - jinja_context:
          # start_date is missing!
          end_date: "2024-01-31"
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00}
    expect:
      - error_contains: "Jinja variable 'start_date' is undefined"

    ---

    name: missing_variable_in_loop
    description: Should fail when variable used in loop is missing
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
          # categories is missing but used in loop
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00, category: "electronics"}
    expect:
      - error_contains: "Jinja variable 'categories' is undefined"

*/
select avg(transaction_price) as avg_price
from testdb.testschema.transactions
where julianday(transaction_date) between
    julianday('{{ start_date }}') and julianday('{{ end_date }}')
{% if categories %}
    and category in (
        {% for cat in categories %}
            '{{ cat }}'{% if not loop.last %},{% endif %}
        {% endfor %}
    )
{% endif %}