## Summary

<!-- What does this change and why. Link the issue it closes, e.g. "Closes #12". -->

## Type of change

- [ ] Bug fix
- [ ] Statistical correctness fix
- [ ] New feature
- [ ] Documentation
- [ ] Build, CI, or tooling
- [ ] Breaking change

## Statistical validation

<!--
Required when this PR adds or changes a statistical method. Delete this
section only if the change cannot affect any computed result.

Shape and run-count assertions alone are not sufficient for statistical code.
-->

- [ ] Compared against an independent reference (textbook example, reference
      software, or an analytical derivation) — cited below
- [ ] Verified an algebraic or invariance property of the design
- [ ] Randomization is seedable and the new test is deterministic

Reference used:

<!-- e.g. Montgomery, "Design and Analysis of Experiments", 10th ed., Example 6.2 -->

## Checklist

- [ ] `pre-commit run --all-files` passes
- [ ] `pytest` passes
- [ ] `mypy` passes, and no module was newly added to the `ignore_errors`
      ratchet in `pyproject.toml`
- [ ] Public functions have NumPy-style docstrings with the parameters,
      returns, and raised exceptions
- [ ] `CHANGELOG.md` has an entry under "Unreleased" if this is user-visible
