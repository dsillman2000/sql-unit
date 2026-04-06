"""Unit tests for YAML parser."""

import pytest

from sql_unit.exceptions import ParserError
from sql_unit.parser import SqlBlockCommentParser, TestDiscoveryParser
from sql_unit.models import TestDefinition


@pytest.fixture
def project_root(tmp_path):
    """Create a temporary project directory with sql-unit.yaml."""
    sql_unit_config = tmp_path / "sql-unit.yaml"
    sql_unit_config.write_text("""# sql-unit configuration
version: "1.0"
allow_paths:
  - "*.yaml"
  - "**/*.yaml"
""")
    return tmp_path


class TestBlockCommentExtraction:
    """Tests for extracting comment blocks."""
    
    def test_extract_single_comment_block(self):
        """Test extracting a single comment block."""
        sql = """
        /* #! sql-unit
        name: test_simple
        given: {}
        expect: {}
        */
        SELECT 1;
        """
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql)
        assert len(blocks) == 1
        assert "test_simple" in blocks[0][0]
    
    def test_extract_multiple_comment_blocks(self):
        """Test extracting multiple comment blocks."""
        sql = """
        /* #! sql-unit
        name: test_1
        given: {}
        expect: {}
        */
        SELECT 1;
        
        /* #! sql-unit
        name: test_2
        given: {}
        expect: {}
        */
        SELECT 2;
        """
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql)
        assert len(blocks) == 2
    
    def test_extract_no_comment_blocks(self):
        """Test file with no comment blocks."""
        sql = "SELECT 1;"
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql)
        assert len(blocks) == 0
    
    def test_line_number_calculation(self):
        """Test that line numbers are calculated correctly."""
        sql = """/* comment */
        /* #! sql-unit
        name: test
        given: {}
        expect: {}
        */
        SELECT 1;
        """
        blocks = SqlBlockCommentParser.extract_comment_blocks(sql)
        assert blocks[0][1] == 2  # Second line


class TestYamlParsing:
    """Tests for YAML content parsing."""
    
    def test_parse_simple_test(self):
        """Test parsing simple test definition."""
        yaml_content = """name: test_simple
given:
  jinja_context:
    x: 1
expect:
  rows_equal:
    - col1: value1
        """
        result = SqlBlockCommentParser.parse_yaml_content(yaml_content, 1)
        assert isinstance(result, list)
        assert result[0]["name"] == "test_simple"
    
    def test_parse_multi_doc_syntax(self):
        """Test parsing multi-doc YAML (--- separator)."""
        yaml_content = """name: test_1
given: {}
expect: {}
---
name: test_2
given: {}
expect: {}
        """
        result = SqlBlockCommentParser.parse_yaml_content(yaml_content, 1)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "test_1"
        assert result[1]["name"] == "test_2"
    
    def test_parse_sequence_syntax(self):
        """Test parsing sequence YAML syntax."""
        yaml_content = """- name: test_1
  given: {}
  expect: {}
- name: test_2
  given: {}
  expect: {}
        """
        result = SqlBlockCommentParser.parse_yaml_content(yaml_content, 1)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_parse_invalid_yaml(self):
        """Test error handling for invalid YAML."""
        yaml_content = "invalid: [yaml content"
        with pytest.raises(ParserError):
            SqlBlockCommentParser.parse_yaml_content(yaml_content, 1)
    
    def test_parse_with_description(self):
        """Test parsing test with description field."""
        yaml_content = """name: test_with_desc
description: "This is a test"
given: {}
expect: {}
        """
        result = SqlBlockCommentParser.parse_yaml_content(yaml_content, 1)
        assert result[0]["description"] == "This is a test"


class TestTestDefinitionBuilding:
    """Tests for building TestDefinition objects."""
    
    def test_build_single_test_definition(self):
        """Test building a single TestDefinition."""
        parsed = [{"name": "test1", "given": {}, "expect": {}}]
        tests = SqlBlockCommentParser.build_test_definitions(
            parsed, "test.sql", 5
        )
        assert len(tests) == 1
        assert tests[0].name == "test1"
        assert tests[0].filepath == "test.sql"
        assert tests[0].line_number == 5
    
    def test_build_with_auto_generated_name(self):
        """Test auto-generation of test names."""
        parsed = [{"given": {}, "expect": {}}]
        tests = SqlBlockCommentParser.build_test_definitions(
            parsed, "test.sql", 1
        )
        assert tests[0].name == "test_1"
    
    def test_build_multiple_tests(self):
        """Test building multiple test definitions."""
        parsed = [
            {"name": "test1", "given": {}, "expect": {}},
            {"name": "test2", "given": {}, "expect": {}},
        ]
        tests = SqlBlockCommentParser.build_test_definitions(
            parsed, "test.sql", 1
        )
        assert len(tests) == 2
        assert tests[0].name == "test1"
        assert tests[1].name == "test2"
    
    def test_test_definition_test_id(self):
        """Test test_id() method."""
        test = TestDefinition(
            name="my_test",
            filepath="queries/test.sql"
        )
        assert test.test_id() == "queries/test.sql::my_test"


class TestFileParsing:
    """Tests for parsing complete SQL files."""
    
    def test_parse_file_with_tests(self, project_root):
        """Test parsing a SQL file with tests."""
        sql_file = project_root / "test.sql"
        sql_file.write_text("""/* #! sql-unit
name: test1
given: {}
expect: {}
*/
SELECT 1;
        """)
        
        tests = TestDiscoveryParser.parse_file(str(sql_file))
        assert len(tests) == 1
        assert tests[0].name == "test1"
    
    def test_parse_file_no_tests(self, project_root):
        """Test parsing a SQL file with no tests."""
        sql_file = project_root / "test.sql"
        sql_file.write_text("SELECT 1;")
        
        tests = TestDiscoveryParser.parse_file(str(sql_file))
        assert len(tests) == 0
    
    def test_parse_file_duplicate_test_names(self, project_root):
        """Test error when duplicate test names in file."""
        sql_file = project_root / "test.sql"
        sql_file.write_text("""
        /* #! sql-unit
        name: test1
        given: {}
        expect: {}
        */
        SELECT 1;
        
        /* #! sql-unit
        name: test1
        given: {}
        expect: {}
        */
        SELECT 2;
        """)
        
        with pytest.raises(ParserError):
            TestDiscoveryParser.parse_file(str(sql_file))


class TestCompleteIntegration:
    """Integration tests combining multiple parsing phases."""
    
    def test_parse_complete_file(self, project_root):
        """Test parsing a complete SQL file with multiple tests."""
        sql_file = project_root / "queries.sql"
        sql_file.write_text("""/* #! sql-unit
name: test_simple_select
description: "Test basic SELECT"
given:
  jinja_context:
    value: 42
expect:
  rows_equal:
    - result: 42
*/
SELECT {{ value }} as result;

/* #! sql-unit
name: test_with_condition
given: {}
expect: {}
*/
SELECT CASE WHEN 1=1 THEN 'yes' ELSE 'no' END as status;
        """)
        
        tests = TestDiscoveryParser.parse_file(str(sql_file))
        assert len(tests) == 2
        assert tests[0].name == "test_simple_select"
        assert tests[0].description == "Test basic SELECT"
        assert tests[1].name == "test_with_condition"


class TestFileDiscovery:
    """Tests for file discovery and batch parsing."""
    
    def test_discover_files_single_directory(self, tmp_path):
        """Test discovering SQL files in a single directory."""
        # Create test files
        (tmp_path / "test1.sql").write_text("SELECT 1;")
        (tmp_path / "test2.sql").write_text("SELECT 2;")
        (tmp_path / "readme.txt").write_text("Not a SQL file")
        
        files = TestDiscoveryParser.discover_files(str(tmp_path), "*.sql")
        assert len(files) == 2
        assert all(f.endswith(".sql") for f in files)
    
    def test_discover_files_nested_directories(self, tmp_path):
        """Test discovering SQL files in nested directories."""
        # Create nested structure
        (tmp_path / "queries").mkdir()
        (tmp_path / "queries" / "test1.sql").write_text("SELECT 1;")
        (tmp_path / "queries" / "nested").mkdir()
        (tmp_path / "queries" / "nested" / "test2.sql").write_text("SELECT 2;")
        
        files = TestDiscoveryParser.discover_files(str(tmp_path), "*.sql")
        assert len(files) == 2
        assert all(f.endswith(".sql") for f in files)
    
    def test_discover_files_custom_pattern(self, tmp_path):
        """Test discovering files with custom glob pattern."""
        (tmp_path / "queries.sql").write_text("SELECT 1;")
        (tmp_path / "schema.ddl").write_text("CREATE TABLE foo;")
        (tmp_path / "migration.sql").write_text("ALTER TABLE foo;")
        
        files = TestDiscoveryParser.discover_files(str(tmp_path), "migration.*")
        assert len(files) == 1
        assert files[0].endswith("migration.sql")
    
    def test_discover_files_directory_not_found(self, tmp_path):
        """Test error when directory doesn't exist."""
        nonexistent = str(tmp_path / "nonexistent")
        
        with pytest.raises(ParserError) as exc_info:
            TestDiscoveryParser.discover_files(nonexistent)
        assert "Directory not found" in str(exc_info.value)
    
    def test_discover_files_sorted(self, tmp_path):
        """Test that files are returned in sorted order."""
        (tmp_path / "z_last.sql").write_text("SELECT 3;")
        (tmp_path / "a_first.sql").write_text("SELECT 1;")
        (tmp_path / "m_middle.sql").write_text("SELECT 2;")
        
        files = TestDiscoveryParser.discover_files(str(tmp_path), "*.sql")
        assert files == sorted(files)
    
    def test_discover_and_parse_success(self, project_root):
        """Test discovering and parsing all tests in directory."""
        # Create files with tests
        (project_root / "test1.sql").write_text("""/* #! sql-unit
name: test_one
given: {}
expect: {}
*/
SELECT 1;
""")
        
        (project_root / "test2.sql").write_text("""/* #! sql-unit
name: test_two
given: {}
expect: {}
*/
SELECT 2;
""")
        
        results = TestDiscoveryParser.discover_and_parse(str(project_root))
        
        # Should have entries for files with tests
        assert len(results) == 2
        # Each file should have its tests
        assert all(len(tests) > 0 for tests in results.values())
    
    def test_discover_and_parse_mixed_files(self, project_root):
        """Test discovering with mix of files with and without tests."""
        # File with tests
        (project_root / "with_tests.sql").write_text("""/* #! sql-unit
name: test_one
given: {}
expect: {}
*/
SELECT 1;
""")
        
        # File without tests
        (project_root / "no_tests.sql").write_text("SELECT * FROM table;")
        
        results = TestDiscoveryParser.discover_and_parse(str(project_root))
        
        # Should only include files with tests
        assert len(results) == 1
        assert any("with_tests" in key for key in results.keys())
    
    def test_discover_and_parse_directory_not_found(self, tmp_path):
        """Test error when sql-unit.yaml is not found in directory or parents."""
        nonexistent = str(tmp_path / "nonexistent")
        
        with pytest.raises(ParserError) as exc_info:
            TestDiscoveryParser.discover_and_parse(nonexistent)
        assert "sql-unit.yaml not found" in str(exc_info.value)
    
    def test_discover_and_parse_invalid_yaml(self, project_root):
        """Test that parse errors are raised immediately (fail fast)."""
        # Create file with invalid YAML
        (project_root / "invalid.sql").write_text("""
        /* #! sql-unit
        name: test_one
        given: {
        expect: {}
        */
        SELECT 1;
        """)
        
        # Should raise ParserError immediately, not silently skip
        with pytest.raises(ParserError):
            TestDiscoveryParser.discover_and_parse(str(project_root))
