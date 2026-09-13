# Milestone 2 DataExcept audit

This note records the current evidence for Milestone 2 so that future work does not duplicate already-implemented operational boundaries.

## Dependency and compatibility

DataExcept is a runtime dependency with a declared compatible range beginning at v1.3.0. The normal CI test matrix installs the package dependencies on every supported Python version (3.11, 3.12, 3.13, and 3.14), so DataExcept is exercised on every supported interpreter.

`tests/test_dataexcept_compatibility.py` provides the explicit compatibility smoke test, and `tests/test_utils/test_io.py` exercises a representative structured boundary exception with original-cause preservation.

Therefore the two remaining Milestone 2.1 checklist items are implementation-complete and only require roadmap reconciliation.

## Structured tabular boundaries already implemented

`industrialstats.utils.io.load_csv()` provides the canonical external CSV boundary:

- loading/filesystem failures -> `DataLoadingError` with exception chaining;
- missing required columns -> `MissingColumnError`;
- exact ordered schema mismatch -> `SchemaMismatchError`;
- dtype mismatch -> `DtypeMismatchError`.

The corresponding tests assert structured exception attributes rather than relying only on message text.

CRD response-data validation extends the same policy to an analysis-facing DataFrame boundary:

- absent response columns -> `MissingColumnError`;
- missing response values -> `MissingDataError`;
- non-numeric response columns -> `DtypeMismatchError`.

## Transformation boundary

`industrialstats.utils.transforms.log_transform()` now makes its data contract explicit:

- missing requested columns -> `MissingColumnError`;
- non-numeric requested columns -> `DtypeMismatchError`;
- zero or negative values -> `DataTransformationError` rather than silent `-inf`/`nan` output.

`center()` and `standardize()` remain unchanged because they do not currently expose the same failure mode.

## Configuration boundary

Configuration loading now distinguishes operational failure classes:

- unsupported suffix -> `ConfigurationError`;
- unreadable file -> `FileReadError` with the original exception preserved;
- malformed JSON/YAML -> `ParsingError`, using the path as context rather than retaining raw potentially secret-bearing config contents;
- missing optional PyYAML -> `DependencyError`.

## Dataset audit

`src/industrialstats/datasets/` contains only package-owned sample data. `load_manufacturing()` reads a constant CSV string through `StringIO`; it does not touch the filesystem, network, database, or user-controlled external source. There is therefore no additional external DataExcept boundary to add in the current datasets package.

## Export audit

`industrialstats.utils.export` already normalizes all shared export paths:

- CSV -> `FileWriteError`;
- Excel -> `FileWriteError`;
- JSON -> `FileWriteError`.

All preserve the underlying exception through chaining.

## Boundaries intentionally left native

The package should continue to preserve native/domain errors for mathematical and statistical preconditions, numerical failures, and programmer-contract violations. Examples include invalid DOE factor structures, negative variance components, singular numerical problems, and invalid API argument types.

## Remaining Milestone 2 work

The genuinely open work is narrower than the current roadmap suggests:

1. Audit response-data ingestion in larger analysis classes such as `ANOVAAnalysis`, `ModelFitting`, and `SplitPlotAnalysis`, migrating only true schema/data boundaries rather than every `ValueError`.
2. Audit validation utilities to distinguish operational schema failures from mathematical design checks.
3. Confirm CLI behavior preserves structured exceptions from shared loaders without unnecessarily flattening them into generic errors.
4. Audit any future network/database-backed dataset loaders when such boundaries are introduced.
5. Reconcile `ROADMAP.md` checkboxes and evidence against the merged implementation and this audit.

The key policy remains: use DataExcept at external or data-operation boundaries, but do not mechanically wrap mathematically meaningful failures.
