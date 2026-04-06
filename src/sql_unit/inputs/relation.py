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

        if not parsed:
            return ""

        if len(parsed) == 1:
            self._traverse_and_replace(parsed[0])
            return str(parsed[0])

        # Handle multi-statement SQL by processing each and joining
        for statement in parsed:
            self._traverse_and_replace(statement)
        return "".join(str(statement) for statement in parsed)

    def _is_relation_keyword(self, token) -> bool:
        """Return True when the token introduces a table-reference context."""
        if token.ttype not in sqlparse.tokens.Keyword:
            return False

        normalized = token.normalized.upper()
        return normalized in {"FROM", "UPDATE", "INTO"} or normalized.endswith("JOIN")

    def _replace_relation_token(self, parent, index: int, token) -> None:
        """Replace a relation token in its parent when it matches a target."""
        identifier_text = str(token).strip()
        candidate_names = {identifier_text.lower()}

        if isinstance(token, sqlparse.sql.Identifier):
            real_name = token.get_real_name()
            if real_name:
                candidate_names.add(real_name.lower())
        elif isinstance(token, sqlparse.sql.Function):
            # For Function tokens (e.g., table_name (column_list) in INSERT INTO),
            # extract the function/table name and replace only that
            real_name = token.get_real_name()
            if real_name:
                candidate_names.add(real_name.lower())
                # Check for match and replace the first token (the function name)
                for target in self.targets:
                    if target.lower() == real_name.lower():
                        # Replace only the function name, not the entire Function token
                        for j, func_token in enumerate(token.tokens):
                            if func_token.ttype is sqlparse.tokens.Name or (
                                isinstance(func_token, sqlparse.sql.Identifier)
                            ):
                                token.tokens[j] = sql_tokens.Token(
                                    sqlparse.tokens.Name, self.replacement
                                )
                                return
                return

        for target in self.targets:
            if target.lower() in candidate_names:
                parent.tokens[index] = sql_tokens.Token(sqlparse.tokens.Name, self.replacement)
                break

    def _replace_identifier_list(self, identifier_list) -> None:
        """Replace matching relations inside an IdentifierList in table context."""
        for i, t in enumerate(identifier_list.tokens):
            if t.ttype is sqlparse.tokens.Name or isinstance(t, sqlparse.sql.Identifier):
                self._replace_relation_token(identifier_list, i, t)

    def _traverse_and_replace(self, token):
        """
        Recursively traverse SQL AST and replace matching identifiers.

        Only substitutes tokens that appear in table-reference contexts
        (for example, immediately after FROM/JOIN/UPDATE/INTO).

        Args:
            token: sqlparse token to process

        Returns:
            Modified token with replacements applied
        """
        if not hasattr(token, "tokens"):
            return token

        expecting_relation = False

        for i, t in enumerate(token.tokens):
            if self._is_relation_keyword(t):
                expecting_relation = True
                continue

            if expecting_relation:
                if t.is_whitespace or t.ttype is sqlparse.tokens.Newline:
                    continue

                if isinstance(t, sqlparse.sql.IdentifierList):
                    self._replace_identifier_list(t)
                elif isinstance(t, sqlparse.sql.Function):
                    # Handle INSERT INTO table_name (column_list) cases
                    self._replace_relation_token(token, i, t)
                elif t.ttype is sqlparse.tokens.Name or isinstance(t, sqlparse.sql.Identifier):
                    self._replace_relation_token(token, i, t)

                expecting_relation = False

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
