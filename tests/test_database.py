"""Unit tests for database layer."""

import pytest

from sql_unit.database import (
    ConnectionConfig,
    ConnectionManager,
)
from sql_unit.exceptions import ExecutionError


class TestConnectionConfig:
    """Tests for database connection configuration."""
    
    def test_sqlite_memory(self):
        """Test creating in-memory SQLite configuration."""
        config = ConnectionConfig.sqlite(":memory:")
        assert config is not None
        assert config.database_type == "sqlite"
        assert config.connection_string == "sqlite:///:memory:"
        assert config.pooling == False
    
    def test_sqlite_file(self, tmp_path):
        """Test creating file-based SQLite configuration."""
        db_file = tmp_path / "test.db"
        config = ConnectionConfig.sqlite(str(db_file))
        assert config is not None
        assert config.database_type == "sqlite"
        assert config.connection_string == f"sqlite:///{db_file}"
        assert config.pooling == True
    
    def test_postgresql_config(self):
        """Test creating PostgreSQL configuration."""
        config = ConnectionConfig.postgresql(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="secret"
        )
        assert config.database_type == "postgresql"
        assert "postgresql://" in config.connection_string
        assert config.pooling == True
    
    def test_mysql_config(self):
        """Test creating MySQL configuration."""
        config = ConnectionConfig.mysql(
            host="localhost",
            port=3306,
            database="testdb",
            user="admin",
            password="secret"
        )
        assert config.database_type == "mysql"
        assert "mysql+pymysql://" in config.connection_string
        assert config.pooling == True
    
    def test_duckdb_memory(self):
        """Test creating in-memory DuckDB configuration."""
        config = ConnectionConfig.duckdb(":memory:")
        assert config.database_type == "duckdb"
        assert config.connection_string == "duckdb:///:memory:"
        assert config.pooling == False
    
    def test_duckdb_file(self, tmp_path):
        """Test creating file-based DuckDB configuration."""
        db_file = tmp_path / "test.duckdb"
        config = ConnectionConfig.duckdb(str(db_file))
        assert config.database_type == "duckdb"
        assert config.connection_string == f"duckdb:///{db_file}"
    
    def test_from_yaml_sqlite(self):
        """Test YAML parsing for SQLite."""
        config_dict = {
            "type": "sqlite",
            "path": ":memory:"
        }
        config = ConnectionConfig.from_yaml(config_dict)
        assert config.database_type == "sqlite"
        assert config.connection_string == "sqlite:///:memory:"
    
    def test_from_yaml_postgresql(self):
        """Test YAML parsing for PostgreSQL."""
        config_dict = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "admin",
            "password": "secret"
        }
        config = ConnectionConfig.from_yaml(config_dict)
        assert config.database_type == "postgresql"
        assert config.pooling == True
    
    def test_from_yaml_invalid_type(self):
        """Test error on invalid database type."""
        config_dict = {"type": "unsupported_db"}
        with pytest.raises(ValueError):
            ConnectionConfig.from_yaml(config_dict)
    
    def test_url_normalization(self):
        """Test URL normalization."""
        url = ConnectionConfig._url("postgresql://user:password@localhost/db")
        assert "postgresql://" in url
        assert "localhost" in url


class TestConnectionManager:
    """Tests for connection manager."""
    
    def test_execute_simple_query(self):
        """Test executing a simple query."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        result = manager.execute_query("SELECT 1 as value;")
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["value"] == 1
    
    def test_execute_query_multiple_rows(self):
        """Test executing query with multiple rows."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        # All operations on same connection manager instance
        manager.execute_setup("CREATE TABLE test (id INTEGER, name TEXT);")
        manager.execute_setup("INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob');")
        
        result = manager.execute_query("SELECT * FROM test ORDER BY id;")
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
    
    def test_execute_setup_query(self):
        """Test executing setup query (CREATE TABLE)."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        # All operations on same connection manager instance
        manager.execute_setup("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        manager.execute_setup("INSERT INTO users (id, name) VALUES (1, 'John');")
        
        result = manager.execute_query("SELECT COUNT(*) as cnt FROM users;")
        assert result[0]["cnt"] == 1
    
    def test_error_on_invalid_query(self):
        """Test error handling for invalid SQL."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        with pytest.raises(ExecutionError):
            manager.execute_query("SELECT * FROM nonexistent_table;")
    
    def test_query_with_special_characters(self):
        """Test query with special characters."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        # All operations on same connection manager instance
        manager.execute_setup("CREATE TABLE test (name TEXT);")
        manager.execute_setup("INSERT INTO test VALUES ('John''s Store');")
        
        result = manager.execute_query("SELECT * FROM test;")
        assert "John's" in result[0]["name"]


class TestConnectionConfigFactory:
    """Tests for ConnectionConfig factory methods."""
    
    def test_create_engine_from_sqlite_config(self):
        """Test engine creation from SQLite config."""
        config = ConnectionConfig.sqlite(":memory:")
        engine = config.create_engine()
        assert engine is not None
        assert "sqlite" in str(engine.url)
    
    def test_create_manager_from_sqlite_config(self):
        """Test manager creation from SQLite config."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        assert isinstance(manager, ConnectionManager)
        assert manager.database_type == "sqlite"
    
    def test_pooling_enabled(self, tmp_path):
        """Test connection pooling is enabled for file-based DB."""
        db_file = tmp_path / "test.db"
        config = ConnectionConfig.sqlite(str(db_file))
        assert config.pooling is True
    
    def test_pooling_disabled_for_memory(self):
        """Test connection pooling is disabled for in-memory DB."""
        config = ConnectionConfig.sqlite(":memory:")
        assert config.pooling is False
    
    def test_config_with_options(self):
        """Test configuration with additional options."""
        config = ConnectionConfig.sqlite(
            ":memory:",
            echo=True,
            pool_size=20
        )
        assert config.kwargs.get("echo") == True
        assert config.pool_size == 20
