# industrialstats Roadmap

This roadmap describes the path from the current pre-1.0 package to a statistically trustworthy, broad, and maintainable industrial Design of Experiments library for Python.

The package is no longer a greenfield DOE implementation. It already contains substantial classical design generation, statistical analysis, diagnostics, power calculations, optimization, visualizations, and operational tooling. The roadmap is therefore organized by **technical priority, statistical release gate, and product scope**, not by elapsed calendar time.

The strategic objective is not to become a collection of unrelated design-matrix generators. `industrialstats` should provide a coherent experimental workflow:

\[
\text{plan}
\rightarrow
\text{design}
\rightarrow
\text{randomize and execute}
\rightarrow
\text{analyse}
\rightarrow
\text{diagnose}
\rightarrow
\text{optimize}
\rightarrow
\text{confirm}
\]

That end-to-end industrial workflow is the package's primary differentiator.

---

# Positioning and scope

`industrialstats` should aim to be the most coherent Python package for **industrial DOE plus statistical analysis**, while interoperating with specialist scientific libraries where they are already stronger numerical foundations.

The intended positioning is:

- **classical and industrial DOE:** first-class package responsibility;
- **analysis, diagnostics, power, optimization, and confirmation:** first-class package responsibility;
- **space-filling and quasi-Monte Carlo sequences:** expose DOE-oriented APIs while reusing trusted numerical backends such as `scipy.stats.qmc` where appropriate;
- **surrogate modelling and computer experiments:** support as a distinct subsystem, without turning the package into a general uncertainty-quantification framework;
- **nonlinear/model-based optimal experimental design:** support as a specialist layer after the classical optimal-design foundation is validated;
- **general-purpose UQ, reliability, and stochastic-process modelling:** remain outside the core scope unless directly required by DOE workflows.

Breadth is useful only when semantics and validation remain explicit.

---

# Guiding principles

1. **Correctness before breadth**
   - A statistically mislabelled method is worse than a missing one.
   - Mathematical properties must be tested directly where possible.

2. **Independent validation**
   - Major methods should be checked against published examples, hand calculations, or trusted external implementations.
   - Shape/run-count tests are necessary but not sufficient.

3. **Transparent semantics**
   - DOE terminology such as effect, resolution, alias, block, whole plot, estimability, and optimality criterion must map to standard statistical definitions.

4. **Experimental-unit semantics matter**
   - Randomization restrictions, blocks, whole plots, subplots, replicates, and repeated measurements must be represented explicitly rather than inferred from row order.

5. **Structured operational exceptions**
   - DataExcept is the preferred exception framework for data-loading, schema, transformation, import/export, and other external operational boundaries.
   - Mathematical precondition failures should not be wrapped mechanically when a native numerical or domain-specific error is clearer.

6. **Reproducibility**
   - All randomized algorithms should provide deterministic seeded execution.
   - Tests should exercise reproducibility guarantees.

7. **Composable statistical objects**
   - Designs, model terms, fitted models, diagnostics, and optimization results should expose inspectable structured objects rather than opaque arrays or ad-hoc dictionaries.

8. **Narrow public claims**
   - Documentation must distinguish implemented, experimental, partial, and planned capabilities.

9. **Use strong numerical foundations instead of duplicating them**
   - Reuse SciPy, NumPy, statsmodels, and other established numerical libraries where doing so improves reliability.
   - `industrialstats` should add DOE semantics, validation, workflow, and diagnostics rather than reimplement numerical primitives without reason.

---

# Current baseline — v0.2.0

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
- DataExcept-backed operational boundaries for selected loading/export workflows;
- statistical validation tests against statsmodels, hand calculations, Monte Carlo recovery, and the R FrF2 catalogue;
- Python 3.11-3.14 support, Ruff, mypy, pytest, Hypothesis, pre-commit, and PEP 561 typing metadata.

The following roadmap assumes this codebase as the starting point.

---

# Milestone 1 — Statistical correctness hardening

**Release gate:** no method documented as stable/implemented should knowingly violate its defining DOE properties.

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
- [ ] Add tests proving blocks are not accidentally confounded with main effects unless explicitly requested.

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
- [ ] Validate total model degrees of freedom against full-factorial identities.

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

# Milestone 2 — Operational boundaries and DataExcept completion

**Release gate:** operational data failures expose structured exceptions with useful context while statistical/numerical failures preserve mathematically meaningful semantics.

DataExcept is already a runtime dependency and is used at selected external boundaries. This milestone completes and normalizes that integration.

## 2.1 Dependency and compatibility

- [x] Add DataExcept as a runtime dependency.
- [x] Document a compatible minimum/current dependency range in package metadata.
- [ ] Verify DataExcept compatibility on every supported Python version in CI.
- [ ] Add a compatibility test covering package import and representative boundary exceptions.

## 2.2 Exception policy

### Use DataExcept for

- [x] selected dataset/file loading failures;
- [x] shared CSV/Excel/JSON export failures;
- [ ] missing required columns;
- [ ] dtype mismatches;
- [ ] malformed tabular schemas;
- [ ] data transformation failures;
- [ ] additional import/export boundaries;
- [ ] wrapped lower-level data-operation failures;
- [ ] optional future network/database-backed dataset boundaries.

### Preserve native/domain errors for

- [x] mathematical parameter-domain failures where `ValueError` remains precise;
- [x] linear-algebra failures where `LinAlgError` or a DOE-specific error is clearer;
- [x] programmer errors such as `TypeError` caused by violating the function contract.

## 2.3 Boundary migration

- [ ] Complete audit of `datasets/`.
- [ ] Complete audit of CSV/Excel/JSON export paths.
- [ ] Audit validation utilities.
- [ ] Audit CLI input boundaries.
- [ ] Audit response-data ingestion paths.
- [ ] Preserve original exceptions through exception chaining/context.
- [ ] Add focused tests for structured exception attributes, not only message text.

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
- [ ] Validate space-filling metrics against SciPy/reference implementations when that subsystem lands.
- [ ] Validate model-based OED against published examples before exposing it as stable.

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
- [ ] estimability;
- [ ] foldover transformations;
- [ ] mixture sum-to-one constraints;
- [ ] block assignment invariants;
- [ ] randomization reproducibility;
- [ ] information-matrix nonsingularity where required;
- [ ] prediction-variance identities;
- [ ] space-filling bounds and discrepancy invariants where appropriate.

## 3.4 Monte Carlo validation

- [ ] effect-estimator unbiasedness under known factorial models;
- [ ] empirical Type I error checks for selected ANOVA workflows;
- [ ] power-calculation verification;
- [ ] response-surface coefficient recovery;
- [ ] split-plot inference under known variance components;
- [ ] model-based OED parameter-recovery studies;
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
- [ ] Mark experimental methods clearly in API and docs.

## 4.2 Shared model-matrix layer

- [ ] Introduce a reusable model-term representation.
- [ ] Support main effects, interactions, polynomial terms, mixture terms, and hierarchical model construction.
- [ ] Reuse the layer across factorial analysis, RSM, mixtures, and optimal-design algorithms.
- [ ] Centralize coding rules for continuous and categorical factors.
- [ ] Expose estimability/rank information from the model-matrix layer.

## 4.3 Shared design metadata

- [ ] Standardize factor metadata: name, type, units, coded levels, natural levels, bounds, and role.
- [ ] Standardize experimental-unit identifiers.
- [ ] Represent blocks, whole plots, subplots, replicates, centre points, and augmentation provenance explicitly.
- [ ] Attach randomization seed and construction metadata to generated designs.

## 4.4 Reproducible RNG policy

- [ ] Use `numpy.random.Generator` consistently.
- [ ] Avoid hidden global RNG state.
- [ ] Standardize `seed` / `random_state` conventions.
- [ ] Add reproducibility contract tests.

---

# Milestone 5 — Classical optimal-design expansion

**Release gate:** optimality criteria have mathematically verified definitions, reproducible search, and independent reference tests.

## 5.1 Search algorithms

- [ ] Add Fedorov exchange.
- [ ] Add modified Fedorov where justified.
- [ ] Add DETMAX-style search.
- [ ] Consider KL/exchange variants after the first three are validated.
- [ ] Add deterministic initialization options.
- [ ] Add seeded multi-start handling.
- [ ] Expose convergence history and stopping reason.
- [ ] Consider genetic search only after deterministic algorithms are validated.

## 5.2 Exact and approximate design semantics

- [ ] Distinguish exact n-run designs from approximate weighted designs.
- [ ] Support replicated candidate points explicitly.
- [ ] Add design weights where mathematically appropriate.
- [ ] Provide rounding/augmentation strategies from approximate to exact designs.

## 5.3 Model and candidate-region support

- [ ] General polynomial model terms.
- [ ] Quadratic response-surface models.
- [ ] Categorical-factor coding beyond binary 0/1 handling.
- [ ] Mixed categorical/continuous candidate sets.
- [ ] Constrained candidate regions.
- [ ] User-supplied model matrices with validation.

## 5.4 Criteria

Existing criteria:

- [ ] fully validate D-optimality;
- [ ] fully validate A-optimality;
- [ ] fully validate G-optimality;
- [ ] fully validate I-optimality.

Expansion:

- [ ] C-optimality for specified contrasts/linear combinations;
- [ ] E-optimality;
- [ ] V-optimality / average prediction variance on a finite region;
- [ ] consider T-optimality for discrimination between rival models;
- [ ] add a custom-criterion interface only after built-in semantics are stable.

## 5.5 Efficiency and equivalence diagnostics

- [ ] standard D-efficiency;
- [ ] standard A-efficiency;
- [ ] G-efficiency / maximum prediction-variance diagnostics;
- [ ] I/V-efficiency diagnostics;
- [ ] sensitivity-function plots;
- [ ] Kiefer-Wolfowitz equivalence-theorem diagnostics where applicable;
- [ ] robustness diagnostics for candidate-point deletion/missing runs.

---

# Milestone 6 — Mixture DOE

Move from simplex-lattice generation to a complete mixture-design and analysis subsystem.

## 6.1 Designs

- [ ] validate and stabilize simplex-lattice;
- [ ] simplex-centroid;
- [ ] augmented simplex-centroid;
- [ ] axial/check-blend points;
- [ ] extreme-vertices designs;
- [ ] lower/upper-bound constrained mixtures;
- [ ] general linear-constraint mixtures;
- [ ] mixture-process variable designs;
- [ ] optimal mixture designs on constrained regions.

## 6.2 Models

- [ ] Scheffé linear model;
- [ ] Scheffé quadratic model;
- [ ] special cubic model;
- [ ] full cubic where justified;
- [ ] mixture-process interaction models;
- [ ] lack-of-fit handling;
- [ ] prediction on the simplex/feasible region.

## 6.3 Diagnostics, optimization, and visualization

- [ ] mixture-model ANOVA/diagnostics;
- [ ] constrained desirability optimization;
- [ ] ternary contours;
- [ ] response surfaces over the simplex;
- [ ] feasible-region visualization;
- [ ] prediction-variance visualization;
- [ ] confirmation blends.

---

# Milestone 7 — Additional classical and industrial designs

Add only after correctness and validation infrastructure is mature.

## 7.1 Blocking and restricted randomization

- [ ] Latin-square design as a first-class class rather than an RCBD helper;
- [ ] Graeco-Latin squares;
- [ ] balanced incomplete block designs;
- [ ] partially balanced incomplete block designs where justified;
- [ ] resolvable block designs where useful;
- [ ] strip-plot designs;
- [ ] split-split-plot designs;
- [ ] nested designs;
- [ ] repeated-measures experimental layouts where DOE semantics are clear.

## 7.2 Response-surface breadth

- [ ] blocked central-composite designs;
- [ ] small composite designs;
- [ ] Doehlert designs;
- [ ] rotatability diagnostics;
- [ ] orthogonality diagnostics;
- [ ] lack-of-fit design augmentation;
- [ ] sequential first-order to second-order RSM workflow.

## 7.3 Robust parameter design

- [ ] Taguchi orthogonal-array catalogue;
- [ ] validate supported OA run/factor-level structures;
- [ ] control/noise-factor separation;
- [ ] inner/outer arrays;
- [ ] signal-to-noise ratios with explicit conventions;
- [ ] robust parameter optimization;
- [ ] confirmation runs;
- [ ] explicit documentation distinguishing Taguchi methods from classical factorial/RSM approaches.

---

# Milestone 8 — Computer experiments and space-filling designs

**Release gate:** computer-experiment design APIs expose clear geometric criteria and reproducible numerical backends, without duplicating trusted QMC implementations unnecessarily.

## 8.1 Latin-hypercube designs

- [ ] standard Latin hypercube sampling;
- [ ] orthogonal-array LHS where supported;
- [ ] maximin Latin hypercubes;
- [ ] correlation-reduced Latin hypercubes;
- [ ] centered/optimized LHS variants;
- [ ] maximum-projection criteria where justified;
- [ ] scaling from the unit hypercube to factor bounds.

Where practical, use `scipy.stats.qmc` as the numerical backend and add `industrialstats` factor semantics, reproducibility contracts, diagnostics, and design metadata.

## 8.2 Low-discrepancy and geometric designs

- [ ] Sobol sequences;
- [ ] Halton sequences;
- [ ] optional additional low-discrepancy sequences only when a clear use case exists;
- [ ] maximin distance designs;
- [ ] minimax/fill-distance designs;
- [ ] projection-quality diagnostics;
- [ ] constrained-region sampling.

## 8.3 Space-filling diagnostics

- [ ] centered discrepancy;
- [ ] wrap-around discrepancy where useful;
- [ ] separation distance;
- [ ] fill distance;
- [ ] pairwise-correlation diagnostics;
- [ ] one- and two-dimensional projection diagnostics;
- [ ] pairwise-distance distributions;
- [ ] compare competing designs on common criteria.

## 8.4 Design augmentation

- [ ] augment an existing LHS without silently destroying stratification where supported;
- [ ] nested/sliced designs where justified;
- [ ] batch space-filling augmentation;
- [ ] constrained augmentation around unavailable/failed runs.

---

# Milestone 9 — Surrogate modelling and sequential computer experiments

Keep this subsystem distinct from classical DOE internally, even if the user-facing API shares factor and design abstractions.

## 9.1 Gaussian-process / kriging layer

- [ ] Gaussian-process response surfaces;
- [ ] configurable covariance kernels appropriate for DOE use;
- [ ] trend/mean-function handling;
- [ ] kriging diagnostics;
- [ ] cross-validation;
- [ ] prediction uncertainty;
- [ ] numerical conditioning diagnostics;
- [ ] explicit separation between deterministic-simulator nugget and observational noise.

## 9.2 Sequential acquisition criteria

- [ ] expected improvement;
- [ ] probability of improvement where justified;
- [ ] uncertainty sampling / maximum posterior variance;
- [ ] integrated variance reduction / IMSE-style criteria;
- [ ] batch acquisition;
- [ ] constrained sequential design;
- [ ] multi-response sequential design only after single-response behaviour is validated.

## 9.3 Surrogate-aware validation

- [ ] benchmark functions with known optima;
- [ ] coverage/calibration of predictive intervals;
- [ ] sequential-regret studies where appropriate;
- [ ] sensitivity to kernel and hyperparameter fitting;
- [ ] deterministic reproducibility of acquisition optimization.

---

# Milestone 10 — Nonlinear and model-based optimal experimental design

This is a specialist layer and should not block the classical DOE roadmap.

## 10.1 Information-matrix abstraction

For models of the form

\[
y = f(x, \theta) + \varepsilon,
\]

support design construction from parameter sensitivities rather than only fixed polynomial model matrices.

- [ ] Fisher-information abstraction;
- [ ] analytic Jacobian/sensitivity interface;
- [ ] finite-difference sensitivity fallback;
- [ ] optional automatic-differentiation integration only if dependency policy remains reasonable;
- [ ] prior information matrices;
- [ ] parameter scaling/identifiability diagnostics.

## 10.2 Local and robust criteria

- [ ] local D-optimality;
- [ ] local A-optimality;
- [ ] local E-optimality;
- [ ] local V/I-style prediction criteria where defined;
- [ ] parameter-subset / Ds-style criteria where useful;
- [ ] robust design across parameter scenarios;
- [ ] Bayesian/pseudo-Bayesian expected-criterion designs.

## 10.3 Dynamic models

- [ ] ODE-model experimental design interface;
- [ ] time-point selection;
- [ ] input/control-profile candidate design where tractable;
- [ ] repeated/sampling-time constraints;
- [ ] parameter-estimation validation studies.

DAE/PDE-specific OED should remain deferred until ODE support is statistically and computationally mature.

---

# Milestone 11 — Sequential and adaptive physical experimentation

## 11.1 General design augmentation

- [ ] augmentation API shared across classical designs;
- [ ] foldover as a general augmentation operation;
- [ ] centre/star-point augmentation with provenance;
- [ ] D/A/I-optimal augmentation of an existing design;
- [ ] augmentation under unavailable candidate combinations;
- [ ] replacement strategy for failed/missing runs.

## 11.2 Screening-to-optimization workflows

- [ ] screening design -> active-factor selection;
- [ ] foldover/augmentation when aliasing remains consequential;
- [ ] first-order RSM / steepest ascent;
- [ ] second-order RSM around the operating region;
- [ ] confirmation experiments at the predicted optimum.

The package should expose this workflow without automatically hiding the statistical decisions from the user.

## 11.3 Sequential inference

- [ ] simulation-based power recalculation for augmentation;
- [ ] adaptive design rules with documented assumptions;
- [ ] interim-analysis/sequential-testing support only with explicit control of error rates;
- [ ] avoid optional-stopping APIs that imply ordinary fixed-design p-values remain valid.

---

# Milestone 12 — Industrial experiment workflow and decision support

This milestone is strategically important: it is where `industrialstats` should differ most clearly from pure design-generator libraries.

## 12.1 Experiment specification

- [ ] structured experiment specification object;
- [ ] factor names, units, natural ranges, coded ranges, and constraints;
- [ ] factor roles: control, noise, mixture, process, block, whole-plot, subplot;
- [ ] response definitions and units;
- [ ] replicate, centre-point, and randomization policy;
- [ ] design objective and model intent recorded as metadata.

## 12.2 Run planning and execution

- [ ] randomized run order with reproducible seed;
- [ ] standard order versus run order preserved separately;
- [ ] block/whole-plot execution sheets;
- [ ] data-collection sheets;
- [ ] operator/batch/instrument metadata hooks;
- [ ] mark failed, skipped, repeated, and invalid runs without mutating the original design silently;
- [ ] export/import round-trip tests for experiment sheets.

## 12.3 Design diagnostics before execution

- [ ] rank and estimability report;
- [ ] alias/confounding report;
- [ ] resolution/aberration summary;
- [ ] leverage and prediction-variance summary;
- [ ] D/A/G/I efficiency where applicable;
- [ ] term-level standard errors for an assumed variance;
- [ ] detectable-effect / power summary from the proposed design;
- [ ] robustness-to-missing-run diagnostics.

## 12.4 Analysis after execution

- [ ] attach observed responses to a design without losing provenance;
- [ ] fit the intended model and record deviations from the planned model;
- [ ] residual and influence diagnostics;
- [ ] term/effect summaries;
- [ ] model hierarchy checks;
- [ ] lack-of-fit checks where pure error exists;
- [ ] split-plot/mixed-model analysis using the correct error structure;
- [ ] multiple-response desirability and trade-off summaries.

## 12.5 Confirmation and reproducibility

- [ ] confirmation-run planning;
- [ ] predicted versus observed confirmation results;
- [ ] reproducible experiment bundle containing design metadata, seed, responses, fitted model, and diagnostics;
- [ ] machine-readable JSON export for audit/replay;
- [ ] human-readable Markdown/HTML summary only after the underlying structured result is complete.

---

# Milestone 13 — Documentation and user experience

## 13.1 Documentation architecture

- [ ] API reference generated from the stable public API;
- [ ] mathematical background pages;
- [ ] design-selection guide;
- [ ] assumptions and limitations for every design family;
- [ ] design-comparison guide explaining classical versus optimal versus space-filling approaches;
- [ ] DataExcept exception guide;
- [ ] reproducibility guide;
- [ ] glossary of DOE terminology used by the package.

## 13.2 Tutorials

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
11. computer experiments and LHS/QMC;
12. Gaussian-process sequential design;
13. model-based optimal design;
14. complete industrial experiment from planning to confirmation.

## 13.3 Domain examples

- [ ] manufacturing process optimization;
- [ ] pharmaceutical formulation/process development;
- [ ] agricultural blocked experiments;
- [ ] quality engineering / robust parameter design;
- [ ] chemical/process mixture experiments;
- [ ] simulation/computer experiments;
- [ ] parameter-estimation experiment design.

---

# Milestone 14 — Quality engineering and release readiness

## 14.1 Tooling

Already established:

- [x] Ruff-based lint/format policy;
- [x] mypy checking with a documented debt ratchet;
- [x] pytest;
- [x] Hypothesis/property-based testing support;
- [x] pre-commit;
- [x] PEP 561 `py.typed` marker.

Remaining:

- [ ] remove remaining `ignore_errors = true` module overrides incrementally;
- [ ] define and enforce a coverage floor based on meaningful tested code;
- [ ] package build verification in CI;
- [ ] dependency/security scanning;
- [ ] API compatibility checks before 1.0.

## 14.2 CI matrix

- [ ] enforce all supported Python versions;
- [ ] Linux;
- [ ] Windows;
- [ ] macOS where practical;
- [ ] documentation build;
- [ ] package install test from built wheel;
- [ ] statistical-reference test subset;
- [ ] slower Monte Carlo validation as a separate scheduled/release job;
- [ ] benchmark regressions as a non-default job.

## 14.3 Performance

- [ ] factorial generation benchmarks;
- [ ] fractional-generator search benchmarks;
- [ ] optimal-design exchange benchmarks;
- [ ] candidate-set scaling benchmarks;
- [ ] response-surface optimization benchmarks;
- [ ] mixture constrained-region benchmarks;
- [ ] space-filling optimization benchmarks;
- [ ] surrogate/sequential acquisition benchmarks;
- [ ] memory checks for large candidate sets.

---

# Milestone 15 — Release path

## v0.2.0 — Shipped foundation

The 0.2.0 line establishes the current baseline rather than serving as a future correctness gate. It includes the present classical DOE/analysis stack, current validation infrastructure, DataExcept dependency, and modern Python tooling.

Known correctness debt remains explicitly tracked in Milestone 1 and is not retroactively claimed as complete.

## v0.3 — Correctness and validation release

Target:

- genuine DSD construction;
- corrected factorial blocking;
- unified effects semantics;
- generalized factorial model structure;
- split-plot replication/error-stratum correction;
- completed first-pass DataExcept boundary policy;
- expanded independent statistical validation.

## v0.4 — Architecture, optimal design, and mixtures

Target:

- coherent public API;
- shared model-matrix/design-metadata layer;
- Fedorov/DETMAX-family optimal search;
- C/E/V criterion expansion;
- equivalence/efficiency diagnostics;
- simplex-centroid and constrained/extreme-vertex mixture designs;
- Scheffé mixture modelling.

## v0.5 — Industrial DOE breadth and workflow

Target:

- additional blocking/restricted-randomization designs;
- expanded RSM catalogue;
- robust/Taguchi design family;
- design diagnostics before execution;
- run sheets, response attachment, missing-run handling, and confirmation workflow.

## v0.6 — Computer experiments

Target:

- LHS and optimized/space-filling designs;
- Sobol/Halton DOE wrappers backed by trusted QMC implementations;
- discrepancy/distance/projection diagnostics;
- Gaussian-process surrogate modelling;
- sequential computer-experiment criteria.

## v0.7 — Model-based and adaptive DOE

Target:

- Fisher-information/sensitivity abstraction;
- nonlinear local optimal design;
- robust/pseudo-Bayesian optimal design;
- initial ODE-model design support;
- general design augmentation and adaptive physical-experiment workflows.

## v1.0 — Stable statistical contract

`1.0` should mean more than API stability. The following conditions should hold:

- [ ] every documented stable design family has independent statistical validation;
- [ ] known statistical limitations are documented explicitly;
- [ ] core APIs are stable and typed;
- [ ] design metadata preserves experimental-unit and randomization semantics;
- [ ] operational boundaries use structured exceptions consistently;
- [ ] supported Python versions and release artifacts are tested in CI;
- [ ] documentation includes design-selection and assumptions guidance;
- [ ] the industrial plan-to-confirm workflow is reproducible;
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
| Mixture | Basic | Sum-to-one + estimability | Cornell/reference software | Add | Beta |
| Robust/Taguchi | Planned | Required | Published OA/reference software | Optional | Planned |
| Space-filling | Planned | Required | SciPy/reference metrics | Optional | Planned |
| GP/sequential computer DOE | Planned | Required | Benchmark functions/reference implementations | Yes | Planned |
| Nonlinear/model-based OED | Planned | Required | Published OED examples | Yes | Planned |
| Industrial workflow/provenance | Partial | Invariants required | Round-trip/reference scenarios | Optional | Beta before 1.0 |

---

# Competitive completeness checklist

This checklist is not a mandate to copy other packages feature-for-feature. It highlights capability gaps that matter to the intended scope.

## Design-generation breadth

- [ ] classical factorial/fractional parity is validated, not merely implemented;
- [ ] expanded screening catalogue;
- [ ] expanded RSM catalogue;
- [ ] mixture centroid/extreme-vertex designs;
- [ ] Fedorov/DETMAX optimal search;
- [ ] C/E/V optimality;
- [ ] Taguchi orthogonal arrays;
- [ ] LHS and optimized LHS;
- [ ] Sobol/Halton and geometric space-filling designs.

## Analysis/workflow differentiation

- [ ] coherent design-to-analysis object model;
- [ ] term-level estimability and alias diagnostics;
- [ ] pre-execution power/detectability diagnostics;
- [ ] correct restricted-randomization inference;
- [ ] multiple-response optimization;
- [ ] missing-run robustness and augmentation;
- [ ] confirmation experiments;
- [ ] reproducible experiment provenance.

The second list is strategically more important than achieving the largest raw catalogue of design generators.

---

# Deferred ideas

These are valid future directions but should not displace the statistical roadmap above:

- dashboard/web UI;
- plugin architecture;
- Bayesian model averaging unrelated to DOE design criteria;
- generic genetic algorithms for design search;
- animation-heavy visualization;
- cloud execution;
- automatic narrative report generation;
- domain-specific wrappers;
- broad reliability/UQ framework functionality already served by specialist libraries;
- DAE/PDE optimal-design support before nonlinear ODE OED is mature.

They can be revisited once the statistical core is trustworthy, the public API is coherent, and the major design families have independent validation.
