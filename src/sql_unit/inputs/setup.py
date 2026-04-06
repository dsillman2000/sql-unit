"""Input setup orchestrator and execution pipeline."""

from typing import Any

from sql_unit.core.exceptions import ConfigError, TemplateError
from sql_unit.core.models import InputType
from sql_unit.inputs import GivenClauseParser, GivenClauseValidator
from sql_unit.inputs.cte import CTEInjector, CTEInput
from sql_unit.inputs.jinja_context import (
    JinjaContextCollisionDetector,
    JinjaContextInput,
)
from sql_unit.inputs.relation import RelationInput, RelationSubstitutor


class InputSetup:
    """Orchestrates input setup from given clause."""

    def __init__(self, given_spec: dict[str, Any]):
        """
        Initialize input setup from given specification.

        Args:
            given_spec: The 'given' dict from test definition
        """
        self.given_spec = given_spec
        self.input_specs = []
        self.cte_inputs = []
        self.relation_inputs = []
        self.jinja_context_input = None

        self._parse_and_validate()

    def _parse_and_validate(self) -> None:
        """Parse given clause and validate inputs."""
        # Parse input specifications
        self.input_specs = GivenClauseParser.parse_given_clause(self.given_spec)

        # Validate inputs for conflicts
        GivenClauseValidator.validate_input_specs(self.input_specs)

        # Separate inputs by type and validate collisions
        for spec in self.input_specs:
            if spec.input_type == InputType.CTE:
                self.cte_inputs.append(CTEInput(spec))

            elif spec.input_type == InputType.RELATION:
                self.relation_inputs.append(RelationInput(spec))

            elif spec.input_type == InputType.JINJA_CONTEXT:
                if self.jinja_context_input:
                    raise ConfigError("Only one jinja_context block allowed per test")
                self.jinja_context_input = JinjaContextInput(spec)

        # Check for collisions between Jinja variables and data source aliases
        if self.jinja_context_input:
            JinjaContextCollisionDetector.check_collisions(
                self.jinja_context_input, self.input_specs
            )

    def build_jinja_context(self) -> dict[str, Any]:
        """
        Build context dict for Jinja rendering.

        Returns:
            Dict mapping Jinja variable names to values/aliases
        """
        if not self.jinja_context_input:
            return {}

        return self.jinja_context_input.build_jinja_context_dict()

    def get_cte_inputs(self) -> list[CTEInput]:
        """Get all CTE inputs."""
        return self.cte_inputs

    def get_relation_inputs(self) -> list[RelationInput]:
        """Get all relation inputs."""
        return self.relation_inputs

    def get_jinja_context_input(self) -> JinjaContextInput | None:
        """Get jinja_context input if present."""
        return self.jinja_context_input


class InputExecutor:
    """Executes the input setup and applies transformations to SQL."""

    @staticmethod
    def apply_inputs(sql: str, input_setup: InputSetup, jinja_renderer=None, database_manager=None) -> str:
        """
        Apply all inputs to SQL in execution order.

        Execution order:
        1. Build jinja_context dict
        2. Render Jinja templates in SQL
        3. Parse rendered SQL
        4. Inject CTEs
        5. Apply relation substitutions

        Args:
            sql: Original SQL query
            input_setup: InputSetup orchestrator
            jinja_renderer: Jinja renderer callable (sql, context) -> rendered_sql
            database_manager: DatabaseManager instance for SQL execution and dialect info

        Returns:
            Final SQL with all inputs applied

        Raises:
            SetupError: If setup fails
            TemplateError: If Jinja rendering fails
        """
        result_sql = sql

        # Step 1: Build jinja context
        jinja_context = input_setup.build_jinja_context()

        # Step 2: Render Jinja templates in SQL
        if jinja_context and jinja_renderer:
            try:
                result_sql = jinja_renderer(result_sql, jinja_context)
            except Exception as e:
                raise TemplateError(f"Jinja rendering failed: {str(e)}")

        # Step 3-4: Inject CTEs
        cte_inputs = input_setup.get_cte_inputs()
        if cte_inputs:
            result_sql = CTEInjector.inject_ctes(result_sql, cte_inputs, database_manager)

        # Step 5: Apply relation substitutions
        relation_inputs = input_setup.get_relation_inputs()
        if relation_inputs:
            result_sql = RelationSubstitutor.apply_substitutions(result_sql, relation_inputs)

        return result_sql


class InputValidator:
    """Validates inputs for completeness and correctness."""

    @staticmethod
    def validate_inputs_compatible(input_setup: InputSetup) -> None:
        """
        Validate that inputs work together correctly.

        Args:
            input_setup: InputSetup to validate

        Raises:
            ConfigError: If inputs are incompatible
        """
        # Check for potential conflicts
        cte_names = set()
        for cte_input in input_setup.get_cte_inputs():
            name = cte_input.get_cte_name()
            if name in cte_names:
                raise ConfigError(f"CTE name collision: '{name}' defined multiple times")
            cte_names.add(name)
