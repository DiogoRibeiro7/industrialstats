"""Model diagnostics for regression analyses.

This module provides tools to evaluate model assumptions, detect
outliers, and visualize influential observations. It is designed to be
used with ``statsmodels`` regression result objects and focuses on
interpretable outputs for practitioners.

References
----------
.. [1] Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
.. [2] Cook, R. D., & Weisberg, S. (1982). *Residuals and Influence in
       Regression*.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson

logger = logging.getLogger(__name__)


class ModelDiagnostics:
    """Run diagnostic checks on fitted regression models.

    Parameters
    ----------
    model : statsmodels.regression.linear_model.RegressionResultsWrapper
        Fitted regression results instance from ``statsmodels``.
    """

    def __init__(self, model) -> None:
        self.model = model
        self.residuals = pd.Series(model.resid, name="residuals")
        self.fitted = pd.Series(model.fittedvalues, name="fitted")
        self.exog = pd.DataFrame(model.model.exog, columns=model.model.exog_names)
        self._test_results: Optional[pd.DataFrame] = None
        self._outliers: Optional[pd.DataFrame] = None

    def assumption_tests(self, alpha: float = 0.05) -> pd.DataFrame:
        """Test key regression assumptions.

        Parameters
        ----------
        alpha : float, optional
            Significance level for hypothesis tests, by default ``0.05``.

        Returns
        -------
        pandas.DataFrame
            Table with test statistics, p-values, and pass/fail indicators.
        """

        shapiro_stat, shapiro_p = stats.shapiro(self.residuals)
        bp_stat, bp_p, _, _ = het_breuschpagan(self.residuals, self.exog)
        dw_stat = durbin_watson(self.residuals)

        results = pd.DataFrame(
            {
                "test": ["Shapiro-Wilk", "Breusch-Pagan", "Durbin-Watson"],
                "statistic": [shapiro_stat, bp_stat, dw_stat],
                "pvalue": [shapiro_p, bp_p, np.nan],
                "passed": [
                    shapiro_p > alpha,
                    bp_p > alpha,
                    (1.5 < dw_stat < 2.5),
                ],
                "assumption": [
                    "normality",
                    "homoscedasticity",
                    "independence",
                ],
            }
        )

        self._test_results = results
        return results

    def detect_outliers(
        self,
        std_resid_thresh: float = 2.0,
        cook_thresh: Optional[float] = None,
        leverage_thresh: Optional[float] = None,
    ) -> pd.DataFrame:
        """Identify influential observations.

        Parameters
        ----------
        std_resid_thresh : float, optional
            Absolute threshold for standardized residuals, by default ``2.0``.
        cook_thresh : float, optional
            Cutoff for Cook's distance. Defaults to ``4 / n`` if ``None``.
        leverage_thresh : float, optional
            Cutoff for leverage values. Defaults to ``2p / n`` if ``None`` where
            ``p`` is the number of parameters.

        Returns
        -------
        pandas.DataFrame
            Residual diagnostics with outlier flags.
        """

        infl = self.model.get_influence()
        std_resid = infl.resid_studentized_internal
        cooks_d = infl.cooks_distance[0]
        leverage = infl.hat_matrix_diag

        n = len(self.residuals)
        p = self.exog.shape[1]
        if cook_thresh is None:
            cook_thresh = 4 / n
        if leverage_thresh is None:
            leverage_thresh = 2 * p / n

        df = pd.DataFrame(
            {
                "standardized_residual": std_resid,
                "cooks_distance": cooks_d,
                "leverage": leverage,
            }
        )
        df["is_outlier"] = (
            (df["standardized_residual"].abs() > std_resid_thresh)
            | (df["cooks_distance"] > cook_thresh)
            | (df["leverage"] > leverage_thresh)
        )

        self._outliers = df
        return df

    def influence_plots(self) -> plt.Figure:
        """Generate diagnostic plots.

        Returns
        -------
        matplotlib.figure.Figure
            Figure with residual, QQ, and influence plots.
        """

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))

        # Residuals vs fitted
        sns.scatterplot(x=self.fitted, y=self.residuals, ax=axes[0], alpha=0.7)
        axes[0].axhline(0, color="red", linestyle="--", linewidth=1)
        axes[0].set_xlabel("Fitted values")
        axes[0].set_ylabel("Residuals")
        axes[0].set_title("Residuals vs Fitted")

        # QQ plot
        stats.probplot(self.residuals, dist="norm", plot=axes[1])
        axes[1].set_title("Normal Q-Q")

        # Cook's distance plot
        infl = self.model.get_influence()
        cooks_d = infl.cooks_distance[0]
        axes[2].stem(np.arange(len(cooks_d)), cooks_d, markerfmt=",", basefmt=" ")
        axes[2].set_xlabel("Observation")
        axes[2].set_ylabel("Cook's D")
        axes[2].set_title("Influence (Cook's D)")

        fig.tight_layout()
        return fig

    def recommendations(self) -> List[str]:
        """Provide recommendations based on diagnostics.

        Returns
        -------
        list of str
            Suggested actions for improving model assumptions.
        """

        recs: List[str] = []
        tests = (
            self._test_results
            if self._test_results is not None
            else self.assumption_tests()
        )
        outliers = (
            self._outliers if self._outliers is not None else self.detect_outliers()
        )

        for _, row in tests.iterrows():
            if not row["passed"]:
                if row["assumption"] == "normality":
                    recs.append(
                        "Residuals appear non-normal; consider a transformation or robust regression."
                    )
                elif row["assumption"] == "homoscedasticity":
                    recs.append(
                        "Heteroscedasticity detected; consider weighted least squares or variance-stabilizing transforms."
                    )
                elif row["assumption"] == "independence":
                    recs.append(
                        "Autocorrelation detected; consider adding lag terms or using time-series models."
                    )

        if outliers["is_outlier"].any():
            recs.append(
                "Potential outliers or influential points detected; investigate observations with high Cook's distance or leverage."
            )

        if not recs:
            recs.append(
                "No major issues detected. Model assumptions appear reasonable."
            )

        return recs
