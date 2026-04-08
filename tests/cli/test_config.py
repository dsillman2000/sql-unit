"""Tests for CLI configuration loading."""

import tempfile
from pathlib import Path

import pytest

from sql_unit.cli.config import ConfigLoader


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_find_config_file_in_current_dir(self):
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text("connection:\n  url: 'sqlite:///test.db'\n")

            found = ConfigLoader._find_config_file(tmpdir)
            assert found == config_path

    def test_find_config_file_returns_none_if_not_found(self):
        """Test returns None when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = ConfigLoader._find_config_file(tmpdir)
            assert found is None

    def test_parse_config_file_basic(self):
        """Test parsing basic config file."""
        config_content = """
connection:
  url: "sqlite:///test.db"
test_paths:
  - "tests/"
  - "src/test_definitions/"
threads: 4
output_format: "json"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text(config_content)

            config = ConfigLoader._parse_config_file(config_path)
            assert config.connection_url == "sqlite:///test.db"
            assert config.test_paths == ["tests/", "src/test_definitions/"]
            assert config.threads == 4
            assert config.output_format == "json"

    def test_parse_config_file_defaults(self):
        """Test parsing config file with defaults."""
        config_content = """
connection:
  url: "postgresql://localhost/testdb"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text(config_content)

            config = ConfigLoader._parse_config_file(config_path)
            assert config.connection_url == "postgresql://localhost/testdb"
            assert config.test_paths == []
            assert config.threads == 1
            assert config.output_format == "human"

    def test_load_config_full(self):
        """Test full config loading."""
        config_content = """
connection:
  url: "sqlite:///test.db"
test_paths:
  - "tests/"
threads: 2
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text(config_content)

            config = ConfigLoader.load_config(tmpdir)
            assert config is not None
            assert config.connection_url == "sqlite:///test.db"
            assert config.test_paths == ["tests/"]
            assert config.threads == 2

    def test_substitute_env_vars_braces(self):
        """Test environment variable substitution with ${VAR}."""
        import os

        os.environ["TEST_DB"] = "test.db"
        value = "sqlite:///${TEST_DB}"
        result = ConfigLoader._substitute_env_vars(value)
        assert result == "sqlite:///test.db"

    def test_substitute_env_vars_dollar(self):
        """Test environment variable substitution with $VAR."""
        import os

        os.environ["TEST_HOST"] = "localhost"
        value = "postgresql://$TEST_HOST/testdb"
        result = ConfigLoader._substitute_env_vars(value)
        assert result == "postgresql://localhost/testdb"

    def test_config_with_env_var(self):
        """Test config file with environment variables."""
        import os

        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"

        config_content = """
connection:
  url: "${DATABASE_URL}"
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sql-unit.yaml"
            config_path.write_text(config_content)

            config = ConfigLoader._parse_config_file(config_path)
            assert config.connection_url == "postgresql://user:pass@localhost/db"


class TestConnectionURLParsing:
    """Tests for connection URL parsing."""

    def test_parse_sqlite_file_url(self):
        """Test parsing SQLite file URL."""
        config = ConfigLoader._parse_connection_url("sqlite:///test.db")
        assert config.database_type == "sqlite"
        assert "test.db" in config.connection_string

    def test_parse_sqlite_memory_url(self):
        """Test parsing SQLite in-memory URL."""
        config = ConfigLoader._parse_connection_url("sqlite:///:memory:")
        assert config.database_type == "sqlite"
        assert config.connection_string == "sqlite:///:memory:"

    def test_parse_duckdb_file_url(self):
        """Test parsing DuckDB file URL."""
        config = ConfigLoader._parse_connection_url("duckdb:///test.duckdb")
        assert config.database_type == "duckdb"
        assert "test.duckdb" in config.connection_string

    def test_parse_duckdb_memory_url(self):
        """Test parsing DuckDB in-memory URL."""
        config = ConfigLoader._parse_connection_url("duckdb:///:memory:")
        assert config.database_type == "duckdb"
        assert config.connection_string == "duckdb:///:memory:"

    def test_parse_postgresql_url(self):
        """Test parsing PostgreSQL URL."""
        config = ConfigLoader._parse_connection_url(
            "postgresql://user:password@localhost:5432/testdb"
        )
        assert config.database_type == "postgresql"
        assert "testdb" in config.connection_string
        assert "localhost" in config.connection_string

    def test_parse_postgresql_url_with_encoded_password(self):
        """Test parsing PostgreSQL URL with URL-encoded password."""
        config = ConfigLoader._parse_connection_url("postgresql://user:p%40ssword@localhost/testdb")
        assert config.database_type == "postgresql"

    def test_parse_postgres_url_shorthand(self):
        """Test parsing 'postgres://' scheme (shorthand for postgresql)."""
        config = ConfigLoader._parse_connection_url("postgres://user:password@localhost/testdb")
        assert config.database_type == "postgresql"

    def test_parse_mysql_url(self):
        """Test parsing MySQL URL."""
        config = ConfigLoader._parse_connection_url("mysql://user:password@localhost:3306/testdb")
        assert config.database_type == "mysql"
        assert "testdb" in config.connection_string

    def test_parse_url_invalid_scheme(self):
        """Test parsing URL with invalid scheme raises error."""
        with pytest.raises(ValueError, match="Unsupported database scheme"):
            ConfigLoader._parse_connection_url("oracle://localhost/testdb")

    def test_parse_postgresql_missing_database(self):
        """Test parsing PostgreSQL URL without database raises error."""
        with pytest.raises(ValueError, match="requires"):
            ConfigLoader._parse_connection_url("postgresql://user:password@localhost")

    def test_parse_mysql_missing_database(self):
        """Test parsing MySQL URL without database raises error."""
        with pytest.raises(ValueError, match="requires"):
            ConfigLoader._parse_connection_url("mysql://user:password@localhost")
