"""Independent published-reference checks for definitive screening designs."""

import numpy as np

from industrialstats.designs.base import Factor
from industrialstats.designs.screening import DefinitiveScreeningDesign

# Jones & Nachtsheim (2011), Journal of Quality Technology 43(1), Table 2.
# A Class of Three-Level Designs for Definitive Screening in the Presence of
# Second-Order Effects.
_JONES_NACHTSHEIM_DSD6 = np.asarray(
    [
        [0, 1, -1, -1, -1, -1],
        [0, -1, 1, 1, 1, 1],
        [1, 0, -1, 1, 1, -1],
        [-1, 0, 1, -1, -1, 1],
        [-1, -1, 0, 1, -1, -1],
        [1, 1, 0, -1, 1, 1],
        [-1, 1, 1, 0, 1, -1],
        [1, -1, -1, 0, -1, 1],
        [1, -1, 1, -1, 0, -1],
        [-1, 1, -1, 1, 0, 1],
        [1, 1, 1, 1, -1, 0],
        [-1, -1, -1, -1, 1, 0],
        [0, 0, 0, 0, 0, 0],
    ],
    dtype=int,
)


def _sorted_rows(matrix: np.ndarray) -> list[tuple[int, ...]]:
    return sorted(tuple(int(value) for value in row) for row in matrix)


def test_dsd6_matches_jones_nachtsheim_table_2_up_to_standard_equivalence() -> None:
    """The conference DSD is the published 6-factor design up to signs/order."""
    factors = [Factor(f"X{index}", [-1, 0, 1]) for index in range(1, 7)]
    design = DefinitiveScreeningDesign(factors, randomize=False)
    generated = design.generate_design()

    actual = generated[[factor.name for factor in factors]].to_numpy(dtype=int)

    # DSD columns may be independently sign-reversed without changing the design.
    # For the package conference convention, columns 3-6 are reversed relative
    # to Jones & Nachtsheim Table 2. Run order is likewise statistically arbitrary.
    normalized = actual * np.asarray([1, 1, -1, -1, -1, -1], dtype=int)

    assert actual.shape == (13, 6)
    assert _sorted_rows(normalized) == _sorted_rows(_JONES_NACHTSHEIM_DSD6)
    np.testing.assert_array_equal(generated["RunOrder"].to_numpy(), np.arange(1, 14))
