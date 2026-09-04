"""Utilities to simulate experimental data.

The :class:`DataSimulator` class centralizes routines for generating
experimental and process-oriented data with rich noise structures. The
implementation follows the mathematical guidelines in Montgomery [1]_ and Box &
Jenkins [2]_ for factorial responses and stochastic process modelling,
respectively.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd


class DataSimulator:
    """Generate realistic experimental data."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize the simulator.

        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility.
        """
        self.random_state = np.random.default_rng(seed)

    def _draw_noise(
        self,
        distribution: str,
        size: int,
        scale: np.ndarray,
        params: dict[str, float] | None = None,
    ) -> np.ndarray:
        """Sample noise from a supported distribution.

        Parameters
        ----------
        distribution : {'normal', 'laplace', 't', 'gamma', 'exponential'}
            Name of the distribution.
        size : int
            Number of samples to draw.
        scale : numpy.ndarray
            Observation-specific scale factors.
        params : dict, optional
            Additional distribution parameters such as degrees of freedom for a
            Student :math:`t` distribution.

        Returns
        -------
        numpy.ndarray
            Random deviates of length ``size``.

        Raises
        ------
        ValueError
            If the distribution is not recognised or required parameters are
            missing.
        """

        params = params or {}
        distribution = distribution.lower()
        if distribution == "normal":
            return self.random_state.normal(scale=scale, size=size)
        if distribution == "laplace":
            return self.random_state.laplace(scale=scale, size=size)
        if distribution == "t":
            df = params.get("df", 5.0)
            samples = self.random_state.standard_t(df, size=size)
            return samples * scale
        if distribution == "gamma":
            shape = params.get("shape", 2.0)
            return self.random_state.gamma(shape, scale=scale / shape, size=size)
        if distribution == "exponential":
            return self.random_state.exponential(scale=scale, size=size)
        raise ValueError(f"Unsupported noise distribution '{distribution}'")

    def _arma_filter(
        self,
        white_noise: np.ndarray,
        ar_params: Sequence[float] | None = None,
        ma_params: Sequence[float] | None = None,
    ) -> np.ndarray:
        r"""Apply ARMA(p, q) filtering to white-noise innovations.

        The recursion follows the convention used in Box & Jenkins [2]_ where
        autoregressive coefficients correspond to the past values of the process
        and moving-average coefficients adjust past innovations.

        Parameters
        ----------
        white_noise : numpy.ndarray
            Input innovations :math:`\varepsilon_t`.
        ar_params : sequence of float, optional
            Autoregressive coefficients :math:`\phi_1, \ldots, \phi_p`.
        ma_params : sequence of float, optional
            Moving-average coefficients :math:`\theta_1, \ldots, \theta_q`.

        Returns
        -------
        numpy.ndarray
            Filtered series obeying the ARMA recursion.
        """

        ar_params = tuple(ar_params or ())
        ma_params = tuple(ma_params or ())
        if not ar_params and not ma_params:
            return white_noise

        p = len(ar_params)
        q = len(ma_params)
        output = np.zeros_like(white_noise, dtype=float)
        for t in range(white_noise.shape[0]):
            value = white_noise[t]
            if ma_params:
                for j in range(1, q + 1):
                    if t - j >= 0:
                        value += ma_params[j - 1] * white_noise[t - j]
            if ar_params:
                for i in range(1, p + 1):
                    if t - i >= 0:
                        value += ar_params[i - 1] * output[t - i]
            output[t] = value
        return output

    def _resolve_scale(
        self,
        base_scale: float,
        heteroskedastic: Iterable[float] | Callable[[pd.DataFrame], np.ndarray] | None,
        design_matrix: pd.DataFrame,
    ) -> np.ndarray:
        """Compute observation-specific scale factors.

        Parameters
        ----------
        base_scale : float
            Homoscedastic noise level.
        heteroskedastic : iterable of float or callable, optional
            Either an iterable with one entry per observation or a callable that
            receives the design matrix and returns a vector of scales.
        design_matrix : pandas.DataFrame
            Design information used for adaptive scales.

        Returns
        -------
        numpy.ndarray
            Scale vector of length equal to the number of rows in
            ``design_matrix``.
        """

        n = len(design_matrix)
        if heteroskedastic is None:
            return np.full(n, base_scale, dtype=float)
        if callable(heteroskedastic):
            values = np.asarray(heteroskedastic(design_matrix), dtype=float)
        else:
            values = np.asarray(list(heteroskedastic), dtype=float)
        if values.shape[0] != n:
            raise ValueError(
                "Heteroskedastic specification must match number of observations"
            )
        return values

    def _inject_outliers(
        self,
        response: np.ndarray,
        outlier_config: dict[str, dict[str, float | int]] | None,
        scale: np.ndarray,
    ) -> np.ndarray:
        """Inject outliers into the response according to configuration."""

        if not outlier_config:
            return response

        result = response.copy()
        n = result.shape[0]
        for key, cfg in outlier_config.items():
            fraction = float(cfg.get("fraction", 0.0))
            magnitude = float(cfg.get("magnitude", 3.0))
            count = max(1, round(fraction * n)) if fraction > 0 else 0
            if key.lower() == "random" and count > 0:
                idx = self.random_state.choice(n, size=count, replace=False)
                result[idx] += (
                    magnitude
                    * scale[idx]
                    * np.sign(self.random_state.standard_normal(size=count))
                )
            elif key.lower() == "systematic" and count > 0:
                start = int(cfg.get("start", 0))
                stop = min(n, start + count)
                result[start:stop] += magnitude * scale[start:stop]
            elif key.lower() == "leverage" and count > 0:
                # leverage points emphasise extreme fitted values
                leverage_idx = np.argsort(np.abs(result))[-count:]
                result[leverage_idx] += magnitude * scale[leverage_idx]
        return result

    def _apply_missingness(
        self,
        values: pd.Series,
        mechanism: str,
        rate: float,
        design_matrix: pd.DataFrame | None = None,
    ) -> pd.Series:
        """Apply MCAR/MAR/MNAR missingness to a series."""

        if rate <= 0:
            return values
        if not 0.0 <= rate <= 1.0:
            raise ValueError("missing_rate must be within [0, 1]")

        n = len(values)
        mask = np.zeros(n, dtype=bool)
        mech = mechanism.upper()
        if mech == "MCAR":
            mask = self.random_state.random(n) < rate
        elif mech == "MAR":
            if design_matrix is None or design_matrix.empty:
                raise ValueError("MAR mechanism requires design_matrix inputs")
            pivot = design_matrix.select_dtypes(include="number").iloc[:, 0]
            prob = (pivot - pivot.min()) / (pivot.max() - pivot.min() + 1e-12)
            prob = 0.5 * (prob + 1e-6)
            mask = self.random_state.random(n) < (prob * rate / prob.mean())
        elif mech == "MNAR":
            scaled = (values - values.min()) / (values.max() - values.min() + 1e-12)
            mask = self.random_state.random(n) < (scaled * rate / scaled.mean())
        elif mech == "BLOCK":
            mask[-int(rate * n) :] = True
        else:
            raise ValueError("Unsupported missing_pattern")
        result = values.copy()
        result.iloc[mask] = np.nan
        return result

    def simulate_factorial_response(
        self,
        design_matrix: pd.DataFrame,
        main_effects: dict[str, float] | None = None,
        interactions: dict[tuple[str, str], float] | None = None,
        noise_level: float = 1.0,
        noise_dist: str = "normal",
        noise_params: dict[str, float] | None = None,
        response_type: str = "continuous",
        random_effects: dict[str, float] | None = None,
        corr: float = 0.0,
        heteroskedastic: Sequence[float]
        | Callable[[pd.DataFrame], np.ndarray]
        | None = None,
        drift: float = 0.0,
        missing_rate: float = 0.0,
        missing_pattern: str = "MCAR",
        measurement_error: dict[str, Any] | None = None,
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
        noise_dist : {'normal', 'laplace', 't', 'gamma', 'exponential'}, optional
            Distribution for noise generation, by default ``'normal'``.
        noise_params : dict, optional
            Additional parameters for the selected distribution, e.g., degrees of
            freedom for ``'t'``.
        response_type : {'continuous', 'binomial', 'poisson'}, optional
            Type of response variable, by default ``'continuous'``.
        random_effects : dict, optional
            Mapping of grouping column names to variance components for
            random intercepts.
        corr : float, optional
            Correlation coefficient for AR(1) noise. A value of ``0`` implies
            independent errors.
        heteroskedastic : sequence of float or callable, optional
            Observation-wise noise scales. Length must equal the number of
            design rows. Overrides ``noise_level`` when provided. If a callable is
            supplied, it receives the design matrix and must return a vector of
            scale factors.
        drift : float, optional
            Linear drift coefficient applied in run order, by default ``0``.
        missing_rate : float, optional
            Fraction of responses to set as missing. Must be in ``[0, 1]``.
        missing_pattern : {'MCAR', 'MAR', 'MNAR', 'block'}, optional
            Missing-data mechanism. ``'block'`` drops the last fraction of
            observations, ``'MAR'`` and ``'MNAR'`` implement missingness at random
            and not at random, respectively.
        measurement_error : dict, optional
            Parameters describing an additive measurement error model applied to
            the final response. Accepts ``{"scale": float, "distribution": str}``
            following the same distribution names as ``noise_dist``.

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
        >>> dm = pd.DataFrame({"A": [1, -1, 1, -1], "B": [1, 1, -1, -1]})
        >>> sim = DataSimulator(seed=1)
        >>> sim.simulate_factorial_response(dm, main_effects={"A": 2, "B": 1}).round(2)
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
        .. [4] Carroll, R.J., Ruppert, D., Stefanski, L.A., & Crainiceanu, C.M.
               (2006). *Measurement Error in Nonlinear Models*, 2nd ed.
               Chapman & Hall/CRC.
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
                mapping = dict(zip(levels, re, strict=True))
                response += groups.map(mapping).to_numpy()

        n = len(response)
        scales = self._resolve_scale(noise_level, heteroskedastic, design_matrix)
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
            noise = self._draw_noise(noise_dist, n, scales, noise_params)

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

        if measurement_error:
            err_scale = measurement_error.get("scale", noise_level)
            err_dist = measurement_error.get("distribution", "normal")
            meas_noise = self._draw_noise(
                err_dist,
                n,
                np.full(n, err_scale, dtype=float),
                measurement_error.get("params"),
            )
            final = final + meas_noise

        if missing_rate > 0:
            final = self._apply_missingness(
                final, missing_pattern, missing_rate, design_matrix
            )

        return final

    def simulate_correlated_responses(
        self,
        design_matrix: pd.DataFrame,
        main_effects_list: list[dict[str, float]],
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
        cols = [f"Y{i + 1}" for i in range(len(main_effects_list))]
        return pd.DataFrame(result, columns=cols)

    def simulate_process_data(
        self,
        n_periods: int,
        model: Callable[[pd.DataFrame], np.ndarray],
        covariates: pd.DataFrame | None = None,
        freq: str = "D",
        noise_dist: str = "normal",
        noise_params: dict[str, float] | None = None,
        trend: dict[str, Any] | None = None,
        seasonality: dict[str, float] | None = None,
        ar_params: Sequence[float] | None = None,
        ma_params: Sequence[float] | None = None,
        heteroskedastic: Iterable[float]
        | Callable[[pd.DataFrame], np.ndarray]
        | None = None,
        outliers: dict[str, dict[str, float | int]] | None = None,
        missing: dict[str, float | str] | None = None,
        measurement_error: dict[str, Any] | None = None,
        return_components: bool = False,
    ) -> pd.DataFrame:
        r"""Simulate a univariate or multivariate process response.

        The function evaluates a custom ``model`` over a time-indexed frame and
        enriches the result with trend, seasonality, heteroskedasticity, and
        ARMA-style autocorrelation. Noise can be drawn from Gaussian, Student
        :math:`t`, Gamma, or Exponential families. Outlier generation follows the
        guidelines of Hawkins [3]_ whereas missingness mechanisms mirror Little &
        Rubin [4]_.

        Parameters
        ----------
        n_periods : int
            Number of time points to simulate.
        model : callable
            Callable mapping a covariate frame to deterministic response values.
        covariates : pandas.DataFrame, optional
            External drivers aligned with ``n_periods``. A ``time`` column is
            appended automatically.
        freq : str, optional
            Frequency string passed to :func:`pandas.date_range` for the time
            index, by default ``'D'``.
        noise_dist : {'normal', 'laplace', 't', 'gamma', 'exponential'}, optional
            Distribution used for the innovation process.
        noise_params : dict, optional
            Distribution-specific parameters.
        trend : dict, optional
            Specification of deterministic trend. Supports ``{'type': 'linear',
            'slope': float, 'intercept': float}`` or ``{'type': 'poly',
            'coeffs': Sequence[float]}``.
        seasonality : dict, optional
            Describes periodic fluctuations with keys ``'period'`` and
            ``'amplitude'``. A ``'phase'`` entry introduces a phase shift.
        ar_params : sequence of float, optional
            Autoregressive parameters :math:`\phi`.
        ma_params : sequence of float, optional
            Moving-average parameters :math:`\theta`.
        heteroskedastic : iterable or callable, optional
            Observation-specific noise scales.
        outliers : dict, optional
            Mapping of outlier types (``'random'``, ``'systematic'``,
            ``'leverage'``) to configuration dictionaries.
        missing : dict, optional
            Missing-data mechanism configuration with keys ``'rate'`` and
            ``'mechanism'``.
        measurement_error : dict, optional
            Additive measurement error with keys ``'scale'`` and
            ``'distribution'`` (defaults to Gaussian).
        return_components : bool, optional
            If ``True``, the returned frame includes deterministic and stochastic
            components for diagnostics.

        Returns
        -------
        pandas.DataFrame
            Simulated process data containing the response and metadata columns.

        References
        ----------
        .. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*,
               9th ed. Wiley.
        .. [2] Box, G.E.P., Jenkins, G.M., Reinsel, G.C., & Ljung, G.M. (2015).
               *Time Series Analysis: Forecasting and Control*, 5th ed. Wiley.
        .. [3] Hawkins, D.M. (1980). *Identification of Outliers*. Chapman and
               Hall.
        .. [4] Little, R.J.A., & Rubin, D.B. (2002). *Statistical Analysis with
               Missing Data*, 2nd ed. Wiley.
        """

        if n_periods <= 0:
            raise ValueError("n_periods must be positive")

        time_index = pd.date_range("2000-01-01", periods=n_periods, freq=freq)
        base_df = covariates.copy() if covariates is not None else pd.DataFrame()
        base_df = base_df.reset_index(drop=True)
        if not base_df.empty and len(base_df) != n_periods:
            raise ValueError("covariates must have n_periods rows")
        base_df["time"] = time_index
        base_df["t"] = np.arange(n_periods, dtype=float)

        deterministic = np.asarray(model(base_df), dtype=float)
        if deterministic.shape not in {(n_periods,), (n_periods, 1)}:
            raise ValueError("model must return a vector of length n_periods")
        deterministic = deterministic.reshape(n_periods)

        if trend:
            kind = trend.get("type", "linear").lower()
            if kind == "linear":
                slope = float(trend.get("slope", 0.0))
                intercept = float(trend.get("intercept", 0.0))
                deterministic = (
                    deterministic + intercept + slope * base_df["t"].to_numpy()
                )
            elif kind == "poly":
                coeffs = trend.get("coeffs", (0.0,))
                poly = np.poly1d(coeffs)
                deterministic = deterministic + poly(base_df["t"].to_numpy())
            else:
                raise ValueError("Unsupported trend specification")

        if seasonality:
            period = float(seasonality.get("period", 12.0))
            amplitude = float(seasonality.get("amplitude", 1.0))
            phase = float(seasonality.get("phase", 0.0))
            deterministic = deterministic + amplitude * np.sin(
                2 * np.pi * (base_df["t"].to_numpy() + phase) / max(period, 1e-6)
            )

        scale_vec = self._resolve_scale(1.0, heteroskedastic, base_df)
        base_noise = self._draw_noise(noise_dist, n_periods, scale_vec, noise_params)
        stochastic = self._arma_filter(base_noise, ar_params, ma_params)
        response = deterministic + stochastic
        response = self._inject_outliers(response, outliers, scale_vec)

        result = pd.DataFrame({"time": time_index, "response": response})
        result["deterministic"] = deterministic
        result["stochastic"] = stochastic

        if measurement_error:
            err_scale = float(measurement_error.get("scale", 0.1))
            err_dist = str(measurement_error.get("distribution", "normal"))
            meas = self._draw_noise(
                err_dist,
                n_periods,
                np.full(n_periods, err_scale),
                measurement_error.get("params"),
            )
            result["response"] = result["response"] + meas
            result["measurement_error"] = meas

        if missing:
            mechanism = str(missing.get("mechanism", "MCAR"))
            rate = float(missing.get("rate", 0.0))
            result["response"] = self._apply_missingness(
                result["response"], mechanism, rate, base_df
            )

        if not return_components:
            cols_to_keep = ["time", "response"]
            if "measurement_error" in result:
                cols_to_keep.append("measurement_error")
            result = result[cols_to_keep]

        return result

    def simulate_multi_response(
        self,
        design_matrix: pd.DataFrame,
        response_models: Sequence[Callable[[pd.DataFrame], np.ndarray]],
        covariance: np.ndarray,
        response_types: Sequence[str] | None = None,
        noise_scales: Sequence[float] | None = None,
        noise_dist: str = "normal",
        measurement_error: Sequence[dict[str, Any] | None] | None = None,
    ) -> pd.DataFrame:
        """Simulate correlated multi-response experimental outcomes.

        Each response is constructed from a deterministic model augmented with a
        correlated latent noise term drawn from ``covariance``. Response types
        may be continuous, categorical (binary logistic), or count (Poisson).

        References
        ----------
        .. [1] Khuri, A.I., & Cornell, J.A. (1996). *Response Surfaces: Design
               and Analyses*. CRC Press.
        .. [2] Johnson, R.A., & Wichern, D.W. (2007). *Applied Multivariate
               Statistical Analysis*, 6th ed. Pearson.

        Parameters
        ----------
        design_matrix : pandas.DataFrame
            Design or feature matrix shared across responses.
        response_models : sequence of callable
            Deterministic response functions applied to the design matrix.
        covariance : numpy.ndarray
            Positive semi-definite covariance matrix governing latent noise.
        response_types : sequence of {'continuous', 'categorical', 'count'}, optional
            Specifies the distribution of each response. Defaults to continuous.
        noise_scales : sequence of float, optional
            Additional scale multipliers applied per response.
        noise_dist : {'normal', 't', 'gamma', 'exponential', 'laplace'}, optional
            Distribution used to generate latent noise prior to correlating.
        measurement_error : sequence of dict, optional
            Optional measurement-error configuration for each response using the
            same schema as :meth:`simulate_factorial_response`.

        Returns
        -------
        pandas.DataFrame
            Multi-response dataset preserving the original design columns.
        """

        n = len(design_matrix)
        r = len(response_models)
        if covariance.shape != (r, r):
            raise ValueError(
                "covariance must be square with dimension equal to responses"
            )
        response_types = response_types or ["continuous"] * r
        if len(response_types) != r:
            raise ValueError("response_types length must match response_models")
        if noise_scales and len(noise_scales) != r:
            raise ValueError("noise_scales length must match response_models")

        deterministic_parts = []
        for model in response_models:
            deterministic_parts.append(np.asarray(model(design_matrix), dtype=float))
        deterministic = np.column_stack(deterministic_parts)

        noise_scales = noise_scales or [1.0] * r
        latent = self.random_state.multivariate_normal(np.zeros(r), covariance, size=n)
        if noise_dist != "normal":
            base = self._draw_noise(
                noise_dist,
                n * r,
                np.repeat(1.0, n * r),
                None,
            ).reshape(n, r)
            chol = np.linalg.cholesky(covariance + 1e-12 * np.eye(r))
            latent = base @ chol.T
        latent = latent * np.asarray(noise_scales, dtype=float)

        responses = np.empty_like(latent)
        columns = []
        meas_configs: list[dict[str, Any] | None] = (
            list(measurement_error) if measurement_error else [None] * r
        )
        for idx, (det_col, noise_col, kind, meas_cfg) in enumerate(
            zip(deterministic.T, latent.T, response_types, meas_configs, strict=True)
        ):
            column_name = f"Y{idx + 1}"
            columns.append(column_name)
            combined = det_col + noise_col
            if kind == "continuous":
                resp = combined
            elif kind == "categorical":
                prob = 1 / (1 + np.exp(-combined))
                resp = self.random_state.binomial(1, prob)
            elif kind == "count":
                rate = np.clip(np.exp(combined), 1e-9, None)
                resp = self.random_state.poisson(rate)
            else:
                raise ValueError("Unsupported response type")
            if meas_cfg:
                scale = float(meas_cfg.get("scale", 0.1))
                dist = str(meas_cfg.get("distribution", "normal"))
                resp = resp + self._draw_noise(
                    dist, n, np.full(n, scale, dtype=float), meas_cfg.get("params")
                )
            responses[:, idx] = resp

        out_df = design_matrix.reset_index(drop=True).copy()
        for column, values in zip(columns, responses.T, strict=True):
            out_df[column] = values
        return out_df

    def validate_against_real_data(
        self, simulated: pd.DataFrame | pd.Series, real_data: pd.DataFrame | pd.Series
    ) -> dict[str, dict[str, float]]:
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
        stats: dict[str, dict[str, float]] = {}
        for col in sim_df.columns:
            sim_col = sim_df[col].dropna()
            real_col = real_df[col].dropna()
            ks_stat = float(
                np.max(
                    np.abs(
                        np.sort(sim_col.to_numpy())
                        - np.sort(real_col.to_numpy())[: len(sim_col)]
                    )
                )
            )
            stats[col] = {
                "mean_diff": float(abs(sim_col.mean() - real_col.mean())),
                "std_diff": float(abs(sim_col.std() - real_col.std())),
                "ks_like": ks_stat,
            }
        return stats
