"""Statistical tests for balanced split-plot inference."""

import numpy as np
import pytest

from industrialstats.analysis.split_plot import SplitPlotAnalysis
from industrialstats.designs.advanced import SplitPlotDesign
from industrialstats.designs.base import Factor


def _generated_split_plot(
    *,
    whole_plot_factors: list[Factor] | None = None,
    subplot_factors: list[Factor] | None = None,
    replicates: int = 3,
):
    whole_plot_factors = whole_plot_factors or [Factor("A", [-1, 1])]
    subplot_factors = subplot_factors or [Factor("B", [-1, 0, 1])]
    design = SplitPlotDesign(
        whole_plot_factors,
        subplot_factors,
        replicates=replicates,
        randomize=False,
    )
    return design.generate_design()


def test_error_strata_match_balanced_split_plot_identities() -> None:
    data = _generated_split_plot(replicates=3)
    data["y"] = np.arange(len(data), dtype=float)

    strata = SplitPlotAnalysis(data, "y", ["A"], ["B"]).error_strata()

    assert strata.whole_plot_treatments == 2
    assert strata.subplot_treatments == 3
    assert strata.replicates == 3
    assert strata.whole_plots == 6
    assert strata.runs == 18
    assert strata.whole_plot_error_df == 2 * (3 - 1)
    assert strata.subplot_error_df == 2 * (3 - 1) * (3 - 1)


def test_error_strata_support_multiple_whole_plot_factors() -> None:
    data = _generated_split_plot(
        whole_plot_factors=[Factor("A", [-1, 1]), Factor("C", [10, 20])],
        subplot_factors=[Factor("B", [0, 1])],
        replicates=2,
    )
    data["y"] = np.arange(len(data), dtype=float)

    strata = SplitPlotAnalysis(data, "y", ["A", "C"], ["B"]).error_strata()

    assert strata.whole_plot_treatments == 4
    assert strata.subplot_treatments == 2
    assert strata.replicates == 2
    assert strata.whole_plot_error_df == 4
    assert strata.subplot_error_df == 4


def test_expected_mean_squares_use_subplot_multiplicity() -> None:
    data = _generated_split_plot(replicates=3)
    data["y"] = 0.0
    analysis = SplitPlotAnalysis(data, "y", ["A"], ["B"])

    ems = analysis.expected_mean_squares(
        whole_plot_variance=2.5,
        residual_variance=1.25,
    )

    assert ems["whole_plot_error"] == pytest.approx(1.25 + 3 * 2.5)
    assert ems["subplot_error"] == pytest.approx(1.25)


@pytest.mark.parametrize(
    ("whole_plot_variance", "residual_variance"),
    [(-1.0, 1.0), (1.0, -1.0)],
)
def test_expected_mean_squares_reject_negative_variances(
    whole_plot_variance: float,
    residual_variance: float,
) -> None:
    data = _generated_split_plot(replicates=2)
    data["y"] = 0.0
    analysis = SplitPlotAnalysis(data, "y", ["A"], ["B"])

    with pytest.raises(ValueError, match="non-negative"):
        analysis.expected_mean_squares(
            whole_plot_variance=whole_plot_variance,
            residual_variance=residual_variance,
        )


def test_whole_plot_factor_cannot_change_within_experimental_unit() -> None:
    data = _generated_split_plot(replicates=2)
    data["y"] = 0.0
    first_whole_plot = data["WholePlot"].iloc[0]
    index = data.index[data["WholePlot"] == first_whole_plot][0]
    data.loc[index, "A"] = 999

    analysis = SplitPlotAnalysis(data, "y", ["A"], ["B"])
    with pytest.raises(ValueError, match="changes within whole plot"):
        analysis.error_strata()


def test_each_whole_plot_requires_one_complete_subplot_factorial() -> None:
    data = _generated_split_plot(replicates=2)
    data["y"] = 0.0
    data = data.drop(index=data.index[0]).reset_index(drop=True)

    analysis = SplitPlotAnalysis(data, "y", ["A"], ["B"])
    with pytest.raises(ValueError, match="complete subplot factorial"):
        analysis.error_strata()


def test_split_plot_mixed_model_recovers_two_variance_strata() -> None:
    data = _generated_split_plot(
        whole_plot_factors=[Factor("A", [-1, 1])],
        subplot_factors=[Factor("B", [-1, 1])],
        replicates=10,
    )
    rng = np.random.default_rng(20260910)
    whole_plot_offsets = {
        whole_plot: offset
        for whole_plot, offset in zip(
            sorted(data["WholePlot"].unique()),
            rng.normal(0.0, 2.0, size=data["WholePlot"].nunique()),
            strict=True,
        )
    }
    data["y"] = (
        10.0
        + 1.5 * data["A"].astype(float)
        + 2.0 * data["B"].astype(float)
        + 0.75 * data["A"].astype(float) * data["B"].astype(float)
        + data["WholePlot"].map(whole_plot_offsets).astype(float)
        + rng.normal(0.0, 0.5, size=len(data))
    )

    result = SplitPlotAnalysis(data, "y", ["A"], ["B"]).fit_mixed_model()

    assert result["converged"] is True
    assert result["whole_plot_variance"] > 0.1
    assert result["residual_variance"] > 0.01
    assert result["error_strata"]["whole_plot_error_df"] == 18
    assert result["error_strata"]["subplot_error_df"] == 18
    assert "C(Q(\"A\"))" in result["formula"]
    assert "C(Q(\"B\"))" in result["formula"]
