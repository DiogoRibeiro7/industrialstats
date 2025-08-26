"""Interactive response surface visualization tools.

This module provides the :class:`ResponseSurfacePlotter` class for generating
3D response surface plots, contour maps with optimization paths, prediction
variance surfaces, and slice plots at fixed factor levels. Plotly is used to
provide interactive figures that can be embedded in notebooks or exported to
HTML.

Examples
--------
>>> from industrialstats.designs.response_surface import ResponseSurfaceDesign, Factor
>>> import pandas as pd
>>> import statsmodels.formula.api as smf
>>> factors = [Factor("x1", [-1, 1]), Factor("x2", [-1, 1])]
>>> design = ResponseSurfaceDesign(factors)
>>> dm = design.generate_design()
>>> dm["y"] = dm["x1"]**2 + dm["x2"]**2
>>> model = smf.ols("y ~ x1 + x2 + I(x1**2) + I(x2**2) + x1:x2", data=dm).fit()
>>> plotter = ResponseSurfacePlotter(design, model)
>>> fig = plotter.surface_plot("x1", "x2")
>>> isinstance(fig.to_dict(), dict)
True
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from industrialstats.designs.response_surface import ResponseSurfaceDesign


@dataclass
class ResponseSurfacePlotter:
    """Visualize fitted response surface models in three dimensions.

    Parameters
    ----------
    design : ResponseSurfaceDesign
        Generated response surface design containing factor ranges.
    model : Any
        Fitted model with a :meth:`predict` method and optionally a
        :meth:`get_prediction` method returning prediction variance.
    """

    design: ResponseSurfaceDesign
    model: Any

    def _factor_range(self, name: str, resolution: int) -> np.ndarray:
        factor = next(f for f in self.design.factors if f.name == name)
        low, high = factor.levels
        return np.linspace(low, high, resolution)

    def _grid(
        self,
        x1: str,
        x2: str,
        resolution: int,
        fixed: Optional[Dict[str, float]] = None,
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        x1_vals = self._factor_range(x1, resolution)
        x2_vals = self._factor_range(x2, resolution)
        xx, yy = np.meshgrid(x1_vals, x2_vals)
        grid = pd.DataFrame({x1: xx.ravel(), x2: yy.ravel()})
        if fixed:
            for k, v in fixed.items():
                grid[k] = v
        return grid, x1_vals, x2_vals

    def surface_plot(self, x1: str, x2: str, resolution: int = 50) -> go.Figure:
        """Plot a 3D response surface for two factors.

        Parameters
        ----------
        x1, x2 : str
            Factor names for the x- and y-axes.
        resolution : int, optional
            Number of grid points per axis. Defaults to ``50``.

        Returns
        -------
        plotly.graph_objects.Figure
            Interactive 3D surface plot.
        """

        grid, x1_vals, x2_vals = self._grid(x1, x2, resolution)
        z = self.model.predict(grid).to_numpy().reshape(resolution, resolution)
        fig = go.Figure(data=[go.Surface(x=x1_vals, y=x2_vals, z=z)])
        fig.update_layout(
            scene=dict(xaxis_title=x1, yaxis_title=x2, zaxis_title="Response")
        )
        return fig

    def contour_plot(
        self,
        x1: str,
        x2: str,
        resolution: int = 50,
        path: Optional[Iterable[Tuple[float, float]]] = None,
    ) -> go.Figure:
        """Create a contour plot with optional optimization path overlay.

        Parameters
        ----------
        x1, x2 : str
            Factor names for the axes.
        resolution : int, optional
            Grid resolution per axis. Defaults to ``50``.
        path : iterable of tuple[float, float], optional
            Sequence of (x1, x2) points representing an optimization path.

        Returns
        -------
        plotly.graph_objects.Figure
            Interactive contour plot.
        """

        grid, x1_vals, x2_vals = self._grid(x1, x2, resolution)
        z = self.model.predict(grid).to_numpy().reshape(resolution, resolution)
        fig = go.Figure(data=[go.Contour(x=x1_vals, y=x2_vals, z=z)])
        if path is not None:
            path_x, path_y = zip(*path)
            fig.add_trace(go.Scatter(x=path_x, y=path_y, mode="lines+markers"))
        fig.update_layout(xaxis_title=x1, yaxis_title=x2)
        return fig

    def prediction_variance_surface(
        self, x1: str, x2: str, resolution: int = 50
    ) -> go.Figure:
        """Visualize the prediction variance surface for two factors.

        Parameters
        ----------
        x1, x2 : str
            Factor names for the axes.
        resolution : int, optional
            Grid resolution per axis. Defaults to ``50``.

        Returns
        -------
        plotly.graph_objects.Figure
            Surface plot of prediction variance.

        Raises
        ------
        AttributeError
            If the model does not provide prediction variance via
            ``get_prediction``.
        """

        if not hasattr(self.model, "get_prediction"):
            raise AttributeError("model must provide get_prediction for variance")

        grid, x1_vals, x2_vals = self._grid(x1, x2, resolution)
        pred = self.model.get_prediction(grid)
        var = pred.var_pred_mean.reshape(resolution, resolution)
        fig = go.Figure(data=[go.Surface(x=x1_vals, y=x2_vals, z=var)])
        fig.update_layout(
            scene=dict(xaxis_title=x1, yaxis_title=x2, zaxis_title="Var"),
            title="Prediction Variance",
        )
        return fig

    def slice_plot(
        self,
        varying: str,
        fixed: Dict[str, float],
        resolution: int = 50,
    ) -> go.Figure:
        """Plot model response by varying one factor with others fixed.

        Parameters
        ----------
        varying : str
            Factor to vary along the x-axis.
        fixed : dict[str, float]
            Mapping of other factor names to fixed levels.
        resolution : int, optional
            Number of points along the varying factor. Defaults to ``50``.

        Returns
        -------
        plotly.graph_objects.Figure
            Line plot showing the slice through the response surface.
        """

        x_vals = self._factor_range(varying, resolution)
        grid = pd.DataFrame({varying: x_vals})
        for k, v in fixed.items():
            grid[k] = v
        y = self.model.predict(grid)
        fig = go.Figure(data=[go.Scatter(x=x_vals, y=y)])
        fig.update_layout(xaxis_title=varying, yaxis_title="Response")
        return fig
