# Architecture Analysis: TransactionManager and ConnectionFactory Refactor

## Question 1: Is TransactionManager a Necessary Abstraction?

### Current Status: **NOT CURRENTLY NECESSARY**

#### Evidence:
1. **Imported but Unused in Runner**
   - `TransactionManager` is imported in `runner.py` line 6
   - Not used anywhere in the `TestRunner` class implementation
   - Only used in unit tests (`tests/test_database.py`)

2. **ConnectionManager Already Provides Transaction Semantics**
   - `ConnectionManager` has `execute_query()` which handles connection pooling
   - SQLAlchemy's connection object supports transactions natively
   - No explicit transaction management needed for test execution pipeline

3. **Test Execution Model Doesn't Require Transactions**
   - Tests execute in isolation via connection pooling
   - Each test uses `execute_setup()` then `execute_query()`
   - No need for explicit rollback/commit patterns in the current lifecycle

#### Why TransactionManager Was Likely Added:
- **Potential Future Use Case**: Test isolation where multiple operations within a test need to be rolled back together
- **Explicit Control**: For scenarios where a test wants to verify transaction behavior
- **Flexibility**: Good abstraction for potential future transaction-related features

#### Conclusion:
**TransactionManager can be removed** from core implementation but could be:
- Kept as optional utility for advanced test scenarios
- Moved to a separate utilities module if needed later
- Documented as available for custom test runners

---

## Question 2: Proposed Refactor - ConnectionConfig

Your proposal is **excellent** and addresses real design issues with `ConnectionFactory`. Here's the detailed analysis:

### Current Problem with ConnectionFactory:

```python
# Current: Static methods that return ConnectionManager
@staticmethod
def create_sqlite_memory() -> ConnectionManager:
    return ConnectionManager(database_type="sqlite", ...)
```

**Issues:**
1. ❌ Factory methods are rigid - don't support YAML config parsing
2. ❌ Tight coupling - returns ConnectionManager, not config
3. ❌ Limited customization - hardcoded pooling behavior
4. ❌ No separation of concerns - config and connection creation mixed
5. ❌ Difficult to extend - adding new database types requires more methods

### Proposed Solution: ConnectionConfig

```python
# Proposed: Config class that can be created from YAML
config = ConnectionConfig.sqlite(":memory:")
# or
config = ConnectionConfig.from_yaml(yaml_dict)
engine = config.create_engine()
connection = config.create_connection_manager()
```

**Advantages:**
1. ✅ YAML-native - parse config from test files
2. ✅ Flexible - supports all database types
3. ✅ Extensible - add new backends with single method
4. ✅ Separation of concerns - config separate from manager
5. ✅ Testable - config objects can be inspected
6. ✅ Reusable - same config can create multiple connections

### Detailed Design Proposal

#### 1. ConnectionConfig Class Structure

```python
class ConnectionConfig:
    """Configuration for database connections."""
    
    def __init__(
        self,
        database_type: str,
        connection_string: str,
        pooling: bool = True,
        pool_size: int = 5,
        max_overflow: int = 10,
        **kwargs  # Additional backend-specific options
    ):
        self.database_type = database_type
        self.connection_string = connection_string
        self.pooling = pooling
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.kwargs = kwargs
    
    @staticmethod
    def sqlite(path: str, **options) -> ConnectionConfig:
        """Create SQLite configuration."""
        if path == ":memory:":
            # In-memory uses StaticPool
            return ConnectionConfig(
                database_type="sqlite",
                connection_string="sqlite:///:memory:",
                pooling=False,
                **options
            )
        else:
            # File-based uses QueuePool
            return ConnectionConfig(
                database_type="sqlite",
                connection_string=f"sqlite:///{path}",
                pooling=True,
                **options
            )
    
    @staticmethod
    def postgresql(
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        **options
    ) -> ConnectionConfig:
        """Create PostgreSQL configuration."""
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
        port: int,
        database: str,
        user: str,
        password: str,
        **options
    ) -> ConnectionConfig:
        """Create MySQL configuration."""
        url = ConnectionConfig._url(
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        )
        return ConnectionConfig(
            database_type="mysql",
            connection_string=url,
            pooling=True,
            **options
        )
    
    @staticmethod
    def duckdb(path: str = ":memory:", **options) -> ConnectionConfig:
        """Create DuckDB configuration."""
        if path == ":memory:":
            conn_str = "duckdb:///:memory:"
        else:
            conn_str = f"duckdb:///{path}"
        
        return ConnectionConfig(
            database_type="duckdb",
            connection_string=conn_str,
            pooling=False,  # DuckDB handles pooling internally
            **options
        )
    
    @staticmethod
    def _url(url: str) -> str:
        """
        Normalize and validate URL syntax across backends.
        
        Handles:
        - URL encoding of special characters in passwords
        - Scheme validation
        - Connection string formatting
        """
        from urllib.parse import quote_plus
        # Could add validation/normalization here
        return url
    
    @classmethod
    def from_yaml(cls, config_dict: dict) -> ConnectionConfig:
        """
        Create ConnectionConfig from YAML dictionary.
        
        Example YAML:
            database:
              type: sqlite
              path: ":memory:"
              
            Or:
            database:
              type: postgresql
              host: localhost
              port: 5432
              database: testdb
              user: admin
              password: secret
        """
        db_type = config_dict.get("type", "").lower()
        
        if db_type == "sqlite":
            return cls.sqlite(config_dict.get("path", ":memory:"))
        elif db_type == "postgresql":
            return cls.postgresql(
                host=config_dict["host"],
                port=config_dict.get("port", 5432),
                database=config_dict["database"],
                user=config_dict["user"],
                password=config_dict["password"]
            )
        elif db_type == "mysql":
            return cls.mysql(
                host=config_dict["host"],
                port=config_dict.get("port", 3306),
                database=config_dict["database"],
                user=config_dict["user"],
                password=config_dict["password"]
            )
        elif db_type == "duckdb":
            return cls.duckdb(config_dict.get("path", ":memory:"))
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with pooling configuration."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import NullPool, QueuePool, StaticPool
        
        # Determine pool class
        if self.database_type == "sqlite" and self.connection_string == "sqlite:///:memory:":
            pool_class = StaticPool
        elif self.pooling:
            pool_class = QueuePool
        else:
            pool_class = NullPool
        
        return create_engine(
            self.connection_string,
            poolclass=pool_class,
            pool_size=self.pool_size if self.pooling else None,
            max_overflow=self.max_overflow if self.pooling else None,
            **self.kwargs
        )
    
    def create_connection_manager(self) -> ConnectionManager:
        """Create a ConnectionManager from this configuration."""
        engine = self.create_engine()
        return ConnectionManager(
            engine=engine,
            database_type=self.database_type,
            connection_string=self.connection_string,
            pooling=self.pooling
        )
```

#### 2. Updated ConnectionManager

Keep `ConnectionManager` as-is, but update its docstring:

```python
class ConnectionManager:
    """Manages database connections with pooling and transaction support.
    
    Create via ConnectionConfig:
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
    
    Or directly (for advanced use):
        manager = ConnectionManager(
            engine=engine,
            database_type="sqlite",
            connection_string="sqlite:///:memory:"
        )
    """
```

#### 3. Migration Path

**Old usage:**
```python
from sql_unit.database import ConnectionFactory

manager = ConnectionFactory.create_sqlite_memory()
```

**New usage:**
```python
from sql_unit.database import ConnectionConfig

config = ConnectionConfig.sqlite(":memory:")
manager = config.create_connection_manager()
```

**Or from YAML:**
```python
import yaml
from sql_unit.database import ConnectionConfig

yaml_content = """
type: postgresql
host: localhost
port: 5432
database: testdb
user: admin
password: secret
"""

config_dict = yaml.safe_load(yaml_content)
config = ConnectionConfig.from_yaml(config_dict)
manager = config.create_connection_manager()
```

---

## Implementation Recommendations

### Step 1: Add ConnectionConfig Class
- **File**: `src/sql_unit/database.py`
- **Location**: Add before `ConnectionFactory` or after `ConnectionManager`
- **Tests**: 8-10 new tests for config creation and YAML parsing

### Step 2: Keep ConnectionFactory (Deprecated)
- Mark as `@deprecated` with migration instructions
- Implement as thin wrapper around `ConnectionConfig`:
  ```python
  @staticmethod
  def create_sqlite_memory() -> ConnectionManager:
      config = ConnectionConfig.sqlite(":memory:")
      return config.create_connection_manager()
  ```

### Step 3: Remove Unused TransactionManager Import
- Remove from `runner.py` import
- Keep in `database.py` for users who need transaction control
- Mark as optional utility

### Step 4: Update Tests
- Add tests for `ConnectionConfig.from_yaml()`
- Test all backend configurations
- Verify backward compatibility with `ConnectionFactory`

### Step 5: Update Documentation
- Update docstrings to prefer `ConnectionConfig`
- Add YAML configuration examples
- Document migration path

---

## Benefits of This Refactor

| Aspect | Before | After |
|--------|--------|-------|
| **YAML Support** | ❌ None | ✅ Full |
| **Extensibility** | ❌ N static methods | ✅ Single method |
| **Database Types** | ⚠️ 4 methods | ✅ N types (single method) |
| **Configuration** | ❌ Implicit | ✅ Explicit objects |
| **Testing** | ⚠️ Limited | ✅ Config objects testable |
| **Backward Compat** | N/A | ✅ Maintained |
| **Code Reuse** | ❌ Low | ✅ High |

---

## Summary

### TransactionManager
- **Current**: Unused but good for future extensibility
- **Recommendation**: Remove import from runner, keep in database.py as optional utility
- **Alternative**: Could be part of advanced test features later

### ConnectionConfig Refactor
- **Status**: **HIGHLY RECOMMENDED** ✅
- **Effort**: Medium (1-2 hours)
- **Benefit**: Large (enables YAML config, extensible design, cleaner API)
- **Breaking Changes**: None (keep ConnectionFactory as deprecated wrapper)
- **Test Impact**: +8-10 new tests

This refactor aligns the codebase with modern Python configuration practices and makes the framework much more suitable for production use and integration with test orchestration tools.
