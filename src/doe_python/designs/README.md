# Design Module

The design package contains classes for generating and managing experimental designs.

## Key Classes
- `FactorialDesign`: builds full factorial designs with optional center points and randomization.
- `FractionalFactorialDesign`: creates two-level fractional factorials using generator strings.
- `ResponseSurfaceDesign`: supports central composite and Box–Behnken designs for optimization.
- `RandomizedCompleteBlockDesign`: implements block designs with seedable randomization.

## Usage
```python
from doe_python.designs.factorial import FactorialDesign, Factor

factors = [Factor("A", [-1, 1], "continuous"), Factor("B", [-1, 1], "continuous")]
design = FactorialDesign(factors, replicates=2)
df = design.generate_design()
```

## Mathematical Background
Design generation follows classical DOE texts such as Montgomery (2017) and Box et al. (2005),
providing support for orthogonality, blocking, and alias structure analysis.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
