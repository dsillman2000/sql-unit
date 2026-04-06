"""DataFrame normalization for order-independent comparison."""

try:
    import pandas as pd
except ImportError:
    pd = None

from ..core.exceptions import SetupError


class DataFrameNormalizer:
    """Normalizes DataFrames for order-independent comparison.

    Normalization involves:
    1. Column name lowercase normalization (already done by ResultSetDataFrame)
    2. Column sorting (alphabetical order)
    3. Row sorting (by all columns)
    """

    @staticmethod
    def normalize(df: "pd.DataFrame") -> "pd.DataFrame":
        """
        Normalize a DataFrame for comparison.

        Ensures:
        - Column names are lowercase (should already be done)
        - Columns sorted alphabetically
        - Rows sorted by all columns
        - Index reset to 0,1,2,...

        Args:
            df: pandas DataFrame to normalize

        Returns:
            Normalized DataFrame

        Raises:
            SetupError: If pandas is not installed
        """
        if pd is None:
            raise SetupError("pandas is required for DataFrame normalization")

        # Make a copy to avoid modifying original
        df_copy = df.copy()

        # Handle empty DataFrame
        if len(df_copy.columns) == 0:
            return df_copy

        # Ensure all column names are lowercase
        df_copy.columns = df_copy.columns.str.lower()

        # Sort columns alphabetically
        df_copy = df_copy[sorted(df_copy.columns)]

        # Sort rows by all columns (for order-independent comparison)
        # Use stable sort to preserve row order for equal values
        df_copy = df_copy.sort_values(by=list(df_copy.columns), na_position="last")

        # Reset index to clean integers
        df_copy = df_copy.reset_index(drop=True)

        return df_copy

    @staticmethod
    def normalize_columns(df: "pd.DataFrame", expected_columns: list[str]) -> "pd.DataFrame":
        """
        Normalize DataFrame to only include expected columns.

        Omitted columns in expected are ignored (not compared).
        Columns not in expected are dropped from actual result.

        Args:
            df: pandas DataFrame to normalize
            expected_columns: List of expected column names (lowercase)

        Returns:
            DataFrame with only expected columns, in alphabetical order

        Raises:
            SetupError: If pandas is not installed
        """
        if pd is None:
            raise SetupError("pandas is required for DataFrame normalization")

        df_copy = df.copy()

        # Handle empty DataFrame
        if len(df_copy.columns) == 0:
            return df_copy

        # Ensure all column names are lowercase
        df_copy.columns = df_copy.columns.str.lower()

        # Keep only columns that are in expected
        available_columns = [col for col in sorted(expected_columns) if col in df_copy.columns]
        df_copy = df_copy[available_columns]

        return df_copy
