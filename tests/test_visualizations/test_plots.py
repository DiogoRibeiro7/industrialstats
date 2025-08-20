import matplotlib.pyplot as plt

from industrialstats.designs.factorial import Factor, FactorialDesign
from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign
from industrialstats.visualizations import ExperimentPlotter


def test_design_comparison_plot() -> None:
    factorial = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
    factorial.generate_design()

    rcbd = RandomizedCompleteBlockDesign(["T1", "T2"], ["B1", "B2"])
    rcbd.generate_design()

    fig = ExperimentPlotter.design_comparison_plot(
        {
            "Factorial": factorial,
            "RCBD": rcbd,
        }
    )

    assert isinstance(fig, plt.Figure)
    assert len(fig.axes) == 3  # two plots + metrics table
    plt.close(fig)
