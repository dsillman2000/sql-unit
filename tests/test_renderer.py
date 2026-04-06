"""Unit tests for Jinja2 template rendering."""

import pytest

from sql_unit.core.exceptions import RendererError
from sql_unit.renderer import TemplateRenderer


class TestBasicRendering:
    """Tests for basic Jinja2 template rendering."""

    def test_render_simple_variable(self):
        """Test rendering simple variable substitution."""
        renderer = TemplateRenderer(jinja_context={"name": "users"})
        sql = "SELECT * FROM {{ name }};"
        result = renderer.render(sql)
        assert result == "SELECT * FROM users;"

    def test_render_multiple_variables(self):
        """Test rendering multiple variables."""
        renderer = TemplateRenderer(jinja_context={"table": "users", "schema": "public"})
        sql = "SELECT * FROM {{ schema }}.{{ table }};"
        result = renderer.render(sql)
        assert result == "SELECT * FROM public.users;"

    def test_render_no_variables(self):
        """Test rendering SQL with no variables."""
        renderer = TemplateRenderer()
        sql = "SELECT 1;"
        result = renderer.render(sql)
        assert result == "SELECT 1;"

    def test_render_with_numeric_context(self):
        """Test rendering with numeric context values."""
        renderer = TemplateRenderer(jinja_context={"limit": 10})
        sql = "SELECT * FROM users LIMIT {{ limit }};"
        result = renderer.render(sql)
        assert result == "SELECT * FROM users LIMIT 10;"

    def test_render_with_additional_context(self):
        """Test rendering with additional context merged."""
        renderer = TemplateRenderer(jinja_context={"table": "users"})
        sql = "SELECT {{ col }} FROM {{ table }};"
        result = renderer.render(sql, additional_context={"col": "id"})
        assert result == "SELECT id FROM users;"


class TestConditionalLogic:
    """Tests for Jinja2 conditional blocks."""

    def test_render_if_condition_true(self):
        """Test rendering IF block when condition is true."""
        renderer = TemplateRenderer(jinja_context={"active": True})
        sql = """
        SELECT * FROM users
        {% if active %}WHERE status = 'active'{% endif %}
        """
        result = renderer.render(sql)
        assert "status = 'active'" in result

    def test_render_if_condition_false(self):
        """Test rendering IF block when condition is false."""
        renderer = TemplateRenderer(jinja_context={"active": False})
        sql = """
        SELECT * FROM users
        {% if active %}WHERE status = 'active'{% endif %}
        """
        result = renderer.render(sql)
        assert "status = 'active'" not in result

    def test_render_if_else_block(self):
        """Test rendering IF-ELSE block."""
        renderer = TemplateRenderer(jinja_context={"show_deleted": False})
        sql = """
        SELECT * FROM users
        {% if show_deleted %}
        WHERE deleted = true
        {% else %}
        WHERE deleted = false
        {% endif %}
        """
        result = renderer.render(sql)
        assert "deleted = false" in result
        assert "deleted = true" not in result


class TestFilters:
    """Tests for Jinja2 filters."""

    def test_render_upper_filter(self):
        """Test uppercase filter."""
        renderer = TemplateRenderer(jinja_context={"status": "active"})
        sql = "WHERE status = '{{ status | upper }}';"
        result = renderer.render(sql)
        assert "ACTIVE" in result

    def test_render_lower_filter(self):
        """Test lowercase filter."""
        renderer = TemplateRenderer(jinja_context={"status": "ACTIVE"})
        sql = "WHERE status = '{{ status | lower }}';"
        result = renderer.render(sql)
        assert "active" in result


class TestLoops:
    """Tests for Jinja2 loops."""

    def test_render_for_loop(self):
        """Test rendering FOR loop."""
        renderer = TemplateRenderer(jinja_context={"columns": ["id", "name", "email"]})
        sql = "SELECT {% for col in columns %}{{ col }}, {% endfor %} FROM users;"
        result = renderer.render(sql)
        assert "id" in result
        assert "name" in result
        assert "email" in result


class TestErrorHandling:
    """Tests for error handling in rendering."""

    def test_error_undefined_variable(self):
        """Test error when variable is undefined."""
        renderer = TemplateRenderer()
        sql = "SELECT * FROM {{ undefined_table }};"
        with pytest.raises(RendererError):
            renderer.render(sql)

    def test_error_syntax_error(self):
        """Test error for invalid Jinja2 syntax."""
        renderer = TemplateRenderer()
        sql = "SELECT * FROM {{ table } FROM users;"
        with pytest.raises(RendererError):
            renderer.render(sql)

    def test_error_includes_test_id(self):
        """Test that error includes test ID."""
        renderer = TemplateRenderer()
        sql = "SELECT * FROM {{ undefined }};"
        with pytest.raises(RendererError) as exc_info:
            renderer.render(sql, test_id="test_file.sql::my_test")
        assert "my_test" in str(exc_info.value)

    def test_error_includes_sql(self):
        """Test that error includes the problematic SQL."""
        renderer = TemplateRenderer()
        sql = "SELECT * FROM {{ undefined }};"
        with pytest.raises(RendererError) as exc_info:
            renderer.render(sql)
        assert "SELECT" in str(exc_info.value)


class TestContextManagement:
    """Tests for context management."""

    def test_add_context_variable(self):
        """Test adding context variable."""
        renderer = TemplateRenderer()
        renderer.add_context("table", "users")
        sql = "SELECT * FROM {{ table }};"
        result = renderer.render(sql)
        assert "users" in result

    def test_update_context_dict(self):
        """Test updating context with dict."""
        renderer = TemplateRenderer()
        renderer.update_context({"table": "users", "schema": "public"})
        sql = "SELECT * FROM {{ schema }}.{{ table }};"
        result = renderer.render(sql)
        assert "public.users" in result

    def test_context_isolation(self):
        """Test that contexts are isolated between renderers."""
        renderer1 = TemplateRenderer(jinja_context={"table": "users"})
        renderer2 = TemplateRenderer()

        # renderer1 should work
        sql1 = "SELECT * FROM {{ table }};"
        result1 = renderer1.render(sql1)
        assert "users" in result1

        # renderer2 should fail
        sql2 = "SELECT * FROM {{ table }};"
        with pytest.raises(RendererError):
            renderer2.render(sql2)
