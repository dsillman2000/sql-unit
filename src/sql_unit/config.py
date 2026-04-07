"""SQL-Unit configuration management.

Configuration Format
====================

The sql-unit.yaml file defines project-level settings:

    connection:
      postgresql:
        host: localhost
        port: 5432
        user: postgres
        password: ${DB_PASSWORD}
        database: test_db
        timeout: 30

    test_paths:
      - tests/unit/
      - tests/integration/

    threads: 4

Schema
======

Top-level fields:
  connection (required)  - Database connection configuration (dict)
  test_paths (optional)  - Test discovery paths (list of strings)
  threads (optional)     - Number of worker threads (int, default: 4)
  timeout (optional)     - Query timeout in seconds (int)
  comparison (optional)  - Comparison configuration for assertions (dict)

Connection Block
================

Two syntaxes are supported:

1. Block syntax (driver-specific parameters):
   connection:
     postgresql:
       host: localhost
       port: 5432
       user: postgres
       password: ${DB_PASSWORD}
       database: test_db

2. URL syntax:
   connection:
     url: "postgresql://user:pass@localhost/test_db"

Environment Variable Substitution
==================================

All string values support ${VAR_NAME} syntax to reference environment variables:
  password: ${DB_PASSWORD}  # Substitutes DBPASSWORD environment variable

Escape literal ${} with $${}:
  note: "This is $${literal}"  # Results in: This is ${literal}

Validation
==========

On load, the config is validated:
  - connection block is required (unless overridden via CLI)
  - threads must be >= 1 or exactly -1 (for auto-detect)
  - test_paths must exist (warning if not found)
  - All ${VAR} references must resolve to environment variables
"""

import os
import re

import ruamel.yaml

from sql_unit.core.exceptions import ParserError
from sql_unit.config_validator import ConfigValidator


# Module-level cache for loaded configs
_config_cache: dict[str, "SqlUnitConfig"] = {}


class SqlUnitConfig:
    """Loads and manages sql-unit.yaml configuration."""

    DEFAULT_FLOAT_PRECISION = 1e-10

    def __init__(self, config_dict: dict | None) -> None:
        """
        Initialize config from dict.

        Args:
            config_dict: Parsed sql-unit.yaml content
        """
        self.config = config_dict or {}
        # Validate config schema
        if self.config:
            self.config = ConfigValidator.validate(self.config)
        # Perform variable substitution on the raw config
        self._substitute_variables()
        self.connection = self.config.get("connection", {})
        self.comparison = self.config.get("comparison", {})

    @property
    def float_precision(self) -> float:
        """
        Get float precision tolerance from config.

        Returns:
            Tolerance (10^-N) or default (1e-10)

        Raises:
            ParserError: If float_precision is not a positive integer

        Example:
            float_precision: 8 → returns 1e-8
        """
        if "float_precision" in self.comparison:
            n = self.comparison["float_precision"]
            # Validate that float_precision is a positive integer
            if not isinstance(n, int) or n <= 0:
                raise ParserError(
                    f"float_precision must be a positive integer, got {n!r} ({type(n).__name__})"
                )
            return 10.0 ** (-n)
        return self.DEFAULT_FLOAT_PRECISION

    @classmethod
    def from_file(cls, filepath: str) -> "SqlUnitConfig":
        """
        Load configuration from sql-unit.yaml file.

        Caches loaded configs to avoid repeated file I/O.

        Args:
            filepath: Path to sql-unit.yaml

        Returns:
            SqlUnitConfig instance

        Raises:
            ParserError: If file cannot be read or YAML is invalid
        """
        # Check cache
        abs_path = os.path.abspath(filepath)
        if abs_path in _config_cache:
            return _config_cache[abs_path]

        try:
            if not os.path.isfile(abs_path):
                raise FileNotFoundError(f"File does not exist: {abs_path}")

            with open(abs_path, "r", encoding="utf-8") as f:
                yaml = ruamel.yaml.YAML(typ="safe")
                config_dict = yaml.load(f) or {}

            if not isinstance(config_dict, dict):
                raise ParserError(
                    f"Config must be a YAML mapping, got {type(config_dict).__name__}"
                )

            config_instance = cls(config_dict)
            # Cache the loaded config
            _config_cache[abs_path] = config_instance
            return config_instance

        except FileNotFoundError as e:
            raise ParserError(f"sql-unit.yaml not found: {abs_path}\n{str(e)}")
        except ruamel.yaml.YAMLError as e:
            raise ParserError(f"Invalid YAML in {abs_path}:\n{str(e)}")
        except Exception as e:
            raise ParserError(f"Failed to load {abs_path}: {str(e)}")

    @classmethod
    def from_directory(cls, directory: str) -> "SqlUnitConfig":
        """
        Load configuration from directory (finds sql-unit.yaml).

        Searches for sql-unit.yaml in the directory and parent directories.
        Stops at first match found. Errors if multiple found in the tree.

        Args:
            directory: Directory to search (usually CWD)

        Returns:
            SqlUnitConfig instance

        Raises:
            ParserError: If multiple configs found or if required connection missing
        """
        config_path = cls._find_config_file(directory)
        if config_path:
            return cls.from_file(config_path)
        # Return empty config (will require --connection flag)
        return cls(None)

    @classmethod
    def discover(
        cls, start_directory: str | None = None, explicit_path: str | None = None
    ) -> "SqlUnitConfig":
        """
        Discover and load configuration with proper precedence.

        Precedence:
        1. Explicit --config path (if provided)
        2. Search current/parent directories for sql-unit.yaml
        3. Return empty config (requires CLI --connection)

        Args:
            start_directory: Directory to start search (default: CWD)
            explicit_path: Explicit config file path (from --config flag)

        Returns:
            SqlUnitConfig instance

        Raises:
            ParserError: If explicit path not found or config is invalid
        """
        if explicit_path:
            if not os.path.exists(explicit_path):
                raise ParserError(f"Config file not found: {explicit_path}")
            return cls.from_file(explicit_path)

        start_directory = start_directory or os.getcwd()
        config_path = cls._find_config_file(start_directory)
        if config_path:
            return cls.from_file(config_path)
        return cls(None)

    @staticmethod
    def clear_cache() -> None:
        """
        Clear the configuration cache.

        Use this in tests or when you need to reload configs from disk.
        In normal operation, caching improves performance by avoiding
        repeated file I/O.
        """
        global _config_cache
        _config_cache.clear()

    @staticmethod
    def _find_config_file(start_directory: str) -> str | None:
        """
        Search for sql-unit.yaml in directory tree.

        Searches from start_directory upward, stopping at first match.
        Errors if multiple configs found in tree (indeterminate behavior).

        Args:
            start_directory: Directory to start search

        Returns:
            Path to config file, or None if not found

        Raises:
            ParserError: If multiple configs found in tree
        """
        current = os.path.abspath(start_directory)
        root = os.path.abspath(os.sep)
        found_configs = []

        while current != root:
            config_path = os.path.join(current, "sql-unit.yaml")
            if os.path.isfile(config_path):
                # Check if we've already found one (collision detection)
                if found_configs:
                    raise ParserError(
                        f"Multiple sql-unit.yaml files found (indeterminate behavior):\n"
                        f"  - {found_configs[0]}\n"
                        f"  - {config_path}\n"
                        f"Please remove or rename one of them."
                    )
                found_configs.append(config_path)
                return config_path

            # Move up one directory
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent

        return None

    def _substitute_variables(self) -> None:
        """
        Substitute environment variables in config.

        Processes all string values in config, replacing ${VAR} with environment
        variable values. Validates that all referenced variables exist.

        Escaping:
          $${VAR} → ${VAR} (literal, not substituted)

        Raises:
            ParserError: If referenced environment variable doesn't exist
        """
        try:
            self.config = self._substitute_value(self.config)
        except KeyError as e:
            raise ParserError(f"Undefined environment variable: {str(e)}")

    def _substitute_value(self, value: any) -> any:
        """
        Recursively substitute variables in a value.

        Args:
            value: Value to process (str, dict, list, or other)

        Returns:
            Value with variables substituted

        Raises:
            KeyError: If environment variable is not found
        """
        if isinstance(value, str):
            return self._substitute_string(value)
        elif isinstance(value, dict):
            return {k: self._substitute_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._substitute_value(v) for v in value]
        else:
            return value

    def _substitute_string(self, text: str) -> str:
        """
        Substitute variables in a string.

        Processes ${VAR} syntax, escaping with $${VAR}.

        Args:
            text: String to process

        Returns:
            String with variables substituted

        Raises:
            KeyError: If ${VAR} references undefined environment variable
        """

        def replacer(match: re.Match) -> str:
            # Group 1: escaped $${VAR} → literal
            # Group 2: normal ${VAR} → substitute
            if match.group(1):  # Escaped
                return "${" + match.group(1) + "}"
            else:  # Normal substitution
                var_name = match.group(2)
                if var_name not in os.environ:
                    raise KeyError(f"${{{var_name}}}")
                return os.environ[var_name]

        return re.sub(
            r"\$\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)\}",
            replacer,
            text,
        )
