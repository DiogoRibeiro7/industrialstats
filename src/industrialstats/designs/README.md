# Design Module

The design package contains classes for generating and managing experimental designs.

## Key Classes
- `FactorialDesign`: builds full factorial designs with optional center points, regular treatment blocking, and randomization.
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

### Plackett–Burman run-size catalogue

`PlackettBurmanDesign` selects the smallest implemented Hadamard order `N`
with `N > k`, where `k` is the number of factors. The implemented catalogue is
formed from the Sylvester family together with the classical 12- and 20-run
base constructions and all of their powers-of-two doublings:

\[
N \in \{2^m,\;12\cdot 2^m,\;20\cdot 2^m\},\qquad N\ge 4.
\]

For example, the supported orders up to 80 runs are

```text
4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80
```

The public helpers `supported_run_sizes(max_runs)`,
`run_size_for_factors(k)`, and `run_size()` expose this selection explicitly.
A factor count that falls between two catalogue orders uses the next supported
order rather than failing. Thus 24 factors use a 32-run design.

For every generated design with factor matrix `X`, main-effect orthogonality is
validated by

\[
X^\mathsf{T}X = NI_k.
\]

### Advanced Example: Regular Factorial Blocking

For a two-level full factorial, blocks must be defined by treatment contrasts,
not by splitting rows into arbitrary chunks. In a \(2^3\) experiment divided
into two blocks, using \(ABC\) as the block generator gives

\[
I = ABC\,b,
\]

where \(b\) denotes the block contrast. The three-factor interaction is
therefore confounded with blocks while all main effects and two-factor
interactions remain clear of the block effect.

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign

factors = [
    Factor("A", [-1, 1]),
    Factor("B", [-1, 1]),
    Factor("C", [-1, 1]),
]

design = FactorialDesign(
    factors,
    blocks=2,
    block_generators=["A*B*C"],
    seed=0,
)
X = design.generate_design()
print(design.block_structure())
```

If `block_generators` is omitted, `FactorialDesign` chooses a deterministic set
of independent defining contrasts. `block_structure()` reports both the
independent generators and the complete defining-contrast subgroup, making the
treatment effects sacrificed to blocking explicit.

Regular factorial blocking currently has deliberately narrow semantics:

- all treatment factors must have exactly two levels;
- the number of blocks must be a power of two;
- center points are not silently assigned to treatment blocks;
- main-effect confounding is rejected by default;
- randomization is performed independently inside each block.

For example, four blocks require two independent generators. If the chosen
generators are `A*B` and `A*C`, their product `B*C` is also in the block
defining subgroup, so all three two-factor interactions are confounded with
block degrees of freedom. A generator such as `A` is rejected unless
`allow_main_effect_confounding=True` is supplied explicitly.

Use `RandomizedCompleteBlockDesign` when the scientific problem is treatment
comparison across an observed nuisance factor such as day or batch. Regular
factorial block generators solve the different problem of partitioning a
\(2^k\) treatment design while knowingly sacrificing selected interactions.

### Saturated and truncated factorial models

`FactorialDesign` generates model terms combinatorially rather than stopping at
a fixed interaction order. Calling `model_terms()` returns the saturated
hierarchy through the interaction involving every factor. Supplying
`max_order=m` returns the hierarchical truncation containing every term of
orders `1, ..., m`.

```python
factors = [
    Factor("A", [-1, 1]),
    Factor("B", [-1, 1]),
    Factor("C", [-1, 1]),
    Factor("D", [-1, 1]),
]
design = FactorialDesign(factors, replicates=2, randomize=False)

saturated = design.model_structure()
second_order = design.model_structure(max_order=2)
```

For a term involving factors in a set \(S\), the degrees of freedom are

\[
\nu_S = \prod_{j\in S}(L_j-1),
\]

where \(L_j\) is the number of levels of factor \(j\). Therefore a saturated
full factorial satisfies

\[
\sum_{\varnothing\neq S}\nu_S
=
\prod_j L_j - 1.
\]

`degrees_of_freedom()` uses the saturated hierarchy by default. With a finite
`max_order`, omitted higher-order treatment variation remains in the returned
`Error` degrees of freedom together with replication and center-point residual
degrees of freedom. `model_structure()` reports whether the requested model is
saturated, its terms, and the model/error/total degree-of-freedom decomposition.

## Mathematical Background
- **Factorial designs** exploit the full combination of factor levels, yielding an orthogonal design matrix with information on all main effects and interactions.
- **Regular factorial blocks** use independent treatment words as block generators. With \(2^p\) blocks, the non-identity products of the \(p\) generators form a subgroup of size \(2^p-1\); those treatment contrasts are confounded with the block degrees of freedom.
- **CRD vs. RCBD efficiency**: relative efficiency is computed as
  :math:`(\sigma_e^2 + \sigma_b^2)/\sigma_e^2`, where :math:`\sigma_b^2` is block variance.
- **Screening designs** leverage Hadamard matrices to ensure column orthogonality while minimizing runs.
- **Run count** for a CRD equals :math:`t \times r` where :math:`t` is the number of treatments and :math:`r` the replicates.
- **Alias structure** emerges when columns of the model matrix lie in the null space of the design matrix. If :math:`Xc = 0`
  for some coefficient vector :math:`c`, the effects indicated by the nonzero entries of :math:`c` are perfectly confounded.
- **Variance decomposition** gauges how much of each factor column's variability is explained by the remaining columns using
  :math:`R^2 = 1 - \frac{\text{SS}_{\text{res}}}{\text{SS}_{\text{tot}}`.

### Split-Plot Designs

`SplitPlotDesign` represents each replicated whole plot as a distinct experimental unit and randomizes in two stages: whole plots are shuffled as intact units, then subplot runs are shuffled independently within each whole plot.

For a balanced complete split-plot with `a` whole-plot treatment combinations, `b` subplot treatment combinations, and `r` independent whole-plot replicates, `SplitPlotAnalysis` uses the random-intercept model

\[
y = X\beta + u_{\mathrm{WP}} + \varepsilon,
\]

with

\[
u_{\mathrm{WP}} \sim N(0,\sigma_{\mathrm{WP}}^2),
\qquad
\varepsilon \sim N(0,\sigma_e^2).
\]

The two residual strata have degrees of freedom

\[
\nu_{\mathrm{WP}} = a(r-1),
\qquad
\nu_{\mathrm{SP}} = a(r-1)(b-1),
\]

and the corresponding balanced-design expected mean squares are

\[
E(MS_{\mathrm{WP}})=\sigma_e^2+b\sigma_{\mathrm{WP}}^2,
\qquad
E(MS_{\mathrm{SP}})=\sigma_e^2.
\]

`SplitPlotAnalysis.fit_mixed_model()` fits the complete categorical treatment model with a random intercept grouped by `WholePlot`, after validating that every whole plot contains exactly one replicate, one whole-plot treatment combination, and one complete subplot factorial.

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
