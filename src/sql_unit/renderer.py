"""Jinja2 template rendering for SQL statements."""

from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError

from .exceptions import RendererError


class TemplateRenderer:
    """Renders SQL statements with Jinja2 template support."""
    
    def __init__(self, jinja_context: dict[str, Any] | None = None):
        """
        Initialize template renderer with optional context.
        
        Args:
            jinja_context: Dictionary of variables available in templates
        """
        self.jinja_context = jinja_context or {}
        self.env = Environment(
            # Don't trim blocks or strip newlines to preserve SQL formatting
            trim_blocks=False,
            lstrip_blocks=False,
            # Use StrictUndefined to error on undefined variables
            undefined=StrictUndefined
        )
    
    def render(
        self,
        sql: str,
        test_id: str | None = None,
        additional_context: dict[str, Any] | None = None
    ) -> str:
        """
        Render SQL statement with Jinja2 template support.
        
        Args:
            sql: SQL statement potentially containing Jinja2 templates
            test_id: Test identifier for error reporting
            additional_context: Additional variables to merge with jinja_context
            
        Returns:
            Rendered SQL with templates resolved
            
        Raises:
            RendererError: If template rendering fails
        """
        try:
            # Merge contexts
            context = {**self.jinja_context}
            if additional_context:
                context.update(additional_context)
            
            # Create and render template
            template = self.env.from_string(sql)
            rendered = template.render(**context)
            
            return rendered
            
        except TemplateSyntaxError as e:
            raise RendererError(
                f"Jinja2 syntax error: {str(e)}",
                test_id=test_id,
                sql=sql
            )
        except UndefinedError as e:
            raise RendererError(
                f"Undefined variable in template: {str(e)}",
                test_id=test_id,
                sql=sql
            )
        except Exception as e:
            raise RendererError(
                f"Template rendering failed: {str(e)}",
                test_id=test_id,
                sql=sql
            )
    
    def add_context(self, key: str, value: Any) -> None:
        """Add a variable to the template context."""
        self.jinja_context[key] = value
    
    def update_context(self, context: dict[str, Any]) -> None:
        """Update template context with multiple variables."""
        self.jinja_context.update(context)


class ParameterizedSqlBuilder:
    """Builds parameterized SQL to protect against injection."""
    
    @staticmethod
    def parameterize_context(context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Convert context variables to parameterized form.
        
        Separates SQL identifiers (table/column names) from values.
        
        Args:
            context: Original context dict
            
        Returns:
            Tuple of (identifier_map, param_values) where:
            - identifier_map: Maps variable names to placeholders
            - param_values: Values to be bound as parameters
        """
        identifiers = {}
        params = {}
        
        for key, value in context.items():
            if isinstance(value, str) and _looks_like_identifier(value):
                # Store as identifier (table/column name)
                identifiers[key] = value
            else:
                # Store as parameter
                params[key] = value
        
        return identifiers, params


def _looks_like_identifier(value: str) -> bool:
    """
    Heuristic to detect if a value looks like a SQL identifier.
    
    Returns True if value looks like a table or column name.
    """
    if not isinstance(value, str):
        return False
    
    # Identifiers: alphanumeric + underscore, may have dots (schema.table)
    import re
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', value))
