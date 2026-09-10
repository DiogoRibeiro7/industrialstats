"""Inference helpers for balanced complete split-plot experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from math import prod
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from scipy.linalg import helmert


@dataclass(frozen=True)
class SplitPlotErrorStrata:
    """Balanced split-plot experimental-unit and error-stratum summary."""

    whole_plot_treatments: int
    subplot_treatments: int
    replicates: int
    whole_plots: int
    runs: int
    whole_plot_error_df: int
    subplot_error_df: int


class SplitPlotAnalysis:
    """Validate and analyse a balanced complete split-plot experiment."""

    def __init__(
        self,
        data: pd.DataFrame,
        response_column: str,
        whole_plot_factors: list[str],
        subplot_factors: list[str],
        *,
        whole_plot_column: str = "WholePlot",
        replicate_column: str = "Replicate",
    ) -> None:
        if not whole_plot_factors:
            raise ValueError("At least one whole-plot factor is required")
        if not subplot_factors:
            raise ValueError("At least one subplot factor is required")
        overlap = set(whole_plot_factors) & set(subplot_factors)
        if overlap:
            raise ValueError(
                "Factors cannot be both whole-plot and subplot factors: "
                + ", ".join(sorted(overlap))
            )

        required = {
            response_column,
            whole_plot_column,
            replicate_column,
            *whole_plot_factors,
            *subplot_factors,
        }
        missing = sorted(required - set(data.columns))
        if missing:
            raise ValueError("Missing required column(s): " + ", ".join(missing))

        self.data = data.dropna(subset=[response_column]).copy()
        if self.data.empty:
            raise ValueError("No valid data rows after removing missing responses")

        self.response = response_column
        self.whole_plot_factors = list(whole_plot_factors)
        self.subplot_factors = list(subplot_factors)
        self.whole_plot_column = whole_plot_column
        self.replicate_column = replicate_column

    def error_strata(self) -> SplitPlotErrorStrata:
        """Return balanced whole-plot and subplot error-stratum degrees of freedom."""
        self._validate_whole_plot_units()

        whole_treatment_counts = (
            self.data.groupby(self.whole_plot_factors, observed=True)[
                self.whole_plot_column
            ]
            .nunique()
            .to_numpy()
        )
        if len({int(value) for value in whole_treatment_counts}) != 1:
            raise ValueError(
                "Every whole-plot treatment combination must have the same number "
                "of independent whole-plot replicates"
            )

        replicates = int(whole_treatment_counts[0])
        whole_plot_treatments = int(
            self.data[self.whole_plot_factors].drop_duplicates().shape[0]
        )
        subplot_levels = [
            int(self.data[factor].nunique(dropna=False))
            for factor in self.subplot_factors
        ]
        subplot_treatments = prod(subplot_levels)
        expected_subplot_combinations = int(
            self.data[self.subplot_factors].drop_duplicates().shape[0]
        )
        if expected_subplot_combinations != subplot_treatments:
            raise ValueError(
                "Subplot factors do not form a complete factorial treatment set"
            )

        for whole_plot_id, frame in self.data.groupby(
            self.whole_plot_column, observed=True, sort=False
        ):
            subplot_combinations = frame[self.subplot_factors].drop_duplicates()
            if (
                len(frame) != subplot_treatments
                or len(subplot_combinations) != subplot_treatments
            ):
                raise ValueError(
                    f"Whole plot {whole_plot_id!r} must contain exactly one complete "
                    "subplot factorial"
                )

        whole_plots = whole_plot_treatments * replicates
        runs = whole_plots * subplot_treatments
        if len(self.data) != runs:
            raise ValueError(
                "Observed run count is inconsistent with a balanced split-plot"
            )

        return SplitPlotErrorStrata(
            whole_plot_treatments=whole_plot_treatments,
            subplot_treatments=subplot_treatments,
            replicates=replicates,
            whole_plots=whole_plots,
            runs=runs,
            whole_plot_error_df=whole_plot_treatments * (replicates - 1),
            subplot_error_df=(
                whole_plot_treatments * (replicates - 1) * (subplot_treatments - 1)
            ),
        )

    def anova_table(self) -> pd.DataFrame:
        """Return the classical balanced split-plot ANOVA table.

        Whole-plot-only treatment terms are tested against ``WholePlot Error``.
        Terms containing at least one subplot factor are tested against
        ``Subplot Error``. Sums of squares use orthogonal Helmert-contrast
        projections, so the decomposition is invariant to row order and to
        arbitrary treatment labels.

        Returns
        -------
        pandas.DataFrame
            ANOVA table with source, randomization stratum, degrees of freedom,
            sums of squares, mean squares, F statistics, p-values, and the
            denominator error term used for each fixed effect.
        """
        strata = self.error_strata()
        if strata.whole_plot_error_df <= 0:
            raise ValueError(
                "Whole-plot treatment combinations require replication to estimate "
                "whole-plot error"
            )
        if strata.subplot_error_df <= 0:
            raise ValueError(
                "The subplot stratum requires replication to estimate subplot error"
            )

        all_factors = [*self.whole_plot_factors, *self.subplot_factors]
        level_map = {
            factor: list(pd.unique(self.data[factor])) for factor in all_factors
        }
        all_terms = [
            term
            for order in range(1, len(all_factors) + 1)
            for term in combinations(all_factors, order)
        ]
        whole_plot_factor_set = set(self.whole_plot_factors)
        whole_plot_terms = [
            term for term in all_terms if set(term) <= whole_plot_factor_set
        ]
        subplot_terms = [term for term in all_terms if term not in whole_plot_terms]

        grouped = self.data.groupby(
            self.whole_plot_column,
            observed=True,
            sort=False,
        )
        whole_plot_frame = grouped[self.whole_plot_factors].first().reset_index()
        whole_plot_frame[self.response] = grouped[self.response].mean().to_numpy()

        whole_plot_response = whole_plot_frame[self.response].to_numpy(dtype=float)
        whole_plot_centered = whole_plot_response - whole_plot_response.mean()
        whole_plot_total_ss = (
            float(whole_plot_centered @ whole_plot_centered) * strata.subplot_treatments
        )

        rows: list[dict[str, Any]] = []
        whole_plot_model_ss = 0.0
        for term in whole_plot_terms:
            matrix = self._term_matrix(whole_plot_frame, term, level_map)
            sum_sq = (
                self._projection_sum_of_squares(whole_plot_centered, matrix)
                * strata.subplot_treatments
            )
            whole_plot_model_ss += sum_sq
            rows.append(
                {
                    "Source": self._term_name(term),
                    "Stratum": "whole_plot",
                    "df": int(matrix.shape[1]),
                    "sum_sq": sum_sq,
                }
            )

        whole_plot_error_ss = whole_plot_total_ss - whole_plot_model_ss
        if whole_plot_error_ss < -1e-10:
            raise ValueError("Whole-plot decomposition produced negative error SS")
        whole_plot_error_ss = max(0.0, whole_plot_error_ss)
        whole_plot_error_ms = whole_plot_error_ss / strata.whole_plot_error_df

        response = self.data[self.response].to_numpy(dtype=float)
        whole_plot_means = (
            grouped[self.response].transform("mean").to_numpy(dtype=float)
        )
        within_response = response - whole_plot_means
        subplot_total_ss = float(within_response @ within_response)

        subplot_model_ss = 0.0
        subplot_model_df = 0
        for term in subplot_terms:
            matrix = self._term_matrix(self.data, term, level_map)
            sum_sq = self._projection_sum_of_squares(within_response, matrix)
            term_df = int(matrix.shape[1])
            subplot_model_ss += sum_sq
            subplot_model_df += term_df
            rows.append(
                {
                    "Source": self._term_name(term),
                    "Stratum": "subplot",
                    "df": term_df,
                    "sum_sq": sum_sq,
                }
            )

        derived_subplot_error_df = (
            len(self.data) - strata.whole_plots - subplot_model_df
        )
        if derived_subplot_error_df != strata.subplot_error_df:
            raise ValueError(
                "Subplot error degrees of freedom disagree with the validated "
                "balanced-design identity"
            )

        subplot_error_ss = subplot_total_ss - subplot_model_ss
        if subplot_error_ss < -1e-10:
            raise ValueError("Subplot decomposition produced negative error SS")
        subplot_error_ss = max(0.0, subplot_error_ss)
        subplot_error_ms = subplot_error_ss / strata.subplot_error_df

        rows.extend(
            [
                {
                    "Source": "WholePlot Error",
                    "Stratum": "whole_plot_error",
                    "df": strata.whole_plot_error_df,
                    "sum_sq": whole_plot_error_ss,
                },
                {
                    "Source": "Subplot Error",
                    "Stratum": "subplot_error",
                    "df": strata.subplot_error_df,
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
                denominator_df = strata.whole_plot_error_df
                denominator_name = "WholePlot Error"
            elif stratum == "subplot":
                denominator_ms = subplot_error_ms
                denominator_df = strata.subplot_error_df
                denominator_name = "Subplot Error"
            else:
                continue

            numerator_ms = float(row["mean_sq"])
            if denominator_ms == 0.0:
                f_statistic = np.inf if numerator_ms > 0.0 else np.nan
                p_value = 0.0 if np.isinf(f_statistic) else np.nan
            else:
                f_statistic = numerator_ms / denominator_ms
                p_value = float(stats.f.sf(f_statistic, int(row["df"]), denominator_df))

            table.loc[index, "F"] = f_statistic
            table.loc[index, "PR(>F)"] = p_value
            table.loc[index, "Denominator"] = denominator_name

        return table

    def expected_mean_squares(
        self,
        *,
        whole_plot_variance: float,
        residual_variance: float,
    ) -> dict[str, float]:
        """Return error-stratum EMS values for the random-intercept split-plot model."""
        if whole_plot_variance < 0 or residual_variance < 0:
            raise ValueError("Variance components must be non-negative")
        strata = self.error_strata()
        return {
            "whole_plot_error": residual_variance
            + strata.subplot_treatments * whole_plot_variance,
            "subplot_error": residual_variance,
        }

    def fit_mixed_model(
        self,
        *,
        reml: bool = True,
        method: str = "lbfgs",
    ) -> dict[str, Any]:
        """Fit the full fixed-treatment split-plot model with a random whole-plot intercept."""
        strata = self.error_strata()
        all_factors = [*self.whole_plot_factors, *self.subplot_factors]
        fixed_terms = " * ".join(self._categorical_term(name) for name in all_factors)
        formula = f"{self._quote(self.response)} ~ {fixed_terms}"

        model = sm.MixedLM.from_formula(
            formula,
            data=self.data,
            groups=self.whole_plot_column,
            re_formula="1",
        )
        result = model.fit(reml=reml, method=method)

        whole_plot_variance = float(result.cov_re.iloc[0, 0])
        residual_variance = float(result.scale)
        return {
            "formula": formula,
            "converged": bool(result.converged),
            "reml": reml,
            "fixed_effects": result.fe_params.to_dict(),
            "whole_plot_variance": whole_plot_variance,
            "residual_variance": residual_variance,
            "error_strata": asdict(strata),
            "expected_mean_squares": self.expected_mean_squares(
                whole_plot_variance=whole_plot_variance,
                residual_variance=residual_variance,
            ),
            "log_likelihood": float(result.llf),
        }

    def _validate_whole_plot_units(self) -> None:
        """Ensure identifiers correspond to genuine whole-plot experimental units."""
        if self.data[self.whole_plot_column].isna().any():
            raise ValueError("Whole-plot identifiers cannot be missing")

        for whole_plot_id, frame in self.data.groupby(
            self.whole_plot_column, observed=True, sort=False
        ):
            if frame[self.replicate_column].nunique(dropna=False) != 1:
                raise ValueError(
                    f"Whole plot {whole_plot_id!r} spans multiple replicate identifiers"
                )
            for factor in self.whole_plot_factors:
                if frame[factor].nunique(dropna=False) != 1:
                    raise ValueError(
                        f"Whole-plot factor {factor!r} changes within whole plot "
                        f"{whole_plot_id!r}"
                    )

    @staticmethod
    def _term_name(term: tuple[str, ...]) -> str:
        return "*".join(term)

    @staticmethod
    def _contrast_basis(values: pd.Series, levels: list[Any]) -> np.ndarray:
        level_to_index = {level: index for index, level in enumerate(levels)}
        row_indices = np.asarray(
            [level_to_index[value] for value in values],
            dtype=int,
        )
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

    @staticmethod
    def _quote(name: str) -> str:
        escaped = name.replace("\\", "\\\\").replace('"', '\\"')
        return f'Q("{escaped}")'

    @classmethod
    def _categorical_term(cls, name: str) -> str:
        return f"C({cls._quote(name)})"
