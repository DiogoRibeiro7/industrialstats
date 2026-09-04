# Getting started

## Installation

```bash
python -m pip install industrialstats
```

The supported Python range is 3.11 through 3.14. Core dependencies are NumPy,
pandas, SciPy, statsmodels, scikit-learn, Matplotlib, seaborn, Plotly,
openpyxl, and [DataExcept](https://github.com/DiogoRibeiro7/DataExcept).

## Defining factors

Every design is built from [`Factor`][industrialstats.designs.base.Factor]
objects. A factor has a name, its levels, and a type of either `"continuous"`
or `"categorical"`.

```python
from industrialstats.designs.base import Factor

temperature = Factor("temperature", [180, 220], factor_type="continuous")
material = Factor("material", ["ABS", "PP"], factor_type="categorical")
```

## Generating a full factorial design

```python
from industrialstats.designs.factorial import FactorialDesign

design = FactorialDesign(
    factors=[temperature, material],
    replicates=2,
    randomize=True,
    seed=42,
)
matrix = design.generate_design()
print(matrix)
```

!!! tip "Always pass a seed"
    Randomization is seedable throughout the package. Passing `seed` makes a
    run reproducible, which matters both for auditing an experiment and for
    writing deterministic tests.

## Fractional factorials and aliasing

When the full factorial is too large, use a regular fraction and inspect what
it costs you:

```python
from industrialstats.designs.fractional_factorial import FractionalFactorialDesign

factors = [Factor(name, [-1, 1]) for name in "ABCDEFG"]
design = FractionalFactorialDesign(factors, fraction="1/8", randomize=False)

design.generate_design()
print(design.resolution_analysis())
print(design.alias_structure()["A"])
```

The alias structure tells you which effects are indistinguishable in the
fraction you chose. Read it before running the experiment, not after.

## Response surface methodology

```python
from industrialstats.designs.response_surface import ResponseSurfaceDesign

factors = [
    Factor("temperature", [180, 220], factor_type="continuous"),
    Factor("pressure", [10, 20], factor_type="continuous"),
]

design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=4)
print(design.generate_design())
```

## Analysing results

Once responses are collected, fit a model and produce an ANOVA table:

```python
from industrialstats.analysis.anova import ANOVAAnalysis

analysis = ANOVAAnalysis(data, "Response")
analysis.fit_model("Response ~ temperature + pressure")
print(analysis.anova_table_calculation(typ=2))
```

## Error handling

Data-loading and export boundaries raise
[DataExcept](https://github.com/DiogoRibeiro7/DataExcept) exception types
rather than bare `OSError` or `ValueError`, and preserve the original exception
as the cause:

```python
from dataexcept import FileWriteError
from industrialstats.utils.export import export_to_csv

try:
    export_to_csv(matrix, "missing-directory/design.csv")
except FileWriteError as exc:
    print(exc.path, exc.original)
```

Mathematical precondition failures — an invalid factor level, a singular design
matrix — remain explicit `ValueError` and related exceptions.

## Where to go next

- [Choosing a design](guides/choosing-a-design.md)
- [Command-line interface](guides/cli.md)
- [API reference](reference/designs.md)
