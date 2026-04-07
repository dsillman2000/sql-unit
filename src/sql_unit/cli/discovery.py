"""Test discovery and filtering for CLI."""

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Set

from sql_unit.parser import TestDiscoveryParser


@dataclass
class TestInfo:
    """Information about a discovered test."""

    name: str
    file_path: str
    directory: str


class TestDiscovery:
    """Discovers and indexes SQL unit tests."""

    def __init__(self, root_dir: str = ".", test_paths: list[str] | None = None):
        """Initialize discovery.
        
        Args:
            root_dir: Root directory for discovery (usually CWD)
            test_paths: Optional list of paths to limit discovery scope
        """
        self.root_dir = Path(root_dir).resolve()
        self.test_paths = (
            [Path(p).resolve() for p in test_paths] if test_paths else [self.root_dir]
        )
        self._tests: list[TestInfo] | None = None

    @property
    def tests(self) -> list[TestInfo]:
        """Lazy-load and cache discovered tests."""
        if self._tests is None:
            self._tests = self._discover()
        return self._tests

    def _discover(self) -> list[TestInfo]:
        """Discover all tests in configured paths."""
        tests = []

        for search_path in self.test_paths:
            if not search_path.exists():
                continue

            # Find all .sql files
            sql_files = list(search_path.glob("**/*.sql"))

            for file_path in sql_files:
                # Parse the file to get test definitions
                try:
                    test_file = TestDiscoveryParser.discover_and_parse(str(file_path))
                    if test_file and test_file.test_definitions:
                        for test_def in test_file.test_definitions:
                            tests.append(
                                TestInfo(
                                    name=test_def.name,
                                    file_path=str(file_path),
                                    directory=str(file_path.parent),
                                )
                            )
                except Exception:
                    # Skip files that can't be parsed
                    pass

        return tests

    def filter_by_selectors(self, selectors: list[str]) -> list[TestInfo]:
        """Filter tests by multiple selectors (union operation).
        
        Each selector can be:
        - A test name (exact match)
        - A glob pattern (e.g., "test_*" or "user_*")
        - A file path (e.g., "tests/auth_test.sql")
        - A directory path (e.g., "tests/integration/")
        
        Args:
            selectors: List of selector strings
            
        Returns:
            List of unique tests matching any selector
        """
        if not selectors:
            return self.tests

        matched: Set[str] = set()
        result = []

        for test in self.tests:
            for selector in selectors:
                if self._matches_selector(test, selector):
                    if test.name not in matched:
                        matched.add(test.name)
                        result.append(test)
                    break

        return result

    @staticmethod
    def _matches_selector(test: TestInfo, selector: str) -> bool:
        """Check if a test matches a selector.
        
        Args:
            test: Test info to check
            selector: Selector string
            
        Returns:
            True if test matches selector
        """
        selector_path = Path(selector)

        # Check if selector is a directory path
        if selector.endswith("/") or os.path.isdir(selector):
            test_dir = Path(test.directory)
            sel_dir = selector_path if selector.endswith("/") else selector_path.resolve()
            try:
                test_dir.relative_to(sel_dir)
                return True
            except ValueError:
                pass

        # Check if selector is a file path (ends with .sql or looks like a path)
        if selector.endswith(".sql"):
            # Try exact match
            if test.file_path == selector:
                return True
            # Try resolved path match
            try:
                if Path(test.file_path).resolve() == selector_path.resolve():
                    return True
            except (ValueError, OSError):
                pass

        # Check if selector is a glob pattern
        if "*" in selector or "?" in selector:
            return fnmatch.fnmatch(test.name, selector)

        # Check if selector is an exact test name
        return test.name == selector
