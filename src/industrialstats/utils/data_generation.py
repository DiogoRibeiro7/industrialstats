from __future__ import annotations

"""Utilities to simulate experimental data."""

from typing import Dict, List, Optional, Sequence

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
        random_effects: Optional[Dict[str, float]] = None,
        corr: float = 0.0,
        heteroskedastic: Optional[Sequence[float]] = None,
        drift: float = 0.0,
        missing_rate: float = 0.0,
        missing_pattern: str = "MCAR",
    ) -> pd.Series:
        """Simulate response for a factorial design.

        The deterministic part of the response follows the linear model

        .. math:: y = X\beta + \varepsilon,

        where ``X`` is the encoded design matrix and ``\varepsilon`` denotes the
        stochastic noise component. Interaction terms are formed by pairwise
        products of encoded factors. Optional random effects and AR(1) correlated
        noise may be superimposed on the deterministic structure.

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
        random_effects : dict, optional
            Mapping of grouping column names to variance components for
            random intercepts.
        corr : float, optional
            Correlation coefficient for AR(1) noise. A value of ``0`` implies
            independent errors.
        heteroskedastic : Sequence of float, optional
            Observation-wise noise scales. Length must equal the number of
            design rows. Overrides ``noise_level`` when provided.
        drift : float, optional
            Linear drift coefficient applied in run order, by default ``0``.
        missing_rate : float, optional
            Fraction of responses to set as missing. Must be in ``[0, 1]``.
        missing_pattern : {'MCAR', 'block'}, optional
            Missing-data mechanism. ``'block'`` drops the last fraction of
            observations.

        Returns
        -------
        pandas.Series
            Simulated response values.

        See Also
        --------
        industrialstats.utils.validation.DesignValidator.check_confounding
            Assess correlation-based confounding in design matrices.
        industrialstats.analysis.power_analysis.factorial_power
            Power calculations for factorial designs.

        Examples
        --------
        >>> import pandas as pd
        >>> from industrialstats.utils.data_generation import DataSimulator
        >>> dm = pd.DataFrame({'A':[1,-1,1,-1],'B':[1,1,-1,-1]})
        >>> sim = DataSimulator(seed=1)
        >>> sim.simulate_factorial_response(dm, main_effects={'A':2,'B':1}).round(2)
        0    3.62
        1    1.33
        2    0.88
        3   -3.53
        Name: Response, dtype: float64

        References
        ----------
        .. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*.
               9th ed. Wiley.
        .. [2] Box, G.E.P., Hunter, J.S., Hunter, W.G. (2005). *Statistics for
               Experimenters*, 2nd ed. Wiley.
        .. [3] Laird, N. M., & Ware, J. H. (1982). "Random-effects models for
               longitudinal data." *Biometrics*, 38(4), 963-974.
        """
        if main_effects is None:
            main_effects = {
                c: 1.0
                for c in design_matrix.columns
                if c
                not in {"RunID", "Replicate", "DesignPoint", "StdOrder", "RunOrder"}
            }
        interactions = interactions or {}
        random_effects = random_effects or {}

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

        if interactions:
            cols = list(encoded_df.columns)
            term_matrix = [
                coef
                * encoded_array[:, cols.index(f1)]
                * encoded_array[:, cols.index(f2)]
                for (f1, f2), coef in interactions.items()
                if f1 in cols and f2 in cols
            ]
            if term_matrix:
                response += np.sum(np.stack(term_matrix, axis=0), axis=0)

        for col, var in random_effects.items():
            if col in design_matrix:
                groups = design_matrix[col]
                levels = groups.unique()
                re = self.random_state.normal(scale=np.sqrt(var), size=len(levels))
                mapping = dict(zip(levels, re))
                response += groups.map(mapping).to_numpy()

        n = len(response)
        scales = (
            np.asarray(heteroskedastic, dtype=float)
            if heteroskedastic is not None
            else np.full(n, noise_level, dtype=float)
        )
        if corr != 0.0:
            idx = np.arange(n)
            base = corr ** np.abs(np.subtract.outer(idx, idx))
            cov = np.outer(scales, scales) * base
            if noise_dist != "normal":
                raise ValueError(
                    "Correlated noise currently supported only for normal distribution"
                )
            noise = self.random_state.multivariate_normal(np.zeros(n), cov)
        else:
            if noise_dist == "normal":
                noise = self.random_state.normal(scale=scales, size=n)
            elif noise_dist == "laplace":
                noise = self.random_state.laplace(scale=scales, size=n)
            else:
                raise ValueError("Unsupported noise distribution")

        response = response + noise

        if drift != 0.0:
            order = design_matrix.get("RunOrder", pd.Series(range(n))).to_numpy()
            response = response + drift * order

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

        final = pd.Series(final, name="Response", dtype=float)

        if missing_rate > 0:
            if not 0 <= missing_rate <= 1:
                raise ValueError("missing_rate must be within [0, 1]")
            mask = np.zeros(n, dtype=bool)
            if missing_pattern == "MCAR":
                mask = self.random_state.random(n) < missing_rate
            elif missing_pattern == "block":
                mask[-int(n * missing_rate) :] = True
            else:
                raise ValueError("Unsupported missing_pattern")
            final[mask] = np.nan

        return final

    def simulate_correlated_responses(
        self,
        design_matrix: pd.DataFrame,
        main_effects_list: List[Dict[str, float]],
        cov: np.ndarray,
        **kwargs,
    ) -> pd.DataFrame:
        """Simulate multiple correlated responses.

        Each response uses ``simulate_factorial_response`` for its deterministic
        component. Correlated noise is then added using a multivariate normal
        distribution with covariance ``cov``.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design matrix.
        main_effects_list : list of dict
            Main-effect specifications for each response.
        cov : numpy.ndarray
            Covariance matrix defining correlations between responses.
        **kwargs
            Additional arguments forwarded to
            :meth:`simulate_factorial_response`.

        Returns
        -------
        pandas.DataFrame
            Simulated responses with one column per response.
        """
        means = [
            self.simulate_factorial_response(
                design_matrix, main_effects=effects, noise_level=0.0, **kwargs
            ).to_numpy()
            for effects in main_effects_list
        ]
        mean_mat = np.column_stack(means)
        noise = self.random_state.multivariate_normal(
            np.zeros(len(main_effects_list)), cov, size=len(design_matrix)
        )
        result = mean_mat + noise
        cols = [f"Y{i+1}" for i in range(len(main_effects_list))]
        return pd.DataFrame(result, columns=cols)

    def validate_against_real_data(
        self, simulated: pd.DataFrame | pd.Series, real_data: pd.DataFrame | pd.Series
    ) -> Dict[str, Dict[str, float]]:
        """Compare simulated data to real experimental measurements.

        The function computes absolute differences in means and standard
        deviations for each variable, allowing users to gauge similarity between
        simulated and actual data sets.

        Parameters
        ----------
        simulated : pandas.Series or pandas.DataFrame
            Simulated responses.
        real_data : pandas.Series or pandas.DataFrame
            Empirical measurements to compare against.

        Returns
        -------
        dict of dict
            Mapping each column name to ``{"mean_diff": float, "std_diff": float}``.
        """
        sim_df = pd.DataFrame(simulated)
        real_df = pd.DataFrame(real_data)[sim_df.columns]
        stats: Dict[str, Dict[str, float]] = {}
        for col in sim_df.columns:
            stats[col] = {
                "mean_diff": float(abs(sim_df[col].mean() - real_df[col].mean())),
                "std_diff": float(abs(sim_df[col].std() - real_df[col].std())),
            }
        return stats
