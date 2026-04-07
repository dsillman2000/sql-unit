"""Configuration validation for sql-unit.yaml."""

from typing import Any

from sql_unit.core.exceptions import ParserError


class ConfigValidator:
    """Validates sql-unit configuration against schema."""

    # Supported database drivers
    SUPPORTED_DRIVERS = {"sqlite", "postgresql", "mysql", "duckdb"}

    @staticmethod
    def validate(config: dict) -> dict:
        """
        Validate configuration and return validated copy.

        Args:
            config: Configuration dict from YAML

        Returns:
            Validated config dict

        Raises:
            ParserError: If validation fails
        """
        if not isinstance(config, dict):
            raise ParserError(f"Config must be a YAML mapping, got {type(config).__name__}")

        # Validate top-level structure
        ConfigValidator._validate_top_level(config)

        # Validate connection block
        if "connection" in config:
            ConfigValidator._validate_connection(config["connection"])

        # Validate test_paths
        if "test_paths" in config:
            ConfigValidator._validate_test_paths(config["test_paths"])

        # Validate threads
        if "threads" in config:
            ConfigValidator._validate_threads(config["threads"])

        # Validate timeout
        if "timeout" in config:
            ConfigValidator._validate_timeout(config["timeout"])

        return config

    @staticmethod
    def _validate_top_level(config: dict) -> None:
        """Validate top-level config structure."""
        allowed_keys = {"connection", "test_paths", "threads", "timeout", "comparison"}
        unknown = set(config.keys()) - allowed_keys
        if unknown:
            raise ParserError(f"Unknown config keys: {', '.join(sorted(unknown))}")

    @staticmethod
    def _validate_connection(connection: Any) -> None:
        """Validate connection block."""
        if not isinstance(connection, dict):
            raise ParserError(f"'connection' must be a mapping, got {type(connection).__name__}")

        if not connection:
            raise ParserError("'connection' block is empty")

        # Check for valid syntax (either block syntax or URL syntax, not mixed)
        has_url = "url" in connection
        has_drivers = any(key in connection for key in ConfigValidator.SUPPORTED_DRIVERS)

        if not (has_url or has_drivers):
            raise ParserError(
                f"'connection' must specify either 'url' or one of: "
                f"{', '.join(ConfigValidator.SUPPORTED_DRIVERS)}"
            )

        if has_url and has_drivers:
            raise ParserError("'connection' cannot have both 'url' and driver specifications")

        # Validate URL syntax
        if has_url:
            ConfigValidator._validate_connection_url(connection["url"])

        # Validate block syntax (driver-specific)
        for driver in ConfigValidator.SUPPORTED_DRIVERS:
            if driver in connection:
                ConfigValidator._validate_driver_config(driver, connection[driver])

    @staticmethod
    def _validate_connection_url(url: Any) -> None:
        """Validate connection URL."""
        if not isinstance(url, str):
            raise ParserError(f"'connection.url' must be a string, got {type(url).__name__}")

        if not url:
            raise ParserError("'connection.url' cannot be empty")

        # Basic validation: should look like a database URI
        if "://" not in url:
            raise ParserError(
                f"'connection.url' must be a valid database URI (e.g., 'postgresql://host/db'): {url}"
            )

    @staticmethod
    def _validate_driver_config(driver: str, config: Any) -> None:
        """Validate driver-specific configuration."""
        if isinstance(config, str):
            # Simple string form (e.g., sqlite: ":memory:")
            return

        if not isinstance(config, dict):
            raise ParserError(
                f"'{driver}' config must be a string or mapping, got {type(config).__name__}"
            )

        # Validate driver-specific required fields
        if driver == "sqlite" and not config:
            raise ParserError("SQLite config must specify 'path' or be a string URI")

        if driver == "postgresql" or driver == "mysql":
            # These support flexible config, no strict requirements here
            pass

        if driver == "duckdb" and not config:
            raise ParserError("DuckDB config must specify 'path' or be a string URI")

    @staticmethod
    def _validate_test_paths(paths: Any) -> None:
        """Validate test_paths configuration."""
        if not isinstance(paths, list):
            raise ParserError(f"'test_paths' must be a list, got {type(paths).__name__}")

        if not paths:
            raise ParserError("'test_paths' cannot be empty")

        for i, path in enumerate(paths):
            if not isinstance(path, str):
                raise ParserError(f"'test_paths[{i}]' must be a string, got {type(path).__name__}")
            if not path:
                raise ParserError(f"'test_paths[{i}]' cannot be empty")

    @staticmethod
    def _validate_threads(threads: Any) -> None:
        """Validate threads configuration."""
        if not isinstance(threads, int):
            raise ParserError(f"'threads' must be an integer, got {type(threads).__name__}")

        if threads < 1 and threads != -1:
            raise ParserError(
                f"'threads' must be >= 1 or exactly -1 (for auto-detect), got {threads}"
            )

    @staticmethod
    def _validate_timeout(timeout: Any) -> None:
        """Validate timeout configuration."""
        if not isinstance(timeout, int):
            raise ParserError(f"'timeout' must be an integer, got {type(timeout).__name__}")

        if timeout <= 0:
            raise ParserError(f"'timeout' must be positive, got {timeout}")
