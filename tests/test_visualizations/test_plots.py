import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pytest

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


def test_interactive_design_explorer(tmp_path) -> None:
    design = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
    design.generate_design()
    plotter = ExperimentPlotter(design_matrix=design.design_matrix)
    out_file = tmp_path / "explorer.html"

    fig = plotter.interactive_design_explorer(filename=str(out_file))

    assert isinstance(fig, go.Figure)
    assert out_file.exists()


def test_main_effects_plot_and_errors() -> None:
    design = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
    design.generate_design()
    design.design_matrix["y"] = [1, 2, 3, 4]

    plotter = ExperimentPlotter(data=design.design_matrix)
    fig = plotter.main_effects_plot("y")
    assert isinstance(fig, plt.Figure)
    plt.close(fig)

    empty_plotter = ExperimentPlotter()
    with pytest.raises(ValueError):
        empty_plotter.main_effects_plot("y")

    with pytest.raises(ValueError):
        plotter.main_effects_plot("missing")
