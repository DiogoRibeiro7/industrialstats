# Milestone 3 validation audit

This note records the validation evidence currently present on `main` for the
Milestone 3 statistical-validation roadmap. It is intentionally narrower than
`ROADMAP.md`: the purpose is to distinguish evidence that already exists from
work that still requires an independent reference implementation, textbook
case, or additional statistical study.

The audit was refreshed after the mixture simplex property tests merged in
PR #82.

## Status vocabulary

- **Complete**: the current codebase contains direct tests for the stated
  contract, with evidence strong enough to treat the roadmap item as satisfied.
- **Partial**: useful evidence exists, but it does not yet meet the full roadmap
  wording.
- **Open**: the requested independent comparison or permanent reference case is
  not yet present.
- **Not applicable yet**: the roadmap item targets a subsystem that is not yet
  implemented as a stable package capability.

## 3.1 Reference implementations

| Roadmap item | Status | Current evidence / remaining work |
| --- | --- | --- |
| Extend FrF2 comparison coverage for regular fractional factorials | Partial | Fractional-factorial implementation and examples explicitly reference FrF2/minimum-aberration catalogue semantics, and the package contains extensive algebraic alias/resolution tests. A broader automated catalogue comparison remains useful. |
| Cross-check full and fractional designs with R `DoE.base` | Open | No permanent `DoE.base` comparison suite is present. |
| Cross-check response-surface designs and canonical quantities with R `rsm` | Open | Current RSM validation is internal/analytic plus Monte Carlo recovery; an external `rsm` reference suite is still missing. |
| Compare ANOVA/mixed-model results with statsmodels reference fits | Complete for core ANOVA path; partial for broader mixed-model surface | `tests/test_validation/test_statistical_accuracy.py` compares one-way ANOVA F statistics and p-values directly with statsmodels. Mixed-model comparisons remain less systematic. |
| Validate optimal-design criteria against independently computed information matrices | Open | Requires a dedicated independent criterion audit. |
| Validate mixture designs against published Cornell examples | Open | PR #82 establishes simplex-lattice algebraic properties, but this is not a published Cornell reference example. |
| Validate space-filling metrics against SciPy/reference implementations | Not applicable yet | Keep open until the space-filling subsystem lands. |
| Validate model-based OED against published examples | Not applicable yet | Keep open until model-based OED is exposed as a stable subsystem. |

## 3.2 Textbook regression suite

The repository already contains isolated published/textbook reference checks,
but not yet the small explicit permanent catalogue envisaged by the roadmap.

| Source | Status | Evidence / gap |
| --- | --- | --- |
| Montgomery, *Design and Analysis of Experiments* | Partial | `tests/test_validation/test_statistical_accuracy.py` contains a Montgomery one-way ANOVA example; factorial-blocking and fractional-factorial semantics also follow Montgomery conventions. A named catalogue of minimal permanent examples is still incomplete. |
| Box, Hunter & Hunter, *Statistics for Experimenters* | Open / partial documentation only | The source is cited in design and validation documentation, but a clearly identified permanent regression example should still be added. |
| Wu & Hamada, *Experiments: Planning, Analysis, and Optimization* | Partial | Fractional-factorial minimum-aberration semantics cite Wu & Hamada; a dedicated stored regression example is still missing. |
| Goos & Jones, *Optimal Design of Experiments* | Open | No permanent optimal-design reference case is yet recorded here. |
| Cornell, *Experiments with Mixtures* | Open | Mixture construction cites Cornell, but no published numerical reference example is yet locked. |
| Jones & Nachtsheim DSD examples | Complete | The six-factor published DSD reference is covered by the DSD reference regression test added in PR #53. |

## 3.3 Property-based and algebraic validation

Several roadmap boxes are stale: the relevant properties are already enforced
by deterministic algebraic tests or Hypothesis suites.

| Property | Status | Evidence |
| --- | --- | --- |
| Orthogonality | Complete for core screening/factorial families | DSD algebraic/property tests and Plackett-Burman Gram-matrix tests directly verify orthogonality. |
| Balance | Complete for currently supported balanced/blocking constructions | Factorial blocking tests verify equal block sizes and replicated treatment membership; split-plot tests verify balanced error-stratum identities. |
| Alias equivalence | Complete for regular fractional factorials | Fractional-factorial alias-structure tests exercise defining-relation semantics. |
| Resolution | Complete for regular fractional factorials | Resolution and word-length semantics are directly tested in the fractional-factorial suite. |
| Estimability | Complete for current DSD scope | DSD property tests verify rank of the intercept/main/pure-quadratic model matrix. |
| Foldover transformations | Complete for current factorial/screening implementations | Full/fractional factorial and Plackett-Burman suites include foldover checks; PB tests additionally verify main-effect versus two-factor-interaction de-aliasing. |
| Mixture sum-to-one constraints | Complete | PR #82 adds Hypothesis coverage for 3–6 components and orders 1–5, including non-negativity, sum-to-one, lattice membership, uniqueness, and stars-and-bars run count. |
| Block assignment invariants | Complete for regular two-level factorial blocking | `tests/test_designs/test_factorial_blocking.py` verifies treatment-contrast block membership, independent generators, equal block sizes, replication consistency, opt-in main-effect confounding, and block recomputation. |
| Randomization reproducibility | Partial-to-complete for implemented design families | Seeded reproducibility is explicitly tested for blocked factorials and mixtures, and earlier DSD/screening work includes deterministic randomization. A single cross-family contract suite would improve discoverability but is not required to prove the existing semantics. |
| Information-matrix nonsingularity where required | Partial | Some design classes validate rank/nonsingularity implicitly or directly; a unified property suite across optimal/RSM designs is still missing. |
| Prediction-variance identities | Open | Existing RSM prediction-variance code does not yet have the broader permanent identity/property suite requested by the roadmap. |
| Space-filling bounds/discrepancy invariants | Not applicable yet | Keep open until that subsystem lands. |

## 3.4 Monte Carlo validation

The current codebase now contains repeated-sampling validation for four of the
roadmap items.

| Monte Carlo target | Status | Evidence |
| --- | --- | --- |
| Effect-estimator unbiasedness under known factorial models | Complete | PR #72 validates all seven effects in a noisy `2^3` model over 1,000 fixed-seed realizations. |
| Empirical Type I error for selected ANOVA workflows | Complete for one-way balanced ANOVA | PR #73 validates the package-reported one-way ANOVA p-value at nominal `alpha = 0.05` over 500 null experiments. |
| Power-calculation verification | Partial | `tests/test_validation/test_statistical_accuracy.py` cross-checks ANOVA power against statsmodels exactly, but this is an analytic/reference comparison rather than a repeated-sampling empirical-power study. |
| Response-surface coefficient recovery | Complete | PR #74 validates repeated-sampling recovery of all coefficients of a known quadratic CCD response surface. |
| Split-plot inference under known variance components | Complete for balanced classical error-stratum ANOVA | PR #81 validates recovery of whole-plot and residual variance components from the package ANOVA mean squares over 300 simulated experiments. |
| Model-based OED parameter recovery | Not applicable yet | Keep open until model-based OED exists as a stable subsystem. |
| Mild non-normality / variance-heterogeneity robustness | Open | No explicit robustness study is yet part of the permanent validation suite. |

## Recommended next validation work

The highest-value remaining Milestone 3 work is no longer another generic
property test. The next additions should be independent references:

1. add one published Cornell mixture example;
2. add an R `rsm` cross-check for a small CCD/canonical-analysis case;
3. add an independently computed information-matrix check for D/A/G/I criteria;
4. extend automated FrF2 catalogue comparison beyond the current algebraic and
   example-level evidence;
5. add one documented mild heteroscedastic/non-normal robustness experiment only
   where the package documentation makes a robustness claim.

This ordering preserves the project rule that shape/run-count checks alone are
not enough evidence for statistical correctness.
