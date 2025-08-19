import matplotlib.pyplot as plt
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
