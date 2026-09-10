"""Classical and mixed-model analysis for balanced split-plot experiments."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import prod
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.linalg import helmert


@dataclass(frozen=True, slots=True)
class SplitPlotANOVAResult:
    """ANOVA table plus explicit split-plot error-stratum metadata."""

    table: pd.DataFrame
    whole_plot_error_df: int
    subplot_error_df: int
    n_whole_plots: int
    n_subplots_per_whole_plot: int


class SplitPlotAnalysis:
    """Analyse a balanced full-factorial split-plot experiment.

    The implementation keeps the two randomization strata explicit. Effects
    involving only whole-plot factors are tested against whole-plot error;
    effects containing at least one subplot factor are tested against subplot
    error. A random-intercept mixed model can be fitted separately as a
    variance-component cross-check.

    Parameters
    ----------
    data : pandas.DataFrame
        Experimental data containing response, ``WholePlot``, whole-plot
        factors, and subplot factors.
    response_column : str
        Response variable name.
    whole_plot_factors : list[str]
        Hard-to-change treatment factors applied to whole plots.
    subplot_factors : list[str]
        Easy-to-change factors randomized within whole plots.
    whole_plot_column : str, optional
        Whole-plot experimental-unit identifier. Defaults to ``"WholePlot"``.

    Notes
    -----
    This first implementation deliberately requires a balanced complete
    factorial within each whole plot and equal replication of every whole-plot
    treatment combination. Unbalanced split-plot inference is a separate
    problem and is rejected rather than silently analysed with the wrong error
    term.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        response_column: str,
        whole_plot_factors: list[str],
        subplot_factors: list[str],
        *,
        whole_plot_column: str = "WholePlot",
    ) -> None:
        if not whole_plot_factors:
            raise ValueError("At least one whole-plot factor is required.")
        if not subplot_factors:
            raise ValueError("At least one subplot factor is required.")
        if set(whole_plot_factors) & set(subplot_factors):
            raise ValueError("Whole-plot and subplot factor sets must be disjoint.")

        required = [
            response_column,
            whole_plot_column,
            *whole_plot_factors,
            *subplot_factors,
        ]
        missing = [column for column in required if column not in data.columns]
        if missing:
            raise ValueError(f"Missing required split-plot columns: {missing}.")
        if data.empty:
            raise ValueError("Split-plot data must contain at least one row.")

        self.data = data.loc[:, required].copy()
        self.response_column = response_column
        self.whole_plot_factors = list(whole_plot_factors)
        self.subplot_factors = list(subplot_factors)
        self.whole_plot_column = whole_plot_column
        self._validate_balanced_design()

    @staticmethod
    def _term_name(term: tuple[str, ...]) -> str:
        return "*".join(term)

    def _levels(self, factor: str) -> list[Any]:
        return list(pd.unique(self.data[factor]))

    def _all_terms(self, factors: list[str]) -> list[tuple[str, ...]]:
        return [
            term
            for order in range(1, len(factors) + 1)
            for term in combinations(factors, order)
        ]

    def _validate_balanced_design(self) -> None:
        numeric_response = pd.to_numeric(self.data[self.response_column], errors="coerce")
        if numeric_response.isna().any():
            raise ValueError("Response values must be finite numeric values.")
        response_array = numeric_response.to_numpy(dtype=float)
        if not np.all(np.isfinite(response_array)):
            raise ValueError("Response values must be finite numeric values.")
        self.data[self.response_column] = response_array

        all_factors = [*self.whole_plot_factors, *self.subplot_factors]
        for factor in all_factors:
            if self.data[factor].isna().any():
                raise ValueError(f"Factor {factor!r} contains missing values.")
            if self.data[factor].nunique(dropna=False) < 2:
                raise ValueError(f"Factor {factor!r} must contain at least two levels.")

        wp = self.whole_plot_column
        if self.data[wp].isna().any():
            raise ValueError("WholePlot identifiers must not be missing.")

        subplot_level_counts = [len(self._levels(factor)) for factor in self.subplot_factors]
        expected_subplots = prod(subplot_level_counts)
        grouped = self.data.groupby(wp, sort=False, observed=False)
        sizes = grouped.size()
        if not bool((sizes == expected_subplots).all()):
            raise ValueError(
                "Every whole plot must contain exactly one complete subplot factorial."
            )

        subplot_columns = self.subplot_factors
        expected_subplot_combinations = expected_subplots
        for whole_plot_id, frame in grouped:
            if frame[subplot_columns].drop_duplicates().shape[0] != expected_subplot_combinations:
                raise ValueError(
                    f"Whole plot {whole_plot_id!r} does not contain each subplot "
                    "treatment combination exactly once."
                )
            for factor in self.whole_plot_factors:
                if frame[factor].nunique(dropna=False) != 1:
                    raise ValueError(
                        f"Whole-plot factor {factor!r} changes within whole plot "
                        f"{whole_plot_id!r}."
                    )

        whole_plot_frame = grouped[self.whole_plot_factors].first().reset_index()
        treatment_counts = whole_plot_frame.groupby(
            self.whole_plot_factors,
            observed=False,
        ).size()
        if treatment_counts.nunique() != 1:
            raise ValueError(
                "Every whole-plot treatment combination must have equal replication."
            )

        expected_whole_plot_treatments = prod(
            len(self._levels(factor)) for factor in self.whole_plot_factors
        )
        if len(treatment_counts) != expected_whole_plot_treatments:
            raise ValueError(
                "Whole plots must cover the complete whole-plot treatment factorial."
            )

    @staticmethod
    def _contrast_basis(values: pd.Series, levels: list[Any]) -> np.ndarray:
        """Return orthonormal Helmert contrast columns for one factor."""
        level_to_index = {level: index for index, level in enumerate(levels)}
        try:
            row_indices = np.asarray([level_to_index[value] for value in values], dtype=int)
        except KeyError as exc:  # pragma: no cover - guarded by construction
            raise ValueError("Observed factor level is absent from the level map.") from exc
        basis = helmert(len(levels), full=False).T
        return np.asarray(basis[row_indices, :], dtype=float)

    def _term_matrix(
        self,
        frame: pd.DataFrame,
        term: tuple[str, ...],
        level_map: dict[str, list[Any]],
    ) -> np.ndarray:
        matrices = [
            self._contrast_basis(frame[factor], level_map[factor]) for factor in term
        ]
        matrix = matrices[0]
        for next_matrix in matrices[1:]:
            matrix = (matrix[:, :, None] * next_matrix[:, None, :]).reshape(
                len(frame), -1
            )
        return matrix

    @staticmethod
    def _projection_sum_of_squares(response: np.ndarray, matrix: np.ndarray) -> float:
        coefficients, *_ = np.linalg.lstsq(matrix, response, rcond=None)
        fitted = matrix @ coefficients
        return float(fitted @ fitted)

    def anova(self) -> SplitPlotANOVAResult:
        """Compute the classical balanced split-plot ANOVA table.

        Returns
        -------
        SplitPlotANOVAResult
            Table with treatment and error terms, where each fixed effect is
            tested against the error stratum implied by the randomization.
        """
        wp = self.whole_plot_column
        response = self.response_column
        all_factors = [*self.whole_plot_factors, *self.subplot_factors]
        level_map = {factor: self._levels(factor) for factor in all_factors}
        all_terms = self._all_terms(all_factors)
        whole_plot_terms = [
            term for term in all_terms if set(term) <= set(self.whole_plot_factors)
        ]
        subplot_terms = [term for term in all_terms if term not in whole_plot_terms]

        grouped = self.data.groupby(wp, sort=False, observed=False)
        whole_plot_frame = grouped[self.whole_plot_factors].first().reset_index()
        whole_plot_frame[response] = grouped[response].mean().to_numpy()
        n_whole_plots = len(whole_plot_frame)
        n_subplots = int(grouped.size().iloc[0])

        wp_response = whole_plot_frame[response].to_numpy(dtype=float)
        wp_centered = wp_response - wp_response.mean()
        whole_plot_total_ss = float(wp_centered @ wp_centered) * n_subplots

        rows: list[dict[str, Any]] = []
        whole_plot_model_ss = 0.0
        for term in whole_plot_terms:
            matrix = self._term_matrix(whole_plot_frame, term, level_map)
            ss = self._projection_sum_of_squares(wp_centered, matrix) * n_subplots
            df = int(matrix.shape[1])
            whole_plot_model_ss += ss
            rows.append(
                {
                    "Source": self._term_name(term),
                    "Stratum": "whole_plot",
                    "df": df,
                    "sum_sq": ss,
                }
            )

        whole_plot_error_df = n_whole_plots - prod(
            len(level_map[factor]) for factor in self.whole_plot_factors
        )
        if whole_plot_error_df <= 0:
            raise ValueError(
                "Whole-plot treatment combinations require replication to estimate "
                "whole-plot error."
            )
        whole_plot_error_ss = whole_plot_total_ss - whole_plot_model_ss
        if whole_plot_error_ss < -1e-10:
            raise ValueError("Whole-plot ANOVA decomposition produced negative error SS.")
        whole_plot_error_ss = max(0.0, whole_plot_error_ss)
        whole_plot_error_ms = whole_plot_error_ss / whole_plot_error_df

        response_array = self.data[response].to_numpy(dtype=float)
        whole_plot_means = grouped[response].transform("mean").to_numpy(dtype=float)
        within_response = response_array - whole_plot_means
        subplot_total_ss = float(within_response @ within_response)
        subplot_model_ss = 0.0

        for term in subplot_terms:
            matrix = self._term_matrix(self.data, term, level_map)
            ss = self._projection_sum_of_squares(within_response, matrix)
            df = int(matrix.shape[1])
            subplot_model_ss += ss
            rows.append(
                {
                    "Source": self._term_name(term),
                    "Stratum": "subplot",
                    "df": df,
                    "sum_sq": ss,
                }
            )

        subplot_total_df = len(self.data) - n_whole_plots
        subplot_model_df = sum(int(row["df"]) for row in rows if row["Stratum"] == "subplot")
        subplot_error_df = subplot_total_df - subplot_model_df
        if subplot_error_df <= 0:
            raise ValueError(
                "The subplot stratum requires replication beyond one complete treatment "
                "factorial to estimate residual error."
            )
        subplot_error_ss = subplot_total_ss - subplot_model_ss
        if subplot_error_ss < -1e-10:
            raise ValueError("Subplot ANOVA decomposition produced negative error SS.")
        subplot_error_ss = max(0.0, subplot_error_ss)
        subplot_error_ms = subplot_error_ss / subplot_error_df

        rows.extend(
            [
                {
                    "Source": "WholePlot Error",
                    "Stratum": "whole_plot_error",
                    "df": whole_plot_error_df,
                    "sum_sq": whole_plot_error_ss,
                },
                {
                    "Source": "Subplot Error",
                    "Stratum": "subplot_error",
                    "df": subplot_error_df,
                    "sum_sq": subplot_error_ss,
                },
            ]
        )

        table = pd.DataFrame(rows)
        table["mean_sq"] = table["sum_sq"] / table["df"]
        table["F"] = np.nan
        table["PR(>F)"] = np.nan
        table["Denominator"] = pd.NA

        for index, row in table.iterrows():
            stratum = row["Stratum"]
            if stratum == "whole_plot":
                denominator_ms = whole_plot_error_ms
                denominator_df = whole_plot_error_df
                denominator_name = "WholePlot Error"
            elif stratum == "subplot":
                denominator_ms = subplot_error_ms
                denominator_df = subplot_error_df
                denominator_name = "Subplot Error"
            else:
                continue

            numerator_ms = float(row["mean_sq"])
            if denominator_ms == 0.0:
                f_stat = np.inf if numerator_ms > 0.0 else np.nan
                p_value = 0.0 if np.isinf(f_stat) else np.nan
            else:
                f_stat = numerator_ms / denominator_ms
                p_value = float(stats.f.sf(f_stat, int(row["df"]), denominator_df))
            table.at[index, "F"] = f_stat
            table.at[index, "PR(>F)"] = p_value
            table.at[index, "Denominator"] = denominator_name

        return SplitPlotANOVAResult(
            table=table,
            whole_plot_error_df=whole_plot_error_df,
            subplot_error_df=subplot_error_df,
            n_whole_plots=n_whole_plots,
            n_subplots_per_whole_plot=n_subplots,
        )

    def fit_mixed_model(self) -> Any:
        """Fit a random-intercept mixed model grouped by whole plot.

        The mixed model is a complementary variance-component analysis. Its
        fixed-effect Wald tests are not substituted for the classical stratum-
        specific F tests returned by :meth:`anova`.
        """
        import statsmodels.api as sm

        fixed_terms = " * ".join(f"C(Q('{factor}'))" for factor in [
            *self.whole_plot_factors,
            *self.subplot_factors,
        ])
        formula = f"Q('{self.response_column}') ~ {fixed_terms}"
        model = sm.MixedLM.from_formula(
            formula,
            self.data,
            groups=self.data[self.whole_plot_column],
            re_formula="1",
        )
        return model.fit(reml=True)
