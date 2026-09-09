"""Effect analysis with canonical two-level factorial contrast semantics."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..utils._factorial_contrasts import calculate_two_level_factorial_effects
from ._effects_core import EffectsAnalysis as _EffectsAnalysisCore

_METADATA_COLUMNS = {
    "RunID",
    "Replicate",
    "DesignPoint",
    "RunOrder",
    "StdOrder",
    "Block",
}


class EffectsAnalysis(_EffectsAnalysisCore):
    """Calculate factorial effects with one canonical two-level convention.

    Complete balanced two-level factorials use the same ``-1/+1`` orthogonal
    contrast engine as :meth:`industrialstats.designs.factorial.FactorialDesign.calculate_effects`.
    Multi-level and incomplete layouts retain the established analysis paths.
    """

    def __init__(self, design_matrix: pd.DataFrame, response_data: list[float]):
        """Initialize effect analysis and exclude known design metadata columns."""
        stored_orders = design_matrix.attrs.get("factor_level_orders")
        super().__init__(design_matrix, response_data)
        self.factor_names = [
            column
            for column in design_matrix.columns
            if column not in _METADATA_COLUMNS
        ]
        if not self.factor_names:
            raise ValueError("No factor columns found in design matrix")

        self._factor_level_orders: dict[str, list[Any]] | None = None
        if isinstance(stored_orders, dict) and all(
            name in stored_orders for name in self.factor_names
        ):
            self._factor_level_orders = {
                name: list(stored_orders[name]) for name in self.factor_names
            }

    def _is_complete_balanced_two_level_factorial(self) -> bool:
        """Return whether rows form an equally replicated complete ``2^k`` design."""
        if any(
            self.design_matrix[name].nunique(dropna=False) != 2
            for name in self.factor_names
        ):
            return False

        counts = self.design_matrix.groupby(
            self.factor_names,
            dropna=False,
            observed=True,
        ).size()
        expected_cells = 2 ** len(self.factor_names)
        return len(counts) == expected_cells and counts.nunique() == 1

    def calculate_main_effects(self) -> dict[str, float]:
        """Calculate main effects, using canonical contrasts for complete ``2^k`` data."""
        if not self._is_complete_balanced_two_level_factorial():
            return super().calculate_main_effects()

        return calculate_two_level_factorial_effects(
            self.design_matrix,
            self.response_data,
            self.factor_names,
            max_order=1,
            level_orders=self._factor_level_orders,
        )

    def calculate_interaction_effects(self, max_order: int = 2) -> dict[str, float]:
        """Calculate interaction effects under the canonical factorial convention."""
        if max_order < 2:
            return {}
        if not self._is_complete_balanced_two_level_factorial():
            return super().calculate_interaction_effects(max_order=max_order)

        effects = calculate_two_level_factorial_effects(
            self.design_matrix,
            self.response_data,
            self.factor_names,
            max_order=max_order,
            level_orders=self._factor_level_orders,
        )
        return {name: effect for name, effect in effects.items() if "*" in name}

    def _calculate_three_factor_interaction(
        self,
        factor1: str,
        factor2: str,
        factor3: str,
    ) -> float:
        """Calculate a three-factor effect with the standard low=-1/high=+1 sign."""
        factors = [factor1, factor2, factor3]
        if all(self.design_matrix[name].nunique(dropna=False) == 2 for name in factors):
            level_orders = None
            if self._factor_level_orders is not None:
                level_orders = {
                    name: self._factor_level_orders[name] for name in factors
                }
            effects = calculate_two_level_factorial_effects(
                self.design_matrix,
                self.response_data,
                factors,
                max_order=3,
                level_orders=level_orders,
            )
            return effects[f"{factor1}*{factor2}*{factor3}"]

        return super()._calculate_three_factor_interaction(factor1, factor2, factor3)
