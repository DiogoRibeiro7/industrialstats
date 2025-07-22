# my_python_package

A minimal but production-ready Python package scaffold configured for publishing to [PyPI](https://pypi.org).

---

## 📁 File Tree

```text
doe-python/
├── README.md
├── setup.py
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── index.md
│   ├── getting_started.md
│   ├── tutorials/
│   │   ├── basic_concepts.md
│   │   ├── crd_tutorial.md
│   │   ├── rcbd_tutorial.md
│   │   ├── factorial_tutorial.md
│   │   ├── response_surface_tutorial.md
│   │   └── power_analysis.md
│   ├── examples/
│   │   ├── manufacturing.md
│   │   ├── agriculture.md
│   │   ├── marketing.md
│   │   └── clinical_trials.md
│   └── api_reference/
│       ├── designs.md
│       ├── analysis.md
│       └── visualization.md
├── src/
│   └── doe_python/
│       ├── __init__.py
│       ├── designs/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── crd.py
│       │   ├── rcbd.py
│       │   ├── factorial.py
│       │   ├── fractional_factorial.py
│       │   ├── response_surface.py
│       │   ├── optimal.py
│       │   └── screening.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── anova.py
│       │   ├── effects.py
│       │   ├── model_fitting.py
│       │   ├── diagnostics.py
│       │   └── power_analysis.py
│       ├── visualization/
│       │   ├── __init__.py
│       │   ├── plots.py
│       │   ├── interaction_plots.py
│       │   ├── response_surface_plots.py
│       │   └── diagnostic_plots.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── data_generation.py
│       │   ├── validation.py
│       │   └── export.py
│       └── datasets/
│           ├── __init__.py
│           └── sample_data.py
├── examples/
│   ├── notebooks/
│   │   ├── 01_introduction_to_doe.ipynb
│   │   ├── 02_completely_randomized_design.ipynb
│   │   ├── 03_randomized_complete_block_design.ipynb
│   │   ├── 04_factorial_designs.ipynb
│   │   ├── 05_fractional_factorial.ipynb
│   │   ├── 06_response_surface_methodology.ipynb
│   │   ├── 07_optimal_designs.ipynb
│   │   ├── 08_screening_experiments.ipynb
│   │   ├── 09_power_analysis.ipynb
│   │   └── 10_case_studies.ipynb
│   ├── scripts/
│   │   ├── manufacturing_optimization.py
│   │   ├── agricultural_experiment.py
│   │   ├── web_ab_testing.py
│   │   ├── pharmaceutical_study.py
│   │   └── quality_control.py
│   └── data/
│       ├── manufacturing_data.csv
│       ├── crop_yield_data.csv
│       ├── clinical_trial_data.csv
│       └── web_experiment_data.csv
├── tests/
│   ├── __init__.py
│   ├── test_designs/
│   │   ├── __init__.py
│   │   ├── test_crd.py
│   │   ├── test_rcbd.py
│   │   ├── test_factorial.py
│   │   ├── test_fractional_factorial.py
│   │   └── test_response_surface.py
│   ├── test_analysis/
│   │   ├── __init__.py
│   │   ├── test_anova.py
│   │   ├── test_effects.py
│   │   └── test_model_fitting.py
│   ├── test_visualization/
│   │   ├── __init__.py
│   │   ├── test_plots.py
│   │   └── test_interaction_plots.py
│   └── test_utils/
│       ├── __init__.py
│       └── test_data_generation.py
└── benchmarks/
    ├── performance_tests.py
    ├── memory_usage.py
    └── comparison_with_r.py
```
