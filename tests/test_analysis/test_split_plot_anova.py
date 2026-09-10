"""Reference tests for classical balanced split-plot ANOVA."""

from __future__ import annotations

import pandas as pd
import pytest

from industrialstats.analysis.split_plot import SplitPlotAnalysis


def _known_two_by_two_split_plot() -> pd.DataFrame:
    """Return a 2 x 2 split plot with hand-derived sums of squares."""
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


def test_anova_uses_whole_plot_and_subplot_denominators() -> None:
    analysis = SplitPlotAnalysis(
        _known_two_by_two_split_plot(),
        "Response",
        ["A"],
        ["B"],
    )

    table = analysis.anova_table().set_index("Source")

    assert table.loc["A", "sum_sq"] == pytest.approx(192.0)
    assert table.loc["WholePlot Error", "sum_sq"] == pytest.approx(8.0)
    assert table.loc["WholePlot Error", "df"] == 4
    assert table.loc["A", "F"] == pytest.approx(96.0)
    assert table.loc["A", "Denominator"] == "WholePlot Error"

    assert table.loc["B", "sum_sq"] == pytest.approx(108.0)
    assert table.loc["A*B", "sum_sq"] == pytest.approx(48.0)
    assert table.loc["Subplot Error", "sum_sq"] == pytest.approx(2.0)
    assert table.loc["Subplot Error", "df"] == 4
    assert table.loc["B", "F"] == pytest.approx(216.0)
    assert table.loc["A*B", "F"] == pytest.approx(96.0)
    assert table.loc["B", "Denominator"] == "Subplot Error"
    assert table.loc["A*B", "Denominator"] == "Subplot Error"


def test_anova_is_invariant_to_row_order() -> None:
    frame = _known_two_by_two_split_plot()
    shuffled = frame.sample(frac=1.0, random_state=20260910).reset_index(drop=True)

    left = SplitPlotAnalysis(frame, "Response", ["A"], ["B"]).anova_table()
    right = SplitPlotAnalysis(shuffled, "Response", ["A"], ["B"]).anova_table()

    columns = ["Source", "Stratum", "df", "sum_sq", "mean_sq", "F"]
    left = left[columns].sort_values("Source").reset_index(drop=True)
    right = right[columns].sort_values("Source").reset_index(drop=True)
    pd.testing.assert_frame_equal(
        left,
        right,
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )


def test_anova_requires_replication_for_both_error_strata() -> None:
    frame = _known_two_by_two_split_plot().query("Replicate == 1").copy()
    analysis = SplitPlotAnalysis(frame, "Response", ["A"], ["B"])

    with pytest.raises(ValueError, match="replication.*whole-plot error"):
        analysis.anova_table()
