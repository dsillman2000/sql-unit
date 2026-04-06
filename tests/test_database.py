"""Unit tests for database layer."""

import pytest

from sql_unit.database import (
    ConnectionFactory,
    ConnectionManager,
    TransactionManager,
)
from sql_unit.exceptions import ExecutionError


class TestConnectionFactory:
    """Tests for database connection factory."""
    
    def test_create_sqlite_memory(self):
        """Test creating in-memory SQLite connection."""
        conn = ConnectionFactory.create_sqlite_memory()
        assert conn is not None
        assert isinstance(conn, ConnectionManager)
        assert conn.database_type == "sqlite"
    
    def test_create_sqlite_file(self, tmp_path):
        """Test creating file-based SQLite connection."""
        db_file = tmp_path / "test.db"
        conn = ConnectionFactory.create_sqlite_file(str(db_file))
        assert conn is not None
        assert isinstance(conn, ConnectionManager)


class TestConnectionManager:
    """Tests for connection manager."""
    
    def test_execute_simple_query(self):
        """Test executing a simple query."""
        conn = ConnectionFactory.create_sqlite_memory()
        result = conn.execute_query("SELECT 1 as value;")
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["value"] == 1
    
    def test_execute_query_multiple_rows(self):
        """Test executing query with multiple rows."""
        conn = ConnectionFactory.create_sqlite_memory()
        # All operations on same connection manager instance
        conn.execute_setup("CREATE TABLE test (id INTEGER, name TEXT);")
        conn.execute_setup("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob');")
        
        result = conn.execute_query("SELECT * FROM test ORDER BY id;")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
    
    def test_execute_setup_query(self):
        """Test executing setup query (CREATE TABLE)."""
        conn = ConnectionFactory.create_sqlite_memory()
        # All operations on same connection manager instance
        conn.execute_setup("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        conn.execute_setup("INSERT INTO users (id, name) VALUES (1, 'John');")
        
        result = conn.execute_query("SELECT COUNT(*) as cnt FROM users;")
        assert result[0]["cnt"] == 1
    
    def test_error_on_invalid_query(self):
        """Test error handling for invalid SQL."""
        conn = ConnectionFactory.create_sqlite_memory()
        with pytest.raises(ExecutionError):
            conn.execute_query("SELECT * FROM nonexistent_table;")
    
    def test_query_with_special_characters(self):
        """Test query with special characters."""
        conn = ConnectionFactory.create_sqlite_memory()
        # All operations on same connection manager instance
        conn.execute_setup("CREATE TABLE test (name TEXT);")
        conn.execute_setup("INSERT INTO test VALUES ('John''s Store');")
        
        result = conn.execute_query("SELECT * FROM test;")
        assert "John's" in result[0]["name"]


class TestTransactionManager:
    """Tests for transaction management."""
    
    def test_begin_commit_transaction(self):
        """Test beginning and committing a transaction."""
        engine = ConnectionFactory.create_sqlite_memory().engine
        conn = TransactionManager(engine)
        
        conn.begin()
        rows = conn.execute_query("SELECT 1 as value;")
        assert len(rows) > 0
        conn.commit()
    
    def test_rollback_transaction(self):
        """Test rolling back a transaction."""
        # Create single manager for both setup and transactions
        manager = ConnectionFactory.create_sqlite_memory()
        manager.execute_setup("CREATE TABLE test (id INTEGER, val TEXT);")
        manager.execute_setup("INSERT INTO test VALUES (1, 'original');")
        
        # Use same engine for transaction manager
        txn = TransactionManager(manager.engine)
        txn.begin()
        try:
            txn.execute_query("INSERT INTO test VALUES (2, 'temporary');")
            txn.rollback()
        except:
            txn.rollback()
        
        # Verify the temporary insert was rolled back
        result = manager.execute_query("SELECT COUNT(*) as cnt FROM test;")
        assert result[0]["cnt"] == 1
    
    def test_context_manager_success(self):
        """Test using transaction as context manager (success)."""
        # Create single manager for both setup and transactions
        manager = ConnectionFactory.create_sqlite_memory()
        manager.execute_setup("CREATE TABLE test (id INTEGER, val TEXT);")
        
        with TransactionManager(manager.engine) as txn:
            txn.execute_query("INSERT INTO test VALUES (1, 'test');")
        
        # Verify insert was committed
        result = manager.execute_query("SELECT COUNT(*) as cnt FROM test;")
        assert result[0]["cnt"] == 1
    
    def test_context_manager_rollback_on_error(self):
        """Test context manager rolls back on error."""
        # Create single manager for both setup and transactions
        manager = ConnectionFactory.create_sqlite_memory()
        manager.execute_setup("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT);")
        
        try:
            with TransactionManager(manager.engine) as txn:
                txn.execute_query("INSERT INTO test VALUES (1, 'test');")
                # Simulate error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify insert was rolled back
        result = manager.execute_query("SELECT COUNT(*) as cnt FROM test;")
        assert result[0]["cnt"] == 0


class TestConnectionPooling:
    """Tests for connection pooling behavior."""
    
    def test_pooling_enabled(self, tmp_path):
        """Test connection pooling is enabled for file-based DB."""
        db_file = tmp_path / "test.db"
        conn = ConnectionFactory.create_sqlite_file(str(db_file))
        assert conn.pooling is True
    
    def test_pooling_disabled_for_memory(self):
        """Test connection pooling is disabled for in-memory DB."""
        conn = ConnectionFactory.create_sqlite_memory()
        assert conn.pooling is False
