"""SQL-Unit configuration management."""

import os
from typing import Any, Optional

import ruamel.yaml

from .core.exceptions import ParserError


class SqlUnitConfig:
    """Loads and manages sql-unit.yaml configuration."""

    DEFAULT_FLOAT_PRECISION = 1e-10

    def __init__(self, config_dict: dict) -> None:
        """
        Initialize config from dict.

        Args:
            config_dict: Parsed sql-unit.yaml content
        """
        self.config = config_dict or {}
        self.connection = self.config.get("connection", {})
        self.comparison = self.config.get("comparison", {})

    @property
    def float_precision(self) -> float:
        """
        Get float precision tolerance from config.

        Returns:
            Tolerance (10^-N) or default (1e-10)

        Example:
            float_precision: 8 → returns 1e-8
        """
        if "float_precision" in self.comparison:
            n = self.comparison["float_precision"]
            if isinstance(n, (int, float)) and n > 0:
                return 10.0 ** (-n)
        return self.DEFAULT_FLOAT_PRECISION

    @classmethod
    def from_file(cls, filepath: str) -> "SqlUnitConfig":
        """
        Load configuration from sql-unit.yaml file.

        Args:
            filepath: Path to sql-unit.yaml

        Returns:
            SqlUnitConfig instance

        Raises:
            ParserError: If file cannot be read or YAML is invalid
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                yaml = ruamel.yaml.YAML(typ="safe")
                config_dict = yaml.load(f) or {}
        except FileNotFoundError:
            raise ParserError(f"sql-unit.yaml not found: {filepath}")
        except Exception as e:
            raise ParserError(f"Failed to parse {filepath}: {str(e)}")

        return cls(config_dict)

    @classmethod
    def from_directory(cls, directory: str) -> "SqlUnitConfig":
        """
        Load configuration from directory (finds sql-unit.yaml).

        Args:
            directory: Directory to search

        Returns:
            SqlUnitConfig instance

        Raises:
            ParserError: If sql-unit.yaml not found or invalid
        """
        config_path = os.path.join(directory, "sql-unit.yaml")
        return cls.from_file(config_path)
