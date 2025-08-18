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
