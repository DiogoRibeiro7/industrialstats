# Analysis Module

The analysis package provides tools for evaluating experimental results.

## Key Classes
- `ANOVAAnalysis`: fits linear models and computes ANOVA tables.
- `PowerAnalysis`: performs prospective and retrospective power calculations.
- `EffectsAnalysis`: estimates main and interaction effects with visualization helpers.
- `ModelFitting`: utilities for hierarchical model fitting and validation.

## Usage
```python
from doe_python.analysis.anova import ANOVAAnalysis
import pandas as pd

analysis = ANOVAAnalysis(data=df, response_column="y")
model = analysis.fit_model("y ~ A * B")
table = analysis.anova_table_calculation()
```

## Mathematical Background
Methods align with classical ANOVA and regression theory using `statsmodels` and `scipy` for statistical
testing and effect estimation.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
