import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.effects import EffectsAnalysis


def _simple_effects_analysis() -> EffectsAnalysis:
    design = pd.DataFrame({"A": [-1, 1], "B": [-1, 1]})
    responses = [1.0, 2.0]
    return EffectsAnalysis(design, responses)


def test_half_normal_plot_lenths_method():
    ea = _simple_effects_analysis()
    effects = {"A": 5.0, "B": 4.0, "C": 0.2, "D": 0.1, "E": 0.05, "F": 0.3}
    fig, significant = ea.half_normal_plot(effects, interactive=False)
    plt.close(fig)
    assert set(significant) == {"A", "B"}


def test_half_normal_plot_empty_effects():
    ea = _simple_effects_analysis()
    with pytest.raises(ValueError):
        ea.half_normal_plot({}, interactive=False)


def test_half_normal_plot_reference_lines():
    ea = _simple_effects_analysis()
    effects = {"A": 5.0, "B": 4.0, "C": 0.2, "D": 0.1, "E": 0.05, "F": 0.3}
    fig, _ = ea.half_normal_plot(effects, interactive=False)
    ax = fig.axes[0]
    me_line, sme_line = ax.lines[:2]

    effect_values = np.abs(np.array(list(effects.values())))
    s0 = 1.5 * np.median(effect_values)
    threshold = 2.5 * s0
    filtered = effect_values[effect_values <= threshold]
    s = 1.5 * np.median(filtered) if filtered.size else s0
    me = 2.5 * s
    sme = 3.5 * s

    assert np.allclose(me_line.get_ydata(), [me, me])
    assert np.allclose(sme_line.get_ydata(), [sme, sme])
    plt.close(fig)


@pytest.mark.parametrize("max_interactions", [1, 2, 3, 4])
def test_interaction_plots_handles_every_subplot_layout(max_interactions):
    """Subplot grids of 1x1, 1xN and MxN must all be indexable.

    ``plt.subplots`` returns a bare Axes for a 1x1 grid, a 1-D array for a
    single row, and a 2-D array otherwise. A single-row grid used to be wrapped
    into a one-element list, so plotting two or three interactions raised
    IndexError.
    """
    rng = np.random.default_rng(0)
    design = pd.DataFrame(
        [
            {"A": a, "B": b, "C": c, "D": d}
            for a in (-1, 1)
            for b in (-1, 1)
            for c in (-1, 1)
            for d in (-1, 1)
        ]
    )
    responses = (
        3.0 * design["A"] * design["B"]
        + 2.0 * design["A"] * design["C"]
        + 1.5 * design["B"] * design["C"]
        + 1.0 * design["C"] * design["D"]
        + rng.normal(scale=0.01, size=len(design))
    ).tolist()

    ea = EffectsAnalysis(design, responses)
    fig = ea.interaction_plots(max_interactions=max_interactions)
    plt.close(fig)
