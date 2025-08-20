# Visualizations

Interactive plotting utilities for experimental designs and analysis.

## ResponseSurfacePlotter

Generates Plotly-based interactive plots for response surface models:

- 3D response surfaces
- Contour plots with optimization paths
- Prediction variance surfaces
- Slice plots at fixed factor levels

### Example
```python
from industrialstats.designs.response_surface import ResponseSurfaceDesign, Factor
import statsmodels.formula.api as smf
from industrialstats.visualizations import ResponseSurfacePlotter

factors = [Factor("x1", [-1, 1]), Factor("x2", [-1, 1])]
design = ResponseSurfaceDesign(factors)
dm = design.generate_design()
dm["y"] = dm["x1"]**2 + dm["x2"]**2
model = smf.ols("y ~ x1 + x2 + I(x1**2) + I(x2**2) + x1:x2", data=dm).fit()

plotter = ResponseSurfacePlotter(design, model)
fig = plotter.surface_plot("x1", "x2")
fig.show()
```
