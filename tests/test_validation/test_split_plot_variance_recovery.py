"""Monte Carlo validation for balanced split-plot variance strata."""

import numpy as np
import pytest

from industrialstats.analysis.split_plot import SplitPlotAnalysis
from industrialstats.designs.advanced import SplitPlotDesign
from industrialstats.designs.base import Factor


def test_split_plot_error_strata_recover_variance_components() -> None:
    """Classical split-plot error strata recover the generating variances on average."""
    design = SplitPlotDesign(
        [Factor("A", [-1, 1])],
        [Factor("B", [-1, 0, 1])],
        replicates=8,
        randomize=False,
    )
    base = design.generate_design()

    whole_plot_variance = 2.25
    residual_variance = 0.64
    subplot_treatments = 3
    rng = np.random.default_rng(20260914)

    whole_plot_estimates: list[float] = []
    residual_estimates: list[float] = []

    whole_plot_ids = np.sort(base["WholePlot"].unique())
    for _ in range(300):
        frame = base.copy()
        offsets = dict(
            zip(
                whole_plot_ids,
                rng.normal(
                    0.0,
                    np.sqrt(whole_plot_variance),
                    size=len(whole_plot_ids),
                ),
                strict=True,
            )
        )
        frame["y"] = (
            10.0
            + 1.5 * frame["A"].astype(float)
            + 2.0 * frame["B"].astype(float)
            + 0.75 * frame["A"].astype(float) * frame["B"].astype(float)
            + frame["WholePlot"].map(offsets).astype(float)
            + rng.normal(0.0, np.sqrt(residual_variance), size=len(frame))
        )

        table = SplitPlotAnalysis(frame, "y", ["A"], ["B"]).anova_table()
        by_source = table.set_index("Source")
        ms_whole_plot = float(by_source.loc["WholePlot Error", "mean_sq"])
        ms_subplot = float(by_source.loc["Subplot Error", "mean_sq"])

        residual_estimates.append(ms_subplot)
        whole_plot_estimates.append(
            (ms_whole_plot - ms_subplot) / subplot_treatments
        )

    assert np.mean(residual_estimates) == pytest.approx(residual_variance, abs=0.05)
    assert np.mean(whole_plot_estimates) == pytest.approx(
        whole_plot_variance, abs=0.15
    )
