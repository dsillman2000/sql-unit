"""Database connection management using SQLAlchemy."""

from contextlib import contextmanager
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from .exceptions import ExecutionError


class ConnectionManager:
    """Manages database connections with pooling and transaction support."""
    
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
            database_type: Type of database (sqlite, postgresql, mysql)
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
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool."""
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()
    
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
            with self.get_connection() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                # Convert Row objects to dicts
                return [dict(row._mapping) for row in rows]
        except Exception as e:
            raise ExecutionError(f"Query execution failed: {str(e)}\nSQL: {sql}")
    
    def execute_setup(self, setup_sql: str) -> None:
        """
        Execute setup SQL (e.g., CREATE TABLE, CREATE CTE).
        
        Args:
            setup_sql: SQL to execute for setup
            
        Raises:
            ExecutionError: If setup fails
        """
        try:
            with self.get_connection() as conn:
                # Execute the SQL statement via SQLAlchemy text()
                conn.execute(text(setup_sql))
                conn.commit()
        except Exception as e:
            raise ExecutionError(f"Setup execution failed: {str(e)}\nSQL: {setup_sql}")


class TransactionManager:
    """Manages database transactions for test isolation."""
    
    def __init__(self, engine: Engine):
        """
        Initialize transaction manager.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        self.connection = None
        self.transaction = None
    
    def begin(self) -> None:
        """Begin a new transaction."""
        try:
            self.connection = self.engine.connect()
            self.transaction = self.connection.begin()
        except Exception as e:
            raise ExecutionError(f"Failed to begin transaction: {str(e)}")
    
    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            if self.transaction:
                self.transaction.commit()
        except Exception as e:
            raise ExecutionError(f"Failed to commit transaction: {str(e)}")
        finally:
            self._cleanup()
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            if self.transaction:
                self.transaction.rollback()
        except Exception as e:
            raise ExecutionError(f"Failed to rollback transaction: {str(e)}")
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """Clean up connection and transaction."""
        if self.connection:
            self.connection.close()
        self.transaction = None
        self.connection = None
    
    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute query within transaction.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            List of result rows as dictionaries (empty for INSERT/UPDATE/DELETE)
            
        Raises:
            ExecutionError: If execution fails
        """
        if not self.connection:
            raise ExecutionError("No active transaction")
        
        try:
            result = self.connection.execute(text(sql))
            # Only fetch rows if the result has rows (SELECT queries)
            # INSERT/UPDATE/DELETE queries return no rows
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row._mapping) for row in rows]
            return []
        except Exception as e:
            raise ExecutionError(f"Query execution failed: {str(e)}\nSQL: {sql}")
    
    def __enter__(self):
        """Context manager entry."""
        self.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()


class ConnectionFactory:
    """Factory for creating database connections."""
    
    @staticmethod
    def create_sqlite_memory() -> ConnectionManager:
        """Create in-memory SQLite database."""
        return ConnectionManager(
            database_type="sqlite",
            connection_string="sqlite:///:memory:",
            pooling=False
        )
    
    @staticmethod
    def create_sqlite_file(filepath: str) -> ConnectionManager:
        """Create file-based SQLite database."""
        return ConnectionManager(
            database_type="sqlite",
            connection_string=f"sqlite:///{filepath}",
            pooling=True
        )
    
    @staticmethod
    def create_postgresql(
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> ConnectionManager:
        """Create PostgreSQL connection."""
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        return ConnectionManager(
            database_type="postgresql",
            connection_string=conn_str,
            pooling=True
        )
    
    @staticmethod
    def create_mysql(
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ) -> ConnectionManager:
        """Create MySQL connection."""
        conn_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        return ConnectionManager(
            database_type="mysql",
            connection_string=conn_str,
            pooling=True
        )
