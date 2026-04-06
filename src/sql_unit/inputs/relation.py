"""Relation (table substitution) input type implementation with AST-based replacement."""

import sqlparse
import sqlparse.sql as sql_tokens
from sql_unit.core.models import InputSpec, InputType


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
        return self._substitute_ast_based(sql)

    def _substitute_ast_based(self, sql: str) -> str:
        """
        Substitute identifiers using AST-based matching (sqlparse).

        Args:
            sql: SQL query

        Returns:
            SQL with substitutions applied
        """
        parsed = sqlparse.parse(sql)

        for statement in parsed:
            self._traverse_and_replace(statement)

        return str(parsed[0]) if len(parsed) == 1 else str(parsed)

    def _traverse_and_replace(self, token):
        """
        Recursively traverse SQL AST and replace matching identifiers.

        Args:
            token: sqlparse token to process

        Returns:
            Modified token with replacements applied
        """
        if hasattr(token, "tokens"):
            for i, t in enumerate(token.tokens):
                if t.ttype is sqlparse.tokens.Name or isinstance(t, sqlparse.sql.Identifier):
                    identifier_text = str(t).strip()

                    for target in self.targets:
                        if identifier_text.lower() == target.lower():
                            token.tokens[i] = sql_tokens.Token(
                                sqlparse.tokens.Name, self.replacement
                            )
                            break

                if hasattr(t, "tokens"):
                    self._traverse_and_replace(t)

        return token


class RelationSubstitutor:
    """Applies multiple relation substitutions to SQL."""

    @staticmethod
    def apply_substitutions(sql: str, relation_inputs: list["RelationInput"]) -> str:
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
