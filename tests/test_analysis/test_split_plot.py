"""Statistical validation for balanced split-plot inference."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.split_plot import SplitPlotAnalysis


def _known_two_by_two_split_plot() -> pd.DataFrame:
    """Return a hand-checkable 2 x 2 split plot with three WP replicates."""
    rows: list[dict[str, float | int]] = []
    whole_plot_id = 1
    whole_plot_errors = (-1.0, 0.0, 1.0)
    subplot_perturbations = (0.5, -0.5, 0.0)

    for a in (-1, 1):
        for replicate, (whole_plot_error, perturbation) in enumerate(
            zip(whole_plot_errors, subplot_perturbations, strict=True),
            start=1,
        ):
            for b in (-1, 1):
                subplot_error = -perturbation * b
                response = (
                    10.0
                    + 4.0 * a
                    + 3.0 * b
                    + 2.0 * a * b
                    + whole_plot_error
                    + subplot_error
                )
                rows.append(
                    {
                        "WholePlot": whole_plot_id,
                        "Replicate": replicate,
                        "A": a,
                        "B": b,
                        "Response": response,
                    }
                )
            whole_plot_id += 1

    return pd.DataFrame(rows)


def test_split_plot_anova_uses_correct_error_strata() -> None:
    """Whole-plot and subplot terms must use different denominator errors."""
    analysis = SplitPlotAnalysis(
        _known_two_by_two_split_plot(),
        "Response",
        whole_plot_factors=["A"],
        subplot_factors=["B"],
    )

    result = analysis.anova()
    table = result.table.set_index("Source")

    assert result.n_whole_plots == 6
    assert result.n_subplots_per_whole_plot == 2
    assert result.whole_plot_error_df == 4
    assert result.subplot_error_df == 4

    assert table.loc["A", "sum_sq"] == pytest.approx(192.0)
    assert table.loc["WholePlot Error", "sum_sq"] == pytest.approx(8.0)
    assert table.loc["A", "F"] == pytest.approx(96.0)
    assert table.loc["A", "Denominator"] == "WholePlot Error"

    assert table.loc["B", "sum_sq"] == pytest.approx(108.0)
    assert table.loc["A*B", "sum_sq"] == pytest.approx(48.0)
    assert table.loc["Subplot Error", "sum_sq"] == pytest.approx(2.0)
    assert table.loc["B", "F"] == pytest.approx(216.0)
    assert table.loc["A*B", "F"] == pytest.approx(96.0)
    assert table.loc["B", "Denominator"] == "Subplot Error"
    assert table.loc["A*B", "Denominator"] == "Subplot Error"


def test_split_plot_anova_is_invariant_to_row_order() -> None:
    """Storage order must not define either randomization stratum."""
    frame = _known_two_by_two_split_plot()
    shuffled = frame.sample(frac=1.0, random_state=123).reset_index(drop=True)

    original = SplitPlotAnalysis(
        frame,
        "Response",
        whole_plot_factors=["A"],
        subplot_factors=["B"],
    ).anova().table
    reordered = SplitPlotAnalysis(
        shuffled,
        "Response",
        whole_plot_factors=["A"],
        subplot_factors=["B"],
    ).anova().table

    columns = ["Source", "Stratum", "df", "sum_sq", "mean_sq", "F"]
    left = original[columns].sort_values("Source").reset_index(drop=True)
    right = reordered[columns].sort_values("Source").reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right, check_exact=False, rtol=1e-12, atol=1e-12)


def test_split_plot_requires_whole_plot_replication_for_wp_error() -> None:
    """One whole plot per WP treatment cannot estimate whole-plot error."""
    frame = _known_two_by_two_split_plot().query("Replicate == 1").copy()
    analysis = SplitPlotAnalysis(
        frame,
        "Response",
        whole_plot_factors=["A"],
        subplot_factors=["B"],
    )

    with pytest.raises(ValueError, match="replication.*whole-plot error"):
        analysis.anova()


def test_split_plot_rejects_incomplete_subplot_factorial() -> None:
    """Each whole plot must contain every subplot treatment exactly once."""
    frame = _known_two_by_two_split_plot().drop(index=0).reset_index(drop=True)

    with pytest.raises(ValueError, match="complete subplot factorial"):
        SplitPlotAnalysis(
            frame,
            "Response",
            whole_plot_factors=["A"],
            subplot_factors=["B"],
        )


def test_split_plot_rejects_unbalanced_whole_plot_replication() -> None:
    """Whole-plot treatment combinations need equal independent replication."""
    frame = _known_two_by_two_split_plot()
    frame = frame.loc[~((frame["A"] == 1) & (frame["Replicate"] == 3))].copy()

    with pytest.raises(ValueError, match="equal replication"):
        SplitPlotAnalysis(
            frame,
            "Response",
            whole_plot_factors=["A"],
            subplot_factors=["B"],
        )


def test_split_plot_probability_columns_are_valid() -> None:
    """Finite F statistics should have probabilities in [0, 1]."""
    table = SplitPlotAnalysis(
        _known_two_by_two_split_plot(),
        "Response",
        whole_plot_factors=["A"],
        subplot_factors=["B"],
    ).anova().table

    fixed = table.loc[table["Stratum"].isin(["whole_plot", "subplot"])]
    assert np.isfinite(fixed["F"].to_numpy(dtype=float)).all()
    assert fixed["PR(>F)"].between(0.0, 1.0).all()
