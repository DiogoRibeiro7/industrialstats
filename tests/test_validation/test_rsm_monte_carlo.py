"""Monte Carlo validation for response-surface coefficient recovery."""

import numpy as np
import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign


def test_response_surface_coefficients_are_unbiased_under_gaussian_noise() -> None:
    factors = [
        Factor("x1", [-1.0, 1.0], factor_type="continuous"),
        Factor("x2", [-1.0, 1.0], factor_type="continuous"),
    ]
    design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=5)
    design.generate_design()
    coded = design._get_design_matrix_coded()

    true_coefficients = {
        "Intercept": 10.0,
        "x1": 1.5,
        "x2": -0.75,
        "x1²": 0.8,
        "x2²": 0.4,
        "x1*x2": -0.6,
    }
    mean_response = (
        true_coefficients["Intercept"]
        + true_coefficients["x1"] * coded[:, 0]
        + true_coefficients["x2"] * coded[:, 1]
        + true_coefficients["x1²"] * coded[:, 0] ** 2
        + true_coefficients["x2²"] * coded[:, 1] ** 2
        + true_coefficients["x1*x2"] * coded[:, 0] * coded[:, 1]
    )

    rng = np.random.default_rng(20260914)
    estimates = {name: [] for name in true_coefficients}

    for _ in range(500):
        response = mean_response + rng.normal(0.0, 0.8, size=len(mean_response))
        fitted = design.response_surface_analysis(response.tolist())["coefficients"]
        for name in estimates:
            estimates[name].append(float(fitted[name]))

    for name, truth in true_coefficients.items():
        assert np.mean(estimates[name]) == pytest.approx(truth, abs=0.05)
