import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.power import FTestAnovaPower

from industrialstats.analysis.anova import ANOVAAnalysis
from industrialstats.analysis.effects import EffectsAnalysis
from industrialstats.analysis.model_fitting import ModelFitting
from industrialstats.analysis.power_analysis import PowerAnalysis
from industrialstats.utils.data_generation import DataSimulator


def test_anova_matches_textbook_example():
    """One-way ANOVA example from Montgomery (2017)."""
    values = [6, 8, 4, 5, 3, 4, 8, 12, 9, 11, 6, 8, 13, 9, 11, 8, 7, 12]
    groups = ["g1"] * 6 + ["g2"] * 6 + ["g3"] * 6
    df = pd.DataFrame({"value": values, "group": groups})

    analysis = ANOVAAnalysis(df, "value")
    analysis.fit_model("value ~ C(group)")
    table = analysis.anova_table_calculation()

    sm_model = ols("value ~ C(group)", data=df).fit()
    sm_table = sm.stats.anova_lm(sm_model, typ=2)

    assert table.loc["C(group)", "F"] == pytest.approx(
        sm_table.loc["C(group)", "F"], rel=1e-6
    )
    assert table.loc["C(group)", "PR(>F)"] == pytest.approx(
        sm_table.loc["C(group)", "PR(>F)"], rel=1e-6
    )


def test_anova_power_matches_statsmodels():
    """Validate one-way ANOVA power against statsmodels."""
    pa = PowerAnalysis()
    result = pa.anova_power(effect_size=0.4, alpha=0.05, sample_size=10, n_groups=3)
    sm_power = FTestAnovaPower().power(effect_size=0.4, k_groups=3, nobs=30, alpha=0.05)
    assert result.power == pytest.approx(sm_power, rel=1e-6)


def test_effect_calculation_matches_manual():
    """Compare effect calculations with hand-computed results."""
    design = pd.DataFrame({"A": [-1, 1, -1, 1], "B": [-1, -1, 1, 1]})
    responses = [30, 50, 20, 40]
    effects = EffectsAnalysis(design, responses)
    main = effects.calculate_main_effects()
    inter = effects.calculate_interaction_effects()

    assert main["A"] == pytest.approx(20.0)
    assert main["B"] == pytest.approx(-10.0)
    assert inter["A*B"] == pytest.approx(0.0)


def test_model_fitting_agrees_with_statsmodels():
    """OLS fitting should match statsmodels results."""
    df = pd.DataFrame({"A": ["a", "a", "b", "b"], "Y": [1, 2, 3, 4]})
    fitter = ModelFitting(df, "Y")
    res = fitter._fit_terms(["A"])

    sm_res = ols("Y ~ C(A)", data=df).fit()

    assert res["coefficients"]["Intercept"] == pytest.approx(sm_res.params["Intercept"])
    assert res["coefficients"]["C(A)[T.b]"] == pytest.approx(sm_res.params["C(A)[T.b]"])


def test_data_simulator_monte_carlo_effect():
    """Monte Carlo validation that effect estimates recover true values."""
    design = pd.DataFrame({"A": [0, 1, 0, 1], "B": [0, 0, 1, 1]})
    sim = DataSimulator(seed=0)
    true_effect = 1.0
    estimates = []
    for _ in range(200):
        y = sim.simulate_factorial_response(
            design, main_effects={"A": true_effect, "B": 0.0}, noise_level=0.5
        )
        eff = EffectsAnalysis(design, list(y)).calculate_main_effects()["A"]
        estimates.append(eff)
    assert np.mean(estimates) == pytest.approx(true_effect, abs=0.1)
