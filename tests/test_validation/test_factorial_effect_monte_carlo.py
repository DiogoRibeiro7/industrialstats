"""Monte Carlo validation for canonical two-level factorial effects."""

from __future__ import annotations

import numpy as np
import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


def test_factorial_effect_estimator_is_unbiased_under_known_two_cubed_model() -> None:
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABC"]
    design = FactorialDesign(factors, randomize=False)
    matrix = design.generate_design()

    a = matrix["A"].to_numpy(dtype=float)
    b = matrix["B"].to_numpy(dtype=float)
    c = matrix["C"].to_numpy(dtype=float)
    mean_response = (
        20.0
        + 3.0 * a
        - 2.0 * b
        + 1.5 * c
        + 4.0 * a * b
        - 5.0 * a * c
        + 2.5 * b * c
        + 6.0 * a * b * c
    )

    expected = {
        "A": 6.0,
        "B": -4.0,
        "C": 3.0,
        "A*B": 8.0,
        "A*C": -10.0,
        "B*C": 5.0,
        "A*B*C": 12.0,
    }

    rng = np.random.default_rng(20260913)
    estimates = {name: [] for name in expected}
    for _ in range(1000):
        response = mean_response + rng.normal(0.0, 2.0, size=len(matrix))
        effects = design.calculate_effects(response.tolist(), max_order=3)
        for name in expected:
            estimates[name].append(effects[name])

    for name, true_effect in expected.items():
        monte_carlo_mean = float(np.mean(estimates[name]))
        assert monte_carlo_mean == pytest.approx(true_effect, abs=0.15)
