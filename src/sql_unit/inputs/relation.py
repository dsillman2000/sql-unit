"""Relation (table substitution) input type implementation with AST-based replacement."""

import re
from typing import Any
from ..core.models import InputSpec, InputType
from ..core.exceptions import SetupError, ConfigError

try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False


class RelationInput:
    """Represents and manages relation (table substitution) input specifications."""
    
    def __init__(self, spec: InputSpec):
        """
        Initialize relation input from InputSpec.
        
        Args:
            spec: InputSpec with InputType.RELATION
        """
        if spec.input_type != InputType.RELATION:
            raise ValueError("RelationInput requires InputType.RELATION")
        
        self.spec = spec
        self.targets = spec.targets
        self.replacement = spec.replacement
    
    def substitute_in_sql(self, sql: str) -> str:
        """
        Apply relation substitution to SQL.
        
        Args:
            sql: SQL query to modify
            
        Returns:
            SQL with substitutions applied
            
        Raises:
            SetupError: If SQL parsing fails
        """
        if SQLPARSE_AVAILABLE:
            return self._substitute_ast_based(sql)
        else:
            # Fallback to case-insensitive regex
            return self._substitute_regex_based(sql)
    
    def _substitute_ast_based(self, sql: str) -> str:
        """
        Substitute identifiers using AST-based matching (sqlparse).
        
        Args:
            sql: SQL query
            
        Returns:
            SQL with substitutions applied
        """
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return sql
            
            statement = parsed[0]
            result_sql = self._traverse_and_replace(statement)
            return str(result_sql)
        
        except Exception as e:
            raise SetupError(f"SQL AST parsing error: {str(e)}")
    
    def _traverse_and_replace(self, token):
        """
        Recursively traverse token tree and replace matching identifiers.
        
        Args:
            token: sqlparse token/statement
            
        Returns:
            Modified token with replacements applied
        """
        import sqlparse
        
        if hasattr(token, 'tokens'):
            # Recursively process child tokens
            for i, t in enumerate(token.tokens):
                # Check if this token is an identifier matching a target
                if t.ttype is sqlparse.tokens.Name or isinstance(t, sqlparse.sql.Identifier):
                    identifier_text = str(t).strip()
                    
                    # Match against targets (case-insensitive)
                    for target in self.targets:
                        if identifier_text.lower() == target.lower():
                            token.tokens[i] = sqlparse.Token(sqlparse.tokens.Name, self.replacement)
                            break
                
                # Recurse into nested structures
                if hasattr(t, 'tokens'):
                    self._traverse_and_replace(t)
        
        return token
    
    def _substitute_regex_based(self, sql: str) -> str:
        """
        Substitute identifiers using case-insensitive regex (fallback).
        
        Args:
            sql: SQL query
            
        Returns:
            SQL with substitutions applied
        """
        for target in self.targets:
            # Create case-insensitive regex that matches whole identifiers
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(target) + r'\b'
            sql = re.sub(pattern, self.replacement, sql, flags=re.IGNORECASE)
        
        return sql


class RelationSubstitutor:
    """Applies multiple relation substitutions to SQL."""
    
    @staticmethod
    def apply_substitutions(sql: str, relation_inputs: list[RelationInput]) -> str:
        """
        Apply multiple relation substitutions in sequence.
        
        Args:
            sql: SQL query
            relation_inputs: List of RelationInput objects
            
        Returns:
            SQL with all substitutions applied
        """
        result_sql = sql
        for relation_input in relation_inputs:
            result_sql = relation_input.substitute_in_sql(result_sql)
        
        return result_sql
