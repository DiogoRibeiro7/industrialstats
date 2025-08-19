import pandas as pd
import pytest

from industrialstats.designs.base import Factor
from industrialstats.designs.optimal import OptimalDesign


def _factors():
    return [
        Factor("x1", [0, 1], factor_type="continuous"),
        Factor("x2", [0, 1], factor_type="continuous"),
    ]


@pytest.mark.parametrize("criterion", ["D", "A", "I"])
def test_coordinate_exchange_converges(criterion):
    design = OptimalDesign(_factors(), n_runs=4, criterion=criterion)
    design.generate_candidate_set(grid_density=2)
    result = design.generate_design(
        max_iterations=50,
        random_start=False,
        n_random_starts=1,
        improvement_threshold=1e-6,
    )
    assert result.shape == (4, 3)  # RunID + 2 factors
    assert design.exchange_history
    assert design.exchange_history[-1]["improvement"] <= 1e-6


def test_singular_design_raises():
    design = OptimalDesign(_factors(), n_runs=4, criterion="D")
    design.candidate_set = pd.DataFrame(
        {
            "CandidateID": [1, 2, 3, 4],
            "x1": [0, 0, 0, 0],
            "x2": [0, 0, 0, 0],
        }
    )
    with pytest.raises(ValueError, match="Singular design matrix"):
        design.generate_design(
            max_iterations=10,
            random_start=False,
            n_random_starts=1,
        )
