"""Connection management and dialect detection from config."""

from sql_unit.core.exceptions import ParserError


class ConnectionDialectExtractor:
    """Extracts database dialect and connection details from config."""

    DIALECT_MAP = {
        "sqlite": "sqlite",
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mysql": "mysql",
        "duckdb": "duckdb",
    }

    @staticmethod
    def get_dialect(config: dict) -> str:
        """
        Extract database dialect from connection config.

        Args:
            config: Connection config block

        Returns:
            Dialect name (sqlite, postgresql, mysql, duckdb)

        Raises:
            ParserError: If dialect cannot be determined
        """
        if not config:
            raise ParserError("Connection config is empty")

        # Check for URL syntax first
        if "url" in config:
            return ConnectionDialectExtractor._extract_dialect_from_url(config["url"])

        # Check for block syntax (driver-specific)
        for driver in ConnectionDialectExtractor.DIALECT_MAP:
            if driver in config:
                return ConnectionDialectExtractor.DIALECT_MAP[driver]

        raise ParserError(
            "Cannot determine database dialect from connection config. "
            "Specify either 'url' or one of: sqlite, postgresql, mysql, duckdb"
        )

    @staticmethod
    def _extract_dialect_from_url(url: str) -> str:
        """
        Extract dialect from database URL.

        Args:
            url: Database URL (e.g., postgresql://localhost/db)

        Returns:
            Dialect name

        Raises:
            ParserError: If URL format is invalid or dialect is unsupported
        """
        if not url or "://" not in url:
            raise ParserError(f"Invalid database URL: {url}")

        # Extract scheme from URL
        scheme = url.split("://")[0].lower()

        # Handle postgres/postgresql aliases
        if scheme == "postgres":
            return "postgresql"

        if scheme in ConnectionDialectExtractor.DIALECT_MAP:
            return ConnectionDialectExtractor.DIALECT_MAP[scheme]

        supported = ", ".join(sorted(set(ConnectionDialectExtractor.DIALECT_MAP.values())))
        raise ParserError(f"Unsupported database dialect: {scheme}. Supported: {supported}")

    @staticmethod
    def get_connection_url(config: dict) -> str | None:
        """
        Get connection URL from config.

        Args:
            config: Connection config block

        Returns:
            Database URL string, or None if not URL-based

        Raises:
            ParserError: If URL cannot be constructed
        """
        if "url" in config:
            return config["url"]

        # Construct URL from block syntax
        for driver in ["sqlite", "postgresql", "postgres", "mysql", "duckdb"]:
            if driver in config:
                driver_config = config[driver]
                if isinstance(driver_config, str):
                    # Simple string form (e.g., sqlite: ":memory:")
                    if driver in ["sqlite", "duckdb"]:
                        return f"{driver}:///{driver_config}"
                    return None
                # Complex dict form - let caller handle construction
                return None

        return None
