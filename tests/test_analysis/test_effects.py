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
