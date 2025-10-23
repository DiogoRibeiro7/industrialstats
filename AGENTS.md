# AGENTS.md - AI Coding Agent Instructions

Instructions for AI coding agents to systematically implement the industrialstats package according to the roadmap and specifications.

## 🎯 Overview

This document provides detailed instructions for AI coding agents (like Claude, GPT-4, or other AI assistants) to implement the industrialstats package. The instructions are designed to ensure consistency, quality, and adherence to the project specifications.

## 📋 General Guidelines

### **Code Quality Standards**
- **Python Version**: Target Python 3.10+ compatibility
- **Style Guide**: Follow PEP 8 with Black formatting (line length: 88)
- **Type Hints**: Use comprehensive type annotations throughout
- **Docstrings**: NumPy-style docstrings for all public functions/classes
- **Error Handling**: Comprehensive exception handling with meaningful messages
- **Testing**: Write tests for every new function/class (aim for >95% coverage)

### **Documentation Requirements**
- **All public APIs** must have complete docstrings with examples
- **Complex algorithms** must include mathematical explanations
- **Statistical methods** must reference appropriate literature
- **Examples** should be realistic and educational

### **Import Conventions**
```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from typing import List, Dict, Optional, Any, Tuple, Union
```

---

## 🏗️ Implementation Instructions by Component

## Phase 1: Foundation Components

### **Task 1.1: Enhanced Base Classes** 
*File: `src/industrialstats/designs/base.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to ExperimentalDesign class:

def to_excel(self, filename: str, include_metadata: bool = True) -> None:
    """Export design to Excel with formatting and metadata."""
    
def to_json(self, filename: str) -> None:
    """Export design to JSON format for API integration."""
    
def clone(self) -> 'ExperimentalDesign':
    """Create a deep copy of the design."""
    
def merge_with(self, other_design: 'ExperimentalDesign') -> 'ExperimentalDesign':
    """Merge with another design for augmentation."""
    
@property
def is_balanced(self) -> bool:
    """Check if design is balanced."""
    
@property
def design_efficiency(self) -> Dict[str, float]:
    """Calculate basic design efficiency metrics."""
```

**Validation Requirements**:
- All factor types (categorical, continuous, ordinal)
- Mixed factor designs
- Missing value handling
- Design matrix validation

### **Task 1.2: Validation Utilities**
*File: `src/industrialstats/utils/validation.py`*

**Create comprehensive validation system**:

```python
class DesignValidator:
    """Comprehensive design validation."""
    
    @staticmethod
    def validate_factors(factors: List[Factor]) -> List[str]:
        """Validate factor specifications and return warnings."""
        
    @staticmethod
    def validate_design_matrix(design_matrix: pd.DataFrame) -> Dict[str, Any]:
        """Validate generated design matrix."""
        
    @staticmethod
    def check_confounding(design_matrix: pd.DataFrame) -> Dict[str, List[str]]:
        """Check for confounding patterns."""
        
    @staticmethod
    def estimate_power(design_matrix: pd.DataFrame, effect_size: float) -> float:
        """Estimate design power for given effect size."""
```

### **Task 1.3: Data Generation Utilities**
*File: `src/industrialstats/utils/data_generation.py`*

**Implement realistic data simulation**:

```python
class DataSimulator:
    """Generate realistic experimental data."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize with random seed for reproducibility."""
        
    def simulate_factorial_response(
        self, 
        design_matrix: pd.DataFrame,
        main_effects: Dict[str, float],
        interactions: Dict[str, float],
        noise_level: float = 0.1,
        response_type: str = "continuous"
    ) -> np.ndarray:
        """Simulate factorial experiment responses."""
        
    def simulate_process_data(
        self,
        design_matrix: pd.DataFrame,
        process_model: Callable,
        noise_model: str = "normal"
    ) -> np.ndarray:
        """Simulate process responses with realistic noise."""
```

---

## Phase 2: Core Design Implementations

### **Task 2.1: Enhanced Factorial Design**
*File: `src/industrialstats/designs/factorial.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to FactorialDesign class:

def add_star_points(self, alpha: float = None) -> pd.DataFrame:
    """Add star points to convert to Central Composite Design."""
    
def generate_foldover(self) -> pd.DataFrame:
    """Generate foldover design for de-aliasing."""
    
def blocking_scheme(self, block_size: int) -> pd.DataFrame:
    """Generate blocked factorial design."""
    
def confounding_pattern(self) -> Dict[str, List[str]]:
    """Return confounding pattern for factorial design."""
    
def design_generators(self) -> List[str]:
    """Return generator strings for fractional factorials."""
```

### **Task 2.2: Fractional Factorial Design**
*File: `src/industrialstats/designs/fractional_factorial.py`*

**Create from scratch**:

```python
class FractionalFactorialDesign(ExperimentalDesign):
    """Fractional factorial design implementation."""
    
    def __init__(
        self, 
        factors: List[Factor], 
        fraction: str = "1/2",
        generators: Optional[List[str]] = None,
        resolution: Optional[int] = None
    ):
        """Initialize fractional factorial design."""
        
    def generate_design(self) -> pd.DataFrame:
        """Generate fractional factorial design matrix."""
        
    def alias_structure(self) -> Dict[str, List[str]]:
        """Calculate complete alias structure."""
        
    def resolution_analysis(self) -> Dict[str, Any]:
        """Analyze design resolution and clarity."""
        
    def foldover_options(self) -> List[Dict[str, Any]]:
        """Suggest foldover strategies."""
```

**Key Features to Implement**:
- Automatic generator selection for standard fractions
- Resolution calculation and verification
- Alias structure computation
- Foldover design generation
- Minimum aberration criteria

### **Task 2.3: RCBD Implementation**
*File: `src/industrialstats/designs/rcbd.py`*

**Create complete RCBD implementation**:

```python
class RandomizedCompleteBlockDesign(ExperimentalDesign):
    """Randomized Complete Block Design."""
    
    def __init__(
        self,
        treatments: List[str],
        blocks: List[str],
        blocking_factor: str = "Block"
    ):
        """Initialize RCBD."""
        
    def generate_design(self) -> pd.DataFrame:
        """Generate RCBD matrix with proper randomization."""
        
    def efficiency_vs_crd(self, block_variance: float) -> float:
        """Calculate relative efficiency compared to CRD."""
        
    def missing_plot_analysis(self, missing_positions: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Analyze impact of missing plots."""
        
    def latin_square_option(self) -> Optional[pd.DataFrame]:
        """Generate Latin Square if conditions allow."""
```

### **Task 2.4: Screening Designs**
*File: `src/industrialstats/designs/screening.py`*

**Implement screening design methods**:

```python
class PlackettBurmanDesign(ExperimentalDesign):
    """Plackett-Burman screening design."""
    
    def generate_design(self) -> pd.DataFrame:
        """Generate PB design from Hadamard matrices."""
        
class DefinitiveScreeningDesign(ExperimentalDesign):
    """Definitive Screening Design (DSD)."""
    
    def generate_design(self) -> pd.DataFrame:
        """Generate DSD with 3 levels per factor."""
```

---

## Phase 3: Analysis Engine Implementation

### **Task 3.1: Enhanced ANOVA**
*File: `src/industrialstats/analysis/anova.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to ANOVAAnalysis class:

def mixed_effects_model(
    self, 
    fixed_effects: List[str], 
    random_effects: List[str]
) -> Dict[str, Any]:
    """Fit mixed effects model for designs with random factors."""
    
def unbalanced_anova(self) -> Dict[str, Any]:
    """Handle unbalanced designs with appropriate methods."""
    
def nested_anova(self, nesting_structure: Dict[str, str]) -> Dict[str, Any]:
    """Perform nested ANOVA for hierarchical designs."""
    
def repeated_measures_anova(
    self, 
    subject_column: str, 
    within_factors: List[str]
) -> Dict[str, Any]:
    """Analyze repeated measures designs."""
```

### **Task 3.2: Advanced Model Fitting**
*File: `src/industrialstats/analysis/model_fitting.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to ModelFitting class:

def regularized_fitting(
    self, 
    model_terms: List[str],
    method: str = "lasso",
    alpha: float = 1.0
) -> Dict[str, Any]:
    """Fit regularized models (LASSO, Ridge, Elastic Net)."""
    
def bayesian_model_selection(
    self, 
    candidate_models: List[List[str]],
    prior: str = "uniform"
) -> Dict[str, Any]:
    """Bayesian model selection and averaging."""
    
def robust_fitting(
    self, 
    model_terms: List[str],
    method: str = "huber"
) -> Dict[str, Any]:
    """Robust regression methods for outlier resistance."""
    
def transformation_selection(self) -> Dict[str, Any]:
    """Automatic response transformation selection (Box-Cox, etc.)."""
```

### **Task 3.3: Diagnostic System**
*File: `src/industrialstats/analysis/diagnostics.py`*

**Create comprehensive diagnostic system**:

```python
class ModelDiagnostics:
    """Comprehensive model diagnostics."""
    
    def __init__(self, model_result: Dict[str, Any], data: pd.DataFrame):
        """Initialize with fitted model results."""
        
    def assumption_tests(self) -> Dict[str, Dict[str, Any]]:
        """Test all ANOVA/regression assumptions."""
        
    def outlier_detection(self) -> Dict[str, List[int]]:
        """Detect various types of outliers."""
        
    def influence_analysis(self) -> Dict[str, np.ndarray]:
        """Calculate influence measures."""
        
    def model_adequacy(self) -> Dict[str, Any]:
        """Overall model adequacy assessment."""
        
    def recommendation_system(self) -> List[str]:
        """Generate diagnostic-based recommendations."""
```

---

## Phase 4: Advanced Methods Implementation

### **Task 4.1: Enhanced Response Surface**
*File: `src/industrialstats/designs/response_surface.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to ResponseSurfaceDesign class:

def steepest_ascent(
    self, 
    current_point: Dict[str, float],
    gradient: Dict[str, float],
    step_size: float = 1.0
) -> List[Dict[str, float]]:
    """Generate steepest ascent path."""
    
def ridge_analysis(self, model_coefficients: Dict[str, float]) -> Dict[str, Any]:
    """Perform ridge analysis for constrained optimization."""
    
def canonical_analysis(self, model_coefficients: Dict[str, float]) -> Dict[str, Any]:
    """Canonical analysis of response surface."""
    
def multiple_response_optimization(
    self, 
    responses: List[str],
    weights: Optional[List[float]] = None,
    constraints: Optional[Dict[str, Tuple[float, float]]] = None
) -> Dict[str, Any]:
    """Optimize multiple responses simultaneously."""
```

### **Task 4.2: Enhanced Optimal Designs**
*File: `src/industrialstats/designs/optimal.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to OptimalDesign class:

def federov_exchange(self, max_iterations: int = 1000) -> pd.DataFrame:
    """Implement Federov exchange algorithm."""
    
def genetic_algorithm_optimization(
    self, 
    population_size: int = 100,
    generations: int = 50
) -> pd.DataFrame:
    """Use genetic algorithms for design optimization."""
    
def bayesian_optimal_design(
    self, 
    prior_info: Dict[str, Any],
    utility_function: str = "expected_information"
) -> pd.DataFrame:
    """Generate Bayesian optimal designs."""
    
def sequential_design(
    self, 
    current_data: pd.DataFrame,
    n_additional_runs: int
) -> pd.DataFrame:
    """Sequential design for adaptive experimentation."""
```

### **Task 4.3: Advanced Design Methods**
*File: `src/industrialstats/designs/advanced.py`*

**Create new file for advanced methods**:

```python
class SplitPlotDesign(ExperimentalDesign):
    """Split-plot and strip-plot designs."""
    
class MixtureDesign(ExperimentalDesign):
    """Mixture experiment designs."""
    
class RobustDesign(ExperimentalDesign):
    """Taguchi robust parameter designs."""
    
class ComputerExperimentDesign(ExperimentalDesign):
    """Latin Hypercube and space-filling designs."""
```

---

## Phase 5: Visualization Implementation

### **Task 5.1: Enhanced Core Plotting**
*File: `src/industrialstats/visualization/plots.py`*

**Current Status**: ✅ Basic implementation exists
**Required Enhancements**:

```python
# Add these methods to ExperimentPlotter class:

def design_comparison_plot(
    self, 
    designs: List[pd.DataFrame],
    design_names: List[str]
) -> plt.Figure:
    """Compare multiple designs visually."""
    
def factor_screening_plot(
    self, 
    effects: Dict[str, float],
    method: str = "pareto"
) -> plt.Figure:
    """Enhanced effects screening visualization."""
    
def interactive_design_explorer(self) -> Any:
    """Create interactive design exploration interface."""
    
def animation_sequence(
    self, 
    sequence_data: List[pd.DataFrame],
    save_path: str
) -> None:
    """Create animated sequences for design evolution."""
```

### **Task 5.2: Specialized Visualization**
*File: `src/industrialstats/visualization/response_surface_plots.py`*

**Create comprehensive RSM visualization**:

```python
class ResponseSurfacePlotter:
    """Specialized response surface visualization."""
    
    def __init__(self, design: ResponseSurfaceDesign):
        """Initialize with RSM design."""
        
    def surface_3d(
        self, 
        response_data: np.ndarray,
        factor1: str, 
        factor2: str,
        **kwargs
    ) -> plt.Figure:
        """3D response surface plot."""
        
    def contour_with_path(
        self, 
        response_data: np.ndarray,
        optimization_path: Optional[List[Dict[str, float]]] = None
    ) -> plt.Figure:
        """Contour plot with optimization path."""
        
    def prediction_variance_surface(self) -> plt.Figure:
        """Prediction variance surface visualization."""
        
    def slice_plots(
        self, 
        response_data: np.ndarray,
        fixed_factors: Dict[str, float]
    ) -> plt.Figure:
        """Response surface slices at fixed factor levels."""
```

### **Task 5.3: Interactive Dashboards**
*File: `src/industrialstats/visualization/dashboard.py`*

**Create interactive interface** (Optional but valuable):

```python
class DOEDashboard:
    """Interactive DOE dashboard using Streamlit/Dash."""
    
    def design_builder_interface(self) -> None:
        """Interactive design building interface."""
        
    def analysis_interface(self) -> None:
        """Interactive analysis interface."""
        
    def optimization_interface(self) -> None:
        """Interactive optimization interface."""
```

---

## Phase 6: Documentation & Examples

### **Task 6.1: Example Scripts Enhancement**

**For each example script, ensure:**

1. **Complete workflow** from design to conclusions
2. **Realistic data** with proper noise and effects
3. **Statistical validation** of results
4. **Business context** and interpretation
5. **Actionable recommendations**
6. **Professional visualizations**

**Required example scripts**:
- `examples/scripts/agricultural_experiment.py`
- `examples/scripts/pharmaceutical_development.py`
- `examples/scripts/web_ab_testing.py`
- `examples/scripts/quality_control_study.py`

### **Task 6.2: Jupyter Notebooks**

**Create comprehensive tutorial notebooks**:

```
examples/notebooks/
├── 01_introduction_to_doe.ipynb
├── 02_factorial_designs.ipynb
├── 03_response_surface_methodology.ipynb
├── 04_optimal_designs.ipynb
├── 05_power_analysis.ipynb
├── 06_model_selection.ipynb
├── 07_industrial_applications.ipynb
└── 08_advanced_topics.ipynb
```

**Each notebook should include**:
- Clear learning objectives
- Step-by-step explanations
- Interactive widgets where appropriate
- Exercises for practice
- Real-world context

---

## Phase 7: Testing Implementation

### **Task 7.1: Comprehensive Unit Tests**

**For each module, create tests that cover**:

```python
# Test structure example for designs/factorial.py
class TestFactorialDesign:
    def test_design_generation_basic(self):
        """Test basic design generation."""
        
    def test_design_generation_with_replicates(self):
        """Test design with multiple replicates."""
        
    def test_center_points_addition(self):
        """Test center point functionality."""
        
    def test_effect_calculation_accuracy(self):
        """Test effects calculation against known values."""
        
    def test_invalid_inputs_handling(self):
        """Test proper error handling for invalid inputs."""
        
    def test_design_properties_calculation(self):
        """Test calculation of design properties."""
        
    @pytest.mark.parametrize("factor_levels", [[2,2], [2,3], [3,3]])
    def test_different_factor_levels(self, factor_levels):
        """Test designs with different factor level combinations."""
```

### **Task 7.2: Integration Tests**

**Create end-to-end workflow tests**:

```python
class TestWorkflowIntegration:
    def test_complete_factorial_workflow(self):
        """Test complete factorial design workflow."""
        
    def test_complete_rsm_workflow(self):
        """Test complete RSM workflow."""
        
    def test_design_augmentation_workflow(self):
        """Test design augmentation process."""
```

### **Task 7.3: Statistical Validation Tests**

**Validate against known results**:

```python
class TestStatisticalValidation:
    def test_against_textbook_examples(self):
        """Validate against published textbook examples."""
        
    def test_against_r_package_results(self):
        """Compare results with R packages."""
        
    def test_monte_carlo_validation(self):
        """Monte Carlo validation of statistical properties."""
```

---

## 🔧 Specific Implementation Guidelines

### **Error Handling Patterns**

```python
class DOEError(Exception):
    """Base exception for DOE package."""
    pass

class DesignError(DOEError):
    """Design-related errors."""
    pass

class AnalysisError(DOEError):
    """Analysis-related errors."""
    pass

# Usage pattern:
def validate_factors(factors: List[Factor]) -> None:
    if not factors:
        raise DesignError("At least one factor must be specified")
    
    for factor in factors:
        if len(factor.levels) < 2:
            raise DesignError(f"Factor {factor.name} must have at least 2 levels")
```

### **Logging Patterns**

```python
import logging

logger = logging.getLogger(__name__)

def generate_design(self) -> pd.DataFrame:
    logger.info(f"Generating {self.name} with {len(self.factors)} factors")
    
    # Implementation
    
    logger.info(f"Generated design with {len(design_matrix)} runs")
    return design_matrix
```

### **Configuration Management**

```python
# src/industrialstats/config.py
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DOEConfig:
    """Global configuration for DOE package."""
    default_alpha: float = 0.05
    default_power: float = 0.8
    random_seed: Optional[int] = None
    plot_style: str = "default"
    optimization_tolerance: float = 1e-6
    
# Global config instance
config = DOEConfig()
```

---

## 📊 Performance Requirements

### **Computational Efficiency**
- **Design generation**: <1 second for designs up to 1000 runs
- **ANOVA calculation**: <5 seconds for datasets up to 10,000 observations
- **Optimization**: <30 seconds for optimal designs up to 100 runs
- **Visualization**: <10 seconds for complex plots

### **Memory Usage**
- **Designs**: <100MB for largest practical designs
- **Analysis**: Efficient streaming for large datasets
- **Plotting**: Memory-efficient rendering for complex visualizations

### **Scalability Targets**
- **Factors**: Up to 20 factors in factorial designs
- **Runs**: Up to 10,000 experimental runs
- **Responses**: Multiple response optimization up to 10 responses
- **Data**: Handle datasets up to 1GB efficiently

---

## 🧪 Testing Strategy

### **Test Categories**
1. **Unit Tests**: Individual function/method testing
2. **Integration Tests**: Component interaction testing
3. **Statistical Tests**: Validation against known results
4. **Performance Tests**: Speed and memory benchmarks
5. **Regression Tests**: Ensure no functionality breaks
6. **Property-Based Tests**: Use Hypothesis for edge cases

### **Coverage Requirements**
- **Minimum**: 95% line coverage
- **Target**: 98% line coverage
- **Critical paths**: 100% coverage for core algorithms
- **Documentation**: All public APIs must have docstring examples that run

### **Continuous Integration**
```yaml
# .github/workflows/ci.yml structure
name: CI
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]
        os: [ubuntu-latest, windows-latest, macos-latest]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
      - name: Install dependencies
      - name: Run tests
      - name: Run linting
      - name: Check coverage
      - name: Performance benchmarks
```

---

## 📚 Documentation Standards

### **Docstring Template**

```python
def factorial_design_generator(
    factors: List[Factor], 
    replicates: int = 1,
    center_points: int = 0
) -> pd.DataFrame:
    """
    Generate a full factorial experimental design.
    
    Creates a complete factorial design matrix with all possible combinations
    of factor levels. Supports both categorical and continuous factors with
    optional center points and replication.
    
    Parameters
    ----------
    factors : List[Factor]
        List of experimental factors. Each factor must have at least 2 levels.
    replicates : int, default=1
        Number of replicates for each treatment combination. Must be positive.
    center_points : int, default=0
        Number of center point runs to add. Only applicable for continuous factors.
        
    Returns
    -------
    pd.DataFrame
        Design matrix with columns for each factor plus metadata columns:
        - RunID: Unique identifier for each run
        - Replicate: Replicate number
        - DesignPoint: Type of design point ('Factorial' or 'Center')
        
    Raises
    ------
    DesignError
        If factors list is empty or any factor has fewer than 2 levels.
    ValueError
        If replicates is not positive or center_points is negative.
        
    Examples
    --------
    >>> from industrialstats import Factor, factorial_design_generator
    >>> factors = [
    ...     Factor("Temperature", [100, 200], "continuous"),
    ...     Factor("Catalyst", ["A", "B"], "categorical")
    ... ]
    >>> design = factorial_design_generator(factors, replicates=2)
    >>> print(design.shape)
    (8, 6)
    
    >>> # With center points
    >>> design_with_center = factorial_design_generator(
    ...     factors, replicates=1, center_points=3
    ... )
    >>> center_runs = design_with_center[
    ...     design_with_center['DesignPoint'] == 'Center'
    ... ]
    >>> print(len(center_runs))
    3
    
    Notes
    -----
    The design matrix is automatically randomized unless explicitly disabled.
    For reproducible designs, set a random seed before calling this function.
    
    The number of runs in the resulting design is:
    n_runs = (∏ len(factor.levels)) × replicates + center_points
    
    References
    ----------
    .. [1] Montgomery, D.C. (2017). Design and Analysis of Experiments, 9th ed.
    .. [2] Box, G.E.P., Hunter, J.S., Hunter, W.G. (2005). Statistics for 
           Experimenters, 2nd ed.
    """
```

### **README Section Requirements**
Each major module should have a README section explaining:
- **Purpose and scope**
- **Key classes and functions**
- **Usage examples**
- **Mathematical background** (where applicable)
- **Literature references**

---

## 🚀 Deployment Instructions

### **Package Structure Validation**

Before implementing, validate the package structure:

```bash
# Check structure matches README specification
find src/ -type f -name "*.py" | sort
find tests/ -type f -name "*.py" | sort
find examples/ -type f -name "*.py" | sort
find docs/ -type f -name "*.md" | sort
```

### **Development Workflow**

1. **Feature Branch**: Create feature branch from main
2. **Implementation**: Implement according to these instructions
3. **Testing**: Ensure all tests pass and coverage requirements met
4. **Documentation**: Update docs and examples
5. **Review**: Self-review code against quality standards
6. **PR Creation**: Create pull request with detailed description

### **Quality Gates**

Before marking any component as complete:
- [ ] All tests pass
- [ ] Coverage requirements met
- [ ] Documentation complete
- [ ] Examples work correctly
- [ ] Performance benchmarks within targets
- [ ] No linting errors
- [ ] Type checking passes

---

## 📋 Component Priority Matrix

### **Critical Path Components** (Must be implemented first)
1. **Base classes** (Factor, ExperimentalDesign)
2. **Factorial designs** (basic implementation)
3. **ANOVA analysis** (basic implementation)
4. **Basic plotting** (design space, main effects)
5. **Core testing framework**

### **High Priority Components**
1. **Response surface designs**
2. **Effects analysis**
3. **Power analysis**
4. **Enhanced visualizations**
5. **Example scripts**

### **Medium Priority Components**
1. **Optimal designs**
2. **Advanced model fitting**
3. **Interactive interfaces**
4. **Performance optimization**
5. **Advanced diagnostics**

### **Nice-to-Have Components**
1. **Web dashboard**
2. **Animation capabilities**
3. **Advanced mixture designs**
4. **Bayesian methods**
5. **Machine learning integration**

---

## 🔍 Code Review Checklist

When implementing any component, ensure:

### **Functionality**
- [ ] Implements all required methods from specifications
- [ ] Handles edge cases appropriately
- [ ] Provides meaningful error messages
- [ ] Follows established patterns and conventions

### **Quality**
- [ ] Code is readable and well-commented
- [ ] No code duplication
- [ ] Efficient algorithms and data structures
- [ ] Memory usage is reasonable

### **Testing**
- [ ] Comprehensive test coverage
- [ ] Tests are meaningful and thorough
- [ ] Performance tests where applicable
- [ ] Edge cases covered

### **Documentation**
- [ ] Complete docstrings with examples
- [ ] Type hints throughout
- [ ] README updates where needed
- [ ] Mathematical explanations for complex algorithms

### **Integration**
- [ ] Works with existing components
- [ ] Follows package conventions
- [ ] No breaking changes to public APIs
- [ ] Backward compatibility maintained

---

This document provides comprehensive guidance for implementing the industrialstats package systematically and maintaining high quality standards throughout the development process.
