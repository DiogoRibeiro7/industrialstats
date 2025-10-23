import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.fractional_factorial import FractionalFactorialDesign


def build_factors(names: str) -> list[Factor]:
    """Convenience helper for constructing two-level factors."""

    return [Factor(name, [-1, 1]) for name in names]


def test_automatic_generator_selection_matches_montgomery():
    """Verify automatic generator selection aligns with Montgomery's table."""

    factors = build_factors("ABCDEFG")
    design = FractionalFactorialDesign(factors, fraction="1/8", randomize=False)
    assert design.generators == ["A*B*C", "A*B*D", "A*C*D"]

    resolution = design.resolution_analysis()
    assert resolution["resolution"] == 4
    assert resolution["word_length_pattern"] == {4: 7}
    assert design.verify_resolution(4)
    with pytest.raises(ValueError):
        design.verify_resolution(5)


def test_alias_structure_matches_frF2_catalogue():
    """Compare alias chains with the R FrF2::catlg52 catalogue."""

    factors = build_factors("ABCD")
    design = FractionalFactorialDesign(
        factors,
        fraction="1/2",
        generators=["A*B*C"],
        randomize=False,
    )
    alias = design.alias_structure()
    assert alias["A"] == ["A", "B:C:D"]
    assert alias["A:B"] == ["A:B", "C:D"]


def test_alias_structure_for_seven_factor_design():
    """Ensure alias map enumerates all members for a 2^(7-3) fraction."""

    factors = build_factors("ABCDEFG")
    design = FractionalFactorialDesign(factors, fraction="1/8", randomize=False)
    alias = design.alias_structure()

    assert alias["A"][0] == "A"
    assert "A:B:C:F:G" in alias["A"]
    assert "B" in alias
    assert "C" in alias
    # Montgomery Example 8-3 lists that B is aliased with AC E.
    assert any(entry.endswith("A:C:E") for entry in alias["B"][1:])


def test_foldover_recommendations_prioritise_alias_heavy_factors():
    """Foldover suggestions should include full and targeted strategies."""

    factors = build_factors("ABCDEFG")
    design = FractionalFactorialDesign(factors, fraction="1/8", randomize=False)
    options = design.foldover_options()

    full = options[0]
    assert full["type"] == "full"
    assert full["expected_resolution"] == 5
    assert full["generators_to_reverse"] == design.generators

    partial = [option for option in options if option["type"] == "partial"]
    assert partial
    # The first partial recommendation should target factor A according to the
    # alias chain severity.
    assert partial[0]["factor"] == "A"
    assert "A:B:C:F:G" in partial[0]["confounded_with"]


def test_generate_design_structure_and_values():
    """Generated design matrix should preserve coded structure and metadata."""

    factors = build_factors("ABCD")
    design = FractionalFactorialDesign(
        factors,
        fraction="1/2",
        generators=["A*B*C"],
        replicates=2,
        randomize=False,
    )
    matrix = design.generate_design()
    assert len(matrix) == 16
    assert set(matrix.columns) == {"RunID", "Replicate", "A", "B", "C", "D"}
    assert design._coded_matrix is not None
    assert design._coded_matrix["D"].isin([-1, 1]).all()
