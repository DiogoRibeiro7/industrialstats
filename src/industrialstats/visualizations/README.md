# Visualizations

Interactive plotting utilities for experimental designs and analysis.

## ExperimentPlotter

Provides matplotlib-based plots for experimental designs, including
main-effects, interactions, and design-space visualizations. It also
offers a design comparison utility to aid selection between candidate
designs.

### Example
```python
from industrialstats.designs.factorial import Factor, FactorialDesign
from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign
from industrialstats.visualizations import ExperimentPlotter

factorial = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
factorial.generate_design()

rcbd = RandomizedCompleteBlockDesign(["T1", "T2"], ["B1", "B2"])
rcbd.generate_design()

fig = ExperimentPlotter.design_comparison_plot({
    "Factorial": factorial,
    "RCBD": rcbd,
})
fig.show()
```

### Interactive Explorer

The interactive design explorer provides a Plotly-based interface with
hover details, factor-level filters, and optional response overlays.

```python
from industrialstats.designs.factorial import Factor, FactorialDesign
from industrialstats.visualizations import ExperimentPlotter

design = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
design.generate_design()

plotter = ExperimentPlotter(design_matrix=design.design_matrix)
fig = plotter.interactive_design_explorer()
fig.show()

# Export to HTML
plotter.interactive_design_explorer(filename="design.html")
```

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
