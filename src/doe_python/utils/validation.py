from __future__ import annotations

"""Validation utilities for experimental designs."""

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

from ..designs.base import Factor


class DesignValidator:
    """Comprehensive design validation."""

    @staticmethod
    def validate_factors(factors: List[Factor]) -> List[str]:
        """Validate factor specifications and return warnings.

        Parameters
        ----------
        factors : list of Factor
            Factors to validate.

        Returns
        -------
        list of str
            Validation warnings, if any.
        """
        warnings: List[str] = []
        factor_types = {f.factor_type for f in factors}
        if len(factor_types) > 1:
            warnings.append("Mixed factor types detected")

        for f in factors:
            if len(f.levels) < 2:
                warnings.append(f"Factor {f.name} has fewer than 2 levels")
            if len(set(f.levels)) != len(f.levels):
                warnings.append(f"Factor {f.name} has duplicate levels")
            if f.factor_type == "continuous" and not all(
                isinstance(l, (int, float)) for l in f.levels
            ):
                warnings.append(
                    f"Factor {f.name} is continuous but has non-numeric levels"
                )
        return warnings

    @staticmethod
    def validate_design_matrix(design_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Validate a generated design matrix.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix to inspect.

        Returns
        -------
        dict
            Validation summary including missing values, duplicates and
            single-level factors.
        """
        result: Dict[str, Any] = {
            "missing_values": design_matrix.isnull().any().any(),
            "missing_counts": design_matrix.isnull().sum().to_dict(),
            "duplicate_rows": design_matrix.duplicated().any(),
            "single_level_factors": [
                col
                for col in design_matrix.columns
                if design_matrix[col].nunique() <= 1
            ],
        }
        return result

    @staticmethod
    def check_confounding(design_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Check for confounding patterns.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix to analyze.

        Returns
        -------
        dict
            Dictionary containing high-correlation pairs and variance inflation
            factors (VIF) for numeric columns.
        """
        result: Dict[str, Any] = {"high_correlation": {}, "vif": {}}
        corr = design_matrix.corr(numeric_only=True).abs()
        for i, col in enumerate(corr.columns):
            for j in range(i + 1, len(corr.columns)):
                other = corr.columns[j]
                if corr.iloc[i, j] > 0.95:
                    result["high_correlation"].setdefault(col, []).append(other)

        numeric = design_matrix.select_dtypes(include=[np.number])
        if numeric.shape[1] >= 2:
            X = np.column_stack([np.ones(len(numeric)), numeric.values])
            for i in range(1, X.shape[1]):
                result["vif"][numeric.columns[i - 1]] = variance_inflation_factor(X, i)

        return result

    @staticmethod
    def estimate_power(design_matrix: pd.DataFrame, effect_size: float) -> float:
        """Estimate design power for a given effect size.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix.
        effect_size : float
            Expected effect size.

        Returns
        -------
        float
            Estimated statistical power.

        Raises
        ------
        ValueError
            If the design matrix is empty.
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
