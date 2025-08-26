"""Advanced end-to-end workflow demonstrating design, analysis, and visualization.

This tutorial constructs a central composite design for three factors, simulates
responses with interactions, fits a quadratic model via stepwise selection, and
visualizes the resulting response surface.
"""

from __future__ import annotations

from industrialstats.analysis.model_fitting import ModelFitting
from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign
from industrialstats.utils.data_generation import DataSimulator
from industrialstats.visualizations.response_surface_plots import ResponseSurfacePlotter


def main() -> None:
    """Run the complete response-surface workflow."""
    factors = [
        Factor("Temperature", [-1, 1], "continuous"),
        Factor("Pressure", [-1, 1], "continuous"),
        Factor("Catalyst", [-1, 1], "continuous"),
    ]
    design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=2)
    design_matrix = design.generate_design()

    sim = DataSimulator(seed=42)
    response = sim.simulate_factorial_response(
        design_matrix[[f.name for f in factors]],
        main_effects={"Temperature": 1.0, "Pressure": -0.5, "Catalyst": 0.75},
        interactions={("Temperature", "Pressure"): 0.6},
        noise_level=0.1,
    )
    design_matrix["Yield"] = response

    fitter = ModelFitting(design_matrix, "Yield")
    result = fitter.stepwise_selection()
    model = result["final_model"]["model_object"]

    plotter = ResponseSurfacePlotter(design, model)
    fig = plotter.surface_plot("Temperature", "Pressure", resolution=30)
    fig.write_html("advanced_workflow_surface.html")


if __name__ == "__main__":
    main()
