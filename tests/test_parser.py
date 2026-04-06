"""Unit tests for YAML parser."""

import pytest

from sql_unit.exceptions import ParserError
from sql_unit.parser import SqlBlockCommentParser, TestDiscoveryParser
from sql_unit.models import TestDefinition


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
    
    def test_parse_file_with_tests(self, tmp_path):
        """Test parsing a SQL file with tests."""
        sql_file = tmp_path / "test.sql"
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
    
    def test_parse_file_no_tests(self, tmp_path):
        """Test parsing a SQL file with no tests."""
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("SELECT 1;")
        
        tests = TestDiscoveryParser.parse_file(str(sql_file))
        assert len(tests) == 0
    
    def test_parse_file_duplicate_test_names(self, tmp_path):
        """Test error when duplicate test names in file."""
        sql_file = tmp_path / "test.sql"
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
    
    def test_parse_complete_file(self, tmp_path):
        """Test parsing a complete SQL file with multiple tests."""
        sql_file = tmp_path / "queries.sql"
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
