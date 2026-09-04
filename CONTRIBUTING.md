# Contributing to industrialstats

Thank you for considering a contribution. This project is pre-1.0 and its
first priority is **statistical correctness**, so the guidelines below place
more weight on validation than a typical library would.

By participating you agree to abide by our
[Code of Conduct](https://github.com/DiogoRibeiro7/industrialstats/blob/main/CODE_OF_CONDUCT.md).

## Getting set up

With Poetry, which reads the dev group from `pyproject.toml` directly:

```bash
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
poetry install --with dev
poetry run pre-commit install
```

With pip. The dev dependencies are declared as a Poetry group rather than a PEP
621 extra, so pip cannot resolve them from the project and they are listed
explicitly:

```bash
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
python -m pip install -e .     pytest pytest-cov hypothesis ruff mypy pre-commit     pandas-stubs types-openpyxl types-PyYAML
pre-commit install
```

The stub packages matter: `mypy` reports different results without them, so
install the full set or your local run will not match CI.

Run the checks:

```bash
pytest                      # tests; src/ is on the path automatically
pytest -m "not benchmark"   # skip the timing-based performance checks
ruff check .                # lint
ruff format .               # format
mypy                        # type check
pre-commit run --all-files  # everything the CI quality job runs
```

## Statistical validation

This is the part that matters most.

**Shape and run-count assertions are not sufficient for statistical code.** A
test asserting that a 2^3 factorial has 8 rows tells you almost nothing about
whether the design is correct.

When you add or change a statistical method, the pull request must include at
least one of:

1. **A comparison against an independent reference** — a worked example from a
   textbook, or output from reference software such as R, SAS, JMP, Minitab, or
   Design-Expert. Cite it precisely (author, edition, page or example number;
   or the exact code and package version).
2. **An algebraic property test** — orthogonality of the design matrix, the
   defining relation of a fraction, the resolution implied by its generators,
   variance-balance of a block design, and so on.
3. **A Monte Carlo recovery test** — simulate from known effects with a fixed
   seed and confirm the method recovers them within a stated tolerance.

Existing examples worth reading before you write yours live in
`tests/test_validation/test_statistical_accuracy.py` and the property tests in
`tests/test_designs/`.

Randomization must be seedable, and tests must be deterministic. Hypothesis
profiles are registered in `tests/conftest.py`; the `ci` profile is used in
continuous integration.

### Labelling maturity honestly

If a method is provisional, say so — in its docstring, in the README table, and
in the roadmap. A design family that is present but statistically unverified is
worse than an absent one if users cannot tell the difference.

## Code style

Formatting and linting are handled by [Ruff](https://docs.astral.sh/ruff/),
which replaces black, isort, and flake8. `pre-commit` applies it automatically;
CI enforces it.

- Public functions need NumPy-style docstrings covering parameters, returns,
  and raised exceptions. These docstrings are published as the API reference,
  so they are user-facing.
- Type hints are required on new code.
- Mathematical notation is welcome where it is the clearest spelling. Names
  like `X`, `XtX`, and `SS_A` are exempt from the usual casing rules inside
  `src/industrialstats/`.
- Use [DataExcept](https://github.com/DiogoRibeiro7/DataExcept) types at data
  and operational boundaries — file loading, schema problems, export failures —
  and preserve the original exception as the cause. Do **not** mechanically
  convert mathematical precondition failures; a singular design matrix should
  stay a `ValueError`.

## Type checking

`mypy` runs over `src/industrialstats` and must pass.

A small number of numerically dense modules still carry pre-existing type
errors and are listed under `[[tool.mypy.overrides]]` in `pyproject.toml` with
`ignore_errors = true`. That list is a **ratchet**:

- it may shrink at any time — removing a module from it is a welcome PR on its
  own;
- it must not grow. New code is expected to type-check. If you genuinely cannot
  satisfy the checker because of third-party stub limitations, use a narrow
  `# type: ignore[error-code]` with a comment explaining why, rather than
  disabling checking for a whole module.

## Test coverage

CI enforces a coverage floor. Like the typing ratchet, the floor only moves up.
If your change lowers coverage below it, add tests rather than lowering the
threshold.

## Commits and pull requests

- Branch from `main` and open a pull request against `main`.
- The repository uses [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`).
- Add an entry under `## [Unreleased]` in `CHANGELOG.md` for anything
  user-visible.
- Fill in the pull request template, including the statistical validation
  section when it applies.

## Documentation

The site is built with MkDocs Material and mkdocstrings:

```bash
python -m pip install mkdocs mkdocs-material "mkdocstrings[python]"
mkdocs serve     # preview at http://127.0.0.1:8000
mkdocs build --strict
```

`--strict` is what CI runs, so broken cross-references fail the build. The API
reference is generated from docstrings, so improving a docstring improves the
site.

## Reporting issues

Use the issue templates. For a wrong statistical result, use the **Statistical
correctness** template — it asks for the reference value needed to verify a
fix, which is what makes the report actionable.

Security problems should be reported privately; see [SECURITY.md](https://github.com/DiogoRibeiro7/industrialstats/blob/main/SECURITY.md).
