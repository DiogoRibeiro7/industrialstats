"""Comprehensive regression diagnostics.

This module implements residual diagnostics described by Cook & Weisberg
(1982) and extends classical assumption checks with actionable guidance.
The :class:`ModelDiagnostics` class operates on dictionaries returned by the
high-level fitting utilities in :mod:`industrialstats.analysis.model_fitting`
and requires the original design data to contextualize the diagnostics.

Examples
--------
>>> import pandas as pd
>>> import numpy as np
>>> import statsmodels.api as sm
>>> from industrialstats.analysis.diagnostics import ModelDiagnostics
>>> rng = np.random.default_rng(42)
>>> x1 = rng.normal(size=120)
>>> x2 = rng.normal(size=120)
>>> y = 1.5 + 2.0 * x1 - 1.2 * x2 + rng.normal(size=120)
>>> data = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
>>> model = sm.OLS(data["y"], sm.add_constant(data[["x1", "x2"]])).fit()
>>> model_result = {
...     "model_object": model,
...     "residuals": model.resid,
...     "fitted_values": model.fittedvalues,
...     "model_metrics": {"R2": model.rsquared},
... }
>>> diagnostics = ModelDiagnostics(model_result, data)
>>> summary = diagnostics.assumption_tests()
>>> round(summary["normality"]["shapiro"]["p_value"], 3) >= 0.05
True
"""

from __future__ import annotations

import inspect
import math
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.stattools import durbin_watson

try:  # pragma: no cover - exercised indirectly via availability checks
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - allows graceful degradation in tests
    plt = None  # type: ignore[assignment]

if TYPE_CHECKING:  # pragma: no cover - typing-only import
    from matplotlib.figure import Figure
else:  # pragma: no cover - runtime fallback when matplotlib missing
    Figure = Any

__all__ = ["ModelDiagnostics"]


class ModelDiagnostics:
    """Diagnostic analytics for linear models.

    The diagnostics follow the influence framework of Cook & Weisberg [1]_ and
    are compatible with dictionaries returned by
    :class:`~industrialstats.analysis.model_fitting.ModelFitting`.

    Parameters
    ----------
    model_result : Dict[str, Any]
        Dictionary containing the fitted ``statsmodels`` object under the key
        ``"model_object"`` alongside residual vectors and fitted values. The
        minimal expected keys are ``{"model_object", "residuals",
        "fitted_values"}``.
    data : pandas.DataFrame
        Original dataset used during model fitting. The frame is copied to avoid
        inadvertent mutation during diagnostics.

    Raises
    ------
    TypeError
        If ``model_result`` is not a dictionary or lacks the required
        ``statsmodels`` interfaces.
    KeyError
        When mandatory keys are absent from ``model_result``.
    ValueError
        If residual and fitted vector lengths are inconsistent with ``data``.

    References
    ----------
    .. [1] Cook, R. D., & Weisberg, S. (1982). *Residuals and Influence in
       Regression*. Chapman & Hall/CRC.
    """

    def __init__(self, model_result: dict[str, Any], data: pd.DataFrame) -> None:
        if not isinstance(model_result, dict):
            raise TypeError("model_result must be a dictionary of model outputs")

        required_keys = {"model_object", "residuals", "fitted_values"}
        missing_keys = required_keys.difference(model_result.keys())
        if missing_keys:
            raise KeyError(
                "model_result is missing required keys: "
                + ", ".join(sorted(missing_keys))
            )

        model_object = model_result["model_object"]
        if not hasattr(model_object, "get_influence"):
            raise TypeError(
                "model_result['model_object'] must expose statsmodels influence diagnostics"
            )

        self.model_result = model_result
        self.model = model_object
        self.data = data.copy(deep=True)

        self.residuals = np.asarray(model_result["residuals"], dtype=float)
        self.fitted_values = np.asarray(model_result["fitted_values"], dtype=float)

        if self.residuals.ndim != 1 or self.fitted_values.ndim != 1:
            raise ValueError(
                "residuals and fitted_values must be one-dimensional arrays"
            )

        n_obs = len(self.data)
        if (
            len(self.residuals) != len(self.fitted_values)
            or len(self.residuals) != n_obs
        ):
            raise ValueError(
                "Length of residuals, fitted values, and data rows must match"
            )

        self._assumption_cache: dict[str, dict[str, Any]] | None = None
        self._influence_cache: dict[str, np.ndarray] | None = None
        self._outlier_cache: dict[str, list[int]] | None = None

    # ------------------------------------------------------------------
    @staticmethod
    def _anderson_normality(
        residuals: np.ndarray,
    ) -> tuple[float, float | None, float | None, bool]:
        """Run the Anderson-Darling normality test across SciPy versions.

        SciPy 1.17 introduced an explicit ``method`` argument and deprecated
        the implicit behaviour; from 1.19 the ``critical_values`` and
        ``significance_level`` attributes are removed altogether. This helper
        asks for an interpolated p-value where that is supported and falls
        back to the critical-value table on older SciPy.

        Parameters
        ----------
        residuals : numpy.ndarray
            Model residuals to test for normality.

        Returns
        -------
        tuple of (float, float or None, float or None, bool)
            The test statistic, the p-value when SciPy can supply one, the 5%
            critical value when SciPy still exposes the tables, and whether the
            residuals pass the test at the 5% level. Exactly one of the p-value
            and the critical value is available for a given SciPy version, so
            the verdict is decided here rather than by the caller.
        """

        if "method" in inspect.signature(stats.anderson).parameters:
            result = stats.anderson(residuals, dist="norm", method="interpolate")
            p_value = float(result.pvalue)
            return float(result.statistic), p_value, None, p_value > 0.05

        result = stats.anderson(residuals, dist="norm")
        critical = dict(
            zip(result.significance_level, result.critical_values, strict=True)
        )
        threshold = critical.get(5.0)
        if threshold is None:
            threshold = result.critical_values[-1]
        statistic = float(result.statistic)
        threshold = float(threshold)
        return statistic, None, threshold, statistic < threshold

    # ------------------------------------------------------------------
    def assumption_tests(self) -> dict[str, dict[str, Any]]:
        """Evaluate classical regression assumptions.

        The procedure combines the Shapiro-Wilk and Anderson-Darling tests for
        normality, Levene and Bartlett tests for homoscedasticity across fitted
        quantile groups, and the Durbin-Watson statistic for independence.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Nested mapping summarising each assumption. For example,
            ``result["normality"]["passes"]`` indicates whether both normality
            tests are satisfied at the 5% level.

            The Anderson-Darling entry reports whichever evidence the installed
            SciPy can supply: ``"p_value"`` on SciPy 1.17 and newer, or
            ``"critical_value_5pct"`` on older releases. Both keys are always
            present and the unavailable one is ``None``.

        Examples
        --------
        >>> tests = diagnostics.assumption_tests()
        >>> sorted(tests.keys())
        ['homoscedasticity', 'independence', 'normality']
        >>> tests["independence"]["passes"]
        True
        """

        if self._assumption_cache is not None:
            return self._assumption_cache

        if len(self.residuals) < 8:
            raise ValueError(
                "At least 8 observations are required for assumption tests"
            )

        # Normality diagnostics
        shapiro_stat, shapiro_p = stats.shapiro(self.residuals)
        anderson_stat, anderson_p, anderson_crit, anderson_pass = (
            self._anderson_normality(self.residuals)
        )
        normality_pass = (shapiro_p > 0.05) and anderson_pass

        # Homoscedasticity diagnostics via fitted quantile groups
        df = pd.DataFrame({"fitted": self.fitted_values, "resid": self.residuals})
        try:
            df["group"] = pd.qcut(
                df["fitted"],
                q=min(4, max(2, df["fitted"].nunique())),
                duplicates="drop",
            )
        except ValueError as exc:  # occurs when data are constant
            raise ValueError("Cannot form groups for homoscedasticity checks") from exc

        grouped = [
            grp["resid"].to_numpy() for _, grp in df.groupby("group", observed=True)
        ]
        if len(grouped) < 2:
            raise ValueError("Need at least two groups to run homoscedasticity tests")

        levene_stat, levene_p = stats.levene(*grouped, center="median")
        bartlett_stat, bartlett_p = stats.bartlett(*grouped)
        homoscedastic_pass = (levene_p > 0.05) and (bartlett_p > 0.05)

        # Independence diagnostics via Durbin-Watson
        dw_stat = float(durbin_watson(self.residuals))
        independence_pass = 1.5 <= dw_stat <= 2.5

        self._assumption_cache = {
            "normality": {
                "passes": bool(normality_pass),
                "shapiro": {
                    "statistic": float(shapiro_stat),
                    "p_value": float(shapiro_p),
                },
                "anderson": {
                    "statistic": anderson_stat,
                    "p_value": anderson_p,
                    "critical_value_5pct": anderson_crit,
                },
            },
            "homoscedasticity": {
                "passes": bool(homoscedastic_pass),
                "levene": {
                    "statistic": float(levene_stat),
                    "p_value": float(levene_p),
                },
                "bartlett": {
                    "statistic": float(bartlett_stat),
                    "p_value": float(bartlett_p),
                },
            },
            "independence": {
                "passes": bool(independence_pass),
                "durbin_watson": float(dw_stat),
            },
        }
        return self._assumption_cache

    # ------------------------------------------------------------------
    def influence_analysis(self) -> dict[str, np.ndarray]:
        """Compute influence diagnostics under the Cook & Weisberg framework.

        Returns
        -------
        Dict[str, numpy.ndarray]
            Arrays of studentized residuals, Cook's distances, DFFITS, leverage,
            and DFBETAS for each observation.

        Examples
        --------
        >>> influence = diagnostics.influence_analysis()
        >>> {k: v.shape for k, v in influence.items()}["leverage"]
        (120,)
        """

        if self._influence_cache is not None:
            return self._influence_cache

        influence = self.model.get_influence()
        studentized = influence.resid_studentized_external
        cooks_d = influence.cooks_distance[0]
        dffits = influence.dffits[0]
        leverage = influence.hat_matrix_diag
        dfbetas = influence.dfbetas

        self._influence_cache = {
            "studentized_residuals": np.asarray(studentized, dtype=float),
            "cooks_distance": np.asarray(cooks_d, dtype=float),
            "dffits": np.asarray(dffits, dtype=float),
            "leverage": np.asarray(leverage, dtype=float),
            "dfbetas": np.asarray(dfbetas, dtype=float),
        }
        return self._influence_cache

    # ------------------------------------------------------------------
    def outlier_detection(self) -> dict[str, list[int]]:
        """Identify influential observations with multiple criteria.

        Returns
        -------
        Dict[str, List[int]]
            Observation indices flagged by studentized residual, Cook's distance
            and DFBETAS thresholds. Indices are returned in ascending order.

        Examples
        --------
        >>> diagnostics.outlier_detection()["cooks_distance"]
        []
        """

        if self._outlier_cache is not None:
            return self._outlier_cache

        influence = self.influence_analysis()
        n_obs = len(self.residuals)
        p_params = int(getattr(self.model, "df_model", len(self.model.params) - 1)) + 1

        studentized = influence["studentized_residuals"]
        cooks_d = influence["cooks_distance"]
        dfbetas = influence["dfbetas"]

        student_threshold = 3.0
        cook_threshold = 4.0 / max(n_obs, 1)
        dfbetas_threshold = 2.0 / math.sqrt(max(n_obs, 1))

        student_idx = np.where(np.abs(studentized) > student_threshold)[0]
        cooks_idx = np.where(cooks_d > cook_threshold)[0]
        dfbetas_idx = np.unique(np.where(np.abs(dfbetas) > dfbetas_threshold)[0])

        leverage = influence["leverage"]
        leverage_threshold = 2.0 * p_params / max(n_obs, 1)
        leverage_idx = np.where(leverage > leverage_threshold)[0]

        self._outlier_cache = {
            "studentized_residuals": student_idx.astype(int).tolist(),
            "cooks_distance": cooks_idx.astype(int).tolist(),
            "dfbetas": dfbetas_idx.astype(int).tolist(),
            "leverage": leverage_idx.astype(int).tolist(),
        }
        return self._outlier_cache

    # ------------------------------------------------------------------
    def model_adequacy(self) -> dict[str, Any]:
        """Summarise overall adequacy of the fitted model.

        The summary merges assumption test outcomes, influence diagnostics, and
        model fit statistics. Diagnostic plots for residual behaviour and Cook's
        distance are included to support expert review.

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``assumptions``, ``outliers``, ``influence``,
            ``model_metrics``, ``overall_pass``, and ``plots``.

        Examples
        --------
        >>> adequacy = diagnostics.model_adequacy()
        >>> sorted(adequacy["plots"].keys())
        ['cook_distance', 'qq_plot', 'residuals_vs_fitted']
        """

        assumptions = self.assumption_tests()
        outliers = self.outlier_detection()
        influence = self.influence_analysis()
        metrics = self.model_result.get("model_metrics", {})

        assumption_pass = all(result["passes"] for result in assumptions.values())
        outlier_count = sum(len(indices) for indices in outliers.values())
        influence_summary = {
            key: float(np.nanmax(np.abs(values))) for key, values in influence.items()
        }

        try:
            plots = self._generate_diagnostic_plots(influence)
        except RuntimeError:
            plots = {}

        overall_pass = (
            assumption_pass
            and outlier_count == 0
            and influence_summary["cooks_distance"] < (4.0 / len(self.residuals))
        )

        return {
            "assumptions": assumptions,
            "outliers": outliers,
            "influence": influence_summary,
            "model_metrics": metrics,
            "overall_pass": bool(overall_pass),
            "plots": plots,
        }

    # ------------------------------------------------------------------
    def recommendation_system(self) -> list[str]:
        """Produce actionable recommendations based on diagnostics.

        Recommendations interpret assumption violations and influential point
        detections to guide remedial strategies such as variance-stabilising
        transformations, robust regression, or data review.

        Returns
        -------
        List[str]
            Human-readable recommendations ordered by severity.

        Examples
        --------
        >>> diagnostics.recommendation_system()  # doctest: +SKIP
        ['No major issues detected. Consider validating on a holdout set.']
        """

        suggestions: list[str] = []
        assumptions = self.assumption_tests()
        outliers = self.outlier_detection()
        influence = self.influence_analysis()

        if not assumptions["normality"]["passes"]:
            suggestions.append(
                "Residuals deviate from normality; consider Box-Cox transformations or non-parametric approaches."
            )
        if not assumptions["homoscedasticity"]["passes"]:
            suggestions.append(
                "Variance heterogeneity detected; weighted least squares or modelling variance as a function of predictors is recommended."
            )
        if not assumptions["independence"]["passes"]:
            suggestions.append(
                "Residual autocorrelation present; incorporate lag terms or mixed-effects structures to address dependence."
            )

        if any(outliers.values()):
            suggestions.append(
                "Investigate high-influence observations flagged by studentized residuals, Cook's distance, or DFBETAS before finalising conclusions."
            )

        cooks_peak = float(np.nanmax(np.abs(influence["cooks_distance"])))
        if cooks_peak > (4.0 / len(self.residuals)):
            suggestions.append(
                "Cook's distance exceeds the 4/n heuristic; reassess the modelling assumptions for the flagged runs."
            )

        if not suggestions:
            suggestions.append(
                "No major issues detected. Consider validating on a holdout set to confirm predictive adequacy."
            )

        return suggestions

    # ------------------------------------------------------------------
    def _generate_diagnostic_plots(
        self, influence: dict[str, np.ndarray]
    ) -> dict[str, Figure]:
        """Create diagnostic plots supporting :meth:`model_adequacy`.

        Parameters
        ----------
        influence : Dict[str, numpy.ndarray]
            Influence diagnostics as returned by :meth:`influence_analysis`.

        Returns
        -------
        Dict[str, matplotlib.figure.Figure]
            Figures for residuals vs fitted, Q-Q analysis, and Cook's distance.
        """

        if plt is None:
            raise RuntimeError("matplotlib is required to generate diagnostic plots")

        figures: dict[str, Figure] = {}

        fig_rvf, ax_rvf = plt.subplots(figsize=(6, 4))
        ax_rvf.scatter(self.fitted_values, self.residuals, alpha=0.7)
        ax_rvf.axhline(0.0, color="red", linestyle="--", linewidth=1.0)
        ax_rvf.set_xlabel("Fitted values")
        ax_rvf.set_ylabel("Residuals")
        ax_rvf.set_title("Residuals vs Fitted")
        figures["residuals_vs_fitted"] = fig_rvf

        fig_qq, ax_qq = plt.subplots(figsize=(6, 4))
        stats.probplot(self.residuals, dist="norm", plot=ax_qq)
        ax_qq.set_title("Normal Q-Q Plot")
        figures["qq_plot"] = fig_qq

        fig_cook, ax_cook = plt.subplots(figsize=(6, 4))
        ax_cook.stem(
            np.arange(len(influence["cooks_distance"])),
            influence["cooks_distance"],
            basefmt=" ",
        )
        ax_cook.set_xlabel("Observation")
        ax_cook.set_ylabel("Cook's distance")
        ax_cook.set_title("Cook's Distance by Observation")
        figures["cook_distance"] = fig_cook

        return figures
