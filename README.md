# industrialstats - Industrial Statistics for Python

A professional-grade Python package for Industrial Statistics with advanced experimental design, analysis, optimization methods, and industrial applications.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-beta-orange.svg)](https://github.com/DiogoRibeiro7/industrialstats)

## 🎯 Overview

industrialstats provides a complete toolkit for experimental design and analysis, from basic factorial designs to advanced response surface methodology and optimal designs. Whether you're optimizing manufacturing processes, conducting scientific research, or teaching DOE concepts, this package offers the tools you need.

## 🚀 Key Features

### **Design Types**
- **Factorial Designs** (2^k, 3^k, mixed levels with center points)
- **Fractional Factorial** (2^(k-p) with customizable generators)
- **Response Surface Methodology** (Central Composite, Box-Behnken)
- **Completely Randomized Design** (CRD)
- **Randomized Complete Block Design** (RCBD)
- **Plackett-Burman Screening Designs**
- **Definitive Screening Designs**
- **Optimal Designs** (D, A, G, I-optimal with exchange algorithms)

### **Advanced Analysis**
- **ANOVA** with multiple comparison tests and assumption validation
- **Effects Analysis** with hierarchical screening and interaction detection
- **Model Fitting** with stepwise selection and cross-validation
- **Power Analysis** and sample size determination
- **Response Surface Analysis** with optimization and robustness assessment

### **Visualization Suite**
- Interactive design space plots
- 3D response surfaces and contour maps
- Effects screening plots (Pareto, normal probability)
- Comprehensive diagnostic plots
- Publication-ready visualizations

### **Industrial Applications**
- Manufacturing process optimization
- Quality control integration
- Robust design methodologies
- Economic impact analysis
- Professional reporting templates

## 📦 Installation

```bash
# Install from PyPI (when available)
pip install industrialstats

# Or install from source
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats
pip install -e .

# Install with all optional dependencies
pip install -e ".[all]"
```

### Dependencies

**Core Requirements:**
```
numpy>=1.20.0
pandas>=1.3.0
scipy>=1.7.0
matplotlib>=3.4.0
seaborn>=0.11.0
statsmodels>=0.13.0
scikit-learn>=1.0.0
```

**Optional Dependencies:**
```
# Visualization enhancements
plotly>=5.0          # Interactive plots
bokeh>=2.4           # Web-based visualizations

# Optimization methods
cvxpy>=1.2           # Convex optimization
pyomo>=6.4           # Mathematical programming

# Development tools
pytest>=7.0          # Testing
sphinx>=5.0          # Documentation
black>=22.0          # Code formatting
```

## 📁 Repository Structure

```
industrialstats/
├── README.md
├── setup.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── LICENSE
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── docs.yml
│       └── release.yml
├── docs/
│   ├── index.md
│   ├── getting_started.md
│   ├── tutorials/
│   │   ├── basic_concepts.md
│   │   ├── factorial_designs.md
│   │   ├── response_surface.md
│   │   ├── optimal_designs.md
│   │   └── power_analysis.md
│   ├── examples/
│   │   ├── manufacturing.md
│   │   ├── agriculture.md
│   │   ├── clinical_trials.md
│   │   └── web_experiments.md
│   └── api_reference/
│       ├── designs.md
│       ├── analysis.md
│       ├── visualization.md
│       └── utils.md
├── src/
│   └── industrialstats/
│       ├── __init__.py
│       ├── designs/
│       │   ├── __init__.py
│       │   ├── base.py                    # Factor and ExperimentalDesign base classes
│       │   ├── factorial.py               # Full factorial designs (2^k, 3^k, mixed)
│       │   ├── fractional_factorial.py    # Fractional factorial (2^(k-p))
│       │   ├── crd.py                     # Completely Randomized Design
│       │   ├── rcbd.py                    # Randomized Complete Block Design
│       │   ├── response_surface.py        # CCD and Box-Behnken designs
│       │   ├── optimal.py                 # D/A/G/I-optimal designs
│       │   └── screening.py               # Plackett-Burman and screening designs
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── anova.py                   # ANOVA analysis with diagnostics
│       │   ├── effects.py                 # Factorial effects calculation
│       │   ├── model_fitting.py           # Advanced model selection methods
│       │   ├── power_analysis.py          # Power and sample size analysis
│       │   └── diagnostics.py             # Model diagnostics and validation
│       ├── visualization/
│       │   ├── __init__.py
│       │   ├── plots.py                   # Main plotting functions
│       │   ├── interaction_plots.py       # Interaction and main effects plots
│       │   ├── response_surface_plots.py  # 3D surfaces and contours
│       │   └── diagnostic_plots.py        # Residual and diagnostic plots
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── data_generation.py         # Synthetic data generation
│       │   ├── validation.py              # Input validation utilities
│       │   ├── export.py                  # Export utilities (Excel, reports)
│       │   └── transforms.py              # Data transformations
│       ├── datasets/
│       │   ├── __init__.py
│       │   ├── sample_data.py             # Built-in example datasets
│       │   └── data/
│       │       ├── manufacturing.csv
│       │       ├── chemical_process.csv
│       │       └── clinical_trial.csv
│       └── cli.py                         # Command-line interface
├── examples/
│   ├── notebooks/
│   │   ├── 01_introduction_to_doe.ipynb          # Basic DOE concepts
│   │   ├── 02_factorial_designs.ipynb            # Factorial design tutorial
│   │   ├── 03_response_surface_methodology.ipynb # RSM comprehensive guide
│   │   ├── 04_optimal_designs.ipynb              # Optimal design methods
│   │   ├── 05_power_analysis.ipynb               # Sample size determination
│   │   ├── 06_model_selection.ipynb              # Advanced model fitting
│   │   ├── 07_industrial_applications.ipynb     # Real-world case studies
│   │   └── 08_advanced_topics.ipynb              # Custom designs and methods
│   ├── scripts/
│   │   ├── manufacturing_optimization.py         # Complete manufacturing example
│   │   ├── response_surface_optimization.py      # RSM chemical process example
│   │   ├── agricultural_experiment.py            # Field trial design
│   │   ├── web_ab_testing.py                     # Digital experimentation
│   │   ├── pharmaceutical_development.py         # Drug formulation optimization
│   │   ├── quality_control_study.py              # QC process improvement
│   │   └── custom_design_example.py              # Custom design implementation
│   └── data/
│       ├── manufacturing_data.csv
│       ├── chemical_reaction_data.csv
│       ├── crop_yield_data.csv
│       ├── clinical_trial_data.csv
│       └── web_experiment_data.csv
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_designs/
│   │   ├── __init__.py
│   │   ├── test_base.py
│   │   ├── test_factorial.py              # Comprehensive factorial tests
│   │   ├── test_fractional_factorial.py
│   │   ├── test_crd.py
│   │   ├── test_rcbd.py
│   │   ├── test_screening.py
│   │   ├── test_response_surface.py
│   │   └── test_optimal.py
│   ├── test_analysis/
│   │   ├── __init__.py
│   │   ├── test_anova.py
│   │   ├── test_effects.py
│   │   ├── test_model_fitting.py
│   │   └── test_power_analysis.py
│   ├── test_visualization/
│   │   ├── __init__.py
│   │   ├── test_plots.py
│   │   ├── test_interaction_plots.py
│   │   └── test_response_surface_plots.py
│   └── test_utils/
│       ├── __init__.py
│       ├── test_data_generation.py
│       ├── test_validation.py
│       └── test_export.py
├── benchmarks/
│   ├── performance_tests.py
│   ├── memory_usage_tests.py
│   └── comparison_with_r.py
└── scripts/
    ├── build_docs.py
    ├── run_examples.py
    └── generate_test_data.py
```

## 🔧 Quick Start

### Basic Factorial Design

```python
from industrialstats import FactorialDesign, Factor, ANOVAAnalysis

# Define experimental factors
factors = [
    Factor("Temperature", [180, 220], "continuous"),
    Factor("Pressure", [80, 120], "continuous"),
    Factor("Material", ["A", "B"], "categorical")
]

# Create 2^3 factorial design with replicates
design = FactorialDesign(factors, replicates=2, center_points=4)
design_matrix = design.generate_design()

print(f"Generated {len(design_matrix)} experimental runs")
print(design_matrix.head())

# Add your experimental results
design_matrix['Response'] = your_response_data

# Analyze results
analyzer = ANOVAAnalysis(design_matrix, 'Response')
model = analyzer.fit_model('Response ~ Temperature * Pressure * Material')
anova_table = analyzer.anova_table_calculation()

print(anova_table)
```

### Fractional Factorial Design

```python
from industrialstats.designs.fractional_factorial import (
    FractionalFactorialDesign,
    Factor,
)

factors = [
    Factor("A", [0, 1]),
    Factor("B", [0, 1]),
    Factor("C", [0, 1]),
    Factor("D", [0, 1]),
]

ff = FractionalFactorialDesign(factors, fraction="1/2", generators=["ABC"])
design_matrix = ff.generate_design()
print(design_matrix.head())
```

### Randomized Complete Block Design

```python
from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign

treatments = ["A", "B", "C"]
blocks = ["Block1", "Block2", "Block3"]

rcbd = RandomizedCompleteBlockDesign(treatments, blocks)
design_matrix = rcbd.generate_design()
print(design_matrix.head())
```

### Plackett-Burman Screening Design

```python
from industrialstats.designs.screening import PlackettBurmanDesign, Factor

factors = [
    Factor("A", [1, -1]),
    Factor("B", [1, -1]),
    Factor("C", [1, -1]),
]

pb = PlackettBurmanDesign(factors)
design_matrix = pb.generate_design()
print(design_matrix.head())
```

### Definitive Screening Design

```python
from industrialstats.designs.screening import DefinitiveScreeningDesign, Factor

factors = [
    Factor("A", [-1, 0, 1]),
    Factor("B", [-1, 0, 1]),
]

dsd = DefinitiveScreeningDesign(factors)
design_matrix = dsd.generate_design()
print(design_matrix.head())
```

### Response Surface Optimization

```python
from industrialstats import ResponseSurfaceDesign, Factor

# Define continuous factors for optimization
factors = [
    Factor("Temperature", [250, 350], "continuous"),
    Factor("Pressure", [2, 8], "continuous")
]

# Create Central Composite Design
rsm = ResponseSurfaceDesign(factors, design_type="CCD", center_points=6)
design_matrix = rsm.generate_design()

# Conduct experiments and add response data
design_matrix['Yield'] = your_yield_data

# Fit response surface and find optimum
results = rsm.response_surface_analysis(design_matrix['Yield'])
optimal_conditions = results['optimum_actual']

print(f"Optimal conditions: {optimal_conditions}")
print(f"Model R²: {results['r_squared']:.3f}")
```

### Power Analysis

```python
from industrialstats import PowerAnalysis

# Determine sample size for desired power
power_analyzer = PowerAnalysis()

result = power_analyzer.factorial_power(
    effect_size=0.5,        # Medium effect size
    alpha=0.05,             # 5% significance level
    power=0.8,              # 80% power
    factor_levels=[2, 2, 3] # 2×2×3 factorial design
)

print(f"Required replicates: {result.sample_size}")
print(f"Total runs needed: {result.additional_info['total_sample_size']}")
```

## 📊 Example Applications

### 1. Manufacturing Process Optimization

```python
# Complete manufacturing optimization workflow
from industrialstats import FactorialDesign, Factor, EffectsAnalysis, ExperimentPlotter

# Run the complete example
python examples/scripts/manufacturing_optimization.py
```

**Features:**
- 4-factor injection molding optimization
- Statistical analysis with ANOVA
- Effects screening and ranking
- Optimization recommendations
- Economic impact analysis

### 2. Chemical Process RSM

```python
# Response surface methodology for chemical reactions
python examples/scripts/response_surface_optimization.py
```

**Features:**
- Central Composite Design implementation
- Quadratic model fitting and validation
- 3D response surface visualization
- Robustness analysis
- Process control recommendations

### 3. Quality Control Study

```python
# Quality improvement using DOE
python examples/scripts/quality_control_study.py
```

**Features:**
- Multi-response optimization
- Robust parameter design
- Process capability analysis
- Control chart integration

## 🔬 Advanced Features

### Custom Optimal Designs

```python
from industrialstats import OptimalDesign

# Create D-optimal design for specific model
optimal_design = OptimalDesign(
    factors=factors,
    n_runs=24,
    criterion="D",
    model_terms=["Intercept", "A", "B", "A*B", "A²", "B²"]
)

# Generate candidate set and optimize
optimal_design.generate_candidate_set(grid_density=7)
design_matrix = optimal_design.generate_design(max_iterations=1000)

# Evaluate design efficiency
efficiency = optimal_design.design_efficiency()
print(f"D-efficiency: {efficiency['D_efficiency']:.3f}")
```

### Model Selection and Validation

```python
from industrialstats import ModelFitting

# Advanced model selection
fitter = ModelFitting(data, 'response')

# Stepwise selection with hierarchy
stepwise_result = fitter.stepwise_selection(
    entry_threshold=0.05,
    removal_threshold=0.10
)

# Cross-validation
cv_result = fitter.cross_validation(
    stepwise_result['selected_terms'],
    k_folds=5
)

print(f"CV R²: {cv_result['overall_r2']:.3f}")
print(f"CV RMSE: {cv_result['overall_rmse']:.3f}")
```

### Mixed and Repeated Measures

```python
from industrialstats.analysis.anova import ANOVAAnalysis

# Mixed effects with "Subject" as random factor
mixed = ANOVAAnalysis(data, 'Response')
mixed_result = mixed.mixed_effects_model(['Treatment'], ['Subject'])

# Nested design example
nested_result = mixed.nested_anova({'Batch': 'Day'})

# Repeated measures over time
rm_result = mixed.repeated_measures_anova('Subject', ['Time'])
```

## 📈 Visualization Examples

### Interactive Response Surfaces

```python
from industrialstats import ExperimentPlotter

plotter = ExperimentPlotter(data)

# Main effects plot
fig1 = plotter.main_effects_plot('Response')

# Interaction plot
fig2 = plotter.interaction_plot('Temperature', 'Pressure', 'Response')

# 3D factorial cube
fig3 = plotter.factorial_cube_plot(['A', 'B', 'C'], 'Response')
```

### Effects Screening

```python
from industrialstats import EffectsAnalysis

effects = EffectsAnalysis(design_matrix, response_data)

# Calculate all effects
main_effects = effects.calculate_main_effects()
interactions = effects.calculate_interaction_effects()

# Create screening plots
pareto_fig = effects.pareto_chart(main_effects)
normal_fig = effects.normal_probability_plot({**main_effects, **interactions})
```

## 🎓 Learning Resources

### Tutorials (Jupyter Notebooks)
- **Introduction to DOE** - Basic concepts and terminology
- **Factorial Designs** - Complete guide to factorial experiments
- **Response Surface Methodology** - Optimization using RSM
- **Power Analysis** - Sample size determination
- **Model Selection** - Advanced statistical methods

### Example Scripts
- **Manufacturing Optimization** - Industrial process improvement
- **Agricultural Experiments** - Field trial design and analysis
- **Web A/B Testing** - Digital experimentation methods
- **Pharmaceutical Development** - Drug formulation optimization

### Documentation
- **API Reference** - Detailed function documentation
- **Best Practices** - Industry guidelines and recommendations
- **Troubleshooting** - Common issues and solutions

## 🧪 Command Line Interface

The package provides a lightweight command line tool `industrialstats` for
creating simple designs. For example:

```bash
industrialstats factorial -f A=0,1 -f B=0,1 -r 2 -o design.csv
```

This generates a full factorial design with two factors and stores it in
`design.csv`.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=industrialstats --cov-report=html

# Run specific test categories
pytest tests/test_designs/          # Design generation tests
pytest tests/test_analysis/         # Statistical analysis tests
pytest tests/test_visualization/    # Plotting tests

# Performance benchmarks
python benchmarks/performance_tests.py
```

## 🛡️ Validation Utilities

industrialstats ships with a flexible validation framework to check factor
specifications and generated design matrices.

### Key Classes
- `DesignValidator` – found in `industrialstats.utils.validation`

### Usage Example
```python
from industrialstats.designs.base import Factor
from industrialstats.utils.validation import DesignValidator

factors = [Factor("A", [0, 1]), Factor("B", [1])]
warnings = DesignValidator.validate_factors(factors)
print(warnings)
```

The validator can also detect confounding patterns and estimate power
based on an effect size using correlation and non‑central F
distributions.

## 🔗 Unified Design Interface

Every design subclass inherits common utilities from ``ExperimentalDesign``.  Key
properties include ``run_count`` for the number of generated runs and
``factor_names`` for quick access to factors.

```python
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.designs.base import Factor

design = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
design.generate_design()
print(design.run_count)      # 4
print(design.factor_names)  # ['A', 'B']
```

## 🎲 Data Simulation Utilities

Experimental responses can be simulated using `DataSimulator` in
`industrialstats.utils.data_generation`.

### Usage Example
```python
from industrialstats.utils.data_generation import DataSimulator

sim = DataSimulator(seed=42)
responses = sim.simulate_factorial_response(design_matrix, noise_std=1.0)
```

These utilities are useful for teaching and benchmarking.  See Montgomery
[1] and Box et al. [2] for the underlying statistical models.

## 💾 Data Export and Transformation

Design matrices can be exported and transformed using helpers in
`industrialstats.utils`.

```python
from industrialstats.utils import (
    export_to_csv,
    export_to_excel,
    export_to_json,
    center,
    standardize,
    log_transform,
)

centered = center(design_matrix)
export_to_csv(centered, "design.csv")
```


## 📚 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/DiogoRibeiro7/industrialstats.git
cd industrialstats

# Create development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black src/ tests/
isort src/ tests/

# Check style
flake8 src/ tests/
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **R Project** - Inspiration from R's rich DOE ecosystem
- **statsmodels** - Statistical modeling foundation
- **scikit-learn** - Machine learning integration
- **matplotlib/seaborn** - Visualization capabilities
- **NumPy/SciPy** - Numerical computing foundation

## 📚 Bibliography

- **Factorial and Fractional Factorial Designs** – Montgomery, D.C. *Design and
  Analysis of Experiments*, 9th ed., Wiley, 2017.
- **Response Surface Methodology** – Myers, R.H., Montgomery, D.C.,
  Anderson-Cook, C.M. *Response Surface Methodology: Process and Product
  Optimization Using Designed Experiments*, 4th ed., Wiley, 2016.
- **Optimal Design Algorithms** – Atkinson, A.C., Donev, A.N., Tobias, R.D.
  *Optimum Experimental Designs, With SAS*, 2nd ed., Oxford University Press,
  2007.
- **Plackett–Burman Screening** – Plackett, R.L., Burman, J.P. "The Design of
  Optimum Multifactorial Experiments," *Biometrika*, 1946.
- **Randomized Block Designs** – Cochran, W.G., Cox, G.M. *Experimental
  Designs*, 2nd ed., Wiley, 1957.
- **ANOVA and Effects Analysis** – Box, G.E.P., Hunter, J.S., Hunter, W.G.
  *Statistics for Experimenters*, 2nd ed., Wiley, 2005.

## 📞 Support

- **Documentation**: [https://industrialstats.readthedocs.io/](https://industrialstats.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/DiogoRibeiro7/industrialstats/issues)
- **Discussions**: [GitHub Discussions](https://github.com/DiogoRibeiro7/industrialstats/discussions)
- **Email**: support@industrialstats.org

## 🚀 Citation

If you use industrialstats in your research, please cite:

```bibtex
@software{industrialstats,
  title = {industrialstats: A Comprehensive Design of Experiments Package},
  author = {Diogo Ribeiro},
  year = {2024},
  url = {https://github.com/DiogoRibeiro7/industrialstats},
  version = {0.1.0}
}
```

---

**industrialstats** - Making experimental design accessible, powerful, and professional.

[![GitHub stars](https://img.shields.io/github/stars/DiogoRibeiro7/industrialstats.svg?style=social&label=Star)](https://github.com/DiogoRibeiro7/industrialstats/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/DiogoRibeiro7/industrialstats.svg?style=social&label=Fork)](https://github.com/DiogoRibeiro7/industrialstats/network/members)
