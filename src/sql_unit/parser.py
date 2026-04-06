"""Parser for SQL block comments containing sql-unit test definitions."""

import os
import re
import tempfile
import textwrap
from pathlib import Path
from typing import Any

import ruamel.yaml
import yaml_reference

from sql_unit.core.exceptions import ParserError
from sql_unit.core.models import TestDefinition
from sql_unit.statement import StatementValidator


class YamlReferenceLoader:
    """Loads YAML content with cross-file references support.

    Uses yaml_reference library to resolve !reference and !reference-all tags
    by creating a temporary YAML file in the SQL file's directory, allowing
    relative path resolution to work correctly.

    Implementation Strategy:
    - The yaml_reference library requires actual files on disk to resolve relative paths
    - We create a temporary YAML file in the same directory as the SQL file
    - This ensures that relative paths in !reference tags (e.g., "tests.yaml") resolve
      relative to the SQL file's directory, not the current working directory
    - The temporary file is cleaned up immediately after yaml_reference loads the content
    - This approach handles the key constraint that yaml_reference cannot work with
      in-memory YAML strings for path resolution

    Example:
        SQL file: /project/queries/adult_users.sql
        Reference: !reference-all "tests.yaml"

        Flow:
        1. Create temp file: /project/queries/tmpXXXXXX.yaml (with YAML content)
        2. yaml_reference resolves "tests.yaml" relative to /project/queries/
        3. Temp file is deleted, result returned

    Reference tag behavior:
    - !reference "file.yaml": Include single YAML document from file
    - !reference-all "file.yaml": Include all documents from multi-document YAML file
    - Missing files: yaml_reference returns empty list (no error)
    - Invalid YAML in reference: ParserError raised with context
    """

    @staticmethod
    def load_with_references(
        yaml_text: str,
        sql_file_path: str,
        line_number: int,
        project_directory: str = None,
        allow_paths: list[str] = None,
    ) -> Any:
        """
        Load YAML content, resolving any !reference tags.

        Args:
            yaml_text: YAML content with potential !reference tags
            sql_file_path: Path to the SQL file (for context and relative paths)
            line_number: Line number in SQL file (for error reporting)
            project_directory: Project root directory for allow_paths resolution (optional)
            allow_paths: List of allowed paths relative to project_directory (optional).
                         If provided, yaml_reference will enforce these constraints.
                         Paths outside allow_paths will raise an error.

        Returns:
            Parsed YAML content with all references resolved.
            If YAML contains !reference-all tags pointing to multi-doc files,
            returns a list of all documents. Otherwise returns parsed content.

        Raises:
            ParserError: If reference resolution fails, path is outside allow_paths, or YAML is invalid
        """
        # Determine the directory of the SQL file for relative path resolution
        sql_dir = os.path.dirname(os.path.abspath(sql_file_path))

        # If project_directory provided, convert allow_paths to absolute paths
        resolved_allow_paths = None
        if project_directory and allow_paths:
            project_dir_abs = os.path.abspath(project_directory)
            resolved_allow_paths = [
                os.path.abspath(os.path.join(project_dir_abs, path)) for path in allow_paths
            ]

        # Create a temporary YAML file in the same directory as the SQL file
        # This ensures yaml_reference can resolve relative paths correctly
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", dir=sql_dir, delete=False
            ) as tmp_file:
                tmp_file.write(yaml_text)
                tmp_file.flush()
                tmp_path = tmp_file.name

            try:
                # Load YAML with reference resolution
                # If allow_paths provided, yaml_reference will enforce path constraints
                if resolved_allow_paths:
                    result = yaml_reference.load_yaml_with_references(
                        tmp_path, allow_paths=resolved_allow_paths
                    )
                else:
                    result = yaml_reference.load_yaml_with_references(tmp_path)
                return result
            finally:
                # Clean up temp file immediately after loading
                try:
                    os.unlink(tmp_path)
                except OSError:
                    # Ignore cleanup errors; temp file will be cleaned by OS eventually
                    pass

        except (ValueError, Exception) as e:
            # Catch ValueError from yaml_reference (e.g., absolute paths, circular references)
            # and any other exceptions that might occur during reference loading
            raise ParserError(
                f"Failed to resolve YAML references: {str(e)}",
                filepath=sql_file_path,
                line_number=line_number,
            )


class SqlBlockCommentParser:
    """Parses SQL block comments containing sql-unit test definitions."""

    # Pattern to find /* #! sql-unit ... */ blocks
    BLOCK_COMMENT_PATTERN = re.compile(r"/\*\s*#!\s*sql-unit\s+(.*?)\*/", re.DOTALL)

    # Pattern to find SQL statements (basic, matches SELECT/INSERT/UPDATE/DELETE/WITH)
    SQL_STATEMENT_PATTERN = re.compile(
        r"^\s*(WITH|SELECT|INSERT|UPDATE|DELETE)\b", re.MULTILINE | re.IGNORECASE
    )

    @classmethod
    def extract_comment_blocks(cls, sql_content: str) -> list[tuple[str, int]]:
        """
        Extract all sql-unit comment blocks from SQL content.

        Args:
            sql_content: SQL file content as string

        Returns:
            List of tuples: (comment_text, line_number)
        """
        blocks = []
        for match in cls.BLOCK_COMMENT_PATTERN.finditer(sql_content):
            comment_text = match.group(1)
            # Calculate line number
            line_number = sql_content[: match.start()].count("\n") + 1
            blocks.append((comment_text, line_number))
        return blocks

    @classmethod
    def parse_yaml_content(
        cls,
        comment_text: str,
        line_number: int,
        filepath: str = None,
        project_directory: str = None,
        allow_paths: list[str] = None,
    ) -> Any:
        """
        Parse YAML content from comment block, handling multi-doc, references, and sequences.

        Supports three YAML formats:
        1. Single test definition: name, given, expect
        2. Multi-document: Multiple test definitions separated by --- at start of line
        3. Referenced tests: !reference or !reference-all tags pointing to external files

        Args:
            comment_text: Content inside the /* #! sql-unit ... */ block
            line_number: Line number of the block for error reporting
            filepath: Path to SQL file (optional, but REQUIRED when !reference tags are present)
                       When provided, used to resolve relative paths in !reference tags
            project_directory: Project root directory for allow_paths resolution (optional)
                              If provided, passed to YamlReferenceLoader for path constraint enforcement
            allow_paths: List of allowed paths relative to project_directory (optional)
                        If provided, yaml_reference will enforce path constraints

        Returns:
            List of test definitions (dicts). Each test should have 'name', 'given', 'expect' keys.

        Raises:
            ParserError: If YAML syntax is invalid, filepath missing for !reference, or reference resolution fails

        Examples:
            # Single test definition
            >>> parse_yaml_content("name: test1\\ngiven: {}\\nexpect: {}", 1)
            [{'name': 'test1', 'given': {}, 'expect': {}}]

            # Multi-document with ---
            >>> yaml = "name: test1\\ngiven: {}\\nexpect: {}\\n---\\nname: test2\\ngiven: {}\\nexpect: {}"
            >>> parse_yaml_content(yaml, 1)
            [{'name': 'test1', ...}, {'name': 'test2', ...}]

            # References to external YAML file (requires filepath)
            >>> parse_yaml_content('!reference-all "tests.yaml"', 1, filepath="/path/to/query.sql")
            [{'name': 'test1', ...}, {'name': 'test2', ...}]  # from tests.yaml
        """
        try:
            # Strip and dedent to fix indentation issues
            comment_text = textwrap.dedent(comment_text).strip()

            # Check if content contains !reference tags
            if "!reference" in comment_text:
                if not filepath:
                    raise ParserError(
                        "YAML references (!reference) require filepath context",
                        line_number=line_number,
                    )
                # Use yaml_reference to resolve references
                parsed = YamlReferenceLoader.load_with_references(
                    comment_text,
                    filepath,
                    line_number,
                    project_directory=project_directory,
                    allow_paths=allow_paths,
                )
            else:
                # Use standard YAML parsing
                yaml = ruamel.yaml.YAML(typ="safe")

                # Check for multi-doc syntax (---) at start of line
                if re.search(r"^---\s*$", comment_text, re.MULTILINE):
                    docs = []
                    for doc in yaml.load_all(comment_text):
                        if doc:
                            docs.append(doc)
                    parsed = docs if docs else []
                else:
                    # Parse as single YAML document
                    parsed = yaml.load(comment_text)

            # Normalize to list format
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                raise ParserError(
                    f"Expected dict or list in YAML, got {type(parsed).__name__}",
                    line_number=line_number,
                )

        except ParserError:
            raise
        except ruamel.yaml.YAMLError as e:
            raise ParserError(f"Invalid YAML syntax: {str(e)}", line_number=line_number)

    @classmethod
    def build_test_definitions(
        cls, parsed_yaml: Any, filepath: str, comment_line: int
    ) -> list[TestDefinition]:
        """
        Convert parsed YAML to TestDefinition objects.

        Args:
            parsed_yaml: Parsed YAML content (list of dicts)
            filepath: Source file path
            comment_line: Line number of comment block

        Returns:
            List of TestDefinition objects
        """
        if not isinstance(parsed_yaml, list):
            raise ParserError(
                "Expected list of test definitions", filepath=filepath, line_number=comment_line
            )

        tests = []
        for idx, test_dict in enumerate(parsed_yaml):
            if not isinstance(test_dict, dict):
                raise ParserError(
                    f"Test definition {idx} is not a dict: {type(test_dict).__name__}",
                    filepath=filepath,
                    line_number=comment_line,
                )

            # Extract required fields
            name = test_dict.get("name")
            if not name:
                # Auto-generate name for unnamed tests
                name = f"test_{idx + 1}"

            # Create TestDefinition
            test = TestDefinition(
                name=name,
                given=test_dict.get("given", {}),
                expect=test_dict.get("expect", {}),
                description=test_dict.get("description"),
                filepath=filepath,
                line_number=comment_line,
            )
            tests.append(test)

        return tests

    @classmethod
    def extract_following_statement(
        cls, sql_content: str, comment_end_pos: int
    ) -> tuple[str | None, int | None]:
        """
        Find the SQL statement immediately following a comment block.

        Args:
            sql_content: Full SQL file content
            comment_end_pos: Position where comment block ends

        Returns:
            Tuple of (statement_text, line_number) or (None, None) if no statement found
        """
        # Find the next non-whitespace character after comment
        remaining = sql_content[comment_end_pos:]
        match = re.search(r"\S", remaining)

        if not match:
            return None, None

        start_pos = comment_end_pos + match.start()

        # Find the statement type
        from_pos = start_pos
        statement_match = cls.SQL_STATEMENT_PATTERN.search(remaining[match.start() :])

        if not statement_match:
            return None, None

        # Extract statement (from first SELECT/INSERT/UPDATE/DELETE/WITH until semicolon)
        actual_start = from_pos + statement_match.start()

        # Find the semicolon
        semicolon_pos = sql_content.find(";", actual_start)
        if semicolon_pos == -1:
            # No semicolon found, take rest of content
            statement = sql_content[actual_start:].strip()
        else:
            statement = sql_content[actual_start:semicolon_pos].strip()

        # Calculate line number
        line_number = sql_content[:actual_start].count("\n") + 1

        return statement, line_number


class TestDiscoveryParser:
    """Discovers and parses tests from SQL files and directories."""

    @staticmethod
    def find_project_root(start_path: str) -> str:
        """
        Find the project root by walking up the directory tree to locate sql-unit.yaml.

        Args:
            start_path: Starting directory or file path to search from

        Returns:
            Path to the directory containing sql-unit.yaml

        Raises:
            ParserError: If sql-unit.yaml is not found in start_path or any parent directory
        """
        # If start_path is a file, get its directory
        search_dir = os.path.dirname(os.path.abspath(start_path))
        if os.path.isfile(start_path):
            search_dir = os.path.dirname(os.path.abspath(start_path))
        else:
            search_dir = os.path.abspath(start_path)

        # Walk up the directory tree
        while True:
            config_file = os.path.join(search_dir, "sql-unit.yaml")
            if os.path.isfile(config_file):
                return search_dir

            # Move to parent directory
            parent = os.path.dirname(search_dir)
            if parent == search_dir:
                # Reached filesystem root without finding sql-unit.yaml
                raise ParserError(
                    f"sql-unit.yaml not found in {os.path.abspath(start_path)} or any parent directory"
                )
            search_dir = parent

    @classmethod
    def parse_file(cls, filepath: str, project_directory: str = None) -> list[TestDefinition]:
        """
        Parse all tests from a SQL file.

        Args:
            filepath: Path to SQL file
            project_directory: Project root directory (optional). If not provided, will be auto-detected
                              from sql-unit.yaml. Required for YAML reference path constraint enforcement.

        Returns:
            List of TestDefinition objects found in file

        Raises:
            ParserError: If file cannot be read, parsing fails, or sql-unit.yaml is not found
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()
        except Exception as e:
            raise ParserError(f"Cannot read file: {str(e)}", filepath=filepath)

        # Auto-detect project_directory if not provided
        if not project_directory:
            project_directory = cls.find_project_root(filepath)

        # Extract all comment blocks with their positions
        all_blocks = []
        for match in SqlBlockCommentParser.BLOCK_COMMENT_PATTERN.finditer(sql_content):
            comment_text = match.group(1)
            line_number = sql_content[: match.start()].count("\n") + 1
            all_blocks.append((comment_text, line_number, match.end()))

        all_tests = []
        test_names_in_file = set()

        for comment_text, line_number, comment_end_pos in all_blocks:
            # Parse YAML with filepath context and project_directory for reference resolution
            parsed = SqlBlockCommentParser.parse_yaml_content(
                comment_text, line_number, filepath, project_directory=project_directory
            )

            # Build test definitions
            tests = SqlBlockCommentParser.build_test_definitions(parsed, filepath, line_number)

            # Find the following SQL statement and validate test binding
            following_statement, _ = SqlBlockCommentParser.extract_following_statement(
                sql_content, comment_end_pos
            )
            for test in tests:
                StatementValidator.validate_test_binding(test, following_statement, filepath)

            # Check for duplicate names within file
            for test in tests:
                if test.name in test_names_in_file:
                    raise ParserError(
                        f"Duplicate test name '{test.name}' in file",
                        filepath=filepath,
                        line_number=test.line_number,
                    )
                test_names_in_file.add(test.name)

            all_tests.extend(tests)

        return all_tests

    @classmethod
    def discover_files(cls, directory: str, pattern: str = "*.sql") -> list[str]:
        """
        Discover SQL files in directory matching pattern.

        Args:
            directory: Directory to search
            pattern: Glob pattern for files (default: "*.sql")

        Returns:
            List of file paths matching pattern
        """
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ParserError(f"Directory not found: {directory}")

        # Find all matching files recursively
        matching_files = list(dir_path.rglob(pattern))
        return sorted(str(f) for f in matching_files)

    @classmethod
    def discover_and_parse(
        cls, directory: str, pattern: str = "*.sql"
    ) -> dict[str, list[TestDefinition]]:
        """
        Discover and parse all tests in directory.

        Requires sql-unit.yaml to exist in the provided directory or any parent directory.
        Uses the directory containing sql-unit.yaml as the project root for YAML reference
        path resolution.

        Args:
            directory: Directory to search
            pattern: Glob pattern for files (default: "*.sql")

        Returns:
            Dictionary mapping filepath to list of test definitions

        Raises:
            ParserError: If sql-unit.yaml not found, directory is not found, or any file fails to parse
        """
        # Find the project root (directory with sql-unit.yaml)
        project_directory = cls.find_project_root(directory)

        # This will raise ParserError if directory doesn't exist
        files = cls.discover_files(directory, pattern)
        results = {}

        for filepath in files:
            # Parse each file with project_directory context (pass None to auto-detect from sql-unit.yaml)
            # Actually, since find_project_root already found it, pass it directly
            tests = cls.parse_file(filepath, project_directory=project_directory)
            if tests:
                results[filepath] = tests

        return results
