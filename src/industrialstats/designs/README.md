# Design Module

The design package contains classes for generating and managing experimental designs.

## Key Classes
- `FactorialDesign`: builds full factorial designs with optional center points and randomization.
- `FractionalFactorialDesign`: creates two-level fractional factorials using generator strings.
- `CompletelyRandomizedDesign`: assigns treatments to experimental units without blocking.
- `RandomizedCompleteBlockDesign`: implements block designs with seedable randomization.
- `PlackettBurmanDesign` and `DefinitiveScreeningDesign`: screening designs for identifying important factors.
- `ResponseSurfaceDesign`: supports central composite and Box–Behnken designs for optimization.
- `SplitPlotDesign`: handles hard-to-change whole-plot factors with restricted sub-plot randomization.
- `MixtureDesign`: generates simplex-lattice designs for mixture experiments.

## Usage Examples
```python
from industrialstats.designs.base import Factor
from industrialstats.designs.crd import CompletelyRandomizedDesign
from industrialstats.designs.screening import PlackettBurmanDesign

design = CompletelyRandomizedDesign(["T1", "T2"], replicates=3, seed=42)
design_matrix = design.generate_design()

screen = PlackettBurmanDesign([Factor("A", [1, -1]), Factor("B", [1, -1])], seed=7)
pb_matrix = screen.generate_design()

# Multi-response data sheet
crd_multi = CompletelyRandomizedDesign(
    ["T1", "T2"], replicates=2, seed=1, response_variables=["y1", "y2"]
)
sheet = crd_multi.create_data_collection_sheet()
```

### Advanced Example: Alias Matrix and Blocking

```python
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.utils.validation import DesignValidator

factors = [Factor("A", [-1, 1]), Factor("B", [-1, 1]), Factor("C", [-1, 1])]
design = FactorialDesign(factors, blocks=2, seed=0)
X = design.generate_design()

# Enumerate alias structure via null-space analysis
aliases = DesignValidator.check_confounding(X)

for effect, aliased in aliases.items():
    print(effect, "<->", aliased)
```

Blocking divides the full design into two replicate groups while preserving
orthogonality. Aliasing is detected by computing a basis for the null space of
the model matrix :math:`X` and mapping the nonzero coefficients to aliased
effects. Confounded terms share identical columns in :math:`X` and thus cannot
be estimated independently.

## Mathematical Background
- **Factorial designs** exploit the full combination of factor levels, yielding an orthogonal design matrix with information on all main effects and interactions.
- **CRD vs. RCBD efficiency**: relative efficiency is computed as
  :math:`(\sigma_e^2 + \sigma_b^2)/\sigma_e^2`, where :math:`\sigma_b^2` is block variance.
- **Screening designs** leverage Hadamard matrices to ensure column orthogonality while minimizing runs.
- **Run count** for a CRD equals :math:`t \times r` where :math:`t` is the number of treatments and :math:`r` the replicates.
- **Alias structure** emerges when columns of the model matrix lie in the null space of the design matrix. If :math:`Xc = 0`
  for some coefficient vector :math:`c`, the effects indicated by the nonzero entries of :math:`c` are perfectly confounded.
- **Variance decomposition** gauges how much of each factor column's variability is explained by the remaining columns using
  :math:`R^2 = 1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}}`.

### Split-Plot Designs
With :math:`g` whole-plot factors and :math:`m` sub-plot factors, a split-plot design is constructed by nesting a full
factorial in the sub-plot factors within each combination of whole-plot levels. The expected mean squares for the model
\(y_{ijk} = \mu + W_i + S_j + (WS)_{ij} + \epsilon_{ijk}\) are

\[
\begin{aligned}
E[MS_W] &= \sigma_e^2 + s r \sigma_W^2,\\
E[MS_S] &= \sigma_e^2 + r \sigma_S^2,
\end{aligned}
\]

where :math:`\sigma_W^2` and :math:`\sigma_S^2` denote whole-plot and sub-plot variances and :math:`r` is the number of
replicates per sub-plot treatment combination. See also `SplitPlotDesign` in `advanced.py`.

### Mixture Designs
For a :math:`q`-component mixture, a simplex-lattice design of degree :math:`m` places points at barycentric coordinates
\((m_1/m, \ldots, m_q/m)\) with :math:`\sum_i m_i = m`. The number of design points is

\[
n = \binom{q + m - 1}{m},
\]

providing a polynomial model constrained by :math:`\sum_i x_i = 1`. Extensions to higher dimensions simply increase
\(q\) and maintain the same combinatorial formula. See `MixtureDesign` in `advanced.py` for implementation details.

## References
1. Montgomery, D. C. (2017). *Design and Analysis of Experiments*.
2. Box, G. E. P., Hunter, J. S., & Hunter, W. G. (2005). *Statistics for Experimenters*.
3. Jones, B., Nachtsheim, C. (2011). "A Class of Three-Level Designs for Definitive Screening in the Presence of Second-Order Effects."
4. Goos, P., & Jones, B. (2011). *Optimal Design of Experiments: A Case Study Approach*.
5. Cornell, J. A. (2011). *Experiments with Mixtures*.
