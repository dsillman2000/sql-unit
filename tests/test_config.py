"""Tests for SqlUnitConfig."""

import os
import tempfile

import pytest

from sql_unit.config import SqlUnitConfig
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
