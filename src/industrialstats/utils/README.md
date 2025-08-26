# Utilities Module

Provides helper classes and functions used across the industrialstats project.

## Key Components

- `DesignValidator`: routines for validating factors and design matrices, checking confounding, and estimating statistical power.
- `DataSimulator`: realistic response simulation supporting interactions, heteroskedastic and autocorrelated noise, process drift, missing data patterns, and multi-response generation.
- `export`: helpers for exporting designs to common formats.
- `transforms`: basic data transformations such as centering and standardization.
- `performance`: profiling utilities for identifying bottlenecks in design generation.
- `efficiency`: D-, A-, G-, and I-efficiency calculators, variance inflation
  factors, and design power estimation with simple plotting helpers.

## Usage Example

```python
import numpy as np
from industrialstats.utils.data_generation import DataSimulator
from industrialstats.utils.efficiency import d_efficiency, plot_efficiencies

sim = DataSimulator(seed=42)
response = sim.simulate_factorial_response(design_matrix, noise_level=0.5)

# simulate two correlated responses with 0.8 correlation
responses = sim.simulate_correlated_responses(
    design_matrix,
    main_effects_list=[{"A": 1}, {"A": -1}],
    cov=np.array([[1, 0.8], [0.8, 1]]),
)

from industrialstats.utils.performance import profile_function
profile_stats = profile_function(design.generate_design)

# compute and visualise design efficiencies
effs = {"candidate": d_efficiency(design_matrix)}
ax = plot_efficiencies(effs)
```

### Advanced Example: AR(1) Noise and Missing Data

```python
from industrialstats.utils.data_generation import DataSimulator
from industrialstats.utils.validation import DesignValidator

sim = DataSimulator(seed=7)
Y = sim.simulate_factorial_response(
    design_matrix,
    main_effects={"A": 2.0},
    interactions={"A:B": -1.0},
    noise_level=1.0,
    ar1_rho=0.6,
    missing_rate=0.1,
)

issues = DesignValidator.validate_design_matrix(design_matrix)
print(issues)
```

The AR(1) process assumes :math:`\epsilon_i = \rho \epsilon_{i-1} + u_i` with
\(u_i \sim N(0, \sigma^2(1-\rho^2))\). Missing responses are inserted at random
positions to mimic data collection failures, and the validation report lists any
rows containing missing values or out-of-range factor levels.

## Mathematical Background
- **D-efficiency** measures the generalized variance of parameter estimates and is proportional to
  :math:`\left(\det(X^\top X)^{1/p}/n\right)` where :math:`p` is the number of parameters and :math:`n` the run count.
- **A-efficiency** minimizes average variance with
  :math:`p/\operatorname{tr}\big((X^\top X)^{-1}\big)`.
- **G-efficiency** bounds prediction variance via the maximum diagonal element of
  :math:`X(X^\top X)^{-1}X^\top`.
- **I-efficiency** uses the mean of those diagonal elements to assess overall prediction precision.
- **DataSimulator** supports noise structures such as heteroskedastic variance
  :math:`\sigma_i^2 = \sigma^2(1 + \lambda x_i)` and AR(1) correlation
  :math:`\operatorname{Cov}(\epsilon_i, \epsilon_j) = \sigma^2 \rho^{|i-j|}` to mirror process drift and temporal dependence.

## References

- Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed.
- Box, G.E.P., Hunter, J.S., & Hunter, W.G. (2005). *Statistics for Experimenters*, 2nd ed.
