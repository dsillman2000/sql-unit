#!/usr/bin/env python
"""
Integration Testing Worksheet for SQL Unit Framework
======================================================

This worksheet allows manual testing of the sql-unit framework against custom test cases.
Modify the TEST_CASES and SETUP sections below to test different scenarios.

Usage:
    python david/main.py

The script will:
1. Create an in-memory SQLite database
2. Execute setup SQL
3. Run tests against your custom test cases
4. Display results
"""

from sql_unit.database import ConnectionConfig
from sql_unit.parser import SqlBlockCommentParser, TestDiscoveryParser
from sql_unit.runner import TestRunner, BatchTestRunner
from sql_unit.models import TestDefinition
from sql_unit.statement import StatementValidator


# ============================================================================
# SECTION 1: SETUP SQL
# ============================================================================
# Define your database schema and initial data here
# NOTE: Each statement must be separate - SQLAlchemy executes one at a time

SETUP_STATEMENTS = [
    # Create orders table
    """
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        amount DECIMAL(10, 2),
        status TEXT
    )
    """,
    
    # Insert orders data
    "INSERT INTO orders VALUES (1, 100, 99.99, 'completed')",
    "INSERT INTO orders VALUES (2, 101, 149.50, 'pending')",
    "INSERT INTO orders VALUES (3, 100, 75.00, 'completed')",
    "INSERT INTO orders VALUES (4, 102, 200.00, 'cancelled')",
    
    # Create customers table
    """
    CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT
    )
    """,
    
    # Insert customers data
    "INSERT INTO customers VALUES (100, 'Alice', 'alice@example.com')",
    "INSERT INTO customers VALUES (101, 'Bob', 'bob@example.com')",
    "INSERT INTO customers VALUES (102, 'Charlie', 'charlie@example.com')",
]


# ============================================================================
# SECTION 2: TEST CASES
# ============================================================================
# Define your test cases as TestDefinition objects
# Modify these to experiment with different test scenarios

TEST_CASES = [
    # Test 1: Simple SELECT with basic expectation
    TestDefinition(
        name="test_select_all_orders",
        given={},
        expect={"rows_count": 4},
        description="Should return all 4 orders"
    ),
    
    # Test 2: SELECT with filtering
    TestDefinition(
        name="test_completed_orders",
        given={},
        expect={"rows_count": 2},
        description="Should return only completed orders"
    ),
    
    # Test 3: SELECT with Jinja2 templating
    TestDefinition(
        name="test_customer_total",
        given={
            "jinja_context": {
                "customer_id": 100
            }
        },
        expect={"rows_count": 1},
        description="Should return total for specific customer using Jinja2"
    ),
    
    # Test 4: Simple aggregation
    TestDefinition(
        name="test_order_count",
        given={},
        expect={"rows_count": 1},
        description="Should return single row with count"
    ),
    
    # Test 5: JOIN query
    TestDefinition(
        name="test_customer_orders",
        given={},
        expect={"rows_count": 3},
        description="Should return orders with customer names"
    ),
]


# ============================================================================
# SECTION 3: SQL STATEMENTS TO TEST
# ============================================================================
# Each statement corresponds to a test case (must be in same order)
# These are the actual SQL queries being tested

SQL_STATEMENTS = [
    # Test 1: Simple SELECT
    """
    SELECT * FROM orders
    """,
    
    # Test 2: SELECT with WHERE clause
    """
    SELECT * FROM orders WHERE status = 'completed'
    """,
    
    # Test 3: SELECT with Jinja2 template variable
    """
    SELECT * FROM orders WHERE customer_id = {{ customer_id }}
    """,
    
    # Test 4: COUNT aggregation
    """
    SELECT COUNT(*) as total FROM orders
    """,
    
    # Test 5: JOIN query
    """
    SELECT o.id, c.name, o.amount 
    FROM orders o 
    JOIN customers c ON o.customer_id = c.id
    WHERE o.status = 'completed'
    """,
]


# ============================================================================
# SECTION 4: EXECUTION AND REPORTING
# ============================================================================

def main():
    """Execute integration tests and display results."""
    print("=" * 70)
    print("SQL Unit Framework - Integration Testing Worksheet")
    print("=" * 70)
    print()
    
    # Step 1: Initialize database
    print("Step 1: Initializing database...")
    config = ConnectionConfig.sqlite(":memory:")
    manager = config.create_connection_manager()
    print("✓ Database created")
    
    # Step 2: Setup schema and data
    print("\nStep 2: Setting up schema and data...")
    try:
        for i, stmt in enumerate(SETUP_STATEMENTS, 1):
            manager.execute_setup(stmt)
        print(f"✓ Schema and data loaded ({len(SETUP_STATEMENTS)} statements)")
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        return
    
    # Step 3: Validate setup
    print("\nStep 3: Validating setup...")
    try:
        result = manager.execute_query("SELECT COUNT(*) as cnt FROM orders")
        order_count = result[0]["cnt"]
        print(f"✓ Found {order_count} orders in database")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return
    
    # Step 4: Run tests
    print("\nStep 4: Running tests...")
    print("-" * 70)
    
    runner = TestRunner(manager)
    batch_runner = BatchTestRunner(runner)
    
    # Verify test counts match
    if len(TEST_CASES) != len(SQL_STATEMENTS):
        print(f"✗ ERROR: Test count ({len(TEST_CASES)}) != Statement count ({len(SQL_STATEMENTS)})")
        return
    
    # Run all tests
    results = batch_runner.run_tests(TEST_CASES, SQL_STATEMENTS)
    
    # Step 5: Display results
    print("\nStep 5: Test Results")
    print("-" * 70)
    
    for i, result in enumerate(results, 1):
        test_name = TEST_CASES[i-1].name
        status = "PASS ✓" if result.passed else "FAIL ✗"
        duration = f"{result.duration*1000:.2f}ms"
        
        print(f"\n{i}. {test_name}")
        print(f"   Status: {status}")
        print(f"   Duration: {duration}")
        
        if result.error:
            print(f"   Error: {result.error.error_type}")
            print(f"   Message: {result.error.message}")
            if result.error.executed_sql:
                print(f"   SQL: {result.error.executed_sql[:100]}...")
    
    # Step 6: Summary
    print("\n" + "=" * 70)
    summary = batch_runner.get_summary(results)
    print("Summary:")
    print(f"  Total Tests: {summary['total']}")
    print(f"  Passed: {summary['passed']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Pass Rate: {summary['pass_rate']*100:.1f}%")
    print(f"  Total Duration: {summary['total_duration']*1000:.2f}ms")
    print("=" * 70)


# ============================================================================
# SECTION 5: MANUAL QUERY TESTING
# ============================================================================
# Uncomment the section below to test individual queries interactively

def manual_query_testing():
    """Interactively test individual SQL queries."""
    print("\n" + "=" * 70)
    print("Manual Query Testing Mode")
    print("=" * 70)
    
    config = ConnectionConfig.sqlite(":memory:")
    manager = config.create_connection_manager()
    for stmt in SETUP_STATEMENTS:
        manager.execute_setup(stmt)
    
    # Test individual queries
    test_queries = [
        ("All orders", "SELECT * FROM orders"),
        ("Completed orders", "SELECT * FROM orders WHERE status = 'completed'"),
        ("Customer summary", "SELECT customer_id, COUNT(*) as count, SUM(amount) as total FROM orders GROUP BY customer_id"),
        ("Join example", "SELECT o.id, c.name, o.amount FROM orders o JOIN customers c ON o.customer_id = c.id"),
    ]
    
    for name, query in test_queries:
        print(f"\n{name}:")
        print(f"  Query: {query}")
        try:
            results = manager.execute_query(query)
            print(f"  Results: {len(results)} rows")
            for row in results:
                print(f"    {row}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    main()
    
    # Uncomment the line below to test individual queries
    # manual_query_testing()
