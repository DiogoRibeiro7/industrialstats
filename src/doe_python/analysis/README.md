# Analysis Module

The analysis package provides tools for evaluating experimental results.

## Key Classes
- `ANOVAAnalysis`: fits linear models and computes ANOVA tables.
- `PowerAnalysis`: performs prospective and retrospective power calculations.
- `EffectsAnalysis`: estimates main and interaction effects with visualization helpers.
- `ModelFitting`: utilities for hierarchical model fitting and validation.

## Usage
```python
import pandas as pd
from doe_python.analysis.anova import ANOVAAnalysis

df = pd.DataFrame({"y": [5, 6, 7, 8], "A": ["a", "a", "b", "b"]})
analysis = ANOVAAnalysis(data=df, response_column="y")
analysis.fit_model("y ~ A")
table = analysis.anova_table_calculation()
```

## Mathematical Background
The package implements classical inferential statistics:

- **ANOVA F-statistic**: :math:`F = \frac{\text{MS}_{\text{Treatment}}}{\text{MS}_{\text{Error}}}` where mean squares are derived from sums of squares and degrees of freedom.
- **Power analysis** uses noncentral F distributions to solve for sample sizes given effect sizes.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
3. Fisher, R. A. (1925). *Statistical Methods for Research Workers*.
