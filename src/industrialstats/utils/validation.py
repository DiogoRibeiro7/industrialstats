"""Validation utilities for experimental designs."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

from ..designs.base import Factor


class DesignValidator:
    """Comprehensive design validation."""

    @staticmethod
    def validate_factors(factors: list[Factor]) -> list[str]:
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
        warnings: list[str] = []
        factor_types = {f.factor_type for f in factors}
        if len(factor_types) > 1:
            warnings.append("Mixed factor types detected")

        for f in factors:
            if len(f.levels) < 2:
                warnings.append(f"Factor {f.name} has fewer than 2 levels")
            if len(set(f.levels)) != len(f.levels):
                warnings.append(f"Factor {f.name} has duplicate levels")
            if f.factor_type == "continuous" and not all(
                isinstance(level, (int, float)) for level in f.levels
            ):
                warnings.append(
                    f"Factor {f.name} is continuous but has non-numeric levels"
                )
        return warnings

    @staticmethod
    def validate_design_matrix(design_matrix: pd.DataFrame) -> dict[str, Any]:
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
        result: dict[str, Any] = {
            "missing_values": design_matrix.isna().any().any(),
            "missing_counts": design_matrix.isna().sum().to_dict(),
            "duplicate_rows": design_matrix.duplicated().any(),
            "single_level_factors": [
                col
                for col in design_matrix.columns
                if design_matrix[col].nunique() <= 1
            ],
        }
        return result

    @staticmethod
    def check_confounding(design_matrix: pd.DataFrame) -> dict[str, Any]:
        """Check for confounding patterns.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix to analyze.

        Returns
        -------
        dict
            Dictionary containing high-correlation pairs, variance inflation
            factors (VIF), alias structures derived from the design matrix null
            space, and variance decomposition (:math:`R^2`) for each column.

        References
        ----------
        .. [1] Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics
               for Experimenters*.
        .. [2] Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
        """
        result: dict[str, Any] = {
            "high_correlation": {},
            "vif": {},
            "alias_structure": [],
            "variance_decomposition": {},
        }
        corr = design_matrix.corr(numeric_only=True).abs()
        for i, col in enumerate(corr.columns):
            for j in range(i + 1, len(corr.columns)):
                other = corr.columns[j]
                if corr.iloc[i, j] > 0.95:
                    result["high_correlation"].setdefault(col, []).append(other)

        numeric = design_matrix.select_dtypes(include=[np.number])
        if numeric.shape[1] >= 2:
            X = numeric.values
            X_with_const = np.column_stack([np.ones(len(numeric)), X])
            # A perfectly confounded column has R^2 == 1, so the VIF
            # computation divides by zero and the design matrix is singular.
            # That is the defining case this validator exists to report, not an
            # anomaly, so let the arithmetic yield the mathematically correct
            # infinite inflation rather than surfacing numerical warnings that
            # the caller has already asked about by calling this function.
            with (
                warnings.catch_warnings(),
                np.errstate(divide="ignore", invalid="ignore"),
            ):
                # statsmodels reports degeneracy through several UserWarning
                # subclasses (poor conditioning, rank deficiency, and more in
                # later releases). Matching on message text would need
                # revisiting on every upgrade, so the whole category is
                # silenced for this call and this call only.
                warnings.simplefilter("ignore", UserWarning)
                for i in range(1, X_with_const.shape[1]):
                    result["vif"][numeric.columns[i - 1]] = variance_inflation_factor(
                        X_with_const, i
                    )

            from scipy.linalg import null_space

            ns = null_space(X)
            for vec in ns.T:
                involved = [
                    col
                    for col, coeff in zip(numeric.columns, vec, strict=True)
                    if abs(coeff) > 1e-10
                ]
                if involved:
                    result["alias_structure"].append(involved)

            for i, col in enumerate(numeric.columns):
                y = X[:, i]
                X_other = np.delete(X, i, axis=1)
                if X_other.size == 0:
                    continue
                beta, _, _, _ = np.linalg.lstsq(X_other, y, rcond=None)
                residuals = y - X_other @ beta
                ss_res = np.sum(residuals**2)
                ss_tot = np.sum((y - y.mean()) ** 2)
                r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
                result["variance_decomposition"][col] = r2

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
