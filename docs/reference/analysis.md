# Analysis

Statistical analysis of collected experimental results.

## ANOVA

::: industrialstats.analysis.anova

## Split-plot inference

Split-plot experiments have two randomization stages and therefore two error strata. Whole-plot-only treatment terms must be tested against whole-plot error; terms containing subplot factors must be tested against subplot error.

![Split-plot randomization, error strata, and inference structure](../diagrams/rendered/split_plot_inference.svg)

Source: [`../diagrams/split_plot_inference.dot`](../diagrams/split_plot_inference.dot)

The classical stratum-specific F tests and the random-intercept mixed model answer complementary questions. A generic OLS residual denominator is not valid for whole-plot treatment effects, and mixed-model Wald tests are not substituted for the classical balanced split-plot F tests.

::: industrialstats.analysis.split_plot

## Effects

::: industrialstats.analysis.effects

## Model fitting

::: industrialstats.analysis.model_fitting

## Diagnostics

Model diagnostics are a decision process, not a single goodness-of-fit number. The package combines formal assumption checks, influence diagnostics, explicit outlier thresholds, residual plots, and an adequacy summary before producing remediation guidance.

![industrialstats model diagnostics and remediation flow](../diagrams/rendered/model_diagnostics.svg)

Source: [`../diagrams/model_diagnostics.dot`](../diagrams/model_diagnostics.dot)

Formal assumption tests should be interpreted together with residual plots and influence measures. A model can pass a normality or variance test and still contain observations with enough leverage or Cook's distance to destabilize inference; conversely, a flagged point should be investigated rather than deleted automatically.

::: industrialstats.analysis.diagnostics

## Power analysis

::: industrialstats.analysis.power_analysis
