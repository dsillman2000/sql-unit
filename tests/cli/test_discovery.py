"""Tests for CLI discovery module."""

import tempfile

from sql_unit.cli.discovery import TestDiscovery, TestInfo


class TestTestDiscovery:
    """Tests for TestDiscovery class."""

    def test_discover_no_tests(self):
        """Test discovery with no test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            discovery = TestDiscovery(tmpdir)
            tests = discovery.tests
            assert tests == []

    def test_filter_by_name(self):
        """Test filtering by exact name."""
        tests = [
            TestInfo(name="test_user_login", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_user_logout", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_admin_login", file_path="tests/admin_test.sql", directory="tests"),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors(["test_user_login"])
        assert len(filtered) == 1
        assert filtered[0].name == "test_user_login"

    def test_filter_by_glob_pattern(self):
        """Test filtering by glob pattern."""
        tests = [
            TestInfo(name="test_user_login", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_user_logout", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_admin_login", file_path="tests/admin_test.sql", directory="tests"),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors(["test_user_*"])
        assert len(filtered) == 2
        assert all(t.name.startswith("test_user_") for t in filtered)

    def test_filter_by_file_path(self):
        """Test filtering by file path."""
        tests = [
            TestInfo(name="test_user_login", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_user_logout", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_admin_login", file_path="tests/admin_test.sql", directory="tests"),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors(["tests/auth_test.sql"])
        assert len(filtered) == 2
        assert all(t.file_path == "tests/auth_test.sql" for t in filtered)

    def test_filter_by_directory(self):
        """Test filtering by directory."""
        tests = [
            TestInfo(
                name="test_user_login", file_path="tests/auth/user_test.sql", directory="tests/auth"
            ),
            TestInfo(
                name="test_admin_login",
                file_path="tests/admin/admin_test.sql",
                directory="tests/admin",
            ),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors(["tests/auth/"])
        assert len(filtered) == 1
        assert filtered[0].directory == "tests/auth"

    def test_filter_union_multiple_selectors(self):
        """Test union of multiple selectors."""
        tests = [
            TestInfo(name="test_user_login", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_user_logout", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_admin_login", file_path="tests/admin_test.sql", directory="tests"),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors(["test_user_login", "test_admin_*"])
        assert len(filtered) == 2
        names = {t.name for t in filtered}
        assert names == {"test_user_login", "test_admin_login"}

    def test_filter_no_selectors_returns_all(self):
        """Test with no selectors returns all tests."""
        tests = [
            TestInfo(name="test_user_login", file_path="tests/auth_test.sql", directory="tests"),
            TestInfo(name="test_admin_login", file_path="tests/admin_test.sql", directory="tests"),
        ]

        discovery = TestDiscovery()
        discovery._tests = tests

        filtered = discovery.filter_by_selectors([])
        assert len(filtered) == 2
