/* #! sql-unit

    name: basic_date_range
    description: Calculate average with explicit date range
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00}
            - {id: 2, transaction_date: "2024-01-20", transaction_price: 200.00}
            - {id: 3, transaction_date: "2023-12-25", transaction_price: 50.00}  # Outside range
    expect:
      - rows_equal:
          rows:
            - {avg_price: 150.00}

    ---

    name: with_default_filter
    description: Using default filter for optional end_date
    given:
      - jinja_context:
          start_date: "2024-01-01"
          # end_date omitted, will use default
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-10", transaction_price: 150.00}
            - {id: 2, transaction_date: "2024-01-25", transaction_price: 250.00}
            - {id: 3, transaction_date: "2024-02-01", transaction_price: 350.00}  # Outside default range
    expect:
      - rows_equal:
          rows:
            - {avg_price: 200.00}

    ---

    name: conditional_category_filter
    description: Using Jinja conditional to optionally filter by category
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
          category: "electronics"
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00, category: "electronics"}
            - {id: 2, transaction_date: "2024-01-20", transaction_price: 200.00, category: "electronics"}
            - {id: 3, transaction_date: "2024-01-25", transaction_price: 300.00, category: "clothing"}  # Different category
    expect:
      - rows_equal:
          rows:
            - {avg_price: 150.00}

    ---

    name: no_category_filter
    description: Same query without category filter (conditional skips it)
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
          # category omitted, conditional will skip the filter
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00, category: "electronics"}
            - {id: 2, transaction_date: "2024-01-20", transaction_price: 200.00, category: "electronics"}
            - {id: 3, transaction_date: "2024-01-25", transaction_price: 300.00, category: "clothing"}
    expect:
      - rows_equal:
          rows:
            - {avg_price: 200.00}

    ---

    name: multiple_categories_with_loop
    description: Using Jinja loop to filter by multiple categories
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
          categories: ["electronics", "books"]
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-10", transaction_price: 100.00, category: "electronics"}
            - {id: 2, transaction_date: "2024-01-15", transaction_price: 200.00, category: "books"}
            - {id: 3, transaction_date: "2024-01-20", transaction_price: 300.00, category: "clothing"}  # Not in categories
            - {id: 4, transaction_date: "2024-01-25", transaction_price: 400.00, category: "electronics"}
    expect:
      - rows_equal:
          rows:
            - {avg_price: 233.33}  # (100 + 200 + 400) / 3 ≈ 233.33

    ---

    name: empty_date_range
    description: No transactions in the specified date range
    given:
      - jinja_context:
          start_date: "2024-02-01"
          end_date: "2024-02-28"
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00}
            - {id: 2, transaction_date: "2024-01-20", transaction_price: 200.00}
    expect:
      - row_count:
          eq: 0

    ---

    name: single_transaction
    description: Average of single transaction equals its price
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 150.50}
    expect:
      - rows_equal:
          rows:
            - {avg_price: 150.50}

    ---

    name: using_jinja_filters
    description: Demonstrating Jinja built-in filters
    given:
      - jinja_context:
          start_date: "2024-01-01"
          end_date: "2024-01-31"
          category_prefix: "ELEC"  # Uppercase prefix
      - cte:
          targets: ["testdb.testschema.transactions"]
          rows:
            - {id: 1, transaction_date: "2024-01-15", transaction_price: 100.00, category: "electronics"}
            - {id: 2, transaction_date: "2024-01-20", transaction_price: 200.00, category: "Electronics"}  # Different case
            - {id: 3, transaction_date: "2024-01-25", transaction_price: 300.00, category: "books"}
    expect:
      - rows_equal:
          rows:
            - {avg_price: 150.00}  # Only electronics (case-insensitive match)

*/
select avg(transaction_price) as avg_price
from testdb.testschema.transactions
where julianday(transaction_date) between
    julianday('{{ start_date }}') and julianday('{{ end_date|default("2024-01-31") }}')
{% if category %}
    and lower(category) = lower('{{ category }}')
{% endif %}
{% if categories %}
    and category in (
        {% for cat in categories %}
            '{{ cat }}'{% if not loop.last %},{% endif %}
        {% endfor %}
    )
{% endif %}
{% if category_prefix %}
    and lower(category) like lower('{{ category_prefix|lower }}%')
{% endif %}