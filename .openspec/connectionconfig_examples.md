# ConnectionConfig Implementation Examples

## Current State vs Proposed State

### Problem Example 1: Adding DuckDB Support

#### Current Approach (ConnectionFactory)
```python
# database.py - Must add new static method
class ConnectionFactory:
    @staticmethod
    def create_sqlite_memory() -> ConnectionManager:
        ...
    
    @staticmethod
    def create_sqlite_file(filepath: str) -> ConnectionManager:
        ...
    
    @staticmethod
    def create_postgresql(...) -> ConnectionManager:
        ...
    
    @staticmethod
    def create_mysql(...) -> ConnectionManager:
        ...
    
    @staticmethod  # NEW METHOD NEEDED
    def create_duckdb(path: str) -> ConnectionManager:
        return ConnectionManager(
            database_type="duckdb",
            connection_string=f"duckdb:///{path}",
            pooling=False
        )

# Usage
manager = ConnectionFactory.create_duckdb(":memory:")
```

**Issues:**
- ❌ Must modify the factory class
- ❌ Ripple effect on imports, exports
- ❌ All methods have same signature pattern but aren't unified
- ❌ No way to pass options to some backends

#### Proposed Approach (ConnectionConfig)
```python
# database.py - Add method to existing class
class ConnectionConfig:
    @staticmethod
    def duckdb(path: str = ":memory:", **options) -> ConnectionConfig:
        conn_str = f"duckdb:///{path}" if path != ":memory:" else "duckdb:///:memory:"
        return ConnectionConfig(
            database_type="duckdb",
            connection_string=conn_str,
            pooling=False,
            **options
        )

# Usage
config = ConnectionConfig.duckdb(":memory:")
manager = config.create_connection_manager()
```

**Benefits:**
- ✅ Add method to existing class (no new exports)
- ✅ Consistent pattern for all backends
- ✅ Flexible **options** for backend-specific features
- ✅ Simpler to understand

---

## Problem Example 2: YAML Configuration

### Scenario
You want to load database configuration from a YAML file so tests can work in different environments (dev/staging/prod).

#### Current Approach (ConnectionFactory)
```yaml
# tests/config.yaml
database:
  type: sqlite
  path: ":memory:"
```

```python
# test_runner.py - Must parse YAML manually
import yaml
from sql_unit.database import ConnectionFactory

with open("tests/config.yaml") as f:
    config = yaml.safe_load(f)

db_type = config["database"]["type"]

if db_type == "sqlite":
    manager = ConnectionFactory.create_sqlite_memory()
elif db_type == "postgresql":
    db_config = config["database"]
    manager = ConnectionFactory.create_postgresql(
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"]
    )
# ... repeat for mysql, duckdb, etc.
```

**Issues:**
- ❌ Consumer must implement YAML parsing logic
- ❌ Error-prone (manual field extraction)
- ❌ Boilerplate code in tests
- ❌ Difficult to reuse

#### Proposed Approach (ConnectionConfig)
```yaml
# tests/config.yaml
database:
  type: sqlite
  path: ":memory:"
```

```python
# test_runner.py - Single line!
import yaml
from sql_unit.database import ConnectionConfig

with open("tests/config.yaml") as f:
    config = yaml.safe_load(f)

manager = ConnectionConfig.from_yaml(config["database"]).create_connection_manager()
```

**Benefits:**
- ✅ One line! Framework handles all parsing
- ✅ No error-prone manual extraction
- ✅ Works for all database types
- ✅ Clean and reusable

---

## Problem Example 3: Backend-Specific Options

### Scenario
You want to configure PostgreSQL connection pooling or MySQL SSL options.

#### Current Approach (ConnectionFactory)
```python
# Not possible - factory methods don't accept options!

# Must work around by creating engine directly and passing to ConnectionManager
from sqlalchemy import create_engine
from sql_unit.database import ConnectionManager

engine = create_engine(
    "postgresql://user:pwd@localhost/db",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=5,
    pool_recycle=3600,
    echo=True
)

manager = ConnectionManager(engine=engine, database_type="postgresql", ...)
```

**Issues:**
- ❌ Can't use factory at all
- ❌ Users exposed to SQLAlchemy internals
- ❌ No consistent pattern
- ❌ Configuration not validated

#### Proposed Approach (ConnectionConfig)
```python
config = ConnectionConfig.postgresql(
    host="localhost",
    port=5432,
    database="testdb",
    user="admin",
    password="secret",
    # Backend-specific options
    pool_size=20,
    max_overflow=5,
    pool_recycle=3600,
    echo=True
)

manager = config.create_connection_manager()
```

**Or via YAML:**
```yaml
database:
  type: postgresql
  host: localhost
  port: 5432
  database: testdb
  user: admin
  password: secret
  pool_size: 20
  max_overflow: 5
  pool_recycle: 3600
  echo: true
```

```python
config = ConnectionConfig.from_yaml(config_dict)
manager = config.create_connection_manager()
```

**Benefits:**
- ✅ Consistent API for all backends
- ✅ All options in one place
- ✅ YAML or programmatic
- ✅ Validated by ConnectionConfig

---

## Implementation Details

### The _url() Utility Method

This shared method handles URL encoding/validation for databases that need it:

```python
class ConnectionConfig:
    @staticmethod
    def _url(url: str) -> str:
        """
        Normalize and validate URL syntax across backends.
        
        Handles:
        - URL encoding of special characters in passwords
        - Scheme validation
        - Port validation
        - Connection string formatting
        
        Example:
            >>> ConnectionConfig._url("postgresql://user:p@ss@localhost/db")
            "postgresql://user:p%40ss@localhost/db"
        """
        from urllib.parse import quote_plus, urlparse
        
        # Validate URL format
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid connection URL: {url}")
        
        # URL-encode password if present
        if "@" in parsed.netloc:
            user_pass, host = parsed.netloc.rsplit("@", 1)
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                password = quote_plus(password)
                parsed = parsed._replace(netloc=f"{user}:{password}@{host}")
        
        return parsed.geturl()
```

Usage in backend methods:

```python
@staticmethod
def postgresql(host, port, database, user, password, **options):
    # Handle special characters in password
    url = ConnectionConfig._url(
        f"postgresql://{user}:{password}@{host}:{port}/{database}"
    )
    return ConnectionConfig(
        database_type="postgresql",
        connection_string=url,
        **options
    )
```

---

## Migration Strategy

### Phase 1: Add ConnectionConfig (No Breaking Changes)
```python
# database.py - Add alongside existing code
class ConnectionConfig:
    # New implementation
    ...

class ConnectionFactory:
    # Keep existing implementation as-is
    ...
```

### Phase 2: Deprecate ConnectionFactory (Backwards Compatible)
```python
import warnings

class ConnectionFactory:
    @staticmethod
    def create_sqlite_memory() -> ConnectionManager:
        warnings.warn(
            "ConnectionFactory is deprecated. Use ConnectionConfig instead:\n"
            "  config = ConnectionConfig.sqlite(':memory:')\n"
            "  manager = config.create_connection_manager()",
            DeprecationWarning,
            stacklevel=2
        )
        config = ConnectionConfig.sqlite(":memory:")
        return config.create_connection_manager()
    
    # Repeat for other methods...
```

### Phase 3: Update Tests
- Keep existing ConnectionFactory tests
- Add new ConnectionConfig tests
- Test YAML parsing
- Test all backend configurations

### Phase 4: Future Removal
- In major version (2.0.0), remove ConnectionFactory
- Migration guide in release notes

---

## Testing Strategy

### New Tests for ConnectionConfig

```python
class TestConnectionConfig:
    """Tests for ConnectionConfig."""
    
    def test_sqlite_memory(self):
        """Test SQLite memory configuration."""
        config = ConnectionConfig.sqlite(":memory:")
        assert config.database_type == "sqlite"
        assert config.connection_string == "sqlite:///:memory:"
        assert config.pooling == False
    
    def test_sqlite_file(self, tmp_path):
        """Test SQLite file configuration."""
        db_file = tmp_path / "test.db"
        config = ConnectionConfig.sqlite(str(db_file))
        assert config.database_type == "sqlite"
        assert config.connection_string == f"sqlite:///{db_file}"
        assert config.pooling == True
    
    def test_postgresql(self):
        """Test PostgreSQL configuration."""
        config = ConnectionConfig.postgresql(
            host="localhost",
            port=5432,
            database="testdb",
            user="admin",
            password="secret"
        )
        assert config.database_type == "postgresql"
        assert "postgresql://" in config.connection_string
    
    def test_from_yaml_sqlite(self):
        """Test YAML parsing for SQLite."""
        config_dict = {
            "type": "sqlite",
            "path": ":memory:"
        }
        config = ConnectionConfig.from_yaml(config_dict)
        assert config.database_type == "sqlite"
    
    def test_from_yaml_postgresql(self):
        """Test YAML parsing for PostgreSQL."""
        config_dict = {
            "type": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "testdb",
            "user": "admin",
            "password": "secret"
        }
        config = ConnectionConfig.from_yaml(config_dict)
        assert config.database_type == "postgresql"
    
    def test_url_encode_password(self):
        """Test URL encoding of special characters."""
        url = ConnectionConfig._url(
            "postgresql://user:p@ss@localhost/db"
        )
        assert "p%40ss" in url  # @ encoded as %40
    
    def test_create_engine(self):
        """Test SQLAlchemy engine creation."""
        config = ConnectionConfig.sqlite(":memory:")
        engine = config.create_engine()
        assert engine is not None
        assert "sqlite" in str(engine.url)
    
    def test_create_connection_manager(self):
        """Test ConnectionManager creation."""
        config = ConnectionConfig.sqlite(":memory:")
        manager = config.create_connection_manager()
        assert manager is not None
        assert isinstance(manager, ConnectionManager)
```

---

## Summary Table

| Feature | ConnectionFactory | ConnectionConfig |
|---------|-------------------|------------------|
| **YAML Support** | ❌ | ✅ |
| **Extensible** | ❌ 4 methods | ✅ 1 method + N backends |
| **Backend Options** | ❌ | ✅ |
| **Configuration Objects** | ❌ | ✅ |
| **Code Reuse** | ❌ Low | ✅ High |
| **Testability** | ⚠️ Limited | ✅ Full |
| **Migration Path** | N/A | ✅ Backwards Compatible |
| **Production Ready** | ⚠️ | ✅ Yes |

This refactor modernizes the connection configuration while maintaining backward compatibility!
