import matplotlib
import numpy as np

from industrialstats.designs.advanced import MixtureDesign
from industrialstats.designs.base import Factor

matplotlib.use("Agg")


def _three_factors():
    return [
        Factor("A", [], "continuous"),
        Factor("B", [], "continuous"),
        Factor("C", [], "continuous"),
    ]


def test_simplex_lattice_sum_and_count():
    design = MixtureDesign(_three_factors(), order=2)
    df = design.generate_design()
    assert len(df) == 6
    assert np.allclose(df.sum(axis=1), 1.0)


def test_randomization_deterministic():
    design1 = MixtureDesign(_three_factors(), order=2, randomize=True, seed=7)
    df1 = design1.generate_design()
    design2 = MixtureDesign(_three_factors(), order=2, randomize=True, seed=7)
    df2 = design2.generate_design()
    assert df1.equals(df2)


def test_constraints():
    def constraint(x: np.ndarray) -> bool:
        return x[0] >= 0.5

    design = MixtureDesign(_three_factors(), order=2, constraints=[constraint])
    df = design.generate_design()
    assert np.all(df["A"] >= 0.5)


def test_plot_simplex_returns_axes():
    design = MixtureDesign(_three_factors(), order=2)
    design.generate_design()
    ax = design.plot_simplex()
    assert ax is not None
