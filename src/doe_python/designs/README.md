# Design Module

The design package contains classes for generating and managing experimental designs.

## Key Classes
- `FactorialDesign`: builds full factorial designs with optional center points and randomization.
- `FractionalFactorialDesign`: creates two-level fractional factorials using generator strings.
- `CompletelyRandomizedDesign`: assigns treatments to experimental units without blocking.
- `RandomizedCompleteBlockDesign`: implements block designs with seedable randomization.
- `PlackettBurmanDesign` and `DefinitiveScreeningDesign`: screening designs for identifying important factors.
- `ResponseSurfaceDesign`: supports central composite and Box–Behnken designs for optimization.

## Usage Examples
```python
from doe_python.designs.base import Factor
from doe_python.designs.crd import CompletelyRandomizedDesign
from doe_python.designs.screening import PlackettBurmanDesign

design = CompletelyRandomizedDesign(["T1", "T2"], replicates=3, seed=42)
design_matrix = design.generate_design()

screen = PlackettBurmanDesign([Factor("A", [1, -1]), Factor("B", [1, -1])], seed=7)
pb_matrix = screen.generate_design()
```

## Mathematical Background
- **Factorial designs** exploit the full combination of factor levels, yielding an orthogonal design matrix with information on all main effects and interactions.
- **CRD vs. RCBD efficiency**: relative efficiency is computed as
  :math:`(\sigma_e^2 + \sigma_b^2)/\sigma_e^2`, where :math:`\sigma_b^2` is block variance.
- **Screening designs** leverage Hadamard matrices to ensure column orthogonality while minimizing runs.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
3. Jones, B., Nachtsheim, C. (2011). "A Class of Three-Level Designs for Definitive Screening in the Presence of Second-Order Effects."
