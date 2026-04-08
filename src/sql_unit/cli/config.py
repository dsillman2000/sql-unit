"""Configuration management for CLI."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote

import yaml

from sql_unit.database import ConnectionConfig


@dataclass
class CliConfig:
    """CLI configuration from sql-unit.yaml."""

    connection_url: Optional[str] = None
    test_paths: list[str] = None
    threads: int = 1
    output_format: str = "human"

    def __post_init__(self):
        if self.test_paths is None:
            self.test_paths = []


class ConfigLoader:
    """Loads and manages CLI configuration."""

    CONFIG_FILENAMES = ["sql-unit.yaml", "sql-unit.yml", ".sql-unit.yaml"]

    @classmethod
    def load_config(cls, start_dir: str = ".") -> Optional[CliConfig]:
        """Load configuration from sql-unit.yaml.

        Searches for config file starting from start_dir and going up to root.

        Args:
            start_dir: Directory to start searching from

        Returns:
            CliConfig if found, None otherwise
        """
        config_path = cls._find_config_file(start_dir)
        if not config_path:
            return None

        try:
            return cls._parse_config_file(config_path)
        except Exception as e:
            raise ValueError(f"Error loading config from {config_path}: {e}")

    @classmethod
    def _find_config_file(cls, start_dir: str = ".") -> Optional[Path]:
        """Find config file by searching up directory tree.

        Args:
            start_dir: Directory to start searching from

        Returns:
            Path to config file if found, None otherwise
        """
        current = Path(start_dir).resolve()

        # Search up to root
        while True:
            for filename in cls.CONFIG_FILENAMES:
                config_path = current / filename
                if config_path.exists():
                    return config_path

            parent = current.parent
            if parent == current:
                # Reached root
                break
            current = parent

        return None

    @classmethod
    def _parse_config_file(cls, config_path: Path) -> CliConfig:
        """Parse sql-unit.yaml configuration file.

        Args:
            config_path: Path to config file

        Returns:
            Parsed CliConfig

        Raises:
            ValueError: If config file is invalid
        """
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

        # Extract connection config
        connection_data = data.get("connection", {})
        connection_url = (
            connection_data.get("url") if isinstance(connection_data, dict) else connection_data
        )

        # Substitute environment variables
        if connection_url and "$" in connection_url:
            connection_url = cls._substitute_env_vars(connection_url)

        # Extract test paths
        test_paths = data.get("test_paths", [])
        if isinstance(test_paths, str):
            test_paths = [test_paths]

        # Extract other settings
        threads = data.get("threads", 1)
        output_format = data.get("output_format", "human")

        return CliConfig(
            connection_url=connection_url,
            test_paths=test_paths,
            threads=threads,
            output_format=output_format,
        )

    @staticmethod
    def _substitute_env_vars(value: str) -> str:
        """Substitute environment variables in string.

        Supports ${VAR} and $VAR syntax.

         Args:
            value: String with potential env vars

        Returns:
            String with env vars substituted
        """

        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))

        # ${VAR} or $VAR
        pattern = r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)"
        return re.sub(pattern, replace_var, value)

    @classmethod
    def get_connection_config(
        cls,
        connection_url: Optional[str] = None,
        config_file_config: Optional[CliConfig] = None,
    ) -> Optional[ConnectionConfig]:
        """Get ConnectionConfig from CLI arg or config file.

        CLI arg takes precedence over config file.

        Args:
            connection_url: Connection URL from CLI
            config_file_config: Configuration from config file

        Returns:
            ConnectionConfig or None if no connection available
        """
        # CLI takes precedence
        url = connection_url

        # Fall back to config file
        if not url and config_file_config:
            url = config_file_config.connection_url

        if not url:
            return None

        # Parse connection URL into ConnectionConfig
        return cls._parse_connection_url(url)

    @staticmethod
    def _parse_connection_url(connection_url: str) -> ConnectionConfig:
        """Parse a connection URL string into a ConnectionConfig.

        Supports:
        - sqlite:///path/to/file.db
        - sqlite:///:memory:
        - postgresql://user:password@host:port/database
        - mysql://user:password@host:port/database
        - duckdb:///path/to/file.duckdb
        - duckdb:///:memory:

        Args:
            connection_url: Connection URL string

        Returns:
            ConnectionConfig instance

        Raises:
            ValueError: If URL format is invalid or unsupported
        """
        try:
            parsed = urlparse(connection_url)
            scheme = parsed.scheme.lower()

            if scheme == "sqlite":
                # sqlite:///path or sqlite:///:memory:
                path = parsed.path or ":memory:"
                if path.startswith("/"):
                    path = path[1:]  # Remove leading slash
                if not path:
                    path = ":memory:"
                return ConnectionConfig.sqlite(path)

            elif scheme == "duckdb":
                # duckdb:///path or duckdb:///:memory:
                path = parsed.path or ":memory:"
                if path.startswith("/"):
                    path = path[1:]  # Remove leading slash
                if not path:
                    path = ":memory:"
                return ConnectionConfig.duckdb(path)

            elif scheme == "postgresql" or scheme == "postgres":
                # postgresql://user:password@host:port/database
                host = parsed.hostname or "localhost"
                port = parsed.port or 5432
                database = parsed.path.lstrip("/") if parsed.path else None
                user = parsed.username
                password = unquote(parsed.password) if parsed.password else None

                if not database or not user:
                    raise ValueError(
                        "PostgreSQL URL requires: postgresql://user:password@host:port/database"
                    )

                return ConnectionConfig.postgresql(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password,
                )

            elif scheme == "mysql":
                # mysql://user:password@host:port/database
                host = parsed.hostname or "localhost"
                port = parsed.port or 3306
                database = parsed.path.lstrip("/") if parsed.path else None
                user = parsed.username
                password = unquote(parsed.password) if parsed.password else None

                if not database or not user:
                    raise ValueError("MySQL URL requires: mysql://user:password@host:port/database")

                return ConnectionConfig.mysql(
                    host=host,
                    port=port,
                    database=database,
                    user=user,
                    password=password,
                )

            else:
                raise ValueError(f"Unsupported database scheme: {scheme}")

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to parse connection URL: {e}")
