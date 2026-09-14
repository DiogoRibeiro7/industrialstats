"""Independent reference checks for power calculations."""

import pytest
from statsmodels.stats.power import FTestAnovaPower, TTestIndPower

from industrialstats.analysis.power_analysis import PowerAnalysis


def test_two_sample_t_power_matches_statsmodels() -> None:
    analysis = PowerAnalysis()
    effect_size = 0.5
    alpha = 0.05
    sample_size = 40

    result = analysis.t_test_power(
        effect_size=effect_size,
        alpha=alpha,
        sample_size=sample_size,
        test_type="two_sample",
    )
    reference = TTestIndPower().power(
        effect_size=effect_size,
        nobs1=sample_size,
        alpha=alpha,
        ratio=1.0,
        alternative="two-sided",
    )

    assert result.power == pytest.approx(reference, rel=1e-10, abs=1e-12)


def test_one_way_anova_power_matches_statsmodels() -> None:
    analysis = PowerAnalysis()
    effect_size = 0.25
    alpha = 0.05
    sample_size = 30
    n_groups = 4

    result = analysis.anova_power(
        effect_size=effect_size,
        alpha=alpha,
        sample_size=sample_size,
        n_groups=n_groups,
    )
    reference = FTestAnovaPower().power(
        effect_size=effect_size,
        nobs=sample_size * n_groups,
        alpha=alpha,
        k_groups=n_groups,
    )

    assert result.power == pytest.approx(reference, rel=1e-10, abs=1e-12)
