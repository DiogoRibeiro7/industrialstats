from typing import Any

import statsmodels.formula.api as smf

from industrialstats.designs.response_surface import Factor, ResponseSurfaceDesign
from industrialstats.visualizations import ResponseSurfacePlotter


def _design_and_model() -> tuple[ResponseSurfaceDesign, Any]:
    factors = [
        Factor("x1", [-1, 1], factor_type="continuous"),
        Factor("x2", [-1, 1], factor_type="continuous"),
    ]
    design = ResponseSurfaceDesign(factors)
    dm = design.generate_design()
    dm["y"] = dm["x1"] ** 2 + dm["x2"] ** 2
    model = smf.ols("y ~ x1 + x2 + I(x1**2) + I(x2**2) + x1:x2", data=dm).fit()
    return design, model


def test_surface_plot_returns_figure() -> None:
    design, model = _design_and_model()
    plotter = ResponseSurfacePlotter(design, model)
    fig = plotter.surface_plot("x1", "x2")
    assert isinstance(fig.to_dict(), dict)


def test_contour_and_slice_plots() -> None:
    design, model = _design_and_model()
    plotter = ResponseSurfacePlotter(design, model)
    contour = plotter.contour_plot("x1", "x2", path=[(-1, -1), (0, 0), (1, 1)])
    slice_fig = plotter.slice_plot("x1", {"x2": 0.0})
    assert isinstance(contour.to_dict(), dict)
    assert isinstance(slice_fig.to_dict(), dict)


def test_prediction_variance_surface() -> None:
    design, model = _design_and_model()
    plotter = ResponseSurfacePlotter(design, model)
    fig = plotter.prediction_variance_surface("x1", "x2")
    assert isinstance(fig.to_dict(), dict)
