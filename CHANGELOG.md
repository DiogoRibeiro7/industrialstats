# Changelog

All notable changes to `industrialstats` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- PEP 561 `py.typed` marker, so the shipped type annotations are visible to
  type checkers in downstream projects.
- Documentation site built with MkDocs Material and mkdocstrings, published to
  GitHub Pages.
- `SECURITY.md`, issue forms (including a statistical-correctness report), a
  pull request template, and `CODEOWNERS`.
- Test coverage measurement with an enforced floor, plus CodeQL and
  `pip-audit` scanning in CI.
- CI now runs on pushes to `main` and covers Windows and macOS in addition to
  Linux.

### Changed

- Replaced black, isort, and flake8 with Ruff for both linting and formatting.
  The previous flake8 configuration silenced real defect classes (unused
  imports and variables, bare `except`, star imports); these are now enforced.
- Enabled real type checking. `mypy` previously ran with `ignore_errors = true`,
  which disabled it entirely. Six numerically dense modules carry documented,
  shrinking debt via per-module overrides; everything else is clean.
- `zip()` calls over design matrices now pass `strict=True`, so a length
  mismatch raises instead of silently truncating.
- The CLI reports a stable program name in help output rather than inheriting
  it from `sys.argv[0]`.
- Example scripts use `numpy.random.Generator` instead of the legacy global
  `numpy.random.seed` API.

### Removed

- **BREAKING:** `industrialstats.visualizations` no longer re-exports its
  third-party imports. A star-import plus a computed `__all__` made `np`, `pd`,
  `plt`, `sns`, `go` and `stats` part of the package's public API; the module
  now exports only `ExperimentPlotter` and `ResponseSurfacePlotter`. Import
  those libraries directly instead of via `industrialstats.visualizations`.

### Security

- Raised the `pytest` development dependency past
  [GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g)
  (predictable `/tmp/pytest-of-{user}` handling on UNIX, allowing a local user
  to cause denial of service or possibly escalate privileges). The constraint
  was `^8.0.0`, which pins to a range that is affected in its entirety, and did
  not match the 9.x that CI already installed. It is now `>=9.0.3,<10`, matched
  by `minversion` and by an explicit floor in the workflow install steps.
  `pytest` is a development dependency and is never installed by users of the
  package.

### Fixed

- Eight modules had `from __future__ import annotations` placed above their
  module docstring, which left `__doc__` as `None` and would have produced
  empty API documentation.
- `DesignValidator.check_confounding` no longer emits a divide-by-zero
  `RuntimeWarning` on perfectly confounded designs, which is the case it exists
  to report; it returns an infinite VIF as expected.
- Guarded `design_matrix` access in the CRD, RCBD, and screening designs, which
  previously raised `AttributeError` when called before `generate_design()`.
- `CompletelyRandomizedDesign` validates response columns with
  `pandas.api.types.is_numeric_dtype`, which handles nullable extension dtypes
  that `numpy.issubdtype` rejects.
- Mutable default arguments in `PowerAnalysis` (`factor_levels`, `powers`) are
  no longer shared across calls.
- Exceptions raised while wrapping model-fitting failures now chain the
  original error with `raise ... from`.
- `ModelDiagnostics.assumption_tests` no longer depends on SciPy's deprecated
  implicit Anderson-Darling behaviour. SciPy 1.17 requires an explicit p-value
  method and removes the critical-value tables in 1.19; the test now requests an
  interpolated p-value where that is supported and falls back to the tables on
  older SciPy. The reported `anderson` mapping gains a `p_value` key alongside
  `critical_value_5pct`; whichever the installed SciPy cannot supply is `None`.
- `ModelFitting.regularized_fitting` no longer passes `alphas=None` explicitly
  to scikit-learn, which is deprecated and removed in 1.9. The argument is now
  omitted when unset, preserving the automatic grid on every supported version.
- `DesignValidator.check_confounding` also suppresses the singular-matrix
  conditioning warning newer statsmodels emits for perfectly confounded
  designs, which is the case the function exists to report.
- The performance regression benchmark compared two adjacent timings of the
  same call, so a single descheduled run failed it. It now warms up and takes
  the minimum of several repetitions on each side.

## 0.1.0 (2026-09-04)


### Features

* add DataExcept dependency ([852723c](https://github.com/DiogoRibeiro7/industrialstats/commit/852723c61fd6ba728394468b0422f7b19f8397d4))
* add DataExcept file boundaries ([55f9156](https://github.com/DiogoRibeiro7/industrialstats/commit/55f91566ca2764e9858c9cf1671d73fe8bed7271))
* add structured CSV loading boundary ([df894b0](https://github.com/DiogoRibeiro7/industrialstats/commit/df894b0f56ad3fed3f87f5c7bc0a505c8caaef58))
* export structured CSV loader ([3762fd6](https://github.com/DiogoRibeiro7/industrialstats/commit/3762fd6b80295c8a0f9871b2fbe8281797268240))
* route CLI file I/O through DataExcept boundaries ([3576008](https://github.com/DiogoRibeiro7/industrialstats/commit/3576008818d7ad513895b79510650e71f81d7716))
* wrap export boundary failures with DataExcept ([ba1948d](https://github.com/DiogoRibeiro7/industrialstats/commit/ba1948dec0dff9e49a2389291a1c38447d8046de))


### Bug Fixes

* preserve ANOVA CSV output format ([0a185d8](https://github.com/DiogoRibeiro7/industrialstats/commit/0a185d82b5ddd35246a61f9918496050d5f62a6d))
* preserve configurable CSV index semantics ([4fe6169](https://github.com/DiogoRibeiro7/industrialstats/commit/4fe6169862004bebbc647525d80b8157706c9467))


### Documentation

* add changelog for automated releases ([7ce4c6d](https://github.com/DiogoRibeiro7/industrialstats/commit/7ce4c6db9599b10fae452b3a25220b567595bddd))
* add PyPI and Zenodo release checklist ([471fdb3](https://github.com/DiogoRibeiro7/industrialstats/commit/471fdb37d0489620be0c1f31c2d90feb2cceb0c2))
* document automated release flow ([82d6890](https://github.com/DiogoRibeiro7/industrialstats/commit/82d6890d2558ed4322d2a11ae67e3eaccece435e))
* install development tools in setup instructions ([f148493](https://github.com/DiogoRibeiro7/industrialstats/commit/f148493a8ab0e6f3c1db12bbf38485554c63f9be))
* let release please own changelog entries ([e36a4af](https://github.com/DiogoRibeiro7/industrialstats/commit/e36a4af3ff774ddb892b6225460c096f71d5bcec))
* prepare README for package release ([dc3ddcc](https://github.com/DiogoRibeiro7/industrialstats/commit/dc3ddccdf1e379c7c3c17502b173120bbbcffab5))
* reflect active DataExcept runtime integration ([81c9abe](https://github.com/DiogoRibeiro7/industrialstats/commit/81c9abe98ec41a3c054df90f9cc7fa37087afa92))
* refresh README and correctness-first roadmap ([efbadb8](https://github.com/DiogoRibeiro7/industrialstats/commit/efbadb8e1a778a1752236b9c363e17aa99219511))
* refresh README with current DOE capabilities ([7d5d1cd](https://github.com/DiogoRibeiro7/industrialstats/commit/7d5d1cdc5ba49d24d11604fc568c000a3f6f8ed1))
* replace stale roadmap with correctness-first plan ([7bb2a91](https://github.com/DiogoRibeiro7/industrialstats/commit/7bb2a912bf548b69c3596a145c8f932051ccee8d))
* simplify release flow ([feb4999](https://github.com/DiogoRibeiro7/industrialstats/commit/feb4999e9c654066110398573230bb7435c3f681))
