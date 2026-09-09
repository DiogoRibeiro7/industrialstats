"""Statistical property tests for regular factorial blocking."""

import numpy as np
import pandas as pd
import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


def _two_level_factors(names: str = "ABC") -> list[Factor]:
    return [Factor(name, [-1, 1], "continuous") for name in names]


def test_two_blocks_use_treatment_contrast_not_row_order() -> None:
    design = FactorialDesign(_two_level_factors(), blocks=2, randomize=False)
    matrix = design.generate_design()

    structure = design.block_structure()
    assert structure["generators"] == ["A*B*C"]
    assert structure["defining_contrasts"] == ["A*B*C"]
    assert structure["confounded_main_effects"] == []
    assert matrix.groupby("Block").size().to_dict() == {1: 4, 2: 4}

    block_contrast = np.where(matrix["Block"].to_numpy() == 2, 1, -1)
    abc = matrix["A"].to_numpy() * matrix["B"].to_numpy() * matrix["C"].to_numpy()
    np.testing.assert_array_equal(block_contrast, abc)

    for factor in ("A", "B", "C"):
        assert np.dot(block_contrast, matrix[factor].to_numpy()) == 0


def test_four_blocks_have_independent_generators_without_main_effect_confounding() -> (
    None
):
    design = FactorialDesign(_two_level_factors("ABCD"), blocks=4, randomize=False)
    matrix = design.generate_design()
    structure = design.block_structure()

    assert matrix.groupby("Block").size().to_dict() == {1: 4, 2: 4, 3: 4, 4: 4}
    assert len(structure["generators"]) == 2
    assert len(structure["defining_contrasts"]) == 3
    assert structure["confounded_main_effects"] == []
    assert all("*" in word for word in structure["defining_contrasts"])


def test_explicit_generators_expose_complete_defining_contrast_subgroup() -> None:
    design = FactorialDesign(
        _two_level_factors(),
        blocks=4,
        block_generators=["A*B", "A*C"],
        randomize=False,
    )
    design.generate_design()

    structure = design.block_structure()
    assert structure["generators"] == ["A*B", "A*C"]
    assert set(structure["defining_contrasts"]) == {"A*B", "A*C", "B*C"}
    assert structure["confounded_main_effects"] == []


def test_main_effect_confounding_requires_explicit_opt_in() -> None:
    with pytest.raises(ValueError, match="confound main effect"):
        FactorialDesign(
            _two_level_factors(),
            blocks=2,
            block_generators=["A"],
        )

    design = FactorialDesign(
        _two_level_factors(),
        blocks=2,
        block_generators=["A"],
        allow_main_effect_confounding=True,
        randomize=False,
    )
    matrix = design.generate_design()

    assert design.block_structure()["confounded_main_effects"] == ["A"]
    block_contrast = np.where(matrix["Block"].to_numpy() == 2, 1, -1)
    np.testing.assert_array_equal(block_contrast, matrix["A"].to_numpy())


def test_invalid_regular_blocking_configurations_are_rejected() -> None:
    with pytest.raises(ValueError, match="power of two"):
        FactorialDesign(_two_level_factors(), blocks=3)

    with pytest.raises(ValueError, match="linearly independent"):
        FactorialDesign(
            _two_level_factors(),
            blocks=4,
            block_generators=["A*B", "A*B"],
        )

    with pytest.raises(ValueError, match="exactly two levels"):
        FactorialDesign(
            [
                Factor("A", [-1, 0, 1], "continuous"),
                Factor("B", [-1, 0, 1], "continuous"),
            ],
            blocks=2,
        )

    with pytest.raises(ValueError, match="Center points"):
        FactorialDesign(_two_level_factors(), blocks=2, center_points=1)


def test_replicates_keep_the_same_treatment_combination_in_the_same_block() -> None:
    design = FactorialDesign(
        _two_level_factors(),
        blocks=2,
        replicates=2,
        randomize=False,
    )
    matrix = design.generate_design()

    assert matrix.groupby("Block").size().to_dict() == {1: 8, 2: 8}
    per_treatment = matrix.groupby(["A", "B", "C"])["Block"].nunique()
    assert (per_treatment == 1).all()


def test_blocked_randomization_is_seeded_and_stays_within_block_groups() -> None:
    first = FactorialDesign(_two_level_factors(), blocks=2, seed=17)
    second = FactorialDesign(_two_level_factors(), blocks=2, seed=17)

    first_matrix = first.generate_design()
    second_matrix = second.generate_design()
    pd.testing.assert_frame_equal(first_matrix, second_matrix)

    assert first_matrix["RunOrder"].tolist() == list(range(1, 9))
    assert first_matrix["Block"].tolist()[:4] == [1, 1, 1, 1]
    assert first_matrix["Block"].tolist()[4:] == [2, 2, 2, 2]


def test_blocking_scheme_recomputes_membership_from_treatment_contrasts() -> None:
    design = FactorialDesign(_two_level_factors(), seed=11)
    design.generate_design()

    matrix = design.blocking_scheme(block_size=4)
    block_contrast = np.where(matrix["Block"].to_numpy() == 2, 1, -1)
    abc = matrix["A"].to_numpy() * matrix["B"].to_numpy() * matrix["C"].to_numpy()

    np.testing.assert_array_equal(block_contrast, abc)
    assert design.block_structure()["generators"] == ["A*B*C"]
