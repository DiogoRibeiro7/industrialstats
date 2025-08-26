# industrialstats - Industrial Statistics for Python

Industrial statistics utilities for design of experiments, analysis, and visualization.

## Overview
industrialstats currently implements tools for generating experimental designs, analyzing results, and visualizing effects with an emphasis on reproducible workflows for manufacturing and research.

## Features

### Design generators
- Full and fractional factorial designs
- Response surface designs (central composite, Box–Behnken)
- Completely randomized and randomized block designs
- Screening designs (Plackett–Burman, definitive screening)
- Mixture and split–plot designs
- D-, A-, G-, and I-optimal designs via coordinate exchange

### Analysis tools
- ANOVA and mixed-effects ANOVA
- Effects analysis with Pareto, normal, and half-normal plots
- Model fitting with stepwise and regularized regression
- Power analysis with sample size determination and power curves
- Model diagnostics for residual, leverage, and influence checks

### Visualization
- Interactive design explorer and design comparison plots
- 3D response surface, contour, variance, and slice plots

## Installation
```bash
# install from PyPI (coming soon)
pip install industrialstats

# or install from source
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .
```

Core dependencies include `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `scikit-learn`, `plotly`, and `openpyxl`.

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

## Examples
Example scripts demonstrating manufacturing and pharmaceutical case studies are available in `examples/scripts/`.

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
