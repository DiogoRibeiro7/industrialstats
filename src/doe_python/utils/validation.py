from __future__ import annotations

"""Validation utilities for experimental designs."""

from typing import Any, Dict, List

import pandas as pd

from ..designs.base import Factor


class DesignValidator:
    """Comprehensive design validation."""

    @staticmethod
    def validate_factors(factors: List[Factor]) -> List[str]:
        """Validate factor specifications and return warnings.

        Args:
            factors (List[Factor]): Factors to validate.

        Returns:
            List[str]: Validation warnings, if any.
        """
        warnings: List[str] = []
        for f in factors:
            if len(f.levels) < 2:
                warnings.append(f"Factor {f.name} has fewer than 2 levels")
            if len(set(f.levels)) != len(f.levels):
                warnings.append(f"Factor {f.name} has duplicate levels")
        return warnings

    @staticmethod
    def validate_design_matrix(design_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Validate a generated design matrix.

        Args:
            design_matrix (pd.DataFrame): Design matrix to inspect.

        Returns:
            Dict[str, Any]: Validation summary including missing values and duplicates.
        """
        result = {
            "missing_values": design_matrix.isnull().any().any(),
            "duplicate_rows": design_matrix.duplicated().any(),
        }
        return result

    @staticmethod
    def check_confounding(design_matrix: pd.DataFrame) -> Dict[str, List[str]]:
        """Check for confounding patterns.

        Args:
            design_matrix (pd.DataFrame): Design matrix to analyze.

        Returns:
            Dict[str, List[str]]: Mapping of columns to potential confounders.
        """
        confounding: Dict[str, List[str]] = {}
        corr = design_matrix.corr(numeric_only=True).abs()
        for i, col in enumerate(corr.columns):
            for j in range(i + 1, len(corr.columns)):
                other = corr.columns[j]
                if corr.iloc[i, j] > 0.95:
                    confounding.setdefault(col, []).append(other)
        return confounding

    @staticmethod
    def estimate_power(design_matrix: pd.DataFrame, effect_size: float) -> float:
        """Estimate design power for a given effect size.

        Args:
            design_matrix (pd.DataFrame): Design matrix.
            effect_size (float): Expected effect size.

        Returns:
            float: Estimated statistical power.

        Raises:
            ValueError: If the design matrix is empty.
        """
        from scipy.stats import f, ncf

        n = len(design_matrix)
        if n == 0:
            raise ValueError("Design matrix is empty")
        df_model = design_matrix.shape[1] - 1
        df_error = n - df_model - 1
        lambda_nc = effect_size**2 * n / 2
        f_crit = f.ppf(0.95, df_model, df_error)
        power = 1 - ncf.cdf(f_crit, df_model, df_error, lambda_nc)
        return power
