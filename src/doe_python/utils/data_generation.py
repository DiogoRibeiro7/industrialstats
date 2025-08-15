from __future__ import annotations

"""Utilities to simulate experimental data."""

from typing import Dict, Optional

import numpy as np
import pandas as pd


class DataSimulator:
    """Generate realistic experimental data."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize the simulator.

        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility.
        """
        self.random_state = np.random.default_rng(seed)

    def simulate_factorial_response(
        self,
        design_matrix: pd.DataFrame,
        main_effects: Optional[Dict[str, float]] = None,
        interactions: Optional[Dict[tuple[str, str], float]] = None,
        noise_level: float = 1.0,
        noise_dist: str = "normal",
        response_type: str = "continuous",
    ) -> pd.Series:
        """Simulate response for a factorial design.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix.
        main_effects : dict, optional
            Mapping of factor names to effect sizes. If ``None``, all factors
            receive an effect size of 1.0.
        interactions : dict, optional
            Mapping of ``(factor1, factor2)`` to interaction effect sizes.
        noise_level : float, optional
            Scale of the random noise, by default 1.0.
        noise_dist : {'normal', 'laplace'}, optional
            Distribution for noise generation, by default ``'normal'``.
        response_type : {'continuous', 'binomial', 'poisson'}, optional
            Type of response variable, by default ``'continuous'``.

        Returns
        -------
        pandas.Series
            Simulated response values.

        References
        ----------
        .. [1] Montgomery, D.C. (2017). Design and Analysis of Experiments, 9th ed.
        .. [2] Box, G.E.P., Hunter, J.S., Hunter, W.G. (2005). Statistics for Experimenters, 2nd ed.
        """
        if main_effects is None:
            main_effects = {
                c: 1.0
                for c in design_matrix.columns
                if c
                not in {"RunID", "Replicate", "DesignPoint", "StdOrder", "RunOrder"}
            }
        interactions = interactions or {}

        factor_cols = [
            c
            for c in design_matrix.columns
            if c not in {"RunID", "Replicate", "DesignPoint", "StdOrder", "RunOrder"}
        ]
        encoded_df = design_matrix[factor_cols].copy()
        for col in encoded_df.select_dtypes(exclude="number").columns:
            encoded_df[col] = encoded_df[col].astype("category").cat.codes

        encoded_array = encoded_df.to_numpy(dtype=float)
        coef_vector = np.array(
            [main_effects.get(col, 0.0) for col in encoded_df.columns], dtype=float
        )
        response = encoded_array @ coef_vector

        for (f1, f2), coef in interactions.items():
            if f1 in encoded_df.columns and f2 in encoded_df.columns:
                response += (
                    coef
                    * encoded_df[f1].to_numpy(dtype=float)
                    * encoded_df[f2].to_numpy(dtype=float)
                )

        if noise_dist == "normal":
            noise = self.random_state.normal(scale=noise_level, size=len(response))
        elif noise_dist == "laplace":
            noise = self.random_state.laplace(scale=noise_level, size=len(response))
        else:
            raise ValueError("Unsupported noise distribution")

        response = response + noise

        if response_type == "continuous":
            final = response
        elif response_type == "binomial":
            p = 1 / (1 + np.exp(-response))
            final = self.random_state.binomial(1, p)
        elif response_type == "poisson":
            rate = np.exp(response)
            final = self.random_state.poisson(rate)
        else:
            raise ValueError("Unsupported response_type")

        return pd.Series(final, name="Response")
