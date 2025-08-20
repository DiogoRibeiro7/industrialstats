# Analysis Module

The analysis package provides tools for evaluating experimental results.

## Key Classes
- `ANOVAAnalysis`: fits linear models and computes ANOVA tables.
- `PowerAnalysis`: performs prospective and retrospective power calculations.
- `EffectsAnalysis`: estimates main and interaction effects with visualization helpers.
- `ModelFitting`: utilities for hierarchical model fitting and validation.
- `ModelDiagnostics`: assumption testing, outlier detection, and influence plots.

## Usage
```python
import pandas as pd
from industrialstats.analysis.anova import ANOVAAnalysis

df = pd.DataFrame({"y": [5, 6, 7, 8], "A": ["a", "a", "b", "b"]})
analysis = ANOVAAnalysis(data=df, response_column="y")
analysis.fit_model("y ~ A")
table = analysis.anova_table_calculation()

# Power analysis for a two-sample t-test
from industrialstats.analysis.power_analysis import PowerAnalysis

pa = PowerAnalysis()
result = pa.t_test_power(effect_size=0.5, power=0.8)

# Factorial power including an interaction effect
result_fact = pa.factorial_power(
    effect_size=0.3,
    replicates=3,
    factor_levels=[2, 3],
    effect=(0, 1),
)
curve = pa.factorial_power_curve(
    effect_sizes=[0.1, 0.2, 0.3],
    replicates=3,
    factor_levels=[2, 3],
)

# Stepwise model fitting
from industrialstats.analysis.model_fitting import ModelFitting
from industrialstats.analysis.diagnostics import ModelDiagnostics

mf = ModelFitting(df.assign(B=[1, 0, 1, 0]), response_column="y")
fit = mf.stepwise_selection()

# Model diagnostics
md = ModelDiagnostics(fit["model"])
summary = md.assumption_tests()
```

## Mathematical Background
The package implements classical inferential statistics:

- **ANOVA F-statistic**: :math:`F = \frac{\text{MS}_{\text{Treatment}}}{\text{MS}_{\text{Error}}}` where mean squares are derived from sums of squares and degrees of freedom.
- **Power analysis** uses noncentral F distributions to solve for sample sizes given effect sizes.
- **Stepwise selection** iteratively adds terms with :math:`p < \alpha_{in}` and removes terms with :math:`p > \alpha_{out}` to balance model fit and parsimony.
- **Random-effects models** assume observation-level responses follow
  :math:`y_{ij} = \mu + b_i + \epsilon_{ij}`, where :math:`b_i \sim N(0, \sigma_b^2)`
  represents subject-level variation and :math:`\epsilon_{ij}` is residual error.
- **Correlated errors** can be modeled with an AR(1) structure having covariance
  :math:`\sigma^2 \rho^{|i-j|}` to capture temporal or spatial dependence.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
3. Fisher, R. A. (1925). *Statistical Methods for Research Workers*.
4. Laird, N. M., & Ware, J. H. (1982). "Random-effects models for longitudinal data." *Biometrics*.
