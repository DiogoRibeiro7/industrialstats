"""Regression tests for canonical two-level factorial effect semantics."""

import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.effects import EffectsAnalysis
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


def _three_factor_design(*, replicates: int = 1, blocks: int | None = None):
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABC"]
    design = FactorialDesign(
        factors,
        replicates=replicates,
        blocks=blocks,
        randomize=False,
    )
    matrix = design.generate_design()
    return design, matrix


def _known_model_response(matrix: pd.DataFrame) -> list[float]:
    a = matrix["A"].to_numpy(dtype=float)
    b = matrix["B"].to_numpy(dtype=float)
    c = matrix["C"].to_numpy(dtype=float)
    response = (
        20.0
        + 3.0 * a
        - 2.0 * b
        + 1.5 * c
        + 4.0 * a * b
        - 5.0 * a * c
        + 2.5 * b * c
        + 6.0 * a * b * c
    )
    return response.tolist()


def test_design_and_analysis_share_canonical_factorial_effects() -> None:
    design, matrix = _three_factor_design()
    response = _known_model_response(matrix)

    design_effects = design.calculate_effects(response, max_order=3)
    analysis = EffectsAnalysis(matrix, response)
    analysis_effects = {
        **analysis.calculate_main_effects(),
        **analysis.calculate_interaction_effects(max_order=3),
    }

    expected = {
        "A": 6.0,
        "B": -4.0,
        "C": 3.0,
        "A*B": 8.0,
        "A*C": -10.0,
        "B*C": 5.0,
        "A*B*C": 12.0,
    }
    assert design_effects == pytest.approx(expected)
    assert analysis_effects == pytest.approx(expected)


def test_three_factor_interaction_uses_standard_positive_sign() -> None:
    design, matrix = _three_factor_design()
    response = (5.0 * matrix["A"] * matrix["B"] * matrix["C"]).tolist()

    effect = EffectsAnalysis(matrix, response).calculate_interaction_effects(
        max_order=3
    )["A*B*C"]

    assert effect == pytest.approx(10.0)


def test_factorial_effect_is_twice_coded_regression_coefficient() -> None:
    design, matrix = _three_factor_design()
    response = np.asarray(_known_model_response(matrix))
    effects = design.calculate_effects(response.tolist(), max_order=3)

    a = matrix["A"].to_numpy(dtype=float)
    b = matrix["B"].to_numpy(dtype=float)
    c = matrix["C"].to_numpy(dtype=float)
    model_matrix = np.column_stack(
        (
            np.ones(len(matrix)),
            a,
            b,
            c,
            a * b,
            a * c,
            b * c,
            a * b * c,
        )
    )
    coefficients = np.linalg.lstsq(model_matrix, response, rcond=None)[0]
    names = ["A", "B", "C", "A*B", "A*C", "B*C", "A*B*C"]

    for index, name in enumerate(names, start=1):
        assert effects[name] == pytest.approx(2.0 * coefficients[index])


def test_replication_does_not_change_effect_scale() -> None:
    design, matrix = _three_factor_design(replicates=2)
    response = _known_model_response(matrix)

    effects = design.calculate_effects(response, max_order=3)

    assert effects["A"] == pytest.approx(6.0)
    assert effects["A*B"] == pytest.approx(8.0)
    assert effects["A*B*C"] == pytest.approx(12.0)


def test_generated_level_order_is_preserved_for_effects_analysis() -> None:
    factor = Factor("A", [10, -10], "continuous")
    design = FactorialDesign([factor], randomize=False)
    matrix = design.generate_design()
    response = [2.0, 8.0]

    assert matrix.attrs["factor_level_orders"] == {"A": [10, -10]}
    assert design.calculate_effects(response)["A"] == pytest.approx(6.0)
    assert EffectsAnalysis(matrix, response).calculate_main_effects()["A"] == pytest.approx(
        6.0
    )


def test_raw_dataframe_retains_sorted_level_convention() -> None:
    matrix = pd.DataFrame({"A": [10, -10]})
    response = [2.0, 8.0]

    # With no design metadata, -10 is low and +10 is high.
    assert EffectsAnalysis(matrix, response).calculate_main_effects()["A"] == pytest.approx(
        -6.0
    )


def test_design_metadata_are_not_treated_as_factors() -> None:
    _design, matrix = _three_factor_design(blocks=2)
    response = [0.0] * len(matrix)

    analysis = EffectsAnalysis(matrix, response)

    assert analysis.factor_names == ["A", "B", "C"]
    assert "Block" not in analysis.factor_names
    assert "StdOrder" not in analysis.factor_names


def test_augmented_design_is_rejected_by_factorial_design_effect_api() -> None:
    factors = [
        Factor("A", [-1.0, 1.0], "continuous"),
        Factor("B", [-1.0, 1.0], "continuous"),
    ]
    design = FactorialDesign(factors, center_points=1, randomize=False)
    matrix = design.generate_design()

    with pytest.raises(ValueError, match="factorial treatment points only"):
        design.calculate_effects([0.0] * len(matrix))
