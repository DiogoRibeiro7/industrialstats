# industrialstats Roadmap

This roadmap describes the path from the current pre-1.0 package to a statistically trustworthy and maintainable Design of Experiments library.

The previous roadmap was organized as a week-by-week greenfield implementation plan. That no longer reflects the repository: many advanced methods already exist, while several important correctness and validation issues remain. The roadmap is therefore now organized by **technical priority and release gate**, not by elapsed calendar time.

## Guiding principles

1. **Correctness before breadth**
   - A statistically mislabelled method is worse than a missing one.
   - Mathematical properties must be tested directly where possible.

2. **Independent validation**
   - Major methods should be checked against published examples, hand calculations, or trusted external implementations.
   - Shape/run-count tests are necessary but not sufficient.

3. **Transparent semantics**
   - DOE terminology such as effect, resolution, alias, block, whole plot, and optimality criterion must map to standard statistical definitions.

4. **Structured operational exceptions**
   - DataExcept will be the preferred exception framework for data-loading, schema, transformation, import/export, and other external operational boundaries.
   - Mathematical precondition failures should not be wrapped mechanically when a native numerical or domain-specific error is clearer.

5. **Reproducibility**
   - All randomized algorithms should provide deterministic seeded execution.
   - Tests should exercise reproducibility guarantees.

6. **Narrow public claims**
   - Documentation must distinguish implemented, experimental, partial, and planned capabilities.

---

# Current baseline

The package already includes substantial functionality:

- full factorial designs;
- regular two-level fractional factorial designs with generator parsing, resolution, alias structures, minimum-aberration search, and foldover options;
- CRD and RCBD;
- Plackett-Burman screening designs;
- a provisional DefinitiveScreeningDesign implementation;
- central composite and Box-Behnken response-surface designs;
- steepest ascent, ridge analysis, canonical analysis, and multiple-response response-surface optimization;
- D-, A-, G-, and I-optimal coordinate-exchange designs;
- basic split-plot generation;
- simplex-lattice mixture designs;
- ANOVA, mixed-effects modelling, contrasts, multiple comparisons, diagnostics, effects analysis, and power analysis;
- plotting and export utilities;
- statistical validation tests against statsmodels, hand calculations, Monte Carlo recovery, and the R FrF2 catalogue.

The following roadmap assumes this codebase as the starting point.

---

# Milestone 1 — Statistical correctness hardening

**Release gate:** no method documented as standard/implemented should knowingly violate its defining DOE properties.

## 1.1 Definitive Screening Designs

**Priority: critical**

- [ ] Replace the current axial/OAT-style construction with a genuine DSD construction.
- [ ] Define supported factor counts and run-count rules explicitly.
- [ ] Verify required main-effect orthogonality properties.
- [ ] Verify main-effect versus two-factor-interaction alias properties.
- [ ] Verify quadratic estimability properties where applicable.
- [ ] Add deterministic randomization.
- [ ] Add published-reference examples.
- [ ] Add property-based tests for the design matrix.
- [ ] Keep the public status labelled experimental until these tests pass.

## 1.2 Factorial blocking

**Priority: critical**

- [ ] Remove row-index modulo blocking as the statistical blocking mechanism.
- [ ] Add explicit defining contrasts / block generators for regular two-level factorials.
- [ ] Make intended confounding visible in design metadata.
- [ ] Validate treatment/block orthogonality when appropriate.
- [ ] Reject impossible or statistically invalid block configurations.
- [ ] Add textbook examples for blocked 2^k experiments.
- [ ] Add tests that prove blocks are not accidentally confounded with main effects unless explicitly requested.

## 1.3 Canonical factorial effects

**Priority: high**

- [ ] Define one canonical effect convention for two-level factorials using orthogonal contrasts.
- [ ] Remove semantic disagreement between `FactorialDesign.calculate_effects` and `EffectsAnalysis`.
- [ ] Centralize effect computation in one implementation.
- [ ] Validate main effects, two-factor interactions, and higher-order interactions with hand-derived examples.
- [ ] Add tests with non-zero interactions to distinguish marginal factorial effects from conditional 0/1 regression coefficients.
- [ ] Document the relationship between coded regression coefficients and factorial effects.

## 1.4 General factorial model structure

**Priority: high**

- [ ] Generate interaction terms combinatorially up to arbitrary requested order.
- [ ] Generalize degrees-of-freedom decomposition beyond three-way interactions.
- [ ] Support saturated and truncated hierarchical models explicitly.
- [ ] Add tests for k >= 4 factors.
- [ ] Validate total model degrees of freedom against full factorial identities.

## 1.5 Split-plot correctness

**Priority: high**

- [ ] Treat replicated whole plots as distinct experimental units.
- [ ] Preserve restricted randomization within whole plots.
- [ ] Add explicit whole-plot and subplot identifiers.
- [ ] Implement whole-plot/subplot error-stratum analysis.
- [ ] Integrate mixed-effects modelling for correct inference.
- [ ] Add expected-mean-square tests for canonical examples.
- [ ] Add tests for multiple replicates and multiple whole-plot factors.

## 1.6 Plackett-Burman catalogue and guarantees

**Priority: medium**

- [ ] Document exactly which run sizes are currently supported.
- [ ] Expand the supported catalogue or use a general construction where feasible.
- [ ] Verify pairwise orthogonality for every supported run size.
- [ ] Add reference tables for selected designs.
- [ ] Validate foldover properties.

---

# Milestone 2 — DataExcept integration

**Release gate:** operational data failures expose structured exceptions with useful context while statistical/numerical failures preserve mathematically meaningful semantics.

DataExcept is a planned core integration for `industrialstats`.

## 2.1 Dependency and compatibility

- [ ] Add `DataExcept` as a package dependency using a compatible released version.
- [ ] Verify Python-version compatibility across the industrialstats CI matrix.
- [ ] Pin only where required by reproducibility policy; otherwise use an appropriate compatible range.
- [ ] Document the minimum DataExcept version.

## 2.2 Exception policy

Define and document a project-wide policy.

### Use DataExcept for

- [ ] dataset/file loading failures;
- [ ] missing required columns;
- [ ] dtype mismatches;
- [ ] malformed tabular schemas;
- [ ] data transformation failures;
- [ ] import/export failures;
- [ ] external serialization failures;
- [ ] wrapped lower-level data-operation failures;
- [ ] optional future network/database-backed dataset boundaries.

### Do not mechanically wrap

- [ ] invalid mathematical parameter domains where `ValueError` remains precise;
- [ ] linear-algebra singularity where `LinAlgError` or an explicit DOE error is more informative;
- [ ] unsupported statistical method choices unless a structured exception materially improves the API;
- [ ] programmer errors such as `TypeError` caused by violating the function contract.

## 2.3 Boundary migration

- [ ] Audit `datasets/`.
- [ ] Audit CSV/Excel/JSON export paths.
- [ ] Audit validation utilities.
- [ ] Audit CLI input boundaries.
- [ ] Audit response-data ingestion paths.
- [ ] Preserve original exceptions using exception chaining / DataExcept context.
- [ ] Add focused tests for structured exception attributes, not only message text.

## 2.4 Documentation

- [ ] Add a DataExcept section to API documentation.
- [ ] Add migration examples from generic errors to structured operational errors.
- [ ] Document which errors intentionally remain native.

---

# Milestone 3 — Statistical validation framework

**Release gate:** every core design family has algebraic/property tests and at least one independent reference check.

## 3.1 Reference implementations

- [ ] Extend FrF2 comparison coverage for regular fractional factorials.
- [ ] Cross-check full and fractional designs with R `DoE.base` where appropriate.
- [ ] Cross-check response-surface designs and canonical quantities with R `rsm`.
- [ ] Compare ANOVA/mixed-model results with statsmodels reference fits.
- [ ] Validate optimal-design criteria against independently computed information matrices.
- [ ] Validate mixture designs against published Cornell examples.

## 3.2 Textbook regression suite

Build a small permanent catalogue from:

- [ ] Montgomery, *Design and Analysis of Experiments*;
- [ ] Box, Hunter & Hunter, *Statistics for Experimenters*;
- [ ] Wu & Hamada, *Experiments: Planning, Analysis, and Optimization*;
- [ ] Goos & Jones, *Optimal Design of Experiments*;
- [ ] Cornell, *Experiments with Mixtures*;
- [ ] Jones & Nachtsheim DSD examples.

For each reference example, store only the minimal data and expected statistical results required for verification.

## 3.3 Property-based testing

Use Hypothesis or deterministic algebraic checks for:

- [ ] orthogonality;
- [ ] balance;
- [ ] alias equivalence;
- [ ] resolution;
- [ ] foldover transformations;
- [ ] mixture sum-to-one constraints;
- [ ] block assignment invariants;
- [ ] randomization reproducibility;
- [ ] information-matrix nonsingularity where required.

## 3.4 Monte Carlo validation

- [ ] effect-estimator unbiasedness under known factorial models;
- [ ] empirical Type I error checks for selected ANOVA workflows;
- [ ] power-calculation verification;
- [ ] response-surface coefficient recovery;
- [ ] robustness checks under mild non-normality / variance heterogeneity where documented.

---

# Milestone 4 — API and architecture cleanup

**Release gate:** a coherent public API exists and internal duplication is removed.

## 4.1 Public exports

- [ ] Export CRD from the documented public design namespace.
- [ ] Export ResponseSurfaceDesign.
- [ ] Export OptimalDesign.
- [ ] Export SplitPlotDesign.
- [ ] Export MixtureDesign.
- [ ] Decide whether top-level `industrialstats` should expose all major design classes or only stable ones.
- [ ] Mark experimental methods clearly.

## 4.2 Shared model-matrix layer

- [ ] Introduce a reusable model-term representation.
- [ ] Support main effects, interactions, polynomial terms, and hierarchical model construction.
- [ ] Reuse the layer across factorial analysis, RSM, and optimal-design algorithms.
- [ ] Centralize coding rules for continuous and categorical factors.

## 4.3 Validation layer

- [ ] Separate structural design validation from data validation.
- [ ] Avoid duplicate checks across design classes.
- [ ] Integrate DataExcept only at appropriate operational boundaries.
- [ ] Add reusable validation result objects where they improve user diagnostics.

## 4.4 Reproducible RNG policy

- [ ] Use `numpy.random.Generator` consistently.
- [ ] Avoid hidden global RNG state.
- [ ] Standardize `seed` / `random_state` conventions.
- [ ] Add reproducibility contract tests.

---

# Milestone 5 — Optimal-design hardening

## 5.1 Search algorithms

- [ ] Add Fedorov exchange.
- [ ] Consider modified Fedorov / KL exchange where justified.
- [ ] Add deterministic initialization options.
- [ ] Add seeded random-start handling.
- [ ] Consider genetic search only after deterministic algorithms are validated.

## 5.2 Model support

- [ ] General polynomial model terms.
- [ ] Quadratic response-surface models.
- [ ] Categorical-factor coding beyond simple binary 0/1 handling.
- [ ] Constrained candidate regions.

## 5.3 Criteria

- [ ] Validate D-optimality.
- [ ] Validate A-optimality.
- [ ] Validate G-optimality.
- [ ] Validate I-optimality.
- [ ] Add tests for all four criteria.
- [ ] Add custom criterion interface only after built-in semantics are stable.

## 5.4 Efficiency and diagnostics

- [ ] Standard D-efficiency definition.
- [ ] Standard A-efficiency definition.
- [ ] G-efficiency / maximum prediction variance diagnostics.
- [ ] I-efficiency / integrated prediction variance diagnostics.
- [ ] equivalence-theorem diagnostics where practical.

---

# Milestone 6 — Mixture DOE

Move from simplex-lattice generation to a complete mixture-analysis subsystem.

## 6.1 Designs

- [ ] simplex-lattice;
- [ ] simplex-centroid;
- [ ] augmented simplex-centroid;
- [ ] extreme-vertices designs;
- [ ] constrained mixtures;
- [ ] mixture-process variable designs.

## 6.2 Models

- [ ] Scheffé linear model;
- [ ] Scheffé quadratic model;
- [ ] special cubic model;
- [ ] lack-of-fit handling;
- [ ] prediction on the simplex.

## 6.3 Optimization and visualization

- [ ] constrained desirability optimization;
- [ ] ternary contours;
- [ ] response surfaces over the simplex;
- [ ] feasible-region visualization.

---

# Milestone 7 — Additional classical designs

Add only after correctness and validation infrastructure is mature.

## 7.1 Blocking and restricted randomization

- [ ] Latin-square design as a first-class class rather than an RCBD helper;
- [ ] Graeco-Latin squares;
- [ ] balanced incomplete block designs;
- [ ] partially balanced incomplete block designs where justified;
- [ ] strip-plot designs;
- [ ] split-split-plot designs;
- [ ] nested designs.

## 7.2 Robust parameter design

- [ ] Taguchi orthogonal arrays;
- [ ] control/noise-factor separation;
- [ ] inner/outer arrays;
- [ ] signal-to-noise ratios;
- [ ] robust parameter optimization;
- [ ] explicit documentation distinguishing Taguchi methods from classical factorial/RSM approaches.

---

# Milestone 8 — Computer experiments and space-filling designs

## 8.1 Space-filling designs

- [ ] Latin hypercube sampling;
- [ ] maximin Latin hypercubes;
- [ ] correlation-reduced Latin hypercubes;
- [ ] Sobol / low-discrepancy designs where they fit the package scope;
- [ ] maximin distance designs.

## 8.2 Surrogate modelling

- [ ] Gaussian-process response surfaces;
- [ ] kriging diagnostics;
- [ ] prediction uncertainty;
- [ ] sequential design criteria.

## 8.3 Sequential computer experiments

- [ ] expected improvement;
- [ ] uncertainty sampling;
- [ ] integrated variance reduction;
- [ ] constrained sequential design.

This milestone should remain separate from classical DOE internally even if the user-facing API shares common factor/design abstractions.

---

# Milestone 9 — Sequential and adaptive experimentation

- [ ] design augmentation APIs;
- [ ] foldover as a general augmentation operation;
- [ ] sequential RSM workflows;
- [ ] adaptive screening-to-optimization workflows;
- [ ] Bayesian optimal design where mathematically justified;
- [ ] interim-analysis/sequential-testing support only with explicit control of error rates.

---

# Milestone 10 — Documentation and user experience

## 10.1 Documentation architecture

- [ ] API reference generated from the stable public API;
- [ ] mathematical background pages;
- [ ] design-selection guide;
- [ ] assumptions and limitations for every design family;
- [ ] DataExcept exception guide;
- [ ] reproducibility guide.

## 10.2 Tutorials

Planned notebook sequence:

1. introduction to DOE;
2. full factorials and interactions;
3. fractional factorials, aliasing, and foldover;
4. blocking and RCBD;
5. screening designs;
6. response-surface methodology;
7. split-plot experiments;
8. optimal designs;
9. mixture experiments;
10. robust parameter design;
11. computer experiments.

## 10.3 Domain examples

- [ ] manufacturing process optimization;
- [ ] pharmaceutical formulation/process development;
- [ ] agricultural blocked experiments;
- [ ] quality engineering;
- [ ] web/product experiments;
- [ ] simulation/computer experiments.

---

# Milestone 11 — Quality engineering and release readiness

## 11.1 Tooling

- [ ] replace legacy lint configuration with a single modern Ruff-based policy;
- [ ] enable strict or near-strict mypy incrementally;
- [ ] remove `ignore_errors = true` from mypy configuration;
- [ ] define a coverage floor based on meaningful tested code;
- [ ] package build verification in CI;
- [ ] dependency/security scanning.

## 11.2 CI matrix

- [ ] supported Python versions;
- [ ] Linux;
- [ ] Windows;
- [ ] macOS where practical;
- [ ] documentation build;
- [ ] package install test from built wheel;
- [ ] statistical-reference test subset.

## 11.3 Performance

- [ ] factorial generation benchmarks;
- [ ] fractional-generator search benchmarks;
- [ ] optimal-design exchange benchmarks;
- [ ] response-surface optimization benchmarks;
- [ ] memory checks for large candidate sets.

---

# Milestone 12 — Release path

## v0.2 — Correctness release

Target:

- corrected DSD;
- corrected factorial blocking;
- unified effects semantics;
- generalized factorial DF/interactions;
- split-plot replication correction;
- first DataExcept integration;
- expanded statistical validation.

## v0.3 — Analysis and architecture release

Target:

- coherent public API;
- shared model-matrix layer;
- optimal-design hardening;
- mixture-model analysis;
- improved CLI and documentation.

## v0.4 — Classical DOE breadth

Target:

- incomplete block designs;
- expanded restricted-randomization designs;
- robust/Taguchi design family.

## v0.5 — Computer experiments

Target:

- Latin hypercube and space-filling designs;
- Gaussian-process surrogate modelling;
- sequential computer-experiment criteria.

## v1.0 — Stable statistical contract

`1.0` should mean more than API stability. The following conditions should hold:

- [ ] every documented stable design family has independent statistical validation;
- [ ] known statistical limitations are documented explicitly;
- [ ] core APIs are stable and typed;
- [ ] operational boundaries use structured exceptions consistently;
- [ ] supported Python versions and release artifacts are tested in CI;
- [ ] documentation includes design-selection and assumptions guidance;
- [ ] no experimental method is presented as statistically validated without evidence.

---

# Validation matrix

The following matrix should be maintained as functionality matures.

| Area | Unit tests | Algebra/property tests | Independent reference | Monte Carlo | Status target |
| --- | --- | --- | --- | --- | --- |
| Full factorial | Yes | Expand | Add textbook/R | Yes | Stable |
| Fractional factorial | Yes | Yes | FrF2 | Add | Stable |
| CRD | Yes | Expand | statsmodels/textbook | Add | Stable |
| RCBD | Yes | Expand | textbook | Add | Stable |
| Plackett-Burman | Yes | Orthogonality | Add catalogue reference | Optional | Stable |
| Definitive screening | Minimal | Required | Required | Optional | Experimental until complete |
| RSM | Yes | Expand | R rsm/textbook | Add | Stable |
| Optimal design | Basic | Required | Independent criterion calculations | Optional | Beta |
| Split-plot | Basic | Required | Mixed-model/textbook | Add | Beta |
| Mixture | Basic | Sum-to-one | Cornell/reference software | Add | Beta |

---

# Deferred ideas

These are valid future directions but should not displace the correctness milestones above:

- dashboard/web UI;
- plugin architecture;
- Bayesian model averaging;
- genetic algorithms for design search;
- animation-heavy visualization;
- cloud execution;
- automatic report generation;
- domain-specific wrappers.

They can be revisited once the statistical core is trustworthy and the public API is coherent.
