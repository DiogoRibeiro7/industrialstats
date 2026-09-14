"""Property-based validation for simplex-lattice mixture designs."""

from math import comb

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from industrialstats.designs.advanced import MixtureDesign
from industrialstats.designs.base import Factor


@settings(max_examples=25, deadline=None)
@given(
    n_components=st.integers(min_value=3, max_value=6),
    order=st.integers(min_value=1, max_value=5),
)
def test_simplex_lattice_preserves_mixture_invariants(
    n_components: int,
    order: int,
) -> None:
    """Generated simplex-lattice points satisfy the defining mixture identities."""
    factors = [Factor(f"x{i + 1}", [], "continuous") for i in range(n_components)]
    design = MixtureDesign(factors, order=order)
    frame = design.generate_design()
    values = frame.to_numpy(dtype=float)

    expected_runs = comb(order + n_components - 1, n_components - 1)
    assert len(frame) == expected_runs
    assert len(frame.drop_duplicates()) == expected_runs

    assert np.all(values >= 0.0)
    assert np.all(values <= 1.0)
    assert np.allclose(values.sum(axis=1), 1.0)

    scaled = values * order
    assert np.allclose(scaled, np.round(scaled))
