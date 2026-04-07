"""Tests for SqlUnitConfig."""

import os
import tempfile

import pytest

from sql_unit.config import SqlUnitConfig
from sql_unit.connection_dialect import ConnectionDialectExtractor
from sql_unit.core.exceptions import ParserError


class TestSqlUnitConfig:
    """Test SqlUnitConfig."""

    def test_default_float_precision(self):
        """Test default float precision."""
        config = SqlUnitConfig({})
        assert config.float_precision == 1e-10

    def test_custom_float_precision(self):
        """Test custom float precision from config."""
        config_dict = {"comparison": {"float_precision": 8}}
        config = SqlUnitConfig(config_dict)
        assert config.float_precision == 1e-8

    def test_float_precision_from_file(self):
        """Test loading float_precision from yaml file."""
        yaml_content = "comparison:\n  float_precision: 6\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            config = SqlUnitConfig.from_file(filepath)
            assert config.float_precision == 1e-6
        finally:
            os.unlink(filepath)

    def test_float_precision_values(self):
        """Test various float precision values."""
        test_cases = [
            (1, 0.1),
            (2, 0.01),
            (5, 1e-5),
            (10, 1e-10),
            (15, 1e-15),
        ]

        for n, expected in test_cases:
            config = SqlUnitConfig({"comparison": {"float_precision": n}})
            assert config.float_precision == expected

    def test_connection_property(self):
        """Test connection configuration access."""
        config_dict = {"connection": {"sqlite": "sqlite:///:memory:"}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["sqlite"] == "sqlite:///:memory:"

    def test_empty_config(self):
        """Test empty configuration."""
        config = SqlUnitConfig({})
        assert config.config == {}
        assert config.connection == {}
        assert config.comparison == {}

    def test_none_config(self):
        """Test None configuration."""
        config = SqlUnitConfig(None)
        assert config.config == {}
        assert config.float_precision == 1e-10

    def test_file_not_found(self):
        """Test error when config file not found."""
        with pytest.raises(ParserError, match="sql-unit.yaml not found"):
            SqlUnitConfig.from_file("/nonexistent/path/sql-unit.yaml")

    def test_from_directory(self):
        """Test loading from directory."""
        yaml_content = "comparison:\n  float_precision: 7\n"

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "sql-unit.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            config = SqlUnitConfig.from_directory(tmpdir)
            assert config.float_precision == 1e-7

    def test_float_precision_zero_invalid(self):
        """Test that zero precision raises ParserError."""
        config = SqlUnitConfig({"comparison": {"float_precision": 0}})
        # Should raise ParserError since 0 is not > 0
        with pytest.raises(ParserError, match="float_precision must be a positive integer"):
            _ = config.float_precision

    def test_float_precision_negative_invalid(self):
        """Test that negative precision raises ParserError."""
        config = SqlUnitConfig({"comparison": {"float_precision": -5}})
        # Should raise ParserError since -5 is not > 0
        with pytest.raises(ParserError, match="float_precision must be a positive integer"):
            _ = config.float_precision

    def test_connection_sqlite_url_syntax(self):
        """Test SQLite connection with URL syntax."""
        config_dict = {"connection": {"url": "sqlite:///test.db"}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["url"] == "sqlite:///test.db"

    def test_connection_sqlite_block_syntax(self):
        """Test SQLite connection with block syntax."""
        config_dict = {"connection": {"sqlite": {"path": "test.db"}}}
        config = SqlUnitConfig(config_dict)
        assert "sqlite" in config.connection
        assert config.connection["sqlite"]["path"] == "test.db"

    def test_connection_postgresql_url_syntax(self):
        """Test PostgreSQL connection with URL syntax."""
        config_dict = {"connection": {"url": "postgresql://user:pass@localhost/db"}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["url"] == "postgresql://user:pass@localhost/db"

    def test_connection_postgresql_block_syntax(self):
        """Test PostgreSQL connection with block syntax."""
        config_dict = {
            "connection": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "testuser",
                    "password": "testpass",
                    "database": "testdb",
                }
            }
        }
        config = SqlUnitConfig(config_dict)
        assert "postgresql" in config.connection
        assert config.connection["postgresql"]["host"] == "localhost"
        assert config.connection["postgresql"]["port"] == 5432

    def test_connection_mysql_url_syntax(self):
        """Test MySQL connection with URL syntax."""
        config_dict = {"connection": {"url": "mysql://user:pass@localhost/db"}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["url"] == "mysql://user:pass@localhost/db"

    def test_connection_duckdb_url_syntax(self):
        """Test DuckDB connection with URL syntax."""
        config_dict = {"connection": {"url": "duckdb:///test.duckdb"}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["url"] == "duckdb:///test.duckdb"

    def test_connection_with_environment_variables(self):
        """Test connection config with environment variable substitution."""
        os.environ["DB_PASSWORD"] = "secret123"
        try:
            config_dict = {
                "connection": {
                    "postgresql": {
                        "host": "localhost",
                        "user": "admin",
                        "password": "${DB_PASSWORD}",
                        "database": "mydb",
                    }
                }
            }
            config = SqlUnitConfig(config_dict)
            assert config.connection["postgresql"]["password"] == "secret123"
        finally:
            del os.environ["DB_PASSWORD"]

    def test_connection_with_missing_environment_variable(self):
        """Test that missing environment variable raises ParserError."""
        config_dict = {
            "connection": {"postgresql": {"host": "localhost", "password": "${MISSING_VAR}"}}
        }
        with pytest.raises(ParserError, match="Undefined environment variable"):
            SqlUnitConfig(config_dict)

    def test_connection_with_escaped_variable(self):
        """Test escaping of environment variables ($${ becomes literal ${)."""
        config_dict = {"connection": {"postgresql": {"note": "This is $${NOT_A_VAR}"}}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["postgresql"]["note"] == "This is ${NOT_A_VAR}"

    def test_connection_with_timeout(self):
        """Test connection config with timeout parameter."""
        config_dict = {"connection": {"sqlite": {"path": "test.db", "timeout": 30}}}
        config = SqlUnitConfig(config_dict)
        assert config.connection["sqlite"]["timeout"] == 30

    def test_threads_default(self):
        """Test default threads value."""
        config_dict = {}
        config = SqlUnitConfig(config_dict)
        assert config.config.get("threads") is None  # No default in config

    def test_threads_specified(self):
        """Test custom threads value."""
        config_dict = {"threads": 8}
        config = SqlUnitConfig(config_dict)
        assert config.config["threads"] == 8

    def test_threads_auto_detect(self):
        """Test threads set to -1 for auto-detection."""
        config_dict = {"threads": -1}
        config = SqlUnitConfig(config_dict)
        assert config.config["threads"] == -1

    def test_test_paths_specified(self):
        """Test test_paths configuration."""
        config_dict = {"test_paths": ["tests/unit/", "tests/integration/"]}
        config = SqlUnitConfig(config_dict)
        assert config.config["test_paths"] == ["tests/unit/", "tests/integration/"]

    def test_test_paths_with_env_vars(self):
        """Test test_paths with environment variable substitution."""
        os.environ["TEST_DIR"] = "tests"
        try:
            config_dict = {"test_paths": ["${TEST_DIR}/unit/"]}
            config = SqlUnitConfig(config_dict)
            assert config.config["test_paths"] == ["tests/unit/"]
        finally:
            del os.environ["TEST_DIR"]


class TestConnectionDialectExtractor:
    """Test ConnectionDialectExtractor for dialect detection."""

    def test_extract_dialect_from_url_sqlite(self):
        """Test dialect extraction from SQLite URL."""
        config = {"url": "sqlite:///test.db"}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "sqlite"

    def test_extract_dialect_from_url_postgresql(self):
        """Test dialect extraction from PostgreSQL URL."""
        config = {"url": "postgresql://localhost/db"}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "postgresql"

    def test_extract_dialect_from_url_postgres_alias(self):
        """Test dialect extraction from postgres:// URL (alias for postgresql)."""
        config = {"url": "postgres://localhost/db"}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "postgresql"

    def test_extract_dialect_from_url_mysql(self):
        """Test dialect extraction from MySQL URL."""
        config = {"url": "mysql://localhost/db"}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "mysql"

    def test_extract_dialect_from_url_duckdb(self):
        """Test dialect extraction from DuckDB URL."""
        config = {"url": "duckdb:///test.duckdb"}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "duckdb"

    def test_extract_dialect_from_block_sqlite(self):
        """Test dialect extraction from SQLite block syntax."""
        config = {"sqlite": {"path": "test.db"}}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "sqlite"

    def test_extract_dialect_from_block_postgresql(self):
        """Test dialect extraction from PostgreSQL block syntax."""
        config = {"postgresql": {"host": "localhost"}}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "postgresql"

    def test_extract_dialect_from_block_mysql(self):
        """Test dialect extraction from MySQL block syntax."""
        config = {"mysql": {"host": "localhost"}}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "mysql"

    def test_extract_dialect_from_block_duckdb(self):
        """Test dialect extraction from DuckDB block syntax."""
        config = {"duckdb": {"path": ":memory:"}}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "duckdb"

    def test_extract_dialect_url_takes_precedence_over_block(self):
        """Test that URL syntax takes precedence over block syntax."""
        config = {"url": "mysql://localhost/db", "sqlite": {"path": "test.db"}}
        dialect = ConnectionDialectExtractor.get_dialect(config)
        assert dialect == "mysql"

    def test_extract_dialect_invalid_url_format(self):
        """Test error on invalid URL format."""
        config = {"url": "invalid-url-without-scheme"}
        with pytest.raises(ParserError, match="Invalid database URL"):
            ConnectionDialectExtractor.get_dialect(config)

    def test_extract_dialect_unsupported_driver(self):
        """Test error on unsupported database driver."""
        config = {"url": "oracle://localhost/db"}
        with pytest.raises(ParserError, match="Unsupported database dialect"):
            ConnectionDialectExtractor.get_dialect(config)

    def test_extract_dialect_unknown_block_driver(self):
        """Test error when block syntax uses unknown driver."""
        config = {"unknown_db": {"host": "localhost"}}
        with pytest.raises(
            ParserError, match="Cannot determine database dialect from connection config"
        ):
            ConnectionDialectExtractor.get_dialect(config)

    def test_extract_dialect_empty_config(self):
        """Test error on empty connection config."""
        config = {}
        with pytest.raises(ParserError, match="Connection config is empty"):
            ConnectionDialectExtractor.get_dialect(config)

    def test_get_connection_url_from_url_syntax(self):
        """Test getting connection URL from URL syntax."""
        config = {"url": "postgresql://user:pass@localhost/db"}
        url = ConnectionDialectExtractor.get_connection_url(config)
        assert url == "postgresql://user:pass@localhost/db"

    def test_get_connection_url_from_sqlite_block_simple(self):
        """Test getting connection URL from SQLite block with simple string."""
        config = {"sqlite": "test.db"}
        url = ConnectionDialectExtractor.get_connection_url(config)
        assert url == "sqlite:///test.db"

    def test_get_connection_url_from_duckdb_block_simple(self):
        """Test getting connection URL from DuckDB block with simple string."""
        config = {"duckdb": "test.duckdb"}
        url = ConnectionDialectExtractor.get_connection_url(config)
        assert url == "duckdb:///test.duckdb"

    def test_get_connection_url_from_block_complex_returns_none(self):
        """Test getting connection URL from complex block config returns None."""
        config = {"postgresql": {"host": "localhost", "port": 5432}}
        url = ConnectionDialectExtractor.get_connection_url(config)
        assert url is None

    def test_config_with_dialect_extractor_integration(self):
        """Test that config works with dialect extractor."""
        config_dict = {
            "connection": {"url": "postgresql://user:pass@localhost/testdb"},
            "threads": 4,
        }
        config = SqlUnitConfig(config_dict)
        dialect = ConnectionDialectExtractor.get_dialect(config.connection)
        assert dialect == "postgresql"
        assert config.config["threads"] == 4
