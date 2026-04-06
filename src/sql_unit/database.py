"""Database connection management using SQLAlchemy."""

from typing import Any
from urllib.parse import quote_plus, urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from .exceptions import ExecutionError


class DatabaseManager:
    """Manages database connections with pooling support.
    
    Create via ConnectionConfig:
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_database_manager()
    
    Or directly for advanced use:
        engine = create_engine("sqlite:///:memory:")
        manager = DatabaseManager(
            engine=engine,
            database_type="sqlite",
            connection_string="sqlite:///:memory:"
        )
    """
    
    def __init__(
        self,
        engine: Engine | None = None,
        database_type: str = "sqlite",
        connection_string: str | None = None,
        pooling: bool = True
    ):
        """
        Initialize connection manager.
        
        Args:
            engine: SQLAlchemy engine (if pre-created)
            database_type: Type of database (sqlite, postgresql, mysql, duckdb)
            connection_string: Database connection string
            pooling: Whether to use connection pooling
        """
        self.engine = engine
        self.database_type = database_type
        self.connection_string = connection_string or "sqlite:///:memory:"
        self.pooling = pooling
        
        if not self.engine:
            self.engine = self._create_engine()
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine based on configuration."""
        # For in-memory SQLite, use StaticPool to keep connection alive
        if self.connection_string == "sqlite:///:memory:":
            pool_class = StaticPool
        else:
            pool_class = QueuePool if self.pooling else NullPool
        
        try:
            engine = create_engine(
                self.connection_string,
                poolclass=pool_class,
                echo=False
            )
            return engine
        except Exception as e:
            raise ExecutionError(f"Failed to create database engine: {str(e)}")
    
    def get_connection(self):
        """Get a database connection from the pool."""
        return self.engine.connect()
    
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            ExecutionError: If query execution fails
        """
        try:
            conn = self.get_connection()
            try:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                # Convert Row objects to dicts
                return [dict(row._mapping) for row in rows]
            finally:
                conn.close()
        except Exception as e:
            raise ExecutionError(f"Query execution failed: {str(e)}\nSQL: {sql}")
    
    def execute_setup(self, setup_sql: str) -> None:
        """
        Execute setup SQL (e.g., CREATE TABLE, INSERT).
        
        Args:
            setup_sql: SQL to execute for setup
            
        Raises:
            ExecutionError: If setup fails
        """
        try:
            conn = self.get_connection()
            try:
                conn.execute(text(setup_sql))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            raise ExecutionError(f"Setup execution failed: {str(e)}\nSQL: {setup_sql}")


class ConnectionConfig:
    """Configuration for database connections.
    
    Create configurations for different databases:
        config = ConnectionConfig.sqlite(":memory:")
        config = ConnectionConfig.postgresql(host="localhost", port=5432, ...)
        config = ConnectionConfig.mysql(host="localhost", port=3306, ...)
        config = ConnectionConfig.duckdb(":memory:")
    
    Or load from YAML:
        config = ConnectionConfig.from_yaml(config_dict)
    
    Then create a database manager:
        manager = config.create_database_manager()
    """
    
    def __init__(
        self,
        database_type: str,
        connection_string: str,
        pooling: bool = True,
        pool_size: int = 5,
        max_overflow: int = 10,
        **kwargs
    ):
        """
        Initialize connection configuration.
        
        Args:
            database_type: Type of database (sqlite, postgresql, mysql, duckdb)
            connection_string: Database connection URL
            pooling: Whether to use connection pooling
            pool_size: Size of connection pool
            max_overflow: Maximum overflow of pool connections
            **kwargs: Additional SQLAlchemy engine options
        """
        self.database_type = database_type
        self.connection_string = connection_string
        self.pooling = pooling
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.kwargs = kwargs
    
    @staticmethod
    def sqlite(path: str = ":memory:", **options) -> "ConnectionConfig":
        """
        Create SQLite configuration.
        
        Args:
            path: File path ("/path/to/db.sqlite") or ":memory:" for in-memory
            **options: Additional configuration options
            
        Returns:
            ConnectionConfig instance
            
        Example:
            config = ConnectionConfig.sqlite(":memory:")
            config = ConnectionConfig.sqlite("/tmp/test.db")
        """
        if path == ":memory:":
            conn_str = "sqlite:///:memory:"
            pooling = False
        else:
            conn_str = f"sqlite:///{path}"
            pooling = True
        
        return ConnectionConfig(
            database_type="sqlite",
            connection_string=conn_str,
            pooling=pooling,
            **options
        )
    
    @staticmethod
    def postgresql(
        host: str,
        port: int = 5432,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        **options
    ) -> "ConnectionConfig":
        """
        Create PostgreSQL configuration.
        
        Args:
            host: Database server hostname
            port: Database server port (default: 5432)
            database: Database name
            user: Database user
            password: Database password
            **options: Additional options (pool_size, max_overflow, echo, etc.)
            
        Returns:
            ConnectionConfig instance
            
        Example:
            config = ConnectionConfig.postgresql(
                host="localhost",
                port=5432,
                database="testdb",
                user="admin",
                password="secret"
            )
        """
        url = ConnectionConfig._url(
            f"postgresql://{user}:{password}@{host}:{port}/{database}"
        )
        return ConnectionConfig(
            database_type="postgresql",
            connection_string=url,
            pooling=True,
            pool_size=10,
            **options
        )
    
    @staticmethod
    def mysql(
        host: str,
        port: int = 3306,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
        **options
    ) -> "ConnectionConfig":
        """
        Create MySQL configuration.
        
        Args:
            host: Database server hostname
            port: Database server port (default: 3306)
            database: Database name
            user: Database user
            password: Database password
            **options: Additional options (pool_size, max_overflow, echo, etc.)
            
        Returns:
            ConnectionConfig instance
            
        Example:
            config = ConnectionConfig.mysql(
                host="localhost",
                port=3306,
                database="testdb",
                user="admin",
                password="secret"
            )
        """
        url = ConnectionConfig._url(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        )
        return ConnectionConfig(
            database_type="mysql",
            connection_string=url,
            pooling=True,
            pool_size=10,
            **options
        )
    
    @staticmethod
    def duckdb(path: str = ":memory:", **options) -> "ConnectionConfig":
        """
        Create DuckDB configuration.
        
        Args:
            path: File path or ":memory:" for in-memory database
            **options: Additional configuration options
            
        Returns:
            ConnectionConfig instance
            
        Example:
            config = ConnectionConfig.duckdb(":memory:")
            config = ConnectionConfig.duckdb("/tmp/test.duckdb")
        """
        if path == ":memory:":
            conn_str = "duckdb:///:memory:"
        else:
            conn_str = f"duckdb:///{path}"
        
        return ConnectionConfig(
            database_type="duckdb",
            connection_string=conn_str,
            pooling=False,
            **options
        )
    
    @staticmethod
    def _url(url: str) -> str:
        """
        Normalize and validate URL syntax across backends.
        
        Handles:
        - URL encoding of special characters in passwords
        - Scheme validation
        - Basic connection string formatting
        
        Args:
            url: Connection URL string
            
        Returns:
            Normalized URL
            
        Example:
            >>> ConnectionConfig._url("postgresql://user:p@ss@localhost/db")
            'postgresql://user:p%40ss@localhost/db'
        """
        try:
            parsed = urlparse(url)
            
            # Validate that we have a scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid connection URL format: {url}")
            
            # URL-encode password if present and contains special characters
            if "@" in parsed.netloc:
                user_part, host_part = parsed.netloc.rsplit("@", 1)
                if ":" in user_part:
                    user, password = user_part.split(":", 1)
                    # Only encode if it has special characters that need encoding
                    if any(c in password for c in "!@#$%^&*()"):
                        password = quote_plus(password)
                    user_part = f"{user}:{password}"
                
                netloc = f"{user_part}@{host_part}"
            else:
                netloc = parsed.netloc
            
            # Reconstruct URL
            result = f"{parsed.scheme}://{netloc}"
            if parsed.path:
                result += parsed.path
            if parsed.query:
                result += f"?{parsed.query}"
            
            return result
        except Exception as e:
            raise ValueError(f"Failed to parse connection URL: {str(e)}")
    
    @classmethod
    def from_yaml(cls, config_dict: dict) -> "ConnectionConfig":
        """
        Create ConnectionConfig from YAML dictionary.
        
        Args:
            config_dict: Dictionary with database configuration
            
        Returns:
            ConnectionConfig instance
            
        Raises:
            ValueError: If configuration is invalid or missing required fields
            
        Example:
            config_dict = {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database": "testdb",
                "user": "admin",
                "password": "secret"
            }
            config = ConnectionConfig.from_yaml(config_dict)
        """
        db_type = config_dict.get("type", "").lower()
        
        if db_type == "sqlite":
            return cls.sqlite(config_dict.get("path", ":memory:"))
        
        elif db_type == "postgresql":
            return cls.postgresql(
                host=config_dict.get("host", "localhost"),
                port=config_dict.get("port", 5432),
                database=config_dict.get("database"),
                user=config_dict.get("user"),
                password=config_dict.get("password")
            )
        
        elif db_type == "mysql":
            return cls.mysql(
                host=config_dict.get("host", "localhost"),
                port=config_dict.get("port", 3306),
                database=config_dict.get("database"),
                user=config_dict.get("user"),
                password=config_dict.get("password")
            )
        
        elif db_type == "duckdb":
            return cls.duckdb(config_dict.get("path", ":memory:"))
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with pooling configuration.
        
        Returns:
            Configured SQLAlchemy Engine instance
            
        Raises:
            ExecutionError: If engine creation fails
        """
        # Determine pool class
        if self.database_type == "sqlite" and self.connection_string == "sqlite:///:memory:":
            pool_class = StaticPool
        elif self.pooling:
            pool_class = QueuePool
        else:
            pool_class = NullPool
        
        try:
            # Build kwargs for create_engine
            engine_kwargs = {
                "poolclass": pool_class,
                **self.kwargs
            }
            
            # Only add pool sizing options if using QueuePool
            if pool_class == QueuePool:
                engine_kwargs["pool_size"] = self.pool_size
                engine_kwargs["max_overflow"] = self.max_overflow
            
            engine = create_engine(self.connection_string, **engine_kwargs)
            return engine
        except Exception as e:
            raise ExecutionError(f"Failed to create database engine: {str(e)}")
    
    def create_database_manager(self) -> DatabaseManager:
        """
        Create a DatabaseManager from this configuration.
        
        Returns:
            Configured DatabaseManager instance
            
        Example:
            config = ConnectionConfig.sqlite(":memory:")
            manager = config.create_database_manager()
        """
        engine = self.create_engine()
        return DatabaseManager(
            engine=engine,
            database_type=self.database_type,
            connection_string=self.connection_string,
            pooling=self.pooling
        )
