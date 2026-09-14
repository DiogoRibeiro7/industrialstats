"""Monte Carlo calibration tests for fixed-effects ANOVA."""

import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.anova import ANOVAAnalysis


def test_one_way_anova_type1_error_is_calibrated() -> None:
    """Empirical null rejection rate should stay close to nominal alpha."""
    rng = np.random.default_rng(20260913)
    alpha = 0.05
    simulations = 500
    groups = np.repeat(["g1", "g2", "g3"], 12)
    rejections = 0

    for _ in range(simulations):
        frame = pd.DataFrame(
            {
                "group": groups,
                "response": rng.normal(0.0, 1.0, size=len(groups)),
            }
        )
        analysis = ANOVAAnalysis(frame, "response")
        analysis.fit_model("response ~ C(group)")
        table = analysis.anova_table_calculation()
        if float(table.loc["C(group)", "PR(>F)"]) < alpha:
            rejections += 1

    empirical_alpha = rejections / simulations
    assert empirical_alpha == pytest.approx(alpha, abs=0.03)
