from __future__ import annotations

"""Utilities to simulate experimental data."""

from typing import Dict, Optional

import numpy as np
import pandas as pd


class DataSimulator:
    """Generate realistic experimental data."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize with random seed for reproducibility.

        Args:
            seed (Optional[int]): Random seed value.
        """
        self.random_state = np.random.RandomState(seed)

    def simulate_factorial_response(
        self,
        design_matrix: pd.DataFrame,
        effects: Optional[Dict[str, float]] = None,
        noise_std: float = 1.0,
    ) -> pd.Series:
        """Simulate response for a factorial design.

        Args:
            design_matrix (pd.DataFrame): Design matrix.
            effects (Optional[Dict[str, float]], optional): Mapping of factor names to effect sizes. Defaults to ``None``.
            noise_std (float, optional): Standard deviation of Gaussian noise. Defaults to ``1.0``.

        Returns:
            pd.Series: Simulated response values.

        Notes:
            .. [1] Montgomery, D.C. (2017). Design and Analysis of Experiments, 9th ed.
            .. [2] Box, G.E.P., Hunter, J.S., Hunter, W.G. (2005). Statistics for Experimenters, 2nd ed.
        """
        if effects is None:
            effects = {
                c: 1.0
                for c in design_matrix.columns
                if c
                not in {"RunID", "Replicate", "DesignPoint", "StdOrder", "RunOrder"}
            }

        response = np.zeros(len(design_matrix))
        for name, coef in effects.items():
            if name in design_matrix.columns:
                levels = design_matrix[name]
                # simple coding: use raw levels if numeric else indicator
                if np.issubdtype(levels.dtype, np.number):
                    coded = levels.astype(float)
                else:
                    coded = levels.astype("category").cat.codes
                response += coef * coded

        noise = self.random_state.normal(scale=noise_std, size=len(design_matrix))
        response += noise
        return pd.Series(response, name="Response")
