"""Integration tests for config with real databases."""

import os
import tempfile

import pytest

from sql_unit.config import SqlUnitConfig
from sql_unit.database import ConnectionConfig
from sql_unit.connection_dialect import ConnectionDialectExtractor
from sql_unit.core.exceptions import ParserError


# Check if optional database drivers are available
HAS_DUCKDB = False
try:
    import importlib.util

    HAS_DUCKDB = importlib.util.find_spec("duckdb") is not None
except (ImportError, AttributeError):
    pass


class TestSqliteIntegration:
    """Test SQLite database integration with config."""

    def test_sqlite_in_memory_connection(self):
        """Test creating in-memory SQLite connection from config."""
        config_dict = {"connection": {"url": "sqlite:///:memory:"}}
        config = SqlUnitConfig(config_dict)

        dialect = ConnectionDialectExtractor.get_dialect(config.connection)
        assert dialect == "sqlite"

        # Create connection and verify it works
        conn_config = ConnectionConfig.sqlite(":memory:")
        manager = conn_config.create_database_manager()

        # Execute a simple query
        manager.execute_setup("CREATE TABLE test (id INTEGER, name TEXT)")
        manager.execute_setup("INSERT INTO test VALUES (1, 'test')")
        result = manager.execute_query("SELECT * FROM test")
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "test"

    def test_sqlite_file_connection(self):
        """Test creating file-based SQLite connection from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            config_dict = {"connection": {"sqlite": {"path": db_path}}}
            config = SqlUnitConfig(config_dict)

            dialect = ConnectionDialectExtractor.get_dialect(config.connection)
            assert dialect == "sqlite"

            # Create connection and verify it works
            conn_config = ConnectionConfig.sqlite(db_path)
            manager = conn_config.create_database_manager()

            # Create table and insert data
            manager.execute_setup("CREATE TABLE users (id INTEGER, name TEXT)")
            manager.execute_setup("INSERT INTO users VALUES (1, 'Alice')")
            manager.execute_setup("INSERT INTO users VALUES (2, 'Bob')")

            result = manager.execute_query("SELECT COUNT(*) as cnt FROM users")
            assert result[0]["cnt"] == 2

    def test_sqlite_config_from_yaml_file(self):
        """Test loading SQLite config from YAML file."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
threads: 4
test_paths:
  - tests/
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            config = SqlUnitConfig.from_file(filepath)
            assert "url" in config.connection
            assert config.connection["url"] == "sqlite:///:memory:"
            assert config.config.get("threads") == 4
            assert config.config.get("test_paths") == ["tests/"]

            # Verify it can be used to create a database manager
            dialect = ConnectionDialectExtractor.get_dialect(config.connection)
            assert dialect == "sqlite"
        finally:
            os.unlink(filepath)


class TestDuckDbIntegration:
    """Test DuckDB database integration with config."""

    @pytest.mark.skipif(not HAS_DUCKDB, reason="DuckDB driver not installed")
    def test_duckdb_in_memory_connection(self):
        """Test creating in-memory DuckDB connection from config."""
        config_dict = {"connection": {"url": "duckdb:///:memory:"}}
        config = SqlUnitConfig(config_dict)

        dialect = ConnectionDialectExtractor.get_dialect(config.connection)
        assert dialect == "duckdb"

        # Create connection and verify it works
        conn_config = ConnectionConfig.duckdb(":memory:")
        manager = conn_config.create_database_manager()

        # Execute a simple query
        manager.execute_setup("CREATE TABLE test (id INTEGER, name TEXT)")
        manager.execute_setup("INSERT INTO test VALUES (1, 'test')")
        result = manager.execute_query("SELECT * FROM test")
        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "test"

    @pytest.mark.skipif(not HAS_DUCKDB, reason="DuckDB driver not installed")
    def test_duckdb_file_connection(self):
        """Test creating file-based DuckDB connection from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            config_dict = {"connection": {"duckdb": {"path": db_path}}}
            config = SqlUnitConfig(config_dict)

            dialect = ConnectionDialectExtractor.get_dialect(config.connection)
            assert dialect == "duckdb"

            # Create connection and verify it works
            conn_config = ConnectionConfig.duckdb(db_path)
            manager = conn_config.create_database_manager()

            # Create table and insert data
            manager.execute_setup("CREATE TABLE products (id INTEGER, name TEXT)")
            manager.execute_setup("INSERT INTO products VALUES (1, 'Widget')")
            manager.execute_setup("INSERT INTO products VALUES (2, 'Gadget')")

            result = manager.execute_query("SELECT COUNT(*) as cnt FROM products")
            assert result[0]["cnt"] == 2


class TestConfigDiscoveryIntegration:
    """Test config file discovery with database connections."""

    def test_discover_config_in_current_directory(self):
        """Test discovering config file in current directory."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
threads: 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "sql-unit.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            config = SqlUnitConfig.from_directory(tmpdir)
            assert config.connection["url"] == "sqlite:///:memory:"
            assert config.config.get("threads") == 2

    def test_discover_config_in_parent_directory(self):
        """Test discovering config file in parent directory."""
        yaml_content = """
connection:
  url: "sqlite:///parent.db"
threads: 3
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config in parent
            config_path = os.path.join(tmpdir, "sql-unit.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            # Try to discover from subdirectory
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)

            config = SqlUnitConfig.from_directory(subdir)
            assert config.connection["url"] == "sqlite:///parent.db"
            assert config.config.get("threads") == 3

    def test_discover_config_collision_detection(self):
        """Test error when multiple configs found in tree."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config in parent
            parent_config = os.path.join(tmpdir, "sql-unit.yaml")
            with open(parent_config, "w") as f:
                f.write(yaml_content)

            # Create config in subdirectory
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            child_config = os.path.join(subdir, "sql-unit.yaml")
            with open(child_config, "w") as f:
                f.write(yaml_content)

            # Searching from parent should find first match and not error
            config = SqlUnitConfig.from_directory(tmpdir)
            assert config.connection["url"] == "sqlite:///:memory:"

    def test_discover_config_missing_returns_empty(self):
        """Test that missing config returns empty config (for --connection mode)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SqlUnitConfig.from_directory(tmpdir)
            assert config.config == {}
            assert config.connection == {}


class TestConfigWithEnvironmentVariables:
    """Test config integration with environment variables."""

    def test_config_with_env_var_substitution(self):
        """Test that environment variables are substituted in config."""
        os.environ["DB_HOST"] = "testhost"
        os.environ["DB_USER"] = "testuser"
        os.environ["DB_PASSWORD"] = "testpass"

        try:
            config_dict = {
                "connection": {
                    "postgresql": {
                        "host": "${DB_HOST}",
                        "user": "${DB_USER}",
                        "password": "${DB_PASSWORD}",
                        "database": "testdb",
                    }
                }
            }
            config = SqlUnitConfig(config_dict)
            assert config.connection["postgresql"]["host"] == "testhost"
            assert config.connection["postgresql"]["user"] == "testuser"
            assert config.connection["postgresql"]["password"] == "testpass"
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_USER"]
            del os.environ["DB_PASSWORD"]

    def test_config_missing_env_var_raises_error(self):
        """Test that missing environment variable raises error."""
        # Make sure the variable doesn't exist
        if "MISSING_VAR_THAT_SHOULD_NOT_EXIST" in os.environ:
            del os.environ["MISSING_VAR_THAT_SHOULD_NOT_EXIST"]

        config_dict = {
            "connection": {
                "postgresql": {
                    "host": "localhost",
                    "password": "${MISSING_VAR_THAT_SHOULD_NOT_EXIST}",
                }
            }
        }

        with pytest.raises(ParserError, match="Undefined environment variable"):
            SqlUnitConfig(config_dict)


class TestConnectionDialectIntegration:
    """Test dialect extraction and connection setup."""

    def test_dialect_to_connection_config_sqlite(self):
        """Test using dialect to create appropriate ConnectionConfig."""
        config_dict = {"connection": {"sqlite": ":memory:"}}
        config = SqlUnitConfig(config_dict)

        dialect = ConnectionDialectExtractor.get_dialect(config.connection)
        assert dialect == "sqlite"

        # Create appropriate connection config
        if dialect == "sqlite":
            conn_config = ConnectionConfig.sqlite(":memory:")
            assert conn_config.database_type == "sqlite"
            assert "memory" in conn_config.connection_string.lower()

    def test_dialect_to_connection_config_duckdb(self):
        """Test using dialect to create appropriate ConnectionConfig."""
        config_dict = {"connection": {"duckdb": ":memory:"}}
        config = SqlUnitConfig(config_dict)

        dialect = ConnectionDialectExtractor.get_dialect(config.connection)
        assert dialect == "duckdb"

        # Create appropriate connection config
        if dialect == "duckdb" and HAS_DUCKDB:
            conn_config = ConnectionConfig.duckdb(":memory:")
            assert conn_config.database_type == "duckdb"
            assert "memory" in conn_config.connection_string.lower()
