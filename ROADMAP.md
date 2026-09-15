# industrialstats Roadmap to 1.0

This roadmap defines the release path from the shipped `0.3.0` line to a
statistically trustworthy and API-stable `1.0.0` release.

The package is already a substantial industrial Design of Experiments library.
The remaining pre-1.0 work is therefore organized by **release contract** rather
than by an ever-growing catalogue of possible methods.

The strategic workflow remains:

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
\text{confirm}.
\]

The goal for `1.0.0` is not to implement every DOE method. It is to make the
supported industrial DOE workflow stable, explicit, reproducible, validated,
and maintainable.

---

# Release policy

`industrialstats` follows semantic versioning.

- **Patch releases (`0.x.y`)** ship small coherent fixes, reference validations,
  operational hardening, and documentation improvements.
- **Minor releases (`0.x.0`)** introduce or stabilize one coherent capability
  layer.
- **`1.0.0`** freezes the first stable statistical and API contract.

Prefer frequent small releases over large accumulated batches. A validated
slice should not wait for an unrelated milestone before it can ship.

A release is prepared by updating:

- `pyproject.toml`;
- `src/industrialstats/__init__.py`;
- `CITATION.cff`;
- `CHANGELOG.md`.

After the preparation PR merges, the preferred release command is:

```bash
gh workflow run release.yml --ref main -f version=X.Y.Z
```

The release workflow validates metadata and changelog state, builds wheel and
sdist, creates or verifies the GitHub Release, attaches distributions, and
publishes to PyPI using OIDC Trusted Publishing.

---

# Guiding principles

1. **Correctness before breadth**
   - A statistically mislabelled method is worse than a missing one.
   - Mathematical defining properties should be tested directly.

2. **Independent validation**
   - Stable statistical claims require published examples, hand calculations,
     trusted reference software, or independently computed quantities.
   - Shape, run-count, and no-exception checks are smoke tests, not statistical
     evidence by themselves.

3. **Transparent experimental-unit semantics**
   - Blocks, whole plots, subplots, replicates, centre points, and repeated
     measurements must be explicit.
   - Row order must never silently define experimental structure.

4. **Narrow public claims**
   - Documentation must distinguish stable, experimental, partial, and planned
     capabilities.

5. **Structured operational exceptions**
   - DataExcept is used at external operational/data boundaries.
   - Mathematical and numerical failures retain domain-appropriate exceptions
     when those are clearer.

6. **Reproducibility**
   - Randomized algorithms require deterministic seeded execution.
   - Reproducibility contracts are part of the statistical API.

7. **Strong numerical foundations**
   - Prefer NumPy, SciPy, statsmodels, scikit-learn, and other trusted numerical
     foundations over reimplementing generic numerical primitives.

8. **Composable statistical objects**
   - Designs, model terms, fitted models, diagnostics, optimization results, and
     experiment provenance should be inspectable structured objects.

---

# Shipped baseline — v0.3.0

`0.3.0` is the first correctness-and-validation release after the original
package foundation.

It includes:

- genuine definitive screening designs based on conference-matrix structure;
- regular two-level factorial blocking defined by treatment generators;
- unified canonical two-level factorial effect semantics;
- generalized hierarchical factorial model terms and degrees of freedom;
- split-plot experimental-unit semantics, restricted randomization, classical
  error strata, EMS validation, and mixed-model inference;
- expanded Plackett-Burman catalogue support with published-reference and
  foldover validation;
- simplex-lattice mixture property validation and a Cornell/NIST reference case;
- Monte Carlo validation for effect recovery, ANOVA Type I error, RSM
  coefficient recovery, split-plot variance recovery, and mild balanced
  heteroskedasticity;
- independent power checks against statsmodels;
- substantially expanded DataExcept coverage;
- statistical-validation architecture and evidence audits;
- Python 3.11–3.14 CI on Linux, Windows, and macOS;
- package build, coverage, typing, docs, and security gates;
- automated PyPI/GitHub/Zenodo release infrastructure.

`0.3.x` is the current maintenance line.

---

# v0.3.x — Finish the validation foundation

**Goal:** close the remaining validation gaps for functionality that already
exists and is intended to remain part of the stable package.

This line should consist mostly of small patch releases.

## Independent reference validation

- [ ] Merge the R `rsm` canonical-analysis reference regression for the
  published `codata` example.
- [ ] Add an independently computed information-matrix validation for existing
  D-, A-, G-, and I-optimality criteria.
- [ ] Extend FrF2/reference coverage for regular fractional factorials.
- [ ] Add targeted R `DoE.base` comparisons where they validate semantics not
  already locked algebraically.
- [ ] Expand mixed-model reference comparisons against statsmodels where the
  package exposes a stable claim.

## Textbook regression catalogue

Maintain a small permanent catalogue with minimal reference data from:

- [x] Jones & Nachtsheim for DSDs;
- [x] Cornell/NIST for mixture simplex-lattice geometry;
- [x] Montgomery/NIST-style ANOVA and blocking examples already present;
- [ ] Box, Hunter & Hunter RSM example;
- [ ] Wu & Hamada fractional-factorial example;
- [ ] Goos & Jones optimal-design example.

## Property and repeated-sampling contracts

Already established for core families:

- [x] DSD orthogonality and estimability;
- [x] factorial/blocking invariants;
- [x] foldover guarantees;
- [x] mixture simplex constraints;
- [x] effect-estimator recovery;
- [x] one-way ANOVA Type I error;
- [x] RSM coefficient recovery;
- [x] split-plot variance recovery;
- [x] balanced mild-heteroskedastic ANOVA robustness;
- [x] power-reference checks.

Remaining before `0.4.0`:

- [ ] prediction-variance identities for RSM;
- [ ] information-matrix nonsingularity contracts for optimal designs;
- [ ] one cross-family randomization/reproducibility contract suite.

## DataExcept completion

- [x] runtime dependency and representative compatibility contract;
- [x] CRD missing-column, dtype, and missing-data failures;
- [x] configuration read/parse/format/dependency failures;
- [x] CLI loading boundaries;
- [x] structured transform failures;
- [x] split-plot response-data failures;
- [x] exception chaining/context on migrated boundaries.

Remaining:

- [ ] final audit of dataset import paths;
- [ ] final audit of export boundaries;
- [ ] final audit of validation utilities;
- [ ] ensure tests assert structured exception attributes, not only messages.

### Exit criterion for the 0.3.x line

No stable method already exposed by the package should lack either a defining
algebraic/property contract or an independent reference appropriate to its
claim.

---

# v0.4.0 — Stable public API and shared statistical architecture

**Theme:** make the package internally coherent before adding another large
method family.

## Public API

- [ ] Define the stable public design namespace.
- [ ] Export stable CRD, RCBD, factorial, fractional-factorial, screening, RSM,
  split-plot, optimal, and mixture classes consistently.
- [ ] Decide which classes are exported at top-level `industrialstats`.
- [ ] Mark experimental methods explicitly in API docs.
- [ ] Introduce deprecation machinery before removing or renaming public APIs.

## Shared model-term layer

- [ ] Introduce reusable model-term objects for main effects, interactions,
  polynomial terms, and mixture terms.
- [ ] Centralize hierarchy rules.
- [ ] Centralize continuous/categorical coding rules.
- [ ] Reuse the layer across factorial analysis, RSM, mixtures, and optimal
  design.
- [ ] Expose model-matrix rank and estimability diagnostics.

## Shared design metadata

- [ ] Standardize factor name, type, units, coded levels, natural levels,
  bounds, and role.
- [ ] Standardize block, whole-plot, subplot, replicate, centre-point, and
  augmentation metadata.
- [ ] Preserve standard order and randomized run order separately.
- [ ] Attach construction metadata and RNG seed to randomized designs.

## RNG contract

- [ ] Use `numpy.random.Generator` consistently.
- [ ] Remove hidden global RNG dependence.
- [ ] Standardize `seed` / `random_state` semantics.
- [ ] Add cross-family reproducibility tests.

### Exit criterion

The stable public API and metadata model are coherent enough that later feature
families can be added without creating parallel incompatible abstractions.

---

# v0.5.0 — Classical optimal design made trustworthy

**Theme:** turn the existing optimal-design subsystem from a useful beta feature
into a validated classical design layer.

## Existing criteria

- [ ] Independently validate D-optimality.
- [ ] Independently validate A-optimality.
- [ ] Independently validate G-optimality.
- [ ] Independently validate I-optimality.
- [ ] Verify criterion scaling and normalization conventions explicitly.

## Search algorithms

- [ ] Add Fedorov exchange.
- [ ] Add a DETMAX-style search.
- [ ] Add deterministic initialization options.
- [ ] Add seeded multi-start execution.
- [ ] Expose convergence history and stopping reason.
- [ ] Keep genetic/evolutionary search deferred until deterministic algorithms
  are validated.

## Exact and approximate design semantics

- [ ] Distinguish exact n-run designs from approximate weighted designs.
- [ ] Support replicated candidate points explicitly.
- [ ] Add design weights where mathematically appropriate.
- [ ] Add rounding/augmentation from approximate to exact designs.

## Criteria and diagnostics

- [ ] Add C-optimality.
- [ ] Add E-optimality.
- [ ] Add V/average-prediction-variance criteria where appropriate.
- [ ] Add D-, A-, G-, and I/V-efficiency diagnostics.
- [ ] Add sensitivity-function diagnostics.
- [ ] Add Kiefer-Wolfowitz equivalence diagnostics where applicable.
- [ ] Add robustness diagnostics for candidate deletion/missing runs.

### Exit criterion

Every advertised optimality criterion has a mathematically explicit definition,
reproducible search behavior, and independent numerical validation.

---

# v0.6.0 — Complete mixture DOE

**Theme:** move from simplex-lattice generation to a useful mixture design and
analysis subsystem.

## Designs

- [x] Simplex-lattice generation and validation.
- [x] Published Cornell/NIST reference geometry.
- [ ] Simplex-centroid designs.
- [ ] Augmented simplex-centroid designs.
- [ ] Axial/check-blend points.
- [ ] Extreme-vertices designs.
- [ ] Lower/upper-bound constrained mixtures.
- [ ] General linear-constraint mixtures.
- [ ] Mixture-process variable designs.
- [ ] Optimal mixture designs on constrained regions.

## Models

- [ ] Scheffé linear model.
- [ ] Scheffé quadratic model.
- [ ] Special cubic model.
- [ ] Mixture-process interaction models.
- [ ] Lack-of-fit handling and pure-error semantics.
- [ ] Prediction over the simplex/feasible region.

## Diagnostics and optimization

- [ ] Mixture-model ANOVA and diagnostics.
- [ ] Constrained desirability optimization.
- [ ] Ternary contours.
- [ ] Feasible-region visualization.
- [ ] Prediction-variance visualization.
- [ ] Confirmation blends.

### Exit criterion

A user can design, fit, diagnose, optimize, and confirm a standard industrial
mixture experiment without leaving the package.

---

# v0.7.0 — Industrial experiment workflow

**Theme:** make the package more than a collection of design generators.

## Experiment specification

- [ ] Structured experiment specification object.
- [ ] Factor names, units, natural/coded ranges, constraints, and roles.
- [ ] Response definitions and units.
- [ ] Replicate, centre-point, block, and randomization policies.
- [ ] Design objective and intended model recorded as metadata.

## Run planning and execution

- [ ] Reproducible randomized run order.
- [ ] Preserve standard order and run order separately.
- [ ] Block/whole-plot execution sheets.
- [ ] Data-collection sheets.
- [ ] Operator, batch, and instrument metadata hooks.
- [ ] Mark failed, skipped, repeated, and invalid runs without silently mutating
  the original design.
- [ ] Export/import round-trip tests.

## Pre-execution diagnostics

- [ ] Rank and estimability report.
- [ ] Alias/confounding report.
- [ ] Resolution/aberration summary.
- [ ] Leverage and prediction-variance summary.
- [ ] Optimality-efficiency diagnostics where applicable.
- [ ] Detectable-effect/power summary.
- [ ] Missing-run robustness diagnostics.

## Post-execution analysis

- [ ] Attach responses without losing design provenance.
- [ ] Record deviations from the planned model.
- [ ] Residual and influence diagnostics.
- [ ] Hierarchy and lack-of-fit checks.
- [ ] Correct split-plot/mixed-model inference from stored design metadata.
- [ ] Multiple-response optimization and trade-off summaries.

## Confirmation

- [ ] Confirmation-run planning.
- [ ] Predicted versus observed confirmation results.
- [ ] Reproducible experiment bundle containing design, seed, responses, fitted
  model, diagnostics, and confirmation results.
- [ ] Machine-readable JSON audit/replay representation.
- [ ] Human-readable Markdown/HTML summary generated from the structured bundle.

### Exit criterion

The package can carry one experiment from planning through confirmation while
preserving all statistical and execution provenance.

---

# v0.8.0 — Bounded computer-experiment support

**Theme:** add useful computer-experiment design without turning the pre-1.0
roadmap into a general surrogate/UQ project.

## Space-filling designs

- [ ] Standard Latin hypercube sampling.
- [ ] Optimized/maximin LHS using trusted SciPy QMC backends where practical.
- [ ] Sobol sequence wrapper.
- [ ] Halton sequence wrapper.
- [ ] Scaling to factor bounds and constrained regions.
- [ ] Reproducible seeds and metadata.

## Diagnostics

- [ ] Centered discrepancy.
- [ ] Separation distance.
- [ ] Fill distance.
- [ ] Pairwise-correlation diagnostics.
- [ ] Projection-quality diagnostics.
- [ ] Compare competing designs on common criteria.
- [ ] Independent validation against `scipy.stats.qmc` metrics.

## Augmentation

- [ ] Batch space-filling augmentation.
- [ ] Preserve stratification where the backend supports it.
- [ ] Constrained augmentation around unavailable runs.

### Explicit pre-1.0 boundary

Gaussian-process surrogate modelling and sequential acquisition are **not
required for 1.0**. They are candidates for post-1.0 specialist releases once
the classical/industrial workflow is stable.

---

# v0.9.0 — API freeze and release candidate line

**Theme:** stop adding large features and harden the complete pre-1.0 contract.

## API freeze

- [ ] Freeze stable public namespaces and signatures.
- [ ] Mark all remaining experimental APIs explicitly.
- [ ] Add API compatibility checks.
- [ ] Require deprecation periods for post-0.9 breaking changes.
- [ ] Audit return types for structured typed results versus ad-hoc dictionaries.

## Type and code-quality debt

- [ ] Remove remaining `mypy` `ignore_errors = true` overrides where feasible.
- [ ] Document any justified residual typing exclusions.
- [ ] Maintain the enforced coverage floor.
- [ ] Keep package build, docs, lint, typing, coverage, and security gates green.

## Cross-platform release qualification

- [ ] Python 3.11–3.14 release matrix remains green.
- [ ] Linux, Windows, and macOS release qualification.
- [ ] Built-wheel smoke test.
- [ ] Statistical-reference subset as a dedicated release gate.
- [ ] Monte Carlo validation as a scheduled/release qualification job.
- [ ] Benchmark regressions as non-default CI.

## Documentation

- [ ] Stable API reference.
- [ ] Mathematical background pages for stable design families.
- [ ] Design-selection guide.
- [ ] Assumptions and limitations for every stable method.
- [ ] Reproducibility guide.
- [ ] DataExcept exception guide.
- [ ] DOE terminology glossary.
- [ ] End-to-end industrial experiment tutorial.

## Performance qualification

- [ ] Factorial/fractional generation benchmarks.
- [ ] Optimal-design search benchmarks.
- [ ] Mixture constrained-region benchmarks.
- [ ] Space-filling optimization benchmarks.
- [ ] Memory checks for large candidate sets.

### Exit criterion

No known correctness issue or undocumented breaking API change remains between
`0.9.x` and `1.0.0`.

---

# v1.0.0 — Stable statistical contract

`1.0.0` means more than semantic-versioning API stability.

All of the following must hold:

- [ ] Every documented stable design family has independent statistical
  validation appropriate to its claim.
- [ ] Every stable design family has defining algebraic/property contracts.
- [ ] Known statistical limitations are documented explicitly.
- [ ] Core public APIs are stable and typed.
- [ ] Design metadata preserves factor coding, experimental-unit structure,
  randomization, blocks, replicates, and provenance.
- [ ] Operational boundaries use structured exceptions consistently.
- [ ] Randomized algorithms have deterministic reproducibility contracts.
- [ ] Supported Python versions and release artifacts are tested in CI.
- [ ] Documentation includes design-selection, assumptions, limitations, and
  reproducibility guidance.
- [ ] The industrial plan-to-confirm workflow is reproducible end-to-end.
- [ ] No experimental method is presented as statistically validated without
  evidence.
- [ ] No known critical statistical-correctness defect remains open.

Once these conditions are satisfied, `industrialstats 1.0.0` can claim a stable
industrial DOE contract.

---

# Explicitly post-1.0 candidates

The following remain strategically interesting but do **not** block `1.0.0`:

## Surrogate modelling and sequential computer experiments

- Gaussian-process/kriging response surfaces;
- kernel and trend configuration;
- prediction uncertainty/calibration;
- expected improvement and probability of improvement;
- integrated variance reduction;
- batch and constrained acquisition;
- sequential-regret and benchmark-function studies.

## Nonlinear/model-based optimal experimental design

- Fisher-information abstraction for nonlinear models;
- analytic/finite-difference parameter sensitivities;
- local D/A/E/Ds criteria;
- robust and pseudo-Bayesian OED;
- ODE-model time-point and input-profile design;
- dynamic parameter-estimation studies.

## Advanced adaptive experimentation

- formal adaptive physical-design rules;
- sequential inference with explicit error-rate control;
- general interim-analysis support;
- specialized nested/sliced computer-experiment designs.

These areas should be introduced only after the classical `1.0` contract has
proven stable in real use.

---

# Validation matrix for the 1.0 path

| Area | Algebra/property | Independent reference | Repeated sampling | 1.0 target |
| --- | --- | --- | --- | --- |
| Full factorial | Yes | Textbook/R | Yes | Stable |
| Fractional factorial | Yes | FrF2/DoE.base | Targeted | Stable |
| CRD/RCBD | Yes | Textbook/statsmodels | Targeted | Stable |
| Plackett-Burman | Yes | NIST | Optional | Stable |
| Definitive screening | Yes | Jones-Nachtsheim | Optional | Stable |
| RSM | Yes | R `rsm`/textbook | Yes | Stable |
| Split-plot | Yes | Hand-derived/mixed-model | Yes | Stable |
| Optimal design | Required | Independent criteria | Optional | Stable by 0.5 |
| Mixture | Required | Cornell/reference | Targeted | Stable by 0.6 |
| Space-filling | Required | SciPy QMC | Optional | Stable by 0.8 |
| Industrial workflow/provenance | Invariants | Round-trip scenarios | Optional | Stable by 0.9 |

---

# Version summary

| Version | Primary contract |
| --- | --- |
| `0.3.x` | Finish validation and DataExcept completeness for existing features |
| `0.4.0` | Stable public API, model-term layer, metadata, RNG contract |
| `0.5.0` | Validated classical optimal design |
| `0.6.0` | Complete mixture DOE workflow |
| `0.7.0` | End-to-end industrial experiment workflow |
| `0.8.0` | Bounded space-filling/computer-experiment design support |
| `0.9.0` | API freeze, documentation, typing, performance, release qualification |
| `1.0.0` | Stable validated statistical and industrial DOE contract |
