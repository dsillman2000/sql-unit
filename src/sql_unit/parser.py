"""Parser for SQL block comments containing sql-unit test definitions."""

import re
import textwrap
from typing import Any

import yaml

from .exceptions import ParserError
from .models import TestDefinition


class SqlBlockCommentParser:
    """Parses SQL block comments containing sql-unit test definitions."""
    
    # Pattern to find /* #! sql-unit ... */ blocks
    BLOCK_COMMENT_PATTERN = re.compile(
        r'/\*\s*#!\s*sql-unit\s+(.*?)\*/',
        re.DOTALL
    )
    
    # Pattern to find SQL statements (basic, matches SELECT/INSERT/UPDATE/DELETE/WITH)
    SQL_STATEMENT_PATTERN = re.compile(
        r'^\s*(WITH|SELECT|INSERT|UPDATE|DELETE)\b',
        re.MULTILINE | re.IGNORECASE
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
            line_number = sql_content[:match.start()].count('\n') + 1
            blocks.append((comment_text, line_number))
        return blocks
    
    @classmethod
    def parse_yaml_content(cls, comment_text: str, line_number: int) -> Any:
        """
        Parse YAML content from comment block, handling multi-doc and sequence syntax.
        
        Args:
            comment_text: Content inside the /* #! sql-unit ... */ block
            line_number: Line number of the block for error reporting
            
        Returns:
            Parsed YAML content (dict or list)
            
        Raises:
            ParserError: If YAML syntax is invalid or structure is invalid
        """
        try:
            # Strip and dedent to fix indentation issues
            comment_text = textwrap.dedent(comment_text).strip()
            
            # Check for multi-doc syntax (---)
            if '---' in comment_text:
                # Multi-doc syntax: use safe_load_all and collect all documents
                docs = []
                for doc in yaml.safe_load_all(comment_text):
                    if doc:  # Skip empty documents
                        docs.append(doc)
                return docs if docs else []
            
            # Parse as single YAML document
            content = yaml.safe_load(comment_text)
            
            # Normalize to list format
            if isinstance(content, list):
                # Already a sequence
                return content
            elif isinstance(content, dict):
                # Single test definition
                return [content]
            else:
                raise ParserError(
                    f"Expected dict or list in YAML, got {type(content).__name__}",
                    line_number=line_number
                )
                
        except yaml.YAMLError as e:
            raise ParserError(
                f"Invalid YAML syntax: {str(e)}",
                line_number=line_number
            )
    
    @classmethod
    def build_test_definitions(
        cls,
        parsed_yaml: Any,
        filepath: str,
        comment_line: int
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
                "Expected list of test definitions",
                filepath=filepath,
                line_number=comment_line
            )
        
        tests = []
        for idx, test_dict in enumerate(parsed_yaml):
            if not isinstance(test_dict, dict):
                raise ParserError(
                    f"Test definition {idx} is not a dict: {type(test_dict).__name__}",
                    filepath=filepath,
                    line_number=comment_line
                )
            
            # Extract required fields
            name = test_dict.get('name')
            if not name:
                # Auto-generate name for unnamed tests
                name = f"test_{idx + 1}"
            
            # Create TestDefinition
            test = TestDefinition(
                name=name,
                given=test_dict.get('given', {}),
                expect=test_dict.get('expect', {}),
                description=test_dict.get('description'),
                filepath=filepath,
                line_number=comment_line
            )
            tests.append(test)
        
        return tests
    
    @classmethod
    def extract_following_statement(
        cls,
        sql_content: str,
        comment_end_pos: int
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
        match = re.search(r'\S', remaining)
        
        if not match:
            return None, None
        
        start_pos = comment_end_pos + match.start()
        
        # Find the statement type
        from_pos = start_pos
        statement_match = cls.SQL_STATEMENT_PATTERN.search(remaining[match.start():])
        
        if not statement_match:
            return None, None
        
        # Extract statement (from first SELECT/INSERT/UPDATE/DELETE/WITH until semicolon)
        actual_start = from_pos + statement_match.start()
        
        # Find the semicolon
        semicolon_pos = sql_content.find(';', actual_start)
        if semicolon_pos == -1:
            # No semicolon found, take rest of content
            statement = sql_content[actual_start:].strip()
        else:
            statement = sql_content[actual_start:semicolon_pos].strip()
        
        # Calculate line number
        line_number = sql_content[:actual_start].count('\n') + 1
        
        return statement, line_number


class TestDiscoveryParser:
    """Discovers and parses tests from SQL files and directories."""
    
    @classmethod
    def parse_file(cls, filepath: str) -> list[TestDefinition]:
        """
        Parse all tests from a SQL file.
        
        Args:
            filepath: Path to SQL file
            
        Returns:
            List of TestDefinition objects found in file
            
        Raises:
            ParserError: If file cannot be read or parsing fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()
        except Exception as e:
            raise ParserError(
                f"Cannot read file: {str(e)}",
                filepath=filepath
            )
        
        # Extract all comment blocks
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql_content)
        
        all_tests = []
        test_names_in_file = set()
        
        for comment_text, line_number in blocks:
            # Parse YAML
            parsed = SqlBlockCommentParser.parse_yaml_content(comment_text, line_number)
            
            # Build test definitions
            tests = SqlBlockCommentParser.build_test_definitions(
                parsed, filepath, line_number
            )
            
            # Check for duplicate names within file
            for test in tests:
                if test.name in test_names_in_file:
                    raise ParserError(
                        f"Duplicate test name '{test.name}' in file",
                        filepath=filepath,
                        line_number=test.line_number
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
        from pathlib import Path
        
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ParserError(f"Directory not found: {directory}")
        
        # Find all matching files recursively
        matching_files = list(dir_path.rglob(pattern))
        return sorted(str(f) for f in matching_files)
    
    @classmethod
    def discover_and_parse(cls, directory: str, pattern: str = "*.sql") -> dict[str, list[TestDefinition]]:
        """
        Discover and parse all tests in directory.
        
        Args:
            directory: Directory to search
            pattern: Glob pattern for files (default: "*.sql")
            
        Returns:
            Dictionary mapping filepath to list of test definitions
            
        Raises:
            ParserError: If directory is not found or any file fails to parse
        """
        # This will raise ParserError if directory doesn't exist
        files = cls.discover_files(directory, pattern)
        results = {}
        
        for filepath in files:
            # Parse each file without catching errors - fail fast on parse failures
            tests = cls.parse_file(filepath)
            if tests:
                results[filepath] = tests
        
        return results
