"""Monte Carlo robustness check for fixed-effects ANOVA under mild heteroskedasticity."""

import numpy as np
import pandas as pd

from industrialstats.analysis.anova import ANOVAAnalysis


def test_anova_type_i_error_is_stable_under_mild_variance_heterogeneity() -> None:
    """Balanced one-way ANOVA remains approximately calibrated for mild variance ratios."""
    rng = np.random.default_rng(20260914)
    alpha = 0.05
    repetitions = 1000
    group_size = 20
    standard_deviations = (1.0, 1.25, 1.5)

    rejections = 0
    for _ in range(repetitions):
        frame = pd.DataFrame(
            {
                "group": np.repeat(["A", "B", "C"], group_size),
                "response": np.concatenate(
                    [
                        rng.normal(0.0, sd, size=group_size)
                        for sd in standard_deviations
                    ]
                ),
            }
        )

        analysis = ANOVAAnalysis(frame, "response")
        analysis.fit_model("response ~ C(group)")
        table = analysis.anova_table_calculation(typ=2)
        p_value = float(table.loc["C(group)", "PR(>F)"])
        rejections += p_value < alpha

    empirical_size = rejections / repetitions
    assert abs(empirical_size - alpha) <= 0.03
