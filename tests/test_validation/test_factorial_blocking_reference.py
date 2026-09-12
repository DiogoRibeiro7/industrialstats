"""Independent reference checks for regular factorial blocking."""

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign

# NIST/SEMATECH e-Handbook of Statistical Methods, Table 3.10:
# https://www.itl.nist.gov/div898/handbook/pri/section3/pri3333.htm
#
# For a 2^3 design blocked into two groups of four runs, ABC is confounded
# with blocks. NIST assigns the treatment combinations as
#
#   Block I:  (1), ab, ac, bc
#   Block II: a, b, c, abc
#
# Using coded levels (-1, +1), those treatment combinations are encoded below.
_NIST_BLOCK_I = {
    (-1, -1, -1),
    (1, 1, -1),
    (1, -1, 1),
    (-1, 1, 1),
}
_NIST_BLOCK_II = {
    (1, -1, -1),
    (-1, 1, -1),
    (-1, -1, 1),
    (1, 1, 1),
}


def test_two_block_2_cubed_matches_nist_table_310() -> None:
    factors = [
        Factor("A", [-1, 1], "continuous"),
        Factor("B", [-1, 1], "continuous"),
        Factor("C", [-1, 1], "continuous"),
    ]
    design = FactorialDesign(
        factors,
        blocks=2,
        block_generators=["A*B*C"],
        randomize=False,
    )
    generated = design.generate_design()

    block_i = {
        tuple(row)
        for row in generated.loc[generated["Block"] == 1, ["A", "B", "C"]]
        .to_numpy(dtype=int)
        .tolist()
    }
    block_ii = {
        tuple(row)
        for row in generated.loc[generated["Block"] == 2, ["A", "B", "C"]]
        .to_numpy(dtype=int)
        .tolist()
    }

    assert block_i == _NIST_BLOCK_I
    assert block_ii == _NIST_BLOCK_II
    assert design.block_structure()["defining_contrasts"] == ["A*B*C"]
