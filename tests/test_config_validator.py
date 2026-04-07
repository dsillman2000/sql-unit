"""Unit tests for ConfigValidator class."""

import pytest

from sql_unit.config_validator import ConfigValidator
from sql_unit.core.exceptions import ParserError


class TestConfigValidatorBasics:
    """Test basic config validation."""

    def test_validate_empty_dict_allowed(self):
        """Empty config dict is allowed (for config-free execution with --connection)."""
        config = {}
        result = ConfigValidator.validate(config)
        assert isinstance(result, dict)
        assert result == {}

    def test_validate_returns_dict(self):
        """Valid config should return dict."""
        config = {"connection": {"url": "sqlite:///:memory:"}}
        result = ConfigValidator.validate(config)
        assert isinstance(result, dict)
        assert result == config

    def test_validate_non_dict_raises_error(self):
        """Non-dict config should raise error."""
        with pytest.raises(ParserError, match="Config must be a YAML mapping"):
            ConfigValidator.validate("not a dict")


class TestConnectionValidation:
    """Test connection block validation."""

    def test_connection_url_syntax_valid(self):
        """Valid URL syntax should pass."""
        config = {"connection": {"url": "postgresql://localhost/testdb"}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["url"] == "postgresql://localhost/testdb"

    def test_connection_sqlite_block_syntax(self):
        """Valid SQLite block syntax should pass."""
        config = {"connection": {"sqlite": {"path": "test.db"}}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["sqlite"]["path"] == "test.db"

    def test_connection_sqlite_string_syntax(self):
        """Valid SQLite string syntax should pass."""
        config = {"connection": {"sqlite": "test.db"}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["sqlite"] == "test.db"

    def test_connection_sqlite_in_memory(self):
        """SQLite :memory: string should pass."""
        config = {"connection": {"sqlite": ":memory:"}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["sqlite"] == ":memory:"

    def test_connection_postgresql_block_syntax(self):
        """Valid PostgreSQL block syntax should pass."""
        config = {
            "connection": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "postgres",
                    "password": "secret",
                    "database": "testdb",
                }
            }
        }
        result = ConfigValidator.validate(config)
        assert result["connection"]["postgresql"]["host"] == "localhost"

    def test_connection_mysql_block_syntax(self):
        """Valid MySQL block syntax should pass."""
        config = {
            "connection": {
                "mysql": {
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "secret",
                    "database": "testdb",
                }
            }
        }
        result = ConfigValidator.validate(config)
        assert result["connection"]["mysql"]["user"] == "root"

    def test_connection_duckdb_block_syntax(self):
        """Valid DuckDB block syntax should pass."""
        config = {"connection": {"duckdb": {"path": "test.duckdb"}}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["duckdb"]["path"] == "test.duckdb"

    def test_connection_duckdb_string_syntax(self):
        """Valid DuckDB string syntax should pass."""
        config = {"connection": {"duckdb": "test.duckdb"}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["duckdb"] == "test.duckdb"

    def test_connection_empty_dict_raises_error(self):
        """Empty connection dict should raise error."""
        with pytest.raises(ParserError, match="'connection' block is empty"):
            ConfigValidator.validate({"connection": {}})

    def test_connection_empty_sqlite_string_raises_error(self):
        """Empty SQLite string should raise error."""
        with pytest.raises(ParserError, match="string config cannot be empty"):
            ConfigValidator.validate({"connection": {"sqlite": ""}})

    def test_connection_empty_postgresql_string_raises_error(self):
        """Empty PostgreSQL string should raise error."""
        with pytest.raises(ParserError, match="string config cannot be empty"):
            ConfigValidator.validate({"connection": {"postgresql": ""}})

    def test_connection_empty_driver_dict_raises_error(self):
        """Empty driver dict should raise error."""
        with pytest.raises(ParserError, match="must specify a valid configuration"):
            ConfigValidator.validate({"connection": {"sqlite": {}}})

    def test_connection_url_not_string_raises_error(self):
        """URL that's not a string should raise error."""
        with pytest.raises(ParserError, match="'connection.url' must be a string"):
            ConfigValidator.validate({"connection": {"url": 123}})

    def test_connection_url_empty_raises_error(self):
        """Empty URL should raise error."""
        with pytest.raises(ParserError, match="'connection.url' cannot be empty"):
            ConfigValidator.validate({"connection": {"url": ""}})

    def test_connection_url_missing_scheme_raises_error(self):
        """URL without scheme should raise error."""
        with pytest.raises(ParserError, match="must be a valid database URI"):
            ConfigValidator.validate({"connection": {"url": "localhost/testdb"}})

    def test_connection_url_and_driver_both_present_raises_error(self):
        """Both URL and driver specifications should raise error."""
        with pytest.raises(ParserError, match="cannot have both 'url' and driver"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:", "sqlite": "test.db"}}
            )

    def test_connection_invalid_type_raises_error(self):
        """Connection with invalid type should raise error."""
        with pytest.raises(ParserError, match="'connection' must be a mapping"):
            ConfigValidator.validate({"connection": "not a dict"})

    def test_connection_driver_not_string_or_dict_raises_error(self):
        """Driver config that's not string or dict should raise error."""
        with pytest.raises(ParserError, match="must be a string or mapping"):
            ConfigValidator.validate({"connection": {"sqlite": 123}})


class TestTestPathsValidation:
    """Test test_paths validation."""

    def test_test_paths_valid_list(self):
        """Valid test_paths list should pass."""
        config = {
            "connection": {"url": "sqlite:///:memory:"},
            "test_paths": ["tests/", "integration/"],
        }
        result = ConfigValidator.validate(config)
        assert result["test_paths"] == ["tests/", "integration/"]

    def test_test_paths_single_path(self):
        """Single test path should pass."""
        config = {
            "connection": {"url": "sqlite:///:memory:"},
            "test_paths": ["tests/"],
        }
        result = ConfigValidator.validate(config)
        assert result["test_paths"] == ["tests/"]

    def test_test_paths_not_list_raises_error(self):
        """test_paths that's not a list should raise error."""
        with pytest.raises(ParserError, match="'test_paths' must be a list"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:"}, "test_paths": "tests/"}
            )

    def test_test_paths_empty_list_raises_error(self):
        """Empty test_paths list should raise error."""
        with pytest.raises(ParserError, match="'test_paths' cannot be empty"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:"}, "test_paths": []}
            )

    def test_test_paths_non_string_item_raises_error(self):
        """Non-string path item should raise error."""
        with pytest.raises(ParserError, match="'test_paths\\[0\\]' must be a string"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:"}, "test_paths": [123]}
            )

    def test_test_paths_empty_string_item_raises_error(self):
        """Empty string path item should raise error."""
        with pytest.raises(ParserError, match="'test_paths\\[0\\]' cannot be empty"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:"}, "test_paths": [""]}
            )


class TestThreadsValidation:
    """Test threads validation."""

    def test_threads_valid_positive(self):
        """Valid positive threads should pass."""
        config = {"connection": {"url": "sqlite:///:memory:"}, "threads": 4}
        result = ConfigValidator.validate(config)
        assert result["threads"] == 4

    def test_threads_auto_detect(self):
        """Threads -1 (auto-detect) should pass."""
        config = {"connection": {"url": "sqlite:///:memory:"}, "threads": -1}
        result = ConfigValidator.validate(config)
        assert result["threads"] == -1

    def test_threads_not_integer_raises_error(self):
        """Non-integer threads should raise error."""
        with pytest.raises(ParserError, match="'threads' must be an integer"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "threads": "4"})

    def test_threads_zero_raises_error(self):
        """Threads 0 should raise error."""
        with pytest.raises(ParserError, match="'threads' must be >= 1 or exactly -1"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "threads": 0})

    def test_threads_negative_raises_error(self):
        """Negative threads (other than -1) should raise error."""
        with pytest.raises(ParserError, match="'threads' must be >= 1 or exactly -1"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "threads": -2})

    def test_threads_one_is_valid(self):
        """Threads 1 should pass."""
        config = {"connection": {"url": "sqlite:///:memory:"}, "threads": 1}
        result = ConfigValidator.validate(config)
        assert result["threads"] == 1


class TestTimeoutValidation:
    """Test timeout validation."""

    def test_timeout_valid_positive(self):
        """Valid positive timeout should pass."""
        config = {"connection": {"url": "sqlite:///:memory:"}, "timeout": 30}
        result = ConfigValidator.validate(config)
        assert result["timeout"] == 30

    def test_timeout_not_integer_raises_error(self):
        """Non-integer timeout should raise error."""
        with pytest.raises(ParserError, match="'timeout' must be an integer"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "timeout": "30"})

    def test_timeout_zero_raises_error(self):
        """Timeout 0 should raise error."""
        with pytest.raises(ParserError, match="'timeout' must be positive"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "timeout": 0})

    def test_timeout_negative_raises_error(self):
        """Negative timeout should raise error."""
        with pytest.raises(ParserError, match="'timeout' must be positive"):
            ConfigValidator.validate({"connection": {"url": "sqlite:///:memory:"}, "timeout": -1})

    def test_timeout_one_is_valid(self):
        """Timeout 1 should pass."""
        config = {"connection": {"url": "sqlite:///:memory:"}, "timeout": 1}
        result = ConfigValidator.validate(config)
        assert result["timeout"] == 1


class TestTopLevelValidation:
    """Test top-level config structure validation."""

    def test_unknown_keys_raises_error(self):
        """Unknown top-level keys should raise error."""
        with pytest.raises(ParserError, match="Unknown config keys"):
            ConfigValidator.validate(
                {"connection": {"url": "sqlite:///:memory:"}, "unknown_key": "value"}
            )

    def test_multiple_unknown_keys_raises_error(self):
        """Multiple unknown keys should raise error."""
        with pytest.raises(ParserError, match="Unknown config keys"):
            ConfigValidator.validate(
                {
                    "connection": {"url": "sqlite:///:memory:"},
                    "key1": "value1",
                    "key2": "value2",
                }
            )

    def test_all_valid_keys_allowed(self):
        """All valid top-level keys should be allowed."""
        config = {
            "connection": {"url": "sqlite:///:memory:"},
            "test_paths": ["tests/"],
            "threads": 4,
            "timeout": 30,
            "comparison": {},
        }
        result = ConfigValidator.validate(config)
        assert "comparison" in result


class TestComplexScenarios:
    """Test complex configuration scenarios."""

    def test_full_postgresql_config(self):
        """Full PostgreSQL config with all options should validate."""
        config = {
            "connection": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "user": "postgres",
                    "password": "secret",
                    "database": "testdb",
                    "timeout": 30,
                }
            },
            "test_paths": ["tests/unit/", "tests/integration/"],
            "threads": 8,
            "timeout": 60,
        }
        result = ConfigValidator.validate(config)
        assert result["threads"] == 8
        assert len(result["test_paths"]) == 2

    def test_minimal_sqlite_config(self):
        """Minimal SQLite config should validate."""
        config = {"connection": {"sqlite": ":memory:"}}
        result = ConfigValidator.validate(config)
        assert result["connection"]["sqlite"] == ":memory:"

    def test_url_syntax_with_all_options(self):
        """URL syntax with all options should validate."""
        config = {
            "connection": {
                "url": "postgresql://user:pass@localhost:5432/testdb",
                "timeout": 30,
            },
            "test_paths": ["tests/"],
            "threads": 4,
        }
        result = ConfigValidator.validate(config)
        assert "timeout" in result["connection"]
