"""Inference helpers for balanced complete split-plot experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import prod
from typing import Any

import pandas as pd
import statsmodels.api as sm


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
        if len(set(int(value) for value in whole_treatment_counts)) != 1:
            raise ValueError(
                "Every whole-plot treatment combination must have the same number "
                "of independent whole-plot replicates"
            )

        replicates = int(whole_treatment_counts[0])
        whole_plot_treatments = int(
            self.data[self.whole_plot_factors].drop_duplicates().shape[0]
        )
        subplot_levels = [
            int(self.data[factor].nunique(dropna=False)) for factor in self.subplot_factors
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
            combinations = frame[self.subplot_factors].drop_duplicates()
            if len(frame) != subplot_treatments or len(combinations) != subplot_treatments:
                raise ValueError(
                    f"Whole plot {whole_plot_id!r} must contain exactly one complete "
                    "subplot factorial"
                )

        whole_plots = whole_plot_treatments * replicates
        runs = whole_plots * subplot_treatments
        if len(self.data) != runs:
            raise ValueError("Observed run count is inconsistent with a balanced split-plot")

        return SplitPlotErrorStrata(
            whole_plot_treatments=whole_plot_treatments,
            subplot_treatments=subplot_treatments,
            replicates=replicates,
            whole_plots=whole_plots,
            runs=runs,
            whole_plot_error_df=whole_plot_treatments * (replicates - 1),
            subplot_error_df=(
                whole_plot_treatments
                * (replicates - 1)
                * (subplot_treatments - 1)
            ),
        )

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
        formula = f'{self._quote(self.response)} ~ {fixed_terms}'

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
    def _quote(name: str) -> str:
        escaped = name.replace("\\", "\\\\").replace('"', '\\"')
        return f'Q("{escaped}")'

    @classmethod
    def _categorical_term(cls, name: str) -> str:
        return f"C({cls._quote(name)})"
