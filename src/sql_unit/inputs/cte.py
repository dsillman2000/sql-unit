"""CTE (Common Table Expression) input type implementation."""

from typing import Any

from sql_unit.core.models import InputSpec, InputType, DataSourceConverter
from sql_unit.core.exceptions import SetupError
from sql_unit.inputs.inputs import AliasDeriver


class CTEInput:
    """Represents and manages CTE input specifications."""

    def __init__(self, spec: InputSpec):
        """
        Initialize CTE input from InputSpec.

        Args:
            spec: InputSpec with InputType.CTE
        """
        if spec.input_type != InputType.CTE:
            raise ValueError("CTEInput requires InputType.CTE")

        self.spec = spec
        self.targets = spec.targets
        self.data_source = spec.data_source
        self.alias = spec.alias
        self._cte_name = None

    def get_cte_name(self) -> str:
        """
        Get the CTE identifier name (alias or derived).

        Returns:
            CTE name to use in SQL
        """
        if self._cte_name:
            return self._cte_name

        if self.alias:
            self._cte_name = self.alias
        else:
            # Derive from first target and data content
            base_name = self.targets[0]
            self._cte_name = AliasDeriver.derive_alias(base_name, self.data_source)

        return self._cte_name

    def get_cte_definition(self, database_manager=None) -> str:
        """
        Generate CTE definition SQL.

        Returns:
            SQL snippet for CTE, e.g., "users_abc123 AS (SELECT ...)"

        Raises:
            SetupError: If data source is invalid or database_manager required for SQL
        """
        cte_name = self.get_cte_name()

        if self.data_source.format == "sql":
            # SQL data source: use directly (do not execute)
            cte_sql = self.data_source.content

        else:
            # CSV or rows: convert to VALUES clause using DataSourceConverter
            rows = DataSourceConverter.to_rows(self.data_source, database_manager)
            cte_sql = self._generate_values_clause(rows)

        return f"{cte_name} AS ({cte_sql})"

    def _generate_values_clause(self, rows: list[dict[str, Any]]) -> str:
        """
        Generate VALUES clause from rows.

        Args:
            rows: List of dicts

        Returns:
            SQL SELECT statement using VALUES clause
        """
        if not rows:
            raise SetupError("Cannot generate CTE from empty rows")

        # Get column names from first row
        first_row = rows[0]
        columns = list(first_row.keys())

        # Build VALUES clause
        values_rows = []
        for row in rows:
            values = []
            for col in columns:
                val = row.get(col)
                if val is None:
                    values.append("NULL")
                elif isinstance(val, bool):
                    # Handle booleans before int check since bool is subclass of int
                    values.append("TRUE" if val else "FALSE")
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    # Quote strings
                    escaped = str(val).replace("'", "''")
                    values.append(f"'{escaped}'")
            values_rows.append(f"({', '.join(values)})")

        # Generate SQL
        columns_str = ", ".join(columns)
        values_str = ", ".join(values_rows)

        return f"SELECT {columns_str} FROM (VALUES {values_str}) AS t({columns_str})"


class CTEInjector:
    """Injects CTEs into SQL queries."""

    @staticmethod
    def inject_ctes(sql: str, cte_inputs: list[CTEInput], database_manager=None) -> str:
        """
        Inject CTE definitions into SQL query.

        Args:
            sql: Original SQL query
            cte_inputs: List of CTEInput objects
            database_manager: DatabaseManager instance for SQL execution and dialect info

        Returns:
            SQL with CTEs prepended as WITH clause

        Raises:
            SetupError: If SQL or CTEs are malformed
        """
        if not cte_inputs:
            return sql

        # Generate CTE definitions
        cte_defs = []
        for cte_input in cte_inputs:
            cte_defs.append(cte_input.get_cte_definition(database_manager))

        # Build WITH clause
        cte_list = ", ".join(cte_defs)

        # If SQL already has WITH clause, we need to merge (future enhancement)
        # For now, we'll prepend our CTEs
        if sql.strip().upper().startswith("WITH"):
            # SQL already has CTEs - need to merge
            # Extract existing WITH ... AS part
            # This is simplified; full implementation would use AST parsing
            raise SetupError("Merging multiple WITH clauses not yet implemented")

        # Inject CTEs
        return f"WITH {cte_list}\n{sql}"
