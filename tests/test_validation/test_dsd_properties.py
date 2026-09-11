"""Property-based validation for definitive screening designs."""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from industrialstats.designs.base import Factor
from industrialstats.designs.screening import DefinitiveScreeningDesign


def _factors(count: int) -> list[Factor]:
    return [Factor(f"X{index}", [-1, 0, 1]) for index in range(1, count + 1)]


@given(n_factors=st.integers(min_value=2, max_value=10))
@settings(max_examples=18, deadline=None)
def test_dsd_defining_invariants_hold_across_supported_factor_counts(
    n_factors: int,
) -> None:
    design = DefinitiveScreeningDesign(_factors(n_factors), randomize=False)
    generated = design.generate_design()
    x = generated[[f"X{index}" for index in range(1, n_factors + 1)]].to_numpy(
        dtype=float
    )

    assert set(np.unique(x)).issubset({-1.0, 0.0, 1.0})
    assert np.count_nonzero(np.all(x == 0.0, axis=1)) == 1

    noncenter = x[:-1]
    half = len(noncenter) // 2
    np.testing.assert_array_equal(noncenter[half:], -noncenter[:half])

    cross_product = x.T @ x
    np.testing.assert_allclose(
        cross_product - np.diag(np.diag(cross_product)),
        0.0,
    )
    np.testing.assert_allclose(x.T @ (x**2), 0.0)

    interactions = np.column_stack(
        [
            x[:, left] * x[:, right]
            for left in range(n_factors)
            for right in range(left + 1, n_factors)
        ]
    )
    if interactions.size:
        np.testing.assert_allclose(x.T @ interactions, 0.0)

    model_matrix = np.column_stack((np.ones(len(x)), x, x**2))
    assert np.linalg.matrix_rank(model_matrix) == 1 + 2 * n_factors
