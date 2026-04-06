"""Input specification parsing and validation for given: clause."""

import hashlib
import csv
import io
import json
from typing import Any
from dataclasses import dataclass

from ..core.models import InputType, DataSource, InputSpec
from ..core.exceptions import ConfigError, SetupError, TemplateError


class DataSourceFormat:
    """Supported data source formats."""
    SQL = "sql"
    CSV = "csv"
    ROWS = "rows"


class CSVDialectDetector:
    """Auto-detects CSV dialect from content."""
    
    @staticmethod
    def detect_delimiter(csv_content: str) -> str:
        """
        Auto-detect CSV delimiter from content.
        
        Args:
            csv_content: CSV string content
            
        Returns:
            Detected delimiter character (comma, tab, pipe, or semicolon)
        """
        # Get first non-empty line
        lines = [line for line in csv_content.split('\n') if line.strip()]
        if not lines:
            return ','
        
        first_line = lines[0]
        
        # Count potential delimiters
        delimiters = [',', '\t', '|', ';']
        delimiter_counts = {d: first_line.count(d) for d in delimiters}
        
        # Pick the delimiter with most occurrences (preference: comma > tab > pipe > semicolon)
        for delim in delimiters:
            if delimiter_counts[delim] > 0:
                return delim
        
        return ','  # Default to comma


class CSVParser:
    """Parser for CSV data format."""
    
    @staticmethod
    def parse_csv(csv_content: str) -> list[dict[str, Any]]:
        """
        Parse CSV content into list of dicts.
        
        Args:
            csv_content: CSV string with header row and data rows
            
        Returns:
            List of dicts with CSV data
            
        Raises:
            SetupError: If CSV parsing fails
        """
        delimiter = CSVDialectDetector.detect_delimiter(csv_content)
        
        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
            rows = []
            for i, row in enumerate(reader):
                # Convert empty strings to None
                converted_row = {k: None if v == '' else v for k, v in row.items()}
                rows.append(converted_row)
            
            if not rows:
                raise SetupError("CSV has header but no data rows")
            
            return rows
        except csv.Error as e:
            raise SetupError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            raise SetupError(f"Unexpected error parsing CSV: {str(e)}")


class RowsParser:
    """Parser for rows data format (YAML list of dicts)."""
    
    @staticmethod
    def parse_rows(rows_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Parse rows data format.
        
        Args:
            rows_data: List of dicts
            
        Returns:
            Validated list of dicts
            
        Raises:
            SetupError: If rows format is invalid
        """
        if not rows_data:
            raise SetupError("rows must contain at least one row")
        
        for i, row in enumerate(rows_data):
            if not isinstance(row, dict):
                raise SetupError(f"Row {i} must be a dict, got {type(row).__name__}")
        
        return rows_data


class SQLValidator:
    """Validator for SQL data format."""
    
    @staticmethod
    def validate_sql(sql: str) -> str:
        """
        Validate SQL content.
        
        Args:
            sql: SQL query string
            
        Returns:
            Trimmed SQL string
            
        Raises:
            SetupError: If SQL is invalid
        """
        trimmed = sql.strip()
        if not trimmed:
            raise SetupError("SQL data source cannot be empty")
        
        # Check that it looks like a SELECT statement
        if not trimmed.upper().startswith(('SELECT', 'WITH')):
            raise SetupError("SQL data source must start with SELECT or WITH")
        
        return trimmed


class DataSourceParser:
    """Parser for data source specifications (sql, csv, rows)."""
    
    @staticmethod
    def parse_data_source(source_spec: dict[str, Any]) -> DataSource:
        """
        Parse a data source specification.
        
        Args:
            source_spec: Dict with one of: {sql: "..."}, {csv: "..."}, {rows: [...]}
            
        Returns:
            DataSource object with format and content
            
        Raises:
            ConfigError: If data source format is invalid
        """
        if "sql" in source_spec:
            sql = source_spec["sql"]
            if not isinstance(sql, str):
                raise ConfigError("sql data source must be a string")
            validated_sql = SQLValidator.validate_sql(sql)
            return DataSource(format=DataSourceFormat.SQL, content=validated_sql)
        
        elif "csv" in source_spec:
            csv_content = source_spec["csv"]
            if not isinstance(csv_content, str):
                raise ConfigError("csv data source must be a string")
            # Validate CSV format
            CSVParser.parse_csv(csv_content)  # Will raise SetupError if invalid
            return DataSource(format=DataSourceFormat.CSV, content=csv_content)
        
        elif "rows" in source_spec:
            rows = source_spec["rows"]
            if not isinstance(rows, list):
                raise ConfigError("rows data source must be a list")
            # Validate rows format
            validated_rows = RowsParser.parse_rows(rows)
            # Serialize rows to string for storage
            content = json.dumps(validated_rows)
            return DataSource(format=DataSourceFormat.ROWS, content=content)
        
        else:
            raise ConfigError(
                f"Unknown data source format. Expected one of: sql, csv, rows. "
                f"Got keys: {list(source_spec.keys())}"
            )
    
    @staticmethod
    def get_rows(data_source: DataSource) -> list[dict[str, Any]]:
        """
        Extract rows from a data source.
        
        Args:
            data_source: DataSource object
            
        Returns:
            List of dicts representing rows
            
        Raises:
            SetupError: If data source format is invalid
        """
        if data_source.format == DataSourceFormat.SQL:
            raise SetupError("Cannot extract rows from SQL data source without execution")
        
        elif data_source.format == DataSourceFormat.CSV:
            return CSVParser.parse_csv(data_source.content)
        
        elif data_source.format == DataSourceFormat.ROWS:
            return json.loads(data_source.content)
        
        else:
            raise SetupError(f"Unknown data source format: {data_source.format}")


class AliasDeriver:
    """Derives stable hash-based aliases for data sources."""
    
    @staticmethod
    def derive_alias(base_name: str, data_source: DataSource) -> str:
        """
        Derive a stable hash-based alias.
        
        Args:
            base_name: Base name (targets name or variable name)
            data_source: DataSource object with content
            
        Returns:
            Alias in format: <base_name>_<hash>
        """
        # Create stable hash from data content
        content_bytes = data_source.content.encode('utf-8')
        content_hash = hashlib.sha256(content_bytes).hexdigest()[:8]
        
        # Sanitize base name: replace dots and hyphens with underscores
        sanitized = base_name.replace('.', '_').replace('-', '_').replace(' ', '_')
        
        return f"{sanitized}_{content_hash}"


class GivenClauseParser:
    """Parser for given: clause in test definitions."""
    
    @staticmethod
    def parse_given_clause(given_spec: dict[str, Any]) -> list[InputSpec]:
        """
        Parse the given clause from a test definition.
        
        Args:
            given_spec: The given dict from test definition (may be empty)
            
        Returns:
            List of InputSpec objects representing inputs
            
        Raises:
            ConfigError: If given clause structure is invalid
        """
        if not given_spec:
            return []
        
        input_specs = []
        
        # Handle list format: given: [cte: {...}, relation: {...}, ...]
        if isinstance(given_spec, list):
            for item in given_spec:
                if not isinstance(item, dict):
                    raise ConfigError(f"given list items must be dicts, got {type(item).__name__}")
                input_specs.extend(GivenClauseParser._parse_given_item(item))
        
        # Handle dict format: given: {cte: ..., relation: ...}
        elif isinstance(given_spec, dict):
            input_specs.extend(GivenClauseParser._parse_given_item(given_spec))
        
        else:
            raise ConfigError(f"given must be a list or dict, got {type(given_spec).__name__}")
        
        return input_specs
    
    @staticmethod
    def _parse_given_item(item: dict[str, Any]) -> list[InputSpec]:
        """
        Parse a single item from the given clause.
        
        Args:
            item: Single input specification dict
            
        Returns:
            List of InputSpec objects (usually 1, may be multiple for nested sources)
        """
        specs = []
        
        # CTE input
        if "cte" in item:
            cte_spec = item["cte"]
            if not isinstance(cte_spec, dict):
                raise ConfigError("cte specification must be a dict")
            spec = GivenClauseParser._parse_cte_input(cte_spec)
            specs.append(spec)
        
        # Relation input
        elif "relation" in item:
            relation_spec = item["relation"]
            if not isinstance(relation_spec, dict):
                raise ConfigError("relation specification must be a dict")
            spec = GivenClauseParser._parse_relation_input(relation_spec)
            specs.append(spec)
        
        # Jinja context input
        elif "jinja_context" in item:
            jinja_spec = item["jinja_context"]
            if not isinstance(jinja_spec, dict):
                raise ConfigError("jinja_context specification must be a dict")
            spec = GivenClauseParser._parse_jinja_context_input(jinja_spec)
            specs.append(spec)
        
        else:
            raise ConfigError(
                f"Unknown input type. Expected one of: cte, relation, jinja_context. "
                f"Got keys: {list(item.keys())}"
            )
        
        return specs
    
    @staticmethod
    def _parse_cte_input(cte_spec: dict[str, Any]) -> InputSpec:
        """Parse CTE input specification."""
        targets = cte_spec.get("targets", [])
        if not isinstance(targets, list):
            raise ConfigError("cte.targets must be a list")
        
        if not targets:
            raise ConfigError("cte must have targets field")
        
        # Parse data source
        data_source = DataSourceParser.parse_data_source(cte_spec)
        
        # Optional alias override
        alias = cte_spec.get("alias")
        
        return InputSpec(
            input_type=InputType.CTE,
            targets=targets,
            data_source=data_source,
            alias=alias
        )
    
    @staticmethod
    def _parse_relation_input(relation_spec: dict[str, Any]) -> InputSpec:
        """Parse relation (table substitution) input specification."""
        targets = relation_spec.get("targets", [])
        replacement = relation_spec.get("replacement")
        
        if not isinstance(targets, list):
            raise ConfigError("relation.targets must be a list")
        
        if not targets:
            raise ConfigError("relation must have targets field")
        
        if not replacement or not isinstance(replacement, str):
            raise ConfigError("relation must have replacement field (string)")
        
        # Validate that targets don't contain Jinja syntax
        for target in targets:
            if "{{" in target or "{%" in target:
                raise ConfigError(
                    f"relation.targets cannot contain Jinja syntax: '{target}'. "
                    f"Use jinja_context to parameterize identifiers."
                )
        
        return InputSpec(
            input_type=InputType.RELATION,
            targets=targets,
            replacement=replacement
        )
    
    @staticmethod
    def _parse_jinja_context_input(jinja_spec: dict[str, Any]) -> InputSpec:
        """Parse jinja_context input specification."""
        # Check for duplicate variable names
        var_names = list(jinja_spec.keys())
        if len(var_names) != len(set(var_names)):
            duplicates = [name for name in var_names if var_names.count(name) > 1]
            raise ConfigError(f"Duplicate jinja_context variables: {duplicates}")
        
        return InputSpec(
            input_type=InputType.JINJA_CONTEXT,
            jinja_context=jinja_spec
        )


class GivenClauseValidator:
    """Validator for given clause specifications."""
    
    @staticmethod
    def validate_input_specs(input_specs: list[InputSpec]) -> None:
        """
        Validate input specifications for conflicts and correctness.
        
        Args:
            input_specs: List of InputSpec objects
            
        Raises:
            ConfigError: If validation fails
        """
        # Collect all generated aliases for collision detection
        generated_aliases = {}
        
        # First pass: identify all aliases (generated and explicit)
        for spec in input_specs:
            if spec.input_type in (InputType.CTE, InputType.RELATION):
                if spec.alias:
                    # User-provided alias
                    generated_aliases[spec.alias] = spec
                else:
                    # Generate alias from targets
                    for target in spec.targets:
                        if spec.data_source:
                            derived = AliasDeriver.derive_alias(target, spec.data_source)
                            if derived in generated_aliases:
                                raise ConfigError(
                                    f"Alias collision: '{derived}' derived from targets '{target}' "
                                    f"collides with another data source"
                                )
                            generated_aliases[derived] = spec
        
        # Second pass: check for Jinja variable collisions
        for spec in input_specs:
            if spec.input_type == InputType.JINJA_CONTEXT:
                for var_name in spec.jinja_context.keys():
                    if var_name in generated_aliases:
                        raise ConfigError(
                            f"Jinja variable '{var_name}' collides with auto-derived alias from "
                            f"CTE data source. Rename the Jinja variable or provide explicit `alias:` "
                            f"on the conflicting data source."
                        )
