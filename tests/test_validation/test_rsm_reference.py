"""Independent response-surface reference checks against R's rsm package."""

import numpy as np
import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign


def test_codata_matches_rsm_unthresholded_canonical_analysis() -> None:
    """Match the published rsm canonical analysis for the codata example.

    The 18-run replicated 3^2 automobile-emissions experiment is distributed
    with the R package ``rsm`` and originates from Box, Hunter, and Hunter
    (2005), Table 10.17.  Lenth's ``rsm`` vignette reports the unthresholded
    canonical stationary point and eigenvalues for the fitted second-order
    surface.  This regression locks those external numerical quantities rather
    than reproducing them from the industrialstats implementation.
    """

    x1 = np.array(
        [-1, -1, 0, 0, 1, 1, -1, -1, 0, 0, 1, 1, -1, -1, 0, 0, 1, 1],
        dtype=float,
    )
    x2 = np.array(
        [-1, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        dtype=float,
    )
    response = np.array(
        [
            61.9,
            65.6,
            80.9,
            78.0,
            89.7,
            93.8,
            72.1,
            67.3,
            80.1,
            81.4,
            77.8,
            74.8,
            66.4,
            68.2,
            68.9,
            66.0,
            60.2,
            57.9,
        ],
        dtype=float,
    )

    design = ResponseSurfaceDesign(
        [
            Factor("x1", [-1, 1], factor_type="continuous"),
            Factor("x2", [-1, 1], factor_type="continuous"),
        ],
        design_type="CCD",
        center_points=1,
    )
    design.design_matrix = pd.DataFrame({"x1": x1, "x2": x2})

    model = design.response_surface_analysis(response.tolist())
    canonical = design.canonical_analysis(model)

    # rsm::canonical(CO.rsm, threshold = 0)
    expected_stationary = np.array([-14.81387, 15.44149])
    expected_eigenvalues = np.array([-8.8868328, 0.1868328])

    np.testing.assert_allclose(
        canonical["stationary_point_coded"], expected_stationary, atol=1e-5
    )
    np.testing.assert_allclose(
        np.sort(canonical["eigenvalues"]), expected_eigenvalues, atol=1e-7
    )
    assert canonical["surface_type"] == "saddle"
