# Utilities Module

Provides helper classes and functions used across the DOE Python project.

## Key Components

- `DesignValidator`: routines for validating factors and design matrices, checking confounding, and estimating statistical power.
- `DataSimulator`: realistic response simulation supporting interactions and multiple noise/response models.
- `export`: helpers for exporting designs to common formats.
- `transforms`: basic data transformations such as centering and standardization.
- `performance`: profiling utilities for identifying bottlenecks in design generation.

## Usage Example

```python
from doe_python.utils.data_generation import DataSimulator
sim = DataSimulator(seed=42)
response = sim.simulate_factorial_response(design_matrix, noise_level=0.5)

from doe_python.utils.performance import profile_function
profile_stats = profile_function(design.generate_design)
```

## References

- Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed.
- Box, G.E.P., Hunter, J.S., & Hunter, W.G. (2005). *Statistics for Experimenters*, 2nd ed.
