"""Tests for general factorial model hierarchy and degrees of freedom."""

from math import prod

import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


def test_four_factor_saturated_hierarchy_includes_four_way_interaction() -> None:
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABCD"]
    design = FactorialDesign(factors, replicates=2, randomize=False)

    terms = design.model_terms()
    dof = design.degrees_of_freedom()

    assert terms[-1] == "A*B*C*D"
    assert len(terms) == 2**4 - 1
    assert dof["A*B*C*D"] == 1
    assert sum(dof[term] for term in terms) == 2**4 - 1
    assert dof["Error"] == 16
    assert dof["Total"] == 31


def test_mixed_level_saturated_dof_matches_full_factorial_identity() -> None:
    factors = [
        Factor("A", [0, 1], "categorical"),
        Factor("B", [0, 1, 2], "categorical"),
        Factor("C", [0, 1, 2, 3], "categorical"),
        Factor("D", [0, 1], "categorical"),
    ]
    design = FactorialDesign(factors, randomize=False)

    dof = design.degrees_of_freedom()
    terms = design.model_terms()
    treatment_combinations = prod(len(factor.levels) for factor in factors)

    assert dof["A*B*C*D"] == 1 * 2 * 3 * 1
    assert sum(dof[term] for term in terms) == treatment_combinations - 1
    assert dof["Error"] == 0
    assert dof["Total"] == treatment_combinations - 1


def test_truncated_hierarchy_contains_all_lower_order_terms() -> None:
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABCD"]
    design = FactorialDesign(factors, replicates=2, randomize=False)

    terms = design.model_terms(max_order=2)
    dof = design.degrees_of_freedom(max_order=2)
    structure = design.model_structure(max_order=2)

    assert terms == [
        "A",
        "B",
        "C",
        "D",
        "A*B",
        "A*C",
        "A*D",
        "B*C",
        "B*D",
        "C*D",
    ]
    assert structure["saturated"] is False
    assert structure["max_order"] == 2
    assert structure["terms"] == terms
    assert structure["model_degrees_of_freedom"] == 10
    assert structure["error_degrees_of_freedom"] == 21
    assert dof["Error"] == 21


def test_center_points_contribute_residual_degrees_of_freedom() -> None:
    factors = [
        Factor("A", [-1.0, 1.0], "continuous"),
        Factor("B", [-1.0, 1.0], "continuous"),
    ]
    design = FactorialDesign(
        factors,
        replicates=2,
        center_points=3,
        randomize=False,
    )

    dof = design.degrees_of_freedom()

    assert dof["A"] == 1
    assert dof["B"] == 1
    assert dof["A*B"] == 1
    assert dof["Error"] == 7
    assert dof["Total"] == 10


@pytest.mark.parametrize("value", [0, -1, 5, True, 1.5, "2"])
def test_invalid_model_order_is_rejected(value: object) -> None:
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABCD"]
    design = FactorialDesign(factors, randomize=False)

    with pytest.raises(ValueError):
        design.model_terms(value)  # type: ignore[arg-type]


def test_model_structure_reports_saturated_model() -> None:
    factors = [Factor(name, [-1, 1], "continuous") for name in "ABC"]
    design = FactorialDesign(factors, replicates=2, randomize=False)

    structure = design.model_structure()

    assert structure["saturated"] is True
    assert structure["max_order"] == 3
    assert structure["model_degrees_of_freedom"] == 7
    assert structure["error_degrees_of_freedom"] == 8
    assert structure["total_degrees_of_freedom"] == 15
