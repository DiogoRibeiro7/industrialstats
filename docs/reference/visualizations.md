# Visualization

Plotting helpers for designs, effects, diagnostics, and response surfaces.

Most `ExperimentPlotter` methods return a Matplotlib `Figure`; its
`interactive_design_explorer` is the exception and returns a Plotly
`graph_objects.Figure`. Every `ResponseSurfacePlotter` method returns a Plotly
figure, which is interactive in a notebook and supports `.show()` and
`.write_html()`. Either way the returned object can be customised before
display.

## Experiment plots

::: industrialstats.visualizations.plots

## Response surface plots

::: industrialstats.visualizations.response_surface_plots
