# industrialstats - Industrial Statistics for Python

Industrial statistics utilities for design of experiments, analysis, and visualization.

## Overview
industrialstats currently implements tools for generating experimental designs, analyzing results, and visualizing effects with an emphasis on reproducible workflows for manufacturing and research.

## Features

### Design generators
| Feature | Status | Notes |
|---------|--------|-------|
| Factorial Designs | ✅ Complete | 2^k, 3^k, mixed levels |
| Fractional Factorial | 🔄 Partial | Basic 2^(k-p), needs enhancement |
| Response Surface | 🔄 Partial | CCD and BBD implemented |
| Optimal Designs | 🔄 Partial | Coordinate exchange with D/A/G/I criteria |
| Split-Plot | ❌ Missing | Planned for v0.2 |

### Analysis tools
- ANOVA and mixed-effects ANOVA
- Effects analysis with Pareto, normal, and half-normal plots
- Model fitting with stepwise and regularized regression
- Power analysis with sample size determination and power curves
- Model diagnostics for residual, leverage, and influence checks

### Visualization
- Interactive design explorer and design comparison plots
- 3D response surface, contour, variance, and slice plots

### Datasets
- Built-in manufacturing dataset for quick experimentation
- Easy loading via ``industrialstats.datasets.load_manufacturing``

## Installation
```bash
# install from PyPI (coming soon)
pip install industrialstats

# or install from source
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .
```

### Building distribution artifacts

Create source and wheel distributions for upload to package indexes:

```bash
python scripts/build_dist.py
# twine upload dist/*  # publish to PyPI
```

Core dependencies include `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `scikit-learn`, `plotly`, and `openpyxl`.

### Development setup

```bash
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .[dev]
pre-commit install
```

If installation fails, ensure build tools (`gcc`, `make`) are available and that Python headers are installed for your platform.

## Quick start
```python
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign

factors = [Factor("A", [-1, 1]), Factor("B", [-1, 1])]
design = FactorialDesign(factors, randomize=False)
design.generate_design()
design.randomize(seed=42)
print(design.design_matrix[["RunOrder", "A", "B"]])
```

Expected output:

```
   RunOrder  A  B
0         1  1 -1
1         2 -1  1
2         3  1  1
3         4 -1 -1
```

## CLI examples
industrialstats exposes a command-line interface for quick analyses.

### Power analysis

```bash
industrialstats power --analysis t-test --effect-size 0.5 --power 0.8
```

Expected output:

```
effect_size  alpha  power  sample_size  test_type
0.5          0.05   0.8    32.0         two_sample
```

### Stepwise model fitting

```bash
printf 'y,A,B\n1,0,0\n2,0,1\n3,1,0\n4,1,1\n' > model.csv
industrialstats model --data model.csv --response y --entry-threshold 0.01 --removal-threshold 0.2
```

Expected output:

```
selected_terms
0 A
1 B
```

## Examples
Example scripts demonstrating manufacturing, pharmaceutical, and advanced end-to-end workflows are available in `examples/scripts/`.

## Citation
```bibtex
@software{industrialstats,
  title = {industrialstats: A Comprehensive Design of Experiments Package},
  author = {Diogo Ribeiro},
  year = {2024},
  url = {https://github.com/DiogoRibeiro7/industrialstats},
  version = {0.1.0}
}
```

## License
Licensed under the MIT License. See `LICENSE` for details.
