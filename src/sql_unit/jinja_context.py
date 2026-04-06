"""Jinja context nested data sources implementation."""

from typing import Any

from sql_unit.core.exceptions import ConfigError
from sql_unit.core.models import InputSpec, InputType
from sql_unit.inputs import AliasDeriver, DataSourceParser


class JinjaContextDataSource:
    """Represents a data source nested within jinja_context."""

    def __init__(self, var_name: str, spec: dict[str, Any]):
        """
        Initialize nested data source.

        Args:
            var_name: Jinja variable name
            spec: Nested source specification (cte, temp_table, or scalar value)
        """
        self.var_name = var_name
        self.spec = spec
        self.is_data_source = False
        self.data_source = None
        self.alias = None
        self.source_type = None  # 'cte', 'temp_table', or None for scalar

        self._parse_spec()

    def _parse_spec(self) -> None:
        """Parse the nested specification."""
        if not isinstance(self.spec, dict):
            # Scalar value
            return

        if "cte" in self.spec:
            self.is_data_source = True
            self.source_type = "cte"
            cte_spec = self.spec["cte"]
            self.data_source = DataSourceParser.parse_data_source(cte_spec)
            self.alias = cte_spec.get("alias")
            self.targets = cte_spec.get("targets", [self.var_name])

        elif "temp_table" in self.spec:
            self.is_data_source = True
            self.source_type = "temp_table"
            tt_spec = self.spec["temp_table"]
            self.data_source = DataSourceParser.parse_data_source(tt_spec)
            self.alias = tt_spec.get("alias")
            self.targets = tt_spec.get("targets", [self.var_name])

        # Otherwise it's a scalar value - no further processing needed

    def get_binding_name(self) -> str:
        """
        Get the identifier name for Jinja binding.

        Returns:
            Alias (if provided) or derived hash-based name
        """
        if not self.is_data_source:
            # Scalar value - return as-is
            return str(self.spec)

        if self.alias:
            return self.alias

        # Derive from var_name and data content
        return AliasDeriver.derive_alias(self.var_name, self.data_source)


class JinjaContextInput:
    """Manages jinja_context input specifications."""

    def __init__(self, spec: InputSpec):
        """
        Initialize Jinja context input from InputSpec.

        Args:
            spec: InputSpec with InputType.JINJA_CONTEXT
        """
        if spec.input_type != InputType.JINJA_CONTEXT:
            raise ValueError("JinjaContextInput requires InputType.JINJA_CONTEXT")

        self.spec = spec
        self.jinja_context_raw = spec.jinja_context
        self.nested_sources = {}
        self.scalar_vars = {}

        self._process_context()

    def _process_context(self) -> None:
        """Process jinja_context and extract data sources and scalars."""
        for var_name, var_spec in self.jinja_context_raw.items():
            if isinstance(var_spec, dict):
                # Likely a data source (cte, temp_table)
                nested = JinjaContextDataSource(var_name, var_spec)
                if nested.is_data_source:
                    self.nested_sources[var_name] = nested
                else:
                    # Empty dict treated as scalar
                    self.scalar_vars[var_name] = var_spec
            else:
                # Scalar value
                self.scalar_vars[var_name] = var_spec

    def build_jinja_context_dict(self) -> dict[str, Any]:
        """
        Build the context dict for Jinja rendering.

        Returns:
            Dict mapping variable names to their bound values (alias names for data sources)
        """
        context = {}

        # Add nested data source bindings (alias names)
        for var_name, nested in self.nested_sources.items():
            binding_name = nested.get_binding_name()
            context[var_name] = binding_name

        # Add scalar variables
        for var_name, value in self.scalar_vars.items():
            context[var_name] = value

        return context

    def get_nested_sources(self) -> dict[str, JinjaContextDataSource]:
        """Get all nested data sources."""
        return self.nested_sources

    def get_scalar_vars(self) -> dict[str, Any]:
        """Get all scalar variables."""
        return self.scalar_vars


class JinjaContextCollisionDetector:
    """Detects collisions between Jinja variables and data source aliases."""

    @staticmethod
    def check_collisions(jinja_input: JinjaContextInput, all_input_specs: list[InputSpec]) -> None:
        """
        Check for collisions between Jinja variables and other data source aliases.

        Args:
            jinja_input: JinjaContextInput to check
            all_input_specs: All input specs in the test

        Raises:
            ConfigError: If collision detected
        """
        # Collect all generated aliases from top-level sources
        top_level_aliases = {}

        for spec in all_input_specs:
            if spec.input_type == InputType.CTE and spec.data_source:
                base_name = spec.targets[0] if spec.targets else "unknown"
                if spec.alias:
                    top_level_aliases[spec.alias] = spec
                else:
                    derived = AliasDeriver.derive_alias(base_name, spec.data_source)
                    top_level_aliases[derived] = spec

        # Check Jinja variables against top-level aliases
        for var_name in jinja_input.jinja_context_raw.keys():
            if var_name in top_level_aliases:
                raise ConfigError(
                    f"Jinja variable '{var_name}' collides with auto-derived alias from "
                    f"CTE data source. Rename the Jinja variable or provide explicit `alias:` "
                    f"on the conflicting data source."
                )

        # Check for duplicate Jinja variables (already checked in GivenClauseParser)
        # but we can re-check here for safety
        var_names = list(jinja_input.jinja_context_raw.keys())
        if len(var_names) != len(set(var_names)):
            duplicates = [name for name in var_names if var_names.count(name) > 1]
            raise ConfigError(f"Duplicate jinja_context variables: {duplicates}")
            duplicates = [name for name in var_names if var_names.count(name) > 1]
            raise ConfigError(f"Duplicate jinja_context variables: {duplicates}")
