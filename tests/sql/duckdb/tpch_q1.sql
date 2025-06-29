/*
    # sql-unit
    sql-unit.mock "delta":
      type: int
      default: 60

    sql-unit.mock "lineitem":
      type: table
      columns:
        l_returnflag: string
        l_linestatus: string
        l_quantity: int
        l_extendedprice: float
        l_discount: float
        l_tax: float
        l_shipdate: date

*/
-- noqa: disable=PRS
select
    l_returnflag,
    l_linestatus,
    sum(l_quantity) as sum_qty,
    sum(l_extendedprice) as sum_base_price,
    sum(l_extendedprice * (1 - l_discount)) as sum_disc_price,
    sum(l_extendedprice * (1 - l_discount) * (1 + l_tax)) as sum_charge,
    avg(l_quantity) as avg_qty,
    avg(l_extendedprice) as avg_price,
    avg(l_discount) as avg_disc,
    count(*) as count_order
from
    {{ lineitem }}
where
    l_shipdate <= date '1998-12-01' - interval '{{ delta }}' day
group by
    l_returnflag,
    l_linestatus
order by
    l_returnflag,
    l_linestatus;
-- noqa: disable=LT*
/*

    # sql-unit

    # Empty test case.
    # ===================

    sql-unit.test "empty_lineitem":
      expect: |-
        | l_linestatus | sum_qty | sum_base_price | sum_disc_price | sum_charge | avg_qty | avg_price | avg_disc | count_order |
        | ------------ | ------- | -------------- | -------------- | ---------- | ------- | --------- | -------- | ----------- |

    # Nonempty test case.
    # ===================
    # Note that the first two "y" rows are not included in the result since they are less than 30 days old.

    sql-unit.test "nonempty_lineitem":
      given "delta": 30
      given "lineitem": |-
        | l_returnflag | l_linestatus | l_quantity | l_extendedprice | l_discount | l_tax | l_shipdate   |
        | ------------ | ------------ | ---------- | --------------- | ---------- | ----- | ------------ |
        | "y"          | "0"          | 10         | 100.0           | 0.05       | 0.00  | "1998-12-01" |
        | "y"          | "0"          | 20         | 200.0           | 0.10       | 0.00  | "1998-11-15" |
        | "n"          | "1"          | 30         | 250.0           | 0.15       | 0.00  | "1998-10-10" |
        | "y"          | "0"          | 40         | 300.0           | 0.10       | 0.00  | "1998-09-05" |
      expect: |-
        | l_returnflag | l_linestatus | sum_qty | sum_base_price | sum_disc_price | sum_charge | avg_qty | avg_price | avg_disc | count_order |
        | ------------ | ------------ | ------- | -------------- | -------------- | ---------- | ------- | --------- | -------- | ----------- |
        | "n"          | "1"          | 30      | 250.0          | 212.5          | 212.5      | 30      | 250.0     | 0.15     | 1           |
        | "y"          | "0"          | 40      | 300.0          | 270.0          | 270.0      | 40      | 300.0     | 0.01     | 1           |

*/
