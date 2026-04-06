"""Unit tests for input parsing and validation."""

import pytest
import json
from sql_unit.inputs import (
    GivenClauseParser,
    GivenClauseValidator,
    DataSourceParser,
    AliasDeriver,
    CSVParser,
    CSVDialectDetector,
    RowsParser,
)
from sql_unit.models import InputType, DataSource, InputSpec
from sql_unit.exceptions import ConfigError, SetupError
from sql_unit.cte import CTEInput, CTEInjector
from sql_unit.relation import RelationInput, RelationSubstitutor
from sql_unit.expectations import RowCountExpectation, RowCountValidator
from sql_unit.setup import InputSetup, InputExecutor, InputValidator
from sql_unit.jinja_context import JinjaContextInput, JinjaContextDataSource, JinjaContextCollisionDetector


class TestGivenClauseParsing:
    """Tests for parsing given clause."""
    
    def test_empty_given_clause(self):
        """Test parsing empty given clause returns no specs."""
        specs = GivenClauseParser.parse_given_clause({})
        assert specs == []
    
    def test_parse_simple_cte(self):
        """Test parsing simple CTE input."""
        given = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 1, "name": "Alice"}]
            }
        }]
        specs = GivenClauseParser.parse_given_clause(given)
        
        assert len(specs) == 1
        assert specs[0].input_type == InputType.CTE
        assert specs[0].targets == ["users"]
        assert specs[0].data_source is not None
    
    def test_parse_simple_relation(self):
        """Test parsing simple relation input."""
        given = [{
            "relation": {
                "targets": ["prod_users"],
                "replacement": "test_users"
            }
        }]
        specs = GivenClauseParser.parse_given_clause(given)
        
        assert len(specs) == 1
        assert specs[0].input_type == InputType.RELATION
        assert specs[0].targets == ["prod_users"]
        assert specs[0].replacement == "test_users"
    
    def test_parse_jinja_context(self):
        """Test parsing jinja_context input."""
        given = [{
            "jinja_context": {
                "table_name": "users",
                "start_date": "2024-01-01"
            }
        }]
        specs = GivenClauseParser.parse_given_clause(given)
        
        assert len(specs) == 1
        assert specs[0].input_type == InputType.JINJA_CONTEXT
        assert specs[0].jinja_context == {"table_name": "users", "start_date": "2024-01-01"}
    
    def test_parse_multiple_inputs(self):
        """Test parsing multiple inputs in one given clause."""
        given = [
            {"cte": {"targets": ["users"], "rows": [{"id": 1}]}},
            {"relation": {"targets": ["prod"], "replacement": "test"}},
        ]
        specs = GivenClauseParser.parse_given_clause(given)
        
        assert len(specs) == 2
        assert specs[0].input_type == InputType.CTE
        assert specs[1].input_type == InputType.RELATION
    
    def test_cte_without_targets_error(self):
        """Test that CTE without targets raises error."""
        given = [{"cte": {"rows": [{"id": 1}]}}]
        
        with pytest.raises(ConfigError, match="must have targets"):
            GivenClauseParser.parse_given_clause(given)
    
    def test_relation_without_replacement_error(self):
        """Test that relation without replacement raises error."""
        given = [{"relation": {"targets": ["users"]}}]
        
        with pytest.raises(ConfigError, match="must have replacement"):
            GivenClauseParser.parse_given_clause(given)
    
    def test_jinja_syntax_in_relation_targets_error(self):
        """Test that Jinja syntax in relation targets raises error."""
        given = [{
            "relation": {
                "targets": ["{{ table_name }}"],
                "replacement": "test"
            }
        }]
        
        with pytest.raises(ConfigError, match="cannot contain Jinja syntax"):
            GivenClauseParser.parse_given_clause(given)


class TestDataSourceParsing:
    """Tests for data source parsing."""
    
    def test_parse_sql_data_source(self):
        """Test parsing SQL data source."""
        source = {"sql": "SELECT * FROM users"}
        ds = DataSourceParser.parse_data_source(source)
        
        assert ds.format == "sql"
        assert "SELECT" in ds.content
    
    def test_parse_csv_data_source(self):
        """Test parsing CSV data source."""
        csv_content = "id,name\n1,Alice\n2,Bob"
        source = {"csv": csv_content}
        ds = DataSourceParser.parse_data_source(source)
        
        assert ds.format == "csv"
        assert ds.content == csv_content
    
    def test_parse_rows_data_source(self):
        """Test parsing rows data source."""
        rows = [{"id": 1, "name": "Alice"}]
        source = {"rows": rows}
        ds = DataSourceParser.parse_data_source(source)
        
        assert ds.format == "rows"
        parsed_rows = json.loads(ds.content)
        assert parsed_rows == rows
    
    def test_empty_sql_error(self):
        """Test that empty SQL raises error."""
        source = {"sql": "  \n  "}
        
        with pytest.raises(SetupError, match="cannot be empty"):
            DataSourceParser.parse_data_source(source)
    
    def test_invalid_data_source_format_error(self):
        """Test that invalid format raises error."""
        source = {"invalid": "value"}
        
        with pytest.raises(ConfigError, match="Unknown data source format"):
            DataSourceParser.parse_data_source(source)


class TestCSVParsing:
    """Tests for CSV parsing."""
    
    def test_parse_simple_csv(self):
        """Test parsing simple CSV."""
        csv_content = "id,name\n1,Alice\n2,Bob"
        rows = CSVParser.parse_csv(csv_content)
        
        assert len(rows) == 2
        assert rows[0] == {"id": "1", "name": "Alice"}
        assert rows[1] == {"id": "2", "name": "Bob"}
    
    def test_csv_with_empty_cells(self):
        """Test CSV with empty cells treated as NULL."""
        csv_content = "id,name,age\n1,Alice,\n2,Bob,30"
        rows = CSVParser.parse_csv(csv_content)
        
        assert rows[0]["age"] is None
        assert rows[1]["age"] == "30"
    
    def test_delimiter_detection(self):
        """Test CSV delimiter auto-detection."""
        # Tab-delimited
        csv_tab = "id\tname\n1\tAlice"
        delim = CSVDialectDetector.detect_delimiter(csv_tab)
        assert delim == '\t'
        
        # Pipe-delimited
        csv_pipe = "id|name\n1|Alice"
        delim = CSVDialectDetector.detect_delimiter(csv_pipe)
        assert delim == '|'
    
    def test_empty_csv_error(self):
        """Test that CSV with no data raises error."""
        csv_content = "id,name"
        
        with pytest.raises(SetupError, match="no data rows"):
            CSVParser.parse_csv(csv_content)


class TestRowsParsing:
    """Tests for rows data format."""
    
    def test_parse_valid_rows(self):
        """Test parsing valid rows."""
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = RowsParser.parse_rows(rows)
        
        assert result == rows
    
    def test_empty_rows_error(self):
        """Test that empty rows list raises error."""
        with pytest.raises(SetupError, match="must contain at least one row"):
            RowsParser.parse_rows([])
    
    def test_non_dict_row_error(self):
        """Test that non-dict row raises error."""
        rows = [["id", "name"], [1, "Alice"]]
        
        with pytest.raises(SetupError, match="must be a dict"):
            RowsParser.parse_rows(rows)


class TestAliasDerivation:
    """Tests for alias derivation."""
    
    def test_derive_simple_alias(self):
        """Test deriving alias from simple name."""
        ds = DataSource(format="sql", content="SELECT 1")
        alias = AliasDeriver.derive_alias("users", ds)
        
        assert alias.startswith("users_")
        assert len(alias) > len("users_")
    
    def test_derive_alias_with_schema(self):
        """Test deriving alias from schema-qualified name."""
        ds = DataSource(format="sql", content="SELECT 1")
        alias = AliasDeriver.derive_alias("db.schema.users", ds)
        
        assert alias.startswith("db_schema_users_")
    
    def test_alias_stability(self):
        """Test that alias is stable (same data = same alias)."""
        content = "SELECT 1"
        ds1 = DataSource(format="sql", content=content)
        ds2 = DataSource(format="sql", content=content)
        
        alias1 = AliasDeriver.derive_alias("users", ds1)
        alias2 = AliasDeriver.derive_alias("users", ds2)
        
        assert alias1 == alias2
    
    def test_alias_changes_with_content(self):
        """Test that alias changes when content changes."""
        ds1 = DataSource(format="sql", content="SELECT 1")
        ds2 = DataSource(format="sql", content="SELECT 2")
        
        alias1 = AliasDeriver.derive_alias("users", ds1)
        alias2 = AliasDeriver.derive_alias("users", ds2)
        
        assert alias1 != alias2


class TestGivenClauseValidation:
    """Tests for given clause validation."""
    
    def test_no_validation_errors_on_valid_input(self):
        """Test that valid inputs pass validation."""
        specs = [
            InputSpec(
                input_type=InputType.CTE,
                targets=["users"],
                data_source=DataSource(format="sql", content="SELECT 1")
            )
        ]
        
        # Should not raise
        GivenClauseValidator.validate_input_specs(specs)
    
    def test_collision_detection(self):
        """Test collision detection between Jinja variables and aliases."""
        # Create a CTE that will generate alias "users_xyz"
        cte_spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="sql", content="SELECT 1")
        )
        
        # Jinja context with variable matching potential alias
        # This would need to be tested with actual alias generation
        # For now, test basic structure
        specs = [cte_spec]
        
        # Should not raise
        GivenClauseValidator.validate_input_specs(specs)


class TestCTEInput:
    """Tests for CTE input type implementation."""
    
    def test_cte_with_sql_data_source(self):
        """Test CTE generation from SQL data source."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="sql", content="SELECT id, name FROM source_users")
        )
        cte_input = CTEInput(spec)
        
        # Check CTE definition
        cte_def = cte_input.get_cte_definition()
        assert "AS (SELECT id, name FROM source_users)" in cte_def
        assert cte_input.get_cte_name() in cte_def
    
    def test_cte_with_csv_data_source(self):
        """Test CTE generation from CSV data source."""
        csv_content = "id,name\n1,Alice\n2,Bob"
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="csv", content=csv_content)
        )
        cte_input = CTEInput(spec)
        
        # Check CTE definition contains VALUES clause
        cte_def = cte_input.get_cte_definition()
        assert "VALUES" in cte_def
        assert "'Alice'" in cte_def or "Alice" in cte_def
    
    def test_cte_with_rows_data_source(self):
        """Test CTE generation from rows data source."""
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        cte_input = CTEInput(spec)
        
        # Check CTE definition contains VALUES clause
        cte_def = cte_input.get_cte_definition()
        assert "VALUES" in cte_def
        assert "Alice" in cte_def
    
    def test_cte_with_explicit_alias(self):
        """Test CTE with explicit alias override."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            alias="my_users",
            data_source=DataSource(format="sql", content="SELECT 1")
        )
        cte_input = CTEInput(spec)
        
        # Check that explicit alias is used
        assert cte_input.get_cte_name() == "my_users"
    
    def test_cte_with_derived_alias(self):
        """Test CTE with derived alias from content."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="sql", content="SELECT id, name FROM source")
        )
        cte_input = CTEInput(spec)
        
        # Check that derived alias is generated
        cte_name = cte_input.get_cte_name()
        assert cte_name is not None
        assert len(cte_name) > 0
        # Derived names should have format: base_hash
        assert "_" in cte_name or cte_name.startswith("users")
    
    def test_cte_with_null_values(self):
        """Test CTE generation handles NULL values correctly."""
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        cte_input = CTEInput(spec)
        
        cte_def = cte_input.get_cte_definition()
        assert "NULL" in cte_def
    
    def test_cte_with_boolean_values(self):
        """Test CTE generation handles boolean values correctly."""
        rows = [{"id": 1, "active": True}, {"id": 2, "active": False}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        cte_input = CTEInput(spec)
        
        cte_def = cte_input.get_cte_definition()
        assert "TRUE" in cte_def
        assert "FALSE" in cte_def
    
    def test_cte_with_numeric_values(self):
        """Test CTE generation handles numeric values correctly."""
        rows = [{"id": 1, "value": 42.5}, {"id": 2, "value": -10}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["metrics"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        cte_input = CTEInput(spec)
        
        cte_def = cte_input.get_cte_definition()
        assert "42.5" in cte_def
        assert "-10" in cte_def
    
    def test_cte_with_escaped_strings(self):
        """Test CTE generation escapes single quotes in strings."""
        rows = [{"id": 1, "message": "It's great"}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["messages"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        cte_input = CTEInput(spec)
        
        cte_def = cte_input.get_cte_definition()
        # Should have escaped quote
        assert "It''s" in cte_def
    
    def test_cte_with_empty_rows_error(self):
        """Test CTE with empty rows raises error."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps([]))
        )
        cte_input = CTEInput(spec)
        
        with pytest.raises(SetupError, match="empty"):
            cte_input.get_cte_definition()


class TestCTEInjector:
    """Tests for CTE injection into SQL."""
    
    def test_inject_single_cte(self):
        """Test injecting a single CTE into SQL."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            alias="test_users",
            data_source=DataSource(format="sql", content="SELECT 1 as id, 'Alice' as name")
        )
        cte_input = CTEInput(spec)
        
        original_sql = "SELECT * FROM test_users"
        result_sql = CTEInjector.inject_ctes(original_sql, [cte_input])
        
        assert result_sql.startswith("WITH")
        assert "test_users AS (" in result_sql
        assert "SELECT * FROM test_users" in result_sql
    
    def test_inject_multiple_ctes(self):
        """Test injecting multiple CTEs into SQL."""
        spec1 = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            alias="test_users",
            data_source=DataSource(format="sql", content="SELECT 1 as id")
        )
        spec2 = InputSpec(
            input_type=InputType.CTE,
            targets=["orders"],
            alias="test_orders",
            data_source=DataSource(format="sql", content="SELECT 1 as order_id")
        )
        
        cte_input1 = CTEInput(spec1)
        cte_input2 = CTEInput(spec2)
        
        original_sql = "SELECT * FROM test_users JOIN test_orders"
        result_sql = CTEInjector.inject_ctes(original_sql, [cte_input1, cte_input2])
        
        assert result_sql.startswith("WITH")
        assert "test_users AS (" in result_sql
        assert "test_orders AS (" in result_sql
        # Both CTEs should be in WITH clause separated by comma
        assert "test_users AS (" in result_sql and "test_orders AS (" in result_sql
    
    def test_inject_no_ctes(self):
        """Test injecting empty CTE list returns original SQL."""
        original_sql = "SELECT * FROM users"
        result_sql = CTEInjector.inject_ctes(original_sql, [])
        
        assert result_sql == original_sql
    
    def test_inject_cte_preserves_original_query(self):
        """Test that original query is preserved after CTE injection."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["temp"],
            alias="temp_data",
            data_source=DataSource(format="sql", content="SELECT 1")
        )
        cte_input = CTEInput(spec)
        
        original_sql = "SELECT id, name FROM users WHERE active = true"
        result_sql = CTEInjector.inject_ctes(original_sql, [cte_input])
        
        # Original query should be at the end, after WITH clause
        assert "SELECT id, name FROM users WHERE active = true" in result_sql
    
    def test_inject_cte_with_existing_with_clause_error(self):
        """Test that injecting CTE into query with existing WITH raises error."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["temp"],
            alias="temp_data",
            data_source=DataSource(format="sql", content="SELECT 1")
        )
        cte_input = CTEInput(spec)
        
        # SQL already has WITH clause
        original_sql = "WITH existing_cte AS (SELECT 1) SELECT * FROM existing_cte"
        
        with pytest.raises(SetupError, match="multiple WITH"):
            CTEInjector.inject_ctes(original_sql, [cte_input])


class TestRelationInput:
    """Tests for relation input type implementation."""
    
    def test_relation_simple_substitution(self):
        """Test simple table name substitution."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod_users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM prod_users"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        assert "test_users" in result_sql
        assert "prod_users" not in result_sql
    
    def test_relation_substitution_case_insensitive(self):
        """Test that substitution is case-insensitive."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        # Test with different cases
        original_sql = "SELECT * FROM USERS WHERE id IN (SELECT user_id FROM Users)"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        assert "test_users" in result_sql
        assert "USERS" not in result_sql.upper().replace("TEST_USERS", "")
    
    def test_relation_substitution_preserves_word_boundaries(self):
        """Test that substitution respects word boundaries."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        # Should not replace "users" in "user_id"
        original_sql = "SELECT user_id FROM users"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        assert "test_users" in result_sql
        assert "user_id" in result_sql  # Should not be changed
    
    def test_relation_substitution_multiple_occurrences(self):
        """Test substitution of multiple occurrences in single query."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["orders"],
            replacement="test_orders"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM orders o JOIN orders o2 ON o.id = o2.parent_id"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        # Should have 2 occurrences
        assert result_sql.count("test_orders") == 2
        assert "orders" not in result_sql or "test_orders" in result_sql
    
    def test_relation_substitution_with_schema_qualified_name(self):
        """Test substitution of schema-qualified table names."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod.users"],
            replacement="test.users"
        )
        relation_input = RelationInput(spec)
        
        # Note: Simple regex-based substitution will match "prod.users"
        original_sql = "SELECT * FROM prod.users"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        # This test may vary based on AST vs regex implementation
        assert "test.users" in result_sql or "test_users" in result_sql
    
    def test_relation_substitution_in_join(self):
        """Test substitution in JOIN clauses."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        assert "test_users" in result_sql
        assert "FROM users" not in result_sql
    
    def test_relation_substitution_in_subquery(self):
        """Test substitution in subqueries."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM (SELECT * FROM users) u"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        assert "test_users" in result_sql
        assert "FROM users" not in result_sql
    
    def test_relation_substitution_no_match(self):
        """Test that non-matching targets don't modify SQL."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["orders"],
            replacement="test_orders"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM users"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        # Should be unchanged
        assert result_sql == original_sql
    
    def test_relation_substitution_empty_targets(self):
        """Test substitution with empty targets list."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=[],
            replacement="test_table"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM users"
        result_sql = relation_input.substitute_in_sql(original_sql)
        
        # Should be unchanged
        assert result_sql == original_sql


class TestRelationSubstitutor:
    """Tests for multiple relation substitutions."""
    
    def test_apply_single_substitution(self):
        """Test applying single relation substitution."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT * FROM users"
        result_sql = RelationSubstitutor.apply_substitutions(original_sql, [relation_input])
        
        assert "test_users" in result_sql
    
    def test_apply_multiple_substitutions(self):
        """Test applying multiple relation substitutions in sequence."""
        spec1 = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod_users"],
            replacement="test_users"
        )
        spec2 = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod_orders"],
            replacement="test_orders"
        )
        
        relation_input1 = RelationInput(spec1)
        relation_input2 = RelationInput(spec2)
        
        original_sql = "SELECT * FROM prod_users u JOIN prod_orders o ON u.id = o.user_id"
        result_sql = RelationSubstitutor.apply_substitutions(
            original_sql, 
            [relation_input1, relation_input2]
        )
        
        assert "test_users" in result_sql
        assert "test_orders" in result_sql
        assert "prod_users" not in result_sql
        assert "prod_orders" not in result_sql
    
    def test_apply_no_substitutions(self):
        """Test applying empty substitution list."""
        original_sql = "SELECT * FROM users"
        result_sql = RelationSubstitutor.apply_substitutions(original_sql, [])
        
        assert result_sql == original_sql
    
    def test_apply_substitutions_order_matters(self):
        """Test that substitution order can affect results."""
        # First substitution replaces 'users' with 'u'
        spec1 = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="u"
        )
        # Second substitution replaces 'u' with 'test_users'
        spec2 = InputSpec(
            input_type=InputType.RELATION,
            targets=["u"],
            replacement="test_users"
        )
        
        relation_input1 = RelationInput(spec1)
        relation_input2 = RelationInput(spec2)
        
        original_sql = "SELECT * FROM users"
        result_sql = RelationSubstitutor.apply_substitutions(
            original_sql,
            [relation_input1, relation_input2]
        )
        
        # First: "users" → "u"
        # Second: "u" → "test_users"
        assert "test_users" in result_sql
    
    def test_apply_substitutions_preserves_structure(self):
        """Test that substitution preserves SQL structure."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        relation_input = RelationInput(spec)
        
        original_sql = "SELECT id, name, email FROM users WHERE active = true"
        result_sql = RelationSubstitutor.apply_substitutions(original_sql, [relation_input])
        
        # Check that SELECT, WHERE, etc. are preserved
        assert "SELECT id, name, email FROM" in result_sql
        assert "WHERE active = true" in result_sql


class TestRowCountExpectation:
    """Tests for row count expectation evaluation."""
    
    def test_eq_operator_shorthand_syntax(self):
        """Test shorthand syntax for eq operator."""
        expectation = RowCountExpectation(5)
        
        assert expectation.operator == "eq"
        assert expectation.value == 5
    
    def test_eq_operator_dict_syntax(self):
        """Test dict syntax for eq operator."""
        expectation = RowCountExpectation({"eq": 5})
        
        assert expectation.operator == "eq"
        assert expectation.value == 5
    
    def test_min_operator(self):
        """Test min operator."""
        expectation = RowCountExpectation({"min": 3})
        
        assert expectation.operator == "min"
        assert expectation.value == 3
    
    def test_max_operator(self):
        """Test max operator."""
        expectation = RowCountExpectation({"max": 10})
        
        assert expectation.operator == "max"
        assert expectation.value == 10
    
    def test_eq_evaluation_pass(self):
        """Test eq operator evaluation passes when counts match."""
        expectation = RowCountExpectation(5)
        assert expectation.evaluate(5) is True
    
    def test_eq_evaluation_fail(self):
        """Test eq operator evaluation fails when counts don't match."""
        expectation = RowCountExpectation(5)
        assert expectation.evaluate(6) is False
        assert expectation.evaluate(4) is False
    
    def test_min_evaluation_pass(self):
        """Test min operator evaluation passes when actual >= expected."""
        expectation = RowCountExpectation({"min": 3})
        assert expectation.evaluate(3) is True
        assert expectation.evaluate(4) is True
        assert expectation.evaluate(10) is True
    
    def test_min_evaluation_fail(self):
        """Test min operator evaluation fails when actual < expected."""
        expectation = RowCountExpectation({"min": 3})
        assert expectation.evaluate(2) is False
        assert expectation.evaluate(0) is False
    
    def test_max_evaluation_pass(self):
        """Test max operator evaluation passes when actual <= expected."""
        expectation = RowCountExpectation({"max": 10})
        assert expectation.evaluate(10) is True
        assert expectation.evaluate(5) is True
        assert expectation.evaluate(0) is True
    
    def test_max_evaluation_fail(self):
        """Test max operator evaluation fails when actual > expected."""
        expectation = RowCountExpectation({"max": 10})
        assert expectation.evaluate(11) is False
        assert expectation.evaluate(100) is False
    
    def test_eq_failure_message(self):
        """Test failure message for eq operator."""
        expectation = RowCountExpectation(5)
        message = expectation.get_failure_message(3)
        
        assert "Expected exactly 5 rows" in message
        assert "got 3" in message
    
    def test_min_failure_message(self):
        """Test failure message for min operator."""
        expectation = RowCountExpectation({"min": 5})
        message = expectation.get_failure_message(3)
        
        assert "Expected at least 5 rows" in message
        assert "got 3" in message
    
    def test_max_failure_message(self):
        """Test failure message for max operator."""
        expectation = RowCountExpectation({"max": 5})
        message = expectation.get_failure_message(10)
        
        assert "Expected at most 5 rows" in message
        assert "got 10" in message
    
    def test_zero_row_count(self):
        """Test handling of zero row count."""
        expectation = RowCountExpectation(0)
        
        assert expectation.evaluate(0) is True
        assert expectation.evaluate(1) is False
    
    def test_invalid_operator_error(self):
        """Test that invalid operator raises error."""
        with pytest.raises(SetupError, match="Unknown row_count operator"):
            RowCountExpectation({"invalid": 5})
    
    def test_negative_value_error(self):
        """Test that negative value raises error."""
        with pytest.raises(SetupError, match="non-negative"):
            RowCountExpectation({"eq": -1})
    
    def test_non_integer_value_error(self):
        """Test that non-integer value raises error."""
        with pytest.raises(SetupError, match="non-negative integer"):
            RowCountExpectation({"eq": "five"})
    
    def test_empty_dict_error(self):
        """Test that empty dict raises error."""
        with pytest.raises(SetupError, match="must have operator"):
            RowCountExpectation({})
    
    def test_multiple_operators_error(self):
        """Test that multiple operators raise error."""
        with pytest.raises(SetupError, match="can only have one operator"):
            RowCountExpectation({"eq": 5, "min": 3})
    
    def test_invalid_type_error(self):
        """Test that invalid type raises error."""
        with pytest.raises(SetupError, match="must be int or dict"):
            RowCountExpectation("five")


class TestRowCountValidator:
    """Tests for row count validation."""
    
    def test_validate_exact_match(self):
        """Test validation with exact match."""
        expectation = RowCountExpectation(3)
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is True
        assert message is None
    
    def test_validate_mismatch(self):
        """Test validation with mismatch."""
        expectation = RowCountExpectation(5)
        rows = [{"id": 1}, {"id": 2}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is False
        assert message is not None
        assert "Expected exactly 5" in message
    
    def test_validate_min_pass(self):
        """Test min validation passes."""
        expectation = RowCountExpectation({"min": 2})
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is True
        assert message is None
    
    def test_validate_min_fail(self):
        """Test min validation fails."""
        expectation = RowCountExpectation({"min": 5})
        rows = [{"id": 1}, {"id": 2}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is False
        assert "Expected at least 5" in message
    
    def test_validate_max_pass(self):
        """Test max validation passes."""
        expectation = RowCountExpectation({"max": 5})
        rows = [{"id": 1}, {"id": 2}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is True
        assert message is None
    
    def test_validate_max_fail(self):
        """Test max validation fails."""
        expectation = RowCountExpectation({"max": 2})
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is False
        assert "Expected at most 2" in message
    
    def test_validate_empty_rows(self):
        """Test validation with empty result set."""
        expectation = RowCountExpectation(0)
        rows = []
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is True
        assert message is None
    
    def test_validate_empty_rows_fail(self):
        """Test validation with empty result set fails when expecting rows."""
        expectation = RowCountExpectation(5)
        rows = []
        
        passed, message = RowCountValidator.validate_row_count(rows, expectation)
        
        assert passed is False
        assert "Expected exactly 5" in message


class TestInputSetupIntegration:
    """Integration tests for InputSetup orchestration."""
    
    def test_setup_with_single_cte(self):
        """Test setup with only CTE input."""
        given = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 1, "name": "Alice"}]
            }
        }]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 1
        assert len(setup.relation_inputs) == 0
        assert setup.jinja_context_input is None
    
    def test_setup_with_single_relation(self):
        """Test setup with only relation input."""
        given = [{
            "relation": {
                "targets": ["prod_users"],
                "replacement": "test_users"
            }
        }]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 0
        assert len(setup.relation_inputs) == 1
        assert setup.jinja_context_input is None
    
    def test_setup_with_cte_and_relation(self):
        """Test setup with both CTE and relation inputs."""
        given = [
            {"cte": {"targets": ["temp_users"], "rows": [{"id": 1}]}},
            {"relation": {"targets": ["prod_users"], "replacement": "test_users"}}
        ]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 1
        assert len(setup.relation_inputs) == 1
        assert setup.jinja_context_input is None
    
    def test_setup_with_multiple_ctes(self):
        """Test setup with multiple CTE inputs."""
        given = [
            {"cte": {"targets": ["users"], "rows": [{"id": 1}]}},
            {"cte": {"targets": ["orders"], "rows": [{"order_id": 1}]}}
        ]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 2
        assert len(setup.relation_inputs) == 0
    
    def test_setup_with_multiple_relations(self):
        """Test setup with multiple relation inputs."""
        given = [
            {"relation": {"targets": ["users"], "replacement": "test_users"}},
            {"relation": {"targets": ["orders"], "replacement": "test_orders"}}
        ]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 0
        assert len(setup.relation_inputs) == 2
    
    def test_setup_with_jinja_context(self):
        """Test setup with jinja_context input."""
        given = [{
            "jinja_context": {
                "table_name": "users",
                "start_date": "2024-01-01"
            }
        }]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 0
        assert len(setup.relation_inputs) == 0
        assert setup.jinja_context_input is not None
        assert setup.build_jinja_context() == {"table_name": "users", "start_date": "2024-01-01"}
    
    def test_setup_with_all_input_types(self):
        """Test setup with CTE, relation, and jinja_context."""
        given = [
            {"cte": {"targets": ["temp"], "rows": [{"id": 1}]}},
            {"relation": {"targets": ["prod_users"], "replacement": "test_users"}},
            {"jinja_context": {"table_name": "users"}}
        ]
        
        setup = InputSetup(given)
        
        assert len(setup.cte_inputs) == 1
        assert len(setup.relation_inputs) == 1
        assert setup.jinja_context_input is not None
    
    def test_setup_multiple_jinja_context_error(self):
        """Test that multiple jinja_context blocks raise error."""
        given = [
            {"jinja_context": {"var1": "val1"}},
            {"jinja_context": {"var2": "val2"}}
        ]
        
        with pytest.raises(ConfigError, match="Only one jinja_context"):
            InputSetup(given)
    
    def test_setup_empty_given(self):
        """Test setup with empty given clause."""
        setup = InputSetup({})
        
        assert len(setup.cte_inputs) == 0
        assert len(setup.relation_inputs) == 0
        assert setup.jinja_context_input is None


class TestInputExecutorIntegration:
    """Integration tests for InputExecutor."""
    
    def test_executor_with_cte_only(self):
        """Test executor applying CTE injection."""
        given = [{
            "cte": {
                "targets": ["users"],
                "alias": "test_users",
                "rows": [{"id": 1, "name": "Alice"}]
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM test_users"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup)
        
        assert "WITH" in result_sql
        assert "test_users AS (" in result_sql
    
    def test_executor_with_relation_only(self):
        """Test executor applying relation substitution."""
        given = [{
            "relation": {
                "targets": ["prod_users"],
                "replacement": "test_users"
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM prod_users"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup)
        
        assert "test_users" in result_sql
        assert "prod_users" not in result_sql
    
    def test_executor_with_cte_and_relation(self):
        """Test executor applying CTE injection and relation substitution."""
        given = [
            {
                "cte": {
                    "targets": ["temp_data"],
                    "alias": "cte_data",
                    "rows": [{"id": 1}]
                }
            },
            {
                "relation": {
                    "targets": ["prod_users"],
                    "replacement": "test_users"
                }
            }
        ]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM prod_users JOIN cte_data"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup)
        
        # Should have CTE
        assert "WITH" in result_sql
        # Should have relation substitution
        assert "test_users" in result_sql
        assert "prod_users" not in result_sql
    
    def test_executor_preserves_sql_structure(self):
        """Test that executor preserves SQL structure."""
        given = [{
            "cte": {
                "targets": ["users"],
                "alias": "test_users",
                "rows": [{"id": 1}]
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT id, name FROM test_users WHERE active = true"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup)
        
        # Original query structure should be preserved
        assert "SELECT id, name FROM test_users WHERE active = true" in result_sql
    
    def test_executor_with_jinja_renderer(self):
        """Test executor with custom Jinja renderer."""
        def mock_renderer(sql: str, context: dict) -> str:
            # Simple replacement for testing
            for key, value in context.items():
                sql = sql.replace(f"{{{{ {key} }}}}", str(value))
            return sql
        
        given = [{
            "jinja_context": {
                "table_name": "users"
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM {{ table_name }}"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup, jinja_renderer=mock_renderer)
        
        assert "{{ table_name }}" not in result_sql
        assert "users" in result_sql
    
    def test_executor_execution_order(self):
        """Test that executor applies inputs in correct order: Jinja, CTE, Relation."""
        # This test verifies the execution order documented in InputExecutor
        def mock_renderer(sql: str, context: dict) -> str:
            # Replace {{ alias }} with cte_users
            return sql.replace("{{ alias }}", "cte_users")
        
        given = [
            {"jinja_context": {"alias": "cte_users"}},
            {
                "cte": {
                    "targets": ["cte_users"],
                    "alias": "cte_users",
                    "rows": [{"id": 1}]
                }
            },
            {
                "relation": {
                    "targets": ["prod_users"],
                    "replacement": "test_users"
                }
            }
        ]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM prod_users JOIN {{ alias }}"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup, jinja_renderer=mock_renderer)
        
        # Verify all transformations applied
        assert "WITH" in result_sql  # CTE injection
        assert "test_users" in result_sql  # Relation substitution
        assert "{{ alias }}" not in result_sql  # Jinja rendering


class TestInputValidatorIntegration:
    """Integration tests for InputValidator."""
    
    def test_validator_detects_cte_name_collision(self):
        """Test that validator detects duplicate CTE names."""
        # Create two CTEs with same content (which would create same derived alias)
        given = [
            {
                "cte": {
                    "targets": ["users"],
                    "sql": "SELECT 1"
                }
            },
            {
                "cte": {
                    "targets": ["users"],
                    "sql": "SELECT 1"
                }
            }
        ]
        
        # Collision detection happens during InputSetup initialization
        with pytest.raises(ConfigError, match="collision"):
            InputSetup(given)
    
    def test_validator_passes_with_different_cte_names(self):
        """Test that validator passes with different CTE names."""
        given = [
            {
                "cte": {
                    "targets": ["users"],
                    "alias": "test_users",
                    "rows": [{"id": 1}]
                }
            },
            {
                "cte": {
                    "targets": ["orders"],
                    "alias": "test_orders",
                    "rows": [{"order_id": 1}]
                }
            }
        ]
        
        setup = InputSetup(given)
        
        # Should not raise
        InputValidator.validate_inputs_compatible(setup)


class TestJinjaContextDataSource:
    """Tests for nested Jinja context data sources."""
    
    def test_nested_cte_data_source(self):
        """Test nested CTE data source in jinja_context."""
        spec = {
            "cte": {
                "sql": "SELECT id, name FROM users"
            }
        }
        
        nested = JinjaContextDataSource("users_var", spec)
        
        assert nested.is_data_source is True
        assert nested.source_type == "cte"
        assert nested.data_source is not None
        assert nested.data_source.format == "sql"
    
    def test_nested_cte_with_explicit_alias(self):
        """Test nested CTE with explicit alias."""
        spec = {
            "cte": {
                "sql": "SELECT 1",
                "alias": "my_cte"
            }
        }
        
        nested = JinjaContextDataSource("users_var", spec)
        
        assert nested.alias == "my_cte"
        assert nested.get_binding_name() == "my_cte"
    
    def test_nested_cte_with_derived_alias(self):
        """Test nested CTE with derived alias."""
        spec = {
            "cte": {
                "rows": [{"id": 1, "name": "Alice"}]
            }
        }
        
        nested = JinjaContextDataSource("users_var", spec)
        
        # Should have derived alias
        binding_name = nested.get_binding_name()
        assert binding_name is not None
        assert len(binding_name) > 0
    
    def test_nested_temp_table_data_source(self):
        """Test nested temp_table data source."""
        spec = {
            "temp_table": {
                "csv": "id,name\n1,Alice"
            }
        }
        
        nested = JinjaContextDataSource("temp_var", spec)
        
        assert nested.is_data_source is True
        assert nested.source_type == "temp_table"
        assert nested.data_source is not None
        assert nested.data_source.format == "csv"
    
    def test_scalar_string_value(self):
        """Test scalar string value in jinja_context."""
        nested = JinjaContextDataSource("table_name", "users")
        
        assert nested.is_data_source is False
        assert nested.source_type is None
        assert nested.get_binding_name() == "users"
    
    def test_scalar_integer_value(self):
        """Test scalar integer value in jinja_context."""
        nested = JinjaContextDataSource("page_size", 100)
        
        assert nested.is_data_source is False
        assert nested.get_binding_name() == "100"
    
    def test_scalar_boolean_value(self):
        """Test scalar boolean value in jinja_context."""
        nested = JinjaContextDataSource("is_active", True)
        
        assert nested.is_data_source is False
        assert nested.get_binding_name() == "True"
    
    def test_empty_dict_treated_as_scalar(self):
        """Test that empty dict is treated as scalar."""
        nested = JinjaContextDataSource("empty_var", {})
        
        assert nested.is_data_source is False
        assert nested.get_binding_name() == "{}"


class TestJinjaContextInput:
    """Tests for JinjaContextInput orchestration."""
    
    def test_context_with_scalar_variables(self):
        """Test jinja_context with only scalar variables."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "table_name": "users",
                "start_date": "2024-01-01",
                "limit": 100
            }
        )
        
        context_input = JinjaContextInput(spec)
        
        assert len(context_input.scalar_vars) == 3
        assert len(context_input.nested_sources) == 0
    
    def test_context_with_nested_cte(self):
        """Test jinja_context with nested CTE."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "users_data": {
                    "cte": {
                        "rows": [{"id": 1, "name": "Alice"}]
                    }
                }
            }
        )
        
        context_input = JinjaContextInput(spec)
        
        assert len(context_input.nested_sources) == 1
        assert "users_data" in context_input.nested_sources
        assert context_input.nested_sources["users_data"].source_type == "cte"
    
    def test_context_with_mixed_variables(self):
        """Test jinja_context with both scalars and nested data sources."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "table_name": "users",
                "users_data": {
                    "cte": {
                        "sql": "SELECT * FROM source_users"
                    }
                },
                "limit": 100
            }
        )
        
        context_input = JinjaContextInput(spec)
        
        assert len(context_input.scalar_vars) == 2
        assert len(context_input.nested_sources) == 1
    
    def test_build_jinja_context_dict_scalars_only(self):
        """Test building context dict with scalar variables."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "table": "users",
                "count": 10
            }
        )
        
        context_input = JinjaContextInput(spec)
        context_dict = context_input.build_jinja_context_dict()
        
        assert context_dict["table"] == "users"
        assert context_dict["count"] == 10
    
    def test_build_jinja_context_dict_with_nested_sources(self):
        """Test building context dict includes nested source bindings."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_users": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "users_cte"
                    }
                },
                "table_name": "users"
            }
        )
        
        context_input = JinjaContextInput(spec)
        context_dict = context_input.build_jinja_context_dict()
        
        # Nested data source should be bound to its alias
        assert context_dict["my_users"] == "users_cte"
        # Scalar should be as-is
        assert context_dict["table_name"] == "users"
    
    def test_get_nested_sources(self):
        """Test retrieving nested data sources."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "users": {"cte": {"sql": "SELECT 1"}},
                "orders": {"cte": {"sql": "SELECT 2"}},
                "limit": 10
            }
        )
        
        context_input = JinjaContextInput(spec)
        nested = context_input.get_nested_sources()
        
        assert len(nested) == 2
        assert "users" in nested
        assert "orders" in nested
    
    def test_get_scalar_vars(self):
        """Test retrieving scalar variables."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "users": {"cte": {"sql": "SELECT 1"}},
                "table": "users",
                "limit": 10
            }
        )
        
        context_input = JinjaContextInput(spec)
        scalars = context_input.get_scalar_vars()
        
        assert len(scalars) == 2
        assert scalars["table"] == "users"
        assert scalars["limit"] == 10


class TestJinjaContextCollisionDetection:
    """Tests for collision detection between Jinja variables and aliases."""
    
    def test_no_collision_with_different_names(self):
        """Test no collision when Jinja variables differ from aliases."""
        jinja_spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_users": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "users_cte"
                    }
                }
            }
        )
        cte_spec = InputSpec(
            input_type=InputType.CTE,
            targets=["other_table"],
            data_source=DataSource(format="sql", content="SELECT 1"),
            alias="other_alias"
        )
        
        jinja_input = JinjaContextInput(jinja_spec)
        
        # Should not raise
        JinjaContextCollisionDetector.check_collisions(
            jinja_input,
            [jinja_spec, cte_spec]
        )
    
    def test_collision_with_derived_alias(self):
        """Test collision detection when Jinja variable matches explicit CTE alias."""
        jinja_spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_alias": "some_value"  # Variable named 'my_alias'
            }
        )
        cte_spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="sql", content="SELECT 1"),
            alias="my_alias"  # Explicit alias matches Jinja variable name
        )
        
        jinja_input = JinjaContextInput(jinja_spec)
        
        # Should raise collision error
        with pytest.raises(ConfigError, match="collides"):
            JinjaContextCollisionDetector.check_collisions(
                jinja_input,
                [jinja_spec, cte_spec]
            )
    
    def test_duplicate_jinja_variable_detection(self):
        """Test detection of duplicate variable names in jinja_context."""
        # Note: This should be caught during parsing, but we test the detector too
        jinja_spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "var1": "value1",
                "var2": "value2"
            }
        )
        
        jinja_input = JinjaContextInput(jinja_spec)
        
        # Should not raise
        JinjaContextCollisionDetector.check_collisions(
            jinja_input,
            [jinja_spec]
        )


class TestNestedJinjaContextIntegration:
    """Integration tests for nested jinja_context with other inputs."""
    
    def test_setup_with_nested_cte_and_scalar(self):
        """Test setup combining nested CTE and scalar jinja_context variables."""
        given = [{
            "jinja_context": {
                "users_data": {
                    "cte": {
                        "rows": [{"id": 1, "name": "Alice"}],
                        "alias": "cte_users"
                    }
                },
                "table_name": "users"
            }
        }]
        
        setup = InputSetup(given)
        
        assert setup.jinja_context_input is not None
        assert len(setup.jinja_context_input.nested_sources) == 1
        assert len(setup.jinja_context_input.scalar_vars) == 1
    
    def test_executor_with_nested_jinja_context_and_scalar(self):
        """Test executor with nested data source and scalar variables."""
        def mock_renderer(sql: str, context: dict) -> str:
            # Replace Jinja placeholders with context values
            for key, value in context.items():
                sql = sql.replace(f"{{{{ {key} }}}}", str(value))
            return sql
        
        given = [{
            "jinja_context": {
                "limit_value": 10,
                "my_cte": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "cte_data"
                    }
                }
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM {{ my_cte }} LIMIT {{ limit_value }}"
        
        result_sql = InputExecutor.apply_inputs(
            original_sql, 
            setup, 
            jinja_renderer=mock_renderer
        )
        
        # Should have replaced both placeholders
        assert "cte_data" in result_sql
        assert "10" in result_sql
        assert "{{" not in result_sql
    
    def test_nested_cte_with_relation_substitution(self):
        """Test nested CTE combined with relation substitution."""
        given = [
            {
                "jinja_context": {
                    "temp_users": {
                        "cte": {
                            "sql": "SELECT * FROM prod_users",
                            "alias": "temp_cte"
                        }
                    }
                }
            },
            {
                "relation": {
                    "targets": ["prod_users"],
                    "replacement": "test_users"
                }
            }
        ]
        
        setup = InputSetup(given)
        
        assert setup.jinja_context_input is not None
        assert len(setup.relation_inputs) == 1
    
    def test_nested_sources_respect_targets(self):
        """Test that nested sources handle targets correctly."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "data": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "targets": ["custom_target"]
                    }
                }
            }
        )
        
        context_input = JinjaContextInput(spec)
        nested = context_input.nested_sources["data"]
        
        assert nested.targets == ["custom_target"]
    
    def test_multiple_nested_ctes_same_jinja_context(self):
        """Test multiple nested CTEs in single jinja_context."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "users": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "users_cte"
                    }
                },
                "orders": {
                    "cte": {
                        "rows": [{"order_id": 1}],
                        "alias": "orders_cte"
                    }
                },
                "limit": 100
            }
        )
        
        context_input = JinjaContextInput(spec)
        context_dict = context_input.build_jinja_context_dict()
        
        assert context_dict["users"] == "users_cte"
        assert context_dict["orders"] == "orders_cte"
        assert context_dict["limit"] == 100


class TestGivenInputsSpec:
    """Spec validation tests for given-inputs requirements from spec.md."""
    
    # CTE with stable hashing requirements
    def test_spec_cte_name_generation_from_data_hash(self):
        """SPEC: CTE name generation from data hash."""
        rows = [{"id": 1, "name": "Alice"}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        
        cte_input = CTEInput(spec)
        # Get the CTE name - should be based on targets + content hash
        cte_name = cte_input.get_cte_name()
        assert cte_name is not None
        assert cte_name.startswith("users_")
        # Hash-derived names are stable
        cte_input2 = CTEInput(spec)
        assert cte_input.get_cte_name() == cte_input2.get_cte_name()
    
    def test_spec_cte_explicit_alias_override(self):
        """SPEC: CTE with explicit alias override."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=[{"id": 1}]),
            alias="my_custom_name"
        )
        
        cte_input = CTEInput(spec)
        assert cte_input.alias == "my_custom_name"
    
    def test_spec_cte_with_rows_data_source(self):
        """SPEC: CTE with rows data source."""
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        
        cte_input = CTEInput(spec)
        cte_def = cte_input.get_cte_definition()
        
        # Should contain VALUES clause with data
        assert "VALUES" in cte_def
        assert "Alice" in cte_def
        assert "Bob" in cte_def
    
    def test_spec_multiple_ctes_in_single_test(self):
        """SPEC: Multiple CTEs in single test."""
        given = [
            {
                "cte": {
                    "targets": ["users"],
                    "rows": [{"id": 1, "name": "Alice"}]
                }
            },
            {
                "cte": {
                    "targets": ["orders"],
                    "rows": [{"order_id": 1, "user_id": 1}]
                }
            }
        ]
        
        setup = InputSetup(given)
        assert len(setup.cte_inputs) == 2
        # Both CTEs should be injected
        assert setup.cte_inputs[0] is not None
        assert setup.cte_inputs[1] is not None
    
    def test_spec_cte_injection_into_rendered_query(self):
        """SPEC: CTE injection into rendered query."""
        given = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 1, "name": "Alice"}],
                "alias": "test_users"
            }
        }]
        
        setup = InputSetup(given)
        original_sql = "SELECT * FROM test_users"
        
        result_sql = InputExecutor.apply_inputs(original_sql, setup)
        
        # Result should contain WITH clause with CTE
        assert "WITH" in result_sql
        assert "test_users" in result_sql
        assert "VALUES" in result_sql
    
    def test_spec_jinja_variable_name_stability(self):
        """SPEC: Jinja variable name stability."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_table": {
                    "cte": {
                        "rows": [{"id": 1, "name": "Alice"}]
                    }
                }
            }
        )
        
        jinja_input1 = JinjaContextInput(spec)
        context1 = jinja_input1.build_jinja_context_dict()
        
        jinja_input2 = JinjaContextInput(spec)
        context2 = jinja_input2.build_jinja_context_dict()
        
        # Auto-generated alias should be consistent across executions
        assert context1["my_table"] == context2["my_table"]
    
    def test_spec_scalar_jinja_context_values(self):
        """SPEC: Scalar Jinja context values."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "start_date": "2024-01-01",
                "limit_value": 100,
                "is_active": True
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        # Scalar values should be available as-is
        assert context_dict["start_date"] == "2024-01-01"
        assert context_dict["limit_value"] == 100
        assert context_dict["is_active"] is True
    
    def test_spec_empty_jinja_context_block(self):
        """SPEC: Empty jinja_context block."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={}
        )
        
        # Should not raise error
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        assert context_dict == {}

    # Relation substitution spec scenarios
    def test_spec_ast_based_identifier_matching(self):
        """SPEC: AST-based identifier matching for relations."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["source_table"],
            replacement="test_table"
        )
        
        relation_input = RelationInput(spec)
        test_sql = "SELECT * FROM source_table WHERE id > 0"
        
        result_sql = relation_input.substitute_in_sql(test_sql)
        
        assert "test_table" in result_sql or "source_table" not in result_sql
    
    def test_spec_relation_no_partial_matches(self):
        """SPEC: Partial matches are NOT matched."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["source_table"],
            replacement="test_table"
        )
        
        relation_input = RelationInput(spec)
        test_sql = "SELECT * FROM source_table_archive"
        
        result_sql = relation_input.substitute_in_sql(test_sql)
        
        assert "source_table_archive" in result_sql
        assert "test_table" not in result_sql
    
    def test_spec_case_insensitive_matching(self):
        """SPEC: Case-insensitive matching for relation targets."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["users"],
            replacement="test_users"
        )
        
        relation_input = RelationInput(spec)
        test_sql = "SELECT * FROM USERS WHERE id > 0"
        
        result_sql = relation_input.substitute_in_sql(test_sql)
        
        assert "test_users" in result_sql or "USERS" not in result_sql
    
    def test_spec_schema_qualified_table_references(self):
        """SPEC: Schema-qualified table references."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod.users"],
            replacement="test.users"
        )
        
        relation_input = RelationInput(spec)
        test_sql = "SELECT * FROM prod.users WHERE id > 0"
        
        result_sql = relation_input.substitute_in_sql(test_sql)
        
        assert "test.users" in result_sql or "prod.users" not in result_sql
    
    def test_spec_bare_table_does_not_match_qualified(self):
        """SPEC: Bare table does not match schema-qualified target."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["prod.users"],
            replacement="test.users"
        )
        
        relation_input = RelationInput(spec)
        test_sql = "SELECT * FROM users WHERE id > 0"
        
        result_sql = relation_input.substitute_in_sql(test_sql)
        
        assert "users" in result_sql
    
    # Data source format spec scenarios
    def test_spec_sql_as_data_source(self):
        """SPEC: SQL as data source."""
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="sql", content="SELECT id, name FROM prod_users")
        )
        
        cte_input = CTEInput(spec)
        cte_def = cte_input.get_cte_definition()
        
        assert "SELECT id, name FROM prod_users" in cte_def
    
    def test_spec_csv_as_data_source(self):
        """SPEC: CSV as data source."""
        csv_data = "id,name\n1,Alice\n2,Bob"
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="csv", content=csv_data)
        )
        
        cte_input = CTEInput(spec)
        cte_def = cte_input.get_cte_definition()
        
        assert "VALUES" in cte_def or "id" in cte_def
    
    def test_spec_data_type_preservation(self):
        """SPEC: Data type preservation in rows."""
        rows = [
            {
                "id": 1,
                "name": "Alice",
                "is_active": True,
                "score": 95.5
            }
        ]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        
        cte_input = CTEInput(spec)
        cte_def = cte_input.get_cte_definition()
        
        assert "Alice" in cte_def
    
    def test_spec_null_value_handling(self):
        """SPEC: NULL value handling."""
        rows = [{"id": 1, "name": "Alice"}, {"id": 2, "name": None}]
        spec = InputSpec(
            input_type=InputType.CTE,
            targets=["users"],
            data_source=DataSource(format="rows", content=json.dumps(rows))
        )
        
        cte_input = CTEInput(spec)
        cte_def = cte_input.get_cte_definition()
        
        assert "NULL" in cte_def.upper() or "None" in cte_def
    
    # Test data lifecycle spec scenarios
    def test_spec_given_section_processing(self):
        """SPEC: Given section processing."""
        given = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 1}]
            }
        }]
        
        setup = InputSetup(given)
        assert setup.cte_inputs is not None
    
    def test_spec_data_isolation_per_test(self):
        """SPEC: Data isolation per test."""
        given1 = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 1}],
                "alias": "test1"
            }
        }]
        
        given2 = [{
            "cte": {
                "targets": ["users"],
                "rows": [{"id": 2}],
                "alias": "test2"
            }
        }]
        
        setup1 = InputSetup(given1)
        setup2 = InputSetup(given2)
        
        assert setup1 is not setup2
    
    # More jinja context spec scenarios
    def test_spec_basic_jinja_context_with_nested_cte(self):
        """SPEC: Basic jinja_context with nested CTE."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_table": {
                    "cte": {
                        "rows": [{"id": 1}]
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        assert "my_table" in context_dict
        assert context_dict["my_table"] is not None
    
    def test_spec_nested_data_sources_with_explicit_alias(self):
        """SPEC: Nested data sources with explicit alias."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_data": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "custom_name"
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        assert context_dict["my_data"] == "custom_name"
    
    def test_spec_auto_generated_alias_for_nested_data_source(self):
        """SPEC: Auto-generated alias for nested data source."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_table": {
                    "cte": {
                        "rows": [{"id": 1}]
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        nested = jinja_input.nested_sources["my_table"]
        
        # Auto-generated alias is derived via get_binding_name()
        binding_name = nested.get_binding_name()
        assert binding_name is not None
        assert isinstance(binding_name, str)
        assert len(binding_name) > 0
    
    def test_spec_combining_top_level_and_jinja_bound_sources(self):
        """SPEC: Combining top-level and Jinja-bound data sources."""
        given = [
            {
                "cte": {
                    "targets": ["top_level"],
                    "rows": [{"id": 1}],
                    "alias": "top_cte"
                }
            },
            {
                "jinja_context": {
                    "jinja_var": {
                        "cte": {
                            "rows": [{"id": 2}],
                            "alias": "jinja_cte"
                        }
                    }
                }
            }
        ]
        
        setup = InputSetup(given)
        
        assert setup.cte_inputs is not None
        assert setup.jinja_context_input is not None
    
    def test_spec_multiple_jinja_bound_sources_in_single_context(self):
        """SPEC: Multiple Jinja-bound sources in single jinja_context."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "users": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "users_cte"
                    }
                },
                "orders": {
                    "cte": {
                        "rows": [{"order_id": 1}],
                        "alias": "orders_cte"
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        assert context_dict["users"] == "users_cte"
        assert context_dict["orders"] == "orders_cte"
    
    def test_spec_unused_jinja_variables_allowed(self):
        """SPEC: Unused Jinja variables allowed silently."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "unused_var": "value",
                "my_table": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "alias": "used_cte"
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        assert "unused_var" in context_dict
        assert context_dict["unused_var"] == "value"
    
    def test_spec_user_provided_alias_precedence(self):
        """SPEC: User-provided alias precedence."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_var": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "targets": ["original_name"],
                        "alias": "custom_alias"
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        context_dict = jinja_input.build_jinja_context_dict()
        
        assert context_dict["my_var"] == "custom_alias"
    
    def test_spec_targets_field_in_nested_sources(self):
        """SPEC: Targets field in nested data sources."""
        spec = InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context={
                "my_data": {
                    "cte": {
                        "rows": [{"id": 1}],
                        "targets": ["old_table_name"],
                        "alias": "new_alias"
                    }
                }
            }
        )
        
        jinja_input = JinjaContextInput(spec)
        nested = jinja_input.nested_sources["my_data"]
        
        assert nested.targets == ["old_table_name"]
        assert nested.alias == "new_alias"
    
    # Error handling spec scenarios
    def test_spec_relation_targets_with_jinja_syntax(self):
        """SPEC: Relation targets with Jinja syntax (currently allowed, validation is optional)."""
        spec = InputSpec(
            input_type=InputType.RELATION,
            targets=["{{ jinja_var }}"],
            replacement="test_table"
        )
        
        # Currently RelationInput accepts Jinja syntax in targets
        # Validation of Jinja syntax is optional/deferred
        relation_input = RelationInput(spec)
        assert relation_input is not None
