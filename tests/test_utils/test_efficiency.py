from __future__ import annotations

import numpy as np
import pandas as pd

from industrialstats.utils.efficiency import (
    a_efficiency,
    d_efficiency,
    estimate_power,
    g_efficiency,
    i_efficiency,
    plot_efficiencies,
    relative_efficiency,
    variance_inflation_factors,
)


def _orthogonal_design() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Intercept": 1,
            "A": [-1, 1, -1, 1],
            "B": [-1, -1, 1, 1],
        }
    )


def _candidate_points() -> pd.DataFrame:
    return _orthogonal_design()


def test_efficiency_metrics_return_one_for_orthogonal_design() -> None:
    dm = _orthogonal_design()
    cand = _candidate_points()
    assert np.isclose(d_efficiency(dm), 1.0)
    assert np.isclose(a_efficiency(dm), 1.0)
    assert np.isclose(g_efficiency(dm, cand), 4 / 3)
    assert np.isclose(i_efficiency(dm, cand), 4 / 3)


def test_relative_efficiency_equals_ratio() -> None:
    dm = _orthogonal_design()
    scaled = dm.copy()
    scaled["A"] *= 2
    assert np.isclose(relative_efficiency(dm, dm), 1.0)
    assert not np.isclose(relative_efficiency(dm, scaled), 1.0)


def test_vif_is_one_for_orthogonal_design() -> None:
    dm = _orthogonal_design()
    vifs = variance_inflation_factors(dm)
    assert (vifs.round(5) == 1).all()


def test_power_increases_with_effect_size() -> None:
    dm = _orthogonal_design()
    contrast = np.array([0.0, 1.0, 0.0])
    power_small = estimate_power(dm, contrast, effect_size=1.0)
    power_large = estimate_power(dm, contrast, effect_size=2.0)
    assert 0 <= power_small <= 1
    assert power_large > power_small


def test_plot_efficiencies_returns_axes() -> None:
    dm = _orthogonal_design()
    effs = {"design": d_efficiency(dm)}
    ax = plot_efficiencies(effs)
    assert ax.get_ylabel() == "Efficiency"
