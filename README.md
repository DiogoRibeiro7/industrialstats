# industrialstats

**Industrial statistics and design of experiments for Python.**

`industrialstats` provides reproducible experimental-design generators, statistical analysis tools, diagnostics, power calculations, optimization methods, and visualizations for manufacturing, engineering, research, and other designed experiments.

The project is currently pre-1.0. Its development priority is statistical correctness and validation against established DOE references before expanding the catalogue of design families.

## Project principles

- **Statistical correctness first**: implementations should be validated against textbook results, trusted reference software, or independently derived properties.
- **Reproducible experiments**: randomization must be seedable and design matrices must remain inspectable.
- **Transparent methods**: prefer explicit statistical calculations and documented assumptions over opaque abstractions.
- **Clear design semantics**: terms such as effect, block, alias, resolution, whole plot, and optimality criterion must have precise DOE meanings.
- **Structured operational failures**: DataExcept is the standard exception layer for data-loading, file-export, and other operational boundaries, with further schema and transformation coverage planned.
- **No false completeness**: partially implemented or statistically provisional methods are labelled as such.

## Current capabilities

### Experimental designs

| Design family | Status | Current capability |
| --- | --- | --- |
| Full factorial | Implemented | Two-level, three-level, and mixed-level designs; replication; centre points; randomization; basic blocking; foldover and star-point augmentation |
| Fractional factorial | Implemented | Regular two-level fractions; generator parsing; automatic minimum-aberration generators; defining relations; resolution; alias chains; foldover options |
| Completely randomized design | Implemented | Treatment randomization, replication, multiple responses, sample-size calculation, summary statistics, and data-collection sheets |
| Randomized complete block design | Implemented | Within-block randomization, efficiency comparison, missing-plot inspection, and a Latin-square option |
| Plackett-Burman | Implemented with limited catalogue | Hadamard-based screening designs, reproducible randomization, and foldover |
| Definitive screening design | Experimental | Public API exists, but the construction is scheduled for statistical correction and stronger property-based validation |
| Response surface methodology | Implemented | Central composite and Box-Behnken designs, quadratic response-surface analysis, steepest ascent, ridge analysis, canonical analysis, and multiple-response optimization |
| Optimal designs | Implemented | Coordinate-exchange search with D-, A-, G-, and I-optimal criteria |
| Split-plot | Basic implementation | Restricted randomization and whole-plot/subplot layout generation; dedicated error-stratum analysis remains to be completed |
| Mixture | Basic implementation | Simplex-lattice designs, constraints, randomization, and three-component simplex plotting |

### Analysis

`industrialstats` currently includes:

- ANOVA with Type I, II, and III sums of squares;
- effect-size calculations;
- multiple comparisons and planned expansion of correction methods;
- contrasts;
- mixed-effects modelling;
- factorial main-effect and interaction analysis;
- residual, leverage, influence, and assumption diagnostics;
- power and sample-size calculations;
- stepwise and hierarchical model-fitting utilities;
- response-surface optimization;
- design-efficiency and prediction-variance utilities.

### Visualization

The visualization layer includes design-space plots, effects plots, diagnostic plots, response-surface plots, contour views, prediction-variance views, and related plotting helpers.

### Validation

The repository already contains statistical-validation tests in addition to ordinary unit tests. Examples include comparisons with `statsmodels`, hand-computed factorial effects, Monte Carlo effect recovery, and fractional-factorial alias checks against the R `FrF2` catalogue.

The long-term standard is stronger: every major design family should have algebraic property tests and at least one independent reference implementation or published example.

## Current correctness priorities

Before adding many new DOE families, the package is being hardened around several known issues:

1. replace the provisional definitive-screening construction with a genuine DSD algorithm and tests of its defining properties;
2. replace index-based factorial blocking with deliberate block generators and explicit confounding rules;
3. unify factorial-effect semantics around one canonical contrast-based implementation;
4. generalize factorial degrees of freedom and interaction generation beyond three-way terms;
5. correct split-plot replication semantics and add whole-plot/subplot error-stratum analysis;
6. expand Plackett-Burman coverage and document the supported run catalogue;
7. strengthen optimal-design and mixture-design validation.

See [`ROADMAP.md`](ROADMAP.md) for the full development sequence.

## DataExcept integration

`industrialstats` uses [DataExcept](https://github.com/DiogoRibeiro7/DataExcept) as its structured exception layer at data and operational boundaries.

The current boundary layer covers external CSV loading and shared CSV, Excel, and JSON export failures. The intended policy is:

- use DataExcept for file loading, tabular schema, missing columns, dtype mismatches, data transformations, import/export, and wrapped lower-level operational failures;
- preserve the original exception as context when wrapping an external failure;
- use specific exception types rather than a generic package-wide catch-all;
- do **not** mechanically replace every `ValueError` or numerical exception: mathematical precondition failures should remain explicit unless a DataExcept type gives genuinely better semantics.

DataExcept `^1.3.0` is a runtime dependency. Broader schema and transformation integration remains planned work.

## Installation

The package is still pre-release. Install the development version from source:

```bash
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .
```

The project currently requires Python 3.11 or newer.

Core dependencies include NumPy, pandas, SciPy, statsmodels, scikit-learn, Matplotlib, seaborn, Plotly, openpyxl, and DataExcept.

## Quick start

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign

factors = [
    Factor("temperature", [180, 220], factor_type="continuous"),
    Factor("pressure", [10, 20], factor_type="continuous"),
]

design = FactorialDesign(
    factors=factors,
    replicates=2,
    randomize=True,
    seed=42,
)

matrix = design.generate_design()
print(matrix)
```

For a regular fractional factorial:

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.fractional_factorial import FractionalFactorialDesign

factors = [Factor(name, [-1, 1]) for name in "ABCDEFG"]

design = FractionalFactorialDesign(
    factors,
    fraction="1/8",
    randomize=False,
)

matrix = design.generate_design()
print(design.resolution_analysis())
print(design.alias_structure()["A"])
```

For response-surface methodology:

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign

factors = [
    Factor("temperature", [180, 220], factor_type="continuous"),
    Factor("pressure", [10, 20], factor_type="continuous"),
]

design = ResponseSurfaceDesign(
    factors,
    design_type="CCD",
    center_points=4,
)

matrix = design.generate_design()
print(matrix)
```

## Command-line interface

`industrialstats` exposes a command-line interface for selected analysis workflows.

### Power analysis

```bash
industrialstats power --analysis t-test --effect-size 0.5 --power 0.8
```

### Stepwise model fitting

```bash
printf 'y,A,B\n1,0,0\n2,0,1\n3,1,0\n4,1,1\n' > model.csv
industrialstats model --data model.csv --response y --entry-threshold 0.01 --removal-threshold 0.2
```

## Examples

The repository contains executable examples for:

- manufacturing optimization;
- pharmaceutical development;
- fractional-factorial analysis;
- response-surface optimization;
- simulation studies;
- advanced end-to-end DOE workflows.

Jupyter notebooks cover introductory DOE, response-surface optimization, and model diagnostics.

## Development

```bash
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .[dev]
pre-commit install
pytest
```

When implementing or changing a statistical method, add tests that verify mathematical properties or compare against an independent reference. Passing shape and run-count tests alone is not sufficient for statistical algorithms.

## Package status

Current package version: `0.1.0`.

The public API is still evolving. Design and analysis objects that are not exported from `industrialstats` directly can currently be imported from their submodules. API cleanup is part of the pre-1.0 roadmap.

## Citation

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

## License

Licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
