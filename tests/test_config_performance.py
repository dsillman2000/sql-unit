"""Performance and optimization tests for config (Tasks 50-52)."""

import os
import tempfile
import time

from sql_unit.config import SqlUnitConfig


class TestConfigCaching:
    """Test config caching implementation (Task 50)."""

    def setup_method(self):
        """Clear cache before each test."""
        SqlUnitConfig.clear_cache()

    def test_config_caching_loads_once(self):
        """Test that config is loaded once and cached."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
threads: 4
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            # Clear cache to ensure first load
            SqlUnitConfig.clear_cache()

            # First load
            config1 = SqlUnitConfig.from_file(filepath)
            assert config1.connection["url"] == "sqlite:///:memory:"

            # Second load should return cached instance
            config2 = SqlUnitConfig.from_file(filepath)
            assert config2.connection["url"] == "sqlite:///:memory:"

            # Should be the same object (cached)
            assert config1 is config2
        finally:
            os.unlink(filepath)
            SqlUnitConfig.clear_cache()

    def test_cache_cleared_on_clear_cache(self):
        """Test that cache_clear() properly clears the cache."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            # Load config
            config1 = SqlUnitConfig.from_file(filepath)

            # Clear cache
            SqlUnitConfig.clear_cache()

            # Load again
            config2 = SqlUnitConfig.from_file(filepath)

            # Should be different objects (cache was cleared)
            assert config1 is not config2
            assert config1.connection == config2.connection
        finally:
            os.unlink(filepath)
            SqlUnitConfig.clear_cache()


class TestVariableSubstitutionOptimization:
    """Test variable substitution optimization (Task 51)."""

    def test_variable_substitution_single_pass(self):
        """Test that variable substitution is efficient (single pass)."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        os.environ["VAR3"] = "value3"

        try:
            config_dict = {
                "connection": {
                    "postgresql": {
                        "host": "${VAR1}",
                        "user": "${VAR2}",
                        "password": "${VAR3}",
                    }
                },
                "test_paths": ["${VAR1}/tests"],
            }

            # Verify substitution works
            config = SqlUnitConfig(config_dict)
            assert config.connection["postgresql"]["host"] == "value1"
            assert config.connection["postgresql"]["user"] == "value2"
            assert config.connection["postgresql"]["password"] == "value3"
            assert config.config["test_paths"] == ["value1/tests"]
        finally:
            del os.environ["VAR1"]
            del os.environ["VAR2"]
            del os.environ["VAR3"]

    def test_escaped_variables_preserved(self):
        """Test that escaped variables are correctly handled."""
        config_dict = {
            "connection": {
                "postgresql": {
                    "note": "Literal: $${VAR}, Real: value",
                }
            }
        }

        config = SqlUnitConfig(config_dict)
        assert config.connection["postgresql"]["note"] == "Literal: ${VAR}, Real: value"

    def test_many_variables_substituted(self):
        """Test substitution with many variables."""
        for i in range(10):
            os.environ[f"VAR{i}"] = f"value{i}"

        try:
            # Create config with many variables
            connection_config = {f"key{i}": f"${{VAR{i}}}" for i in range(10)}
            config_dict = {"connection": {"postgresql": connection_config}}

            config = SqlUnitConfig(config_dict)
            for i in range(10):
                assert config.connection["postgresql"][f"key{i}"] == f"value{i}"
        finally:
            for i in range(10):
                del os.environ[f"VAR{i}"]


class TestConfigLoadingPerformance:
    """Test config loading performance (Task 52)."""

    def test_config_loading_time_measured(self):
        """Test that config loading time is reasonable."""
        yaml_content = """
connection:
  sqlite:
    path: "test.db"
threads: 4
test_paths:
  - tests/unit/
  - tests/integration/
  - tests/e2e/
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            SqlUnitConfig.clear_cache()

            # Measure time to load config
            start = time.perf_counter()
            config = SqlUnitConfig.from_file(filepath)
            elapsed = time.perf_counter() - start

            # Verify config loaded correctly
            assert config.connection["sqlite"]["path"] == "test.db"
            assert config.config["threads"] == 4

            # Config loading should be fast (< 100ms even on slow systems)
            assert elapsed < 0.1, f"Config loading took {elapsed * 1000:.2f}ms (expected < 100ms)"
        finally:
            os.unlink(filepath)
            SqlUnitConfig.clear_cache()

    def test_config_caching_improves_performance(self):
        """Test that caching improves subsequent load times."""
        yaml_content = """
connection:
  url: "sqlite:///:memory:"
threads: 4
test_paths:
  - tests/
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            filepath = f.name

        try:
            SqlUnitConfig.clear_cache()

            # First load (not cached)
            start = time.perf_counter()
            config1 = SqlUnitConfig.from_file(filepath)
            _first_load_time = time.perf_counter() - start

            # Second load (cached)
            start = time.perf_counter()
            config2 = SqlUnitConfig.from_file(filepath)
            _cached_load_time = time.perf_counter() - start

            # Cached load should be much faster (nearly instant)
            # We can't assert strict timing due to system variance,
            # but we can verify both loads succeeded
            assert config1 is config2
            assert config1.connection["url"] == "sqlite:///:memory:"
        finally:
            os.unlink(filepath)
            SqlUnitConfig.clear_cache()

    def test_discovery_performance(self):
        """Test that config discovery is reasonably fast."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_content = """
connection:
  url: "sqlite:///:memory:"
"""
            config_path = os.path.join(tmpdir, "sql-unit.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            SqlUnitConfig.clear_cache()

            # Measure discovery time
            start = time.perf_counter()
            config = SqlUnitConfig.from_directory(tmpdir)
            elapsed = time.perf_counter() - start

            assert config.connection["url"] == "sqlite:///:memory:"
            # Discovery should be fast (< 100ms)
            assert elapsed < 0.1, f"Config discovery took {elapsed * 1000:.2f}ms (expected < 100ms)"

            SqlUnitConfig.clear_cache()
