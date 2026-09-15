"""Published-reference validation for Cornell's three-component yarn mixture design."""

import numpy as np

from industrialstats.designs.advanced import MixtureDesign
from industrialstats.designs.base import Factor


def test_cornell_yarn_example_matches_three_two_simplex_lattice() -> None:
    """Reproduce the six unique runs in Cornell's published yarn example.

    Cornell's three-component yarn experiment uses a {3, 2} simplex-lattice:
    the three pure blends and the three 50/50 binary blends. The design is
    reproduced in the NIST/SEMATECH e-Handbook, section 5.5.6.2.
    """
    factors = [
        Factor("Polyethylene", [], "continuous"),
        Factor("Polystyrene", [], "continuous"),
        Factor("Polypropylene", [], "continuous"),
    ]
    frame = MixtureDesign(factors, order=2).generate_design()
    actual = frame[[factor.name for factor in factors]].to_numpy(dtype=float)

    reference = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.5, 0.5, 0.0],
            [0.5, 0.0, 0.5],
            [0.0, 0.5, 0.5],
        ]
    )

    assert {tuple(row) for row in actual} == {tuple(row) for row in reference}
    assert np.count_nonzero(np.isclose(actual, 1.0).sum(axis=1) == 1) == 3
    assert np.count_nonzero(np.isclose(actual, 0.5).sum(axis=1) == 2) == 3
