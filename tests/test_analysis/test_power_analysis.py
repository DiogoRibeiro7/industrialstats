import numpy as np
from scipy import stats

from industrialstats.analysis.power_analysis import PowerAnalysis


def test_t_test_power_calculation():
    pa = PowerAnalysis()
    result = pa.t_test_power(effect_size=0.5, power=0.8, test_type="two_sample")
    assert result.sample_size > 0
    assert result.effect_size == 0.5


def test_anova_power_calculation():
    pa = PowerAnalysis()
    result = pa.anova_power(effect_size=0.25, power=0.8, n_groups=3)
    assert result.sample_size > 0
    assert result.additional_info["n_groups"] == 3


def test_factorial_power_main_and_interaction():
    pa = PowerAnalysis()
    levels = [2, 3]
    # Main effect for factor 0
    res_main = pa.factorial_power(
        effect_size=0.25,
        replicates=3,
        factor_levels=levels,
        effect=(0,),
    )
    df_effect = levels[0] - 1
    df_error = np.prod(levels) * (3 - 1)
    ncp = 0.25**2 * np.prod(levels) * 3
    crit = stats.f.ppf(1 - 0.05, df_effect, df_error)
    expected = 1 - stats.ncf.cdf(crit, df_effect, df_error, ncp)
    assert abs(res_main.power - expected) < 1e-6

    # Interaction effect between factors 0 and 1
    res_int = pa.factorial_power(
        effect_size=0.3,
        replicates=2,
        factor_levels=levels,
        effect=(0, 1),
    )
    df_inter = (levels[0] - 1) * (levels[1] - 1)
    df_error = np.prod(levels) * (2 - 1)
    ncp = 0.3**2 * np.prod(levels) * 2
    crit = stats.f.ppf(1 - 0.05, df_inter, df_error)
    expected_int = 1 - stats.ncf.cdf(crit, df_inter, df_error, ncp)
    assert abs(res_int.power - expected_int) < 1e-6


def test_factorial_sample_size_and_power_curve():
    pa = PowerAnalysis()
    # Solve for replicates to achieve power 0.8
    res = pa.factorial_power(
        effect_size=0.35,
        power=0.8,
        factor_levels=[2, 2],
        effect=(0, 1),
    )
    confirm = pa.factorial_power(
        effect_size=0.35,
        replicates=res.sample_size,
        factor_levels=[2, 2],
        effect=(0, 1),
    )
    assert confirm.power >= 0.8

    curve = pa.factorial_power_curve(
        effect_sizes=[0.1, 0.2, 0.3],
        replicates=2,
        factor_levels=[2, 2],
    )
    assert len(curve["powers"]) == 3
