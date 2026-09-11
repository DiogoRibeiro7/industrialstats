"""Independent reference checks for Plackett-Burman screening designs."""

import numpy as np

from industrialstats.designs.base import Factor
from industrialstats.designs.screening import PlackettBurmanDesign


# NIST/SEMATECH e-Handbook of Statistical Methods, Table 3.18:
# https://www.itl.nist.gov/div898/handbook/pri/section3/pri335.htm
_NIST_PB12_PATTERNS = (
    "+++++++++++",
    "-+-+++---+-",
    "--+-+++---+",
    "+--+-+++---",
    "-+--+-+++--",
    "--+--+-+++-",
    "---+--+-+++",
    "+---+--+-++",
    "++---+--+-+",
    "+++---+--+-",
    "-+++---+--+",
    "+-+++---+--",
)


def _pattern_matrix(patterns: tuple[str, ...]) -> np.ndarray:
    return np.asarray(
        [[1 if symbol == "+" else -1 for symbol in pattern] for pattern in patterns],
        dtype=int,
    )


def test_pb12_matches_nist_table_318_up_to_documented_run_reversal() -> None:
    """The implemented 12-run base is NIST Table 3.18 in reverse run order."""
    factors = [Factor(f"X{index}", [-1, 1]) for index in range(1, 12)]
    design = PlackettBurmanDesign(factors, randomize=False)
    generated = design.generate_design()

    actual = generated[[factor.name for factor in factors]].to_numpy(dtype=int)
    nist = _pattern_matrix(_NIST_PB12_PATTERNS)

    np.testing.assert_array_equal(actual, nist[::-1])
    np.testing.assert_array_equal(generated["RunOrder"].to_numpy(), np.arange(1, 13))
