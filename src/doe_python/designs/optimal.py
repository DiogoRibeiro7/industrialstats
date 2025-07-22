"""Optimal experimental designs using algorithmic approaches."""

from typing import List, Optional, Dict, Any, Tuple, Callable
import pandas as pd
import numpy as np
from itertools import combinations
from .base import ExperimentalDesign, Factor


class OptimalDesign(ExperimentalDesign):
    """
    Generate optimal experimental designs using exchange algorithms.
    
    Supports D-optimal, A-optimal, G-optimal, and I-optimal criteria.
    """
    
    def __init__(self, factors: List[Factor], n_runs: int, 
                 criterion: str = "D", model_terms: Optional[List[str]] = None):
        """
        Initialize optimal design.
        
        Parameters:
        -----------
        factors : List[Factor]
            List of experimental factors
        n_runs : int
            Number of experimental runs
        criterion : str, default="D"
            Optimality criterion: "D", "A", "G", or "I"
        model_terms : List[str], optional
            Model terms to include. If None, uses main effects + interactions
        """
        super().__init__(f"{criterion}-Optimal Design")
        
        if criterion not in ["D", "A", "G", "I"]:
            raise ValueError("criterion must be 'D', 'A', 'G', or 'I'")
        
        if n_runs < len(factors) + 1:
            raise ValueError("n_runs must be greater than number of factors")
        
        self.factors = factors
        self.n_runs = n_runs
        self.criterion = criterion
        self.model_terms = model_terms or self._default_model_terms()
        self.candidate_set: Optional[pd.DataFrame] = None
        self.exchange_history: List[Dict[str, Any]] = []
        
    def _default_model_terms(self) -> List[str]:
        """Generate default model terms (main effects + two-factor interactions)."""
        terms = ["Intercept"]
        
        # Main effects
        for factor in self.factors:
            terms.append(factor.name)
        
        # Two-factor interactions
        for i, factor1 in enumerate(self.factors):
            for factor2 in self.factors[i+1:]:
                terms.append(f"{factor1.name}*{factor2.name}")
        
        return terms
    
    def generate_candidate_set(self, grid_density: int = 5) -> pd.DataFrame:
        """
        Generate candidate set of all possible design points.
        
        Parameters:
        -----------
        grid_density : int, default=5
            Number of levels for continuous factors
            
        Returns:
        --------
        pd.DataFrame
            Candidate set
        """
        candidate_points = []
        
        # Generate levels for each factor
        factor_levels = []
        for factor in self.factors:
            if factor.factor_type == "categorical":
                factor_levels.append(factor.levels)
            else:
                # Create grid for continuous factors
                min_val = min(factor.levels)
                max_val = max(factor.levels)
                levels = np.linspace(min_val, max_val, grid_density)
                factor_levels.append(levels.tolist())
        
        # Generate all combinations
        from itertools import product
        for i, combination in enumerate(product(*factor_levels)):
            point = {'CandidateID': i + 1}
            for j, factor in enumerate(self.factors):
                point[factor.name] = combination[j]
            candidate_points.append(point)
        
        self.candidate_set = pd.DataFrame(candidate_points)
        return self.candidate_set
    
    def generate_design(self, max_iterations: int = 1000, 
                       random_start: bool = True, n_random_starts: int = 5) -> pd.DataFrame:
        """
        Generate optimal design using coordinate exchange algorithm.
        
        Parameters:
        -----------
        max_iterations : int, default=1000
            Maximum number of exchange iterations
        random_start : bool, default=True
            Whether to use random starting design
        n_random_starts : int, default=5
            Number of random starts to try
            
        Returns:
        --------
        pd.DataFrame
            Optimal design matrix
        """
        if not self.validate_design():
            raise ValueError("Invalid design configuration")
        
        if self.candidate_set is None:
            self.generate_candidate_set()
        
        best_design = None
        best_criterion_value = float('-inf') if self.criterion in ['D', 'A'] else float('inf')
        
        # Try multiple random starts
        for start in range(n_random_starts):
            design = self._coordinate_exchange(max_iterations, random_start)
            criterion_value = self._calculate_criterion(design)
            
            if self._is_better_criterion(criterion_value, best_criterion_value):
                best_design = design.copy()
                best_criterion_value = criterion_value
        
        self.design_matrix = best_design
        return self.design_matrix
    
    def _coordinate_exchange(self, max_iterations: int, random_start: bool) -> pd.DataFrame:
        """Perform coordinate exchange algorithm."""
        # Initialize design
        if random_start:
            current_design = self._random_initial_design()
        else:
            current_design = self._systematic_initial_design()
        
        current_criterion = self._calculate_criterion(current_design)
        
        for iteration in range(max_iterations):
            improved = False
            
            # Try to improve each point
            for run_idx in range(self.n_runs):
                best_replacement = None
                best_criterion_value = current_criterion
                
                # Try each candidate point as replacement
                for _, candidate in self.candidate_set.iterrows():
                    # Create trial design
                    trial_design = current_design.copy()
                    for factor in self.factors:
                        trial_design.loc[run_idx, factor.name] = candidate[factor.name]
                    
                    # Calculate criterion
                    trial_criterion = self._calculate_criterion(trial_design)
                    
                    # Check if improvement
                    if self._is_better_criterion(trial_criterion, best_criterion_value):
                        best_replacement = candidate
                        best_criterion_value = trial_criterion
                
                # Apply best replacement if found
                if best_replacement is not None:
                    for factor in self.factors:
                        current_design.loc[run_idx, factor.name] = best_replacement[factor.name]
                    current_criterion = best_criterion_value
                    improved = True
            
            # Record progress
            self.exchange_history.append({
                'iteration': iteration,
                'criterion_value': current_criterion,
                'improved': improved
            })
            
            # Stop if no improvement
            if not improved:
                break
        
        return current_design
    
    def _random_initial_design(self) -> pd.DataFrame:
        """Generate random initial design."""
        np.random.seed()  # Use random seed
        
        design_points = []
        for run in range(self.n_runs):
            # Randomly select from candidate set
            candidate_idx = np.random.randint(0, len(self.candidate_set))
            candidate = self.candidate_set.iloc[candidate_idx]
            
            point = {'RunID': run + 1}
            for factor in self.factors:
                point[factor.name] = candidate[factor.name]
            design_points.append(point)
        
        return pd.DataFrame(design_points)
    
    def _systematic_initial_design(self) -> pd.DataFrame:
        """Generate systematic initial design (space-filling)."""
        design_points = []
        
        # Use evenly spaced points from candidate set
        indices = np.linspace(0, len(self.candidate_set) - 1, self.n_runs, dtype=int)
        
        for i, run in enumerate(range(self.n_runs)):
            candidate = self.candidate_set.iloc[indices[i]]
            
            point = {'RunID': run + 1}
            for factor in self.factors:
                point[factor.name] = candidate[factor.name]
            design_points.append(point)
        
        return pd.DataFrame(design_points)
    
    def _calculate_criterion(self, design: pd.DataFrame) -> float:
        """Calculate optimality criterion value."""
        # Build model matrix
        X = self._build_model_matrix(design)
        
        try:
            # Calculate information matrix
            XtX = X.T @ X
            
            if self.criterion == "D":
                # D-optimal: maximize determinant of X'X
                return np.log(np.linalg.det(XtX))
            
            elif self.criterion == "A":
                # A-optimal: minimize trace of (X'X)^(-1)
                XtX_inv = np.linalg.inv(XtX)
                return -np.trace(XtX_inv)  # Negative for maximization
            
            elif self.criterion == "G":
                # G-optimal: minimize maximum prediction variance
                XtX_inv = np.linalg.inv(XtX)
                max_variance = 0
                
                # Check variance at all candidate points
                for _, candidate in self.candidate_set.iterrows():
                    x_point = self._build_point_vector(candidate)
                    variance = x_point.T @ XtX_inv @ x_point
                    max_variance = max(max_variance, variance)
                
                return -max_variance  # Negative for maximization
            
            elif self.criterion == "I":
                # I-optimal: minimize average prediction variance
                XtX_inv = np.linalg.inv(XtX)
                total_variance = 0
                
                # Average over all candidate points
                for _, candidate in self.candidate_set.iterrows():
                    x_point = self._build_point_vector(candidate)
                    variance = x_point.T @ XtX_inv @ x_point
                    total_variance += variance
                
                avg_variance = total_variance / len(self.candidate_set)
                return -avg_variance  # Negative for maximization
                
        except np.linalg.LinAlgError:
            # Singular matrix - return very bad criterion value
            return float('-inf')
    
    def _build_model_matrix(self, design: pd.DataFrame) -> np.ndarray:
        """Build model matrix X from design."""
        n_runs = len(design)
        n_terms = len(self.model_terms)
        X = np.zeros((n_runs, n_terms))
        
        for i, run in design.iterrows():
            for j, term in enumerate(self.model_terms):
                X[i, j] = self._evaluate_term(term, run)
        
        return X
    
    def _build_point_vector(self, point: pd.Series) -> np.ndarray:
        """Build model vector for a single point."""
        x = np.zeros(len(self.model_terms))
        
        for j, term in enumerate(self.model_terms):
            x[j] = self._evaluate_term(term, point)
        
        return x
    
    def _evaluate_term(self, term: str, point: pd.Series) -> float:
        """Evaluate model term at a point."""
        if term == "Intercept":
            return 1.0
        
        elif "*" in term:
            # Interaction term
            factors = term.split("*")
            value = 1.0
            for factor_name in factors:
                factor_value = point[factor_name]
                
                # Convert to coded value if continuous
                factor_obj = next(f for f in self.factors if f.name == factor_name)
                if factor_obj.factor_type == "continuous":
                    # Code as -1/+1
                    min_val = min(factor_obj.levels)
                    max_val = max(factor_obj.levels)
                    coded_value = 2 * (factor_value - min_val) / (max_val - min_val) - 1
                    value *= coded_value
                else:
                    # Categorical: use 0/1 coding
                    value *= 1.0 if factor_value == factor_obj.levels[-1] else 0.0
            
            return value
        
        else:
            # Main effect
            factor_obj = next(f for f in self.factors if f.name == term)
            factor_value = point[term]
            
            if factor_obj.factor_type == "continuous":
                # Code as -1/+1
                min_val = min(factor_obj.levels)
                max_val = max(factor_obj.levels)
                return 2 * (factor_value - min_val) / (max_val - min_val) - 1
            else:
                # Categorical: use 0/1 coding
                return 1.0 if factor_value == factor_obj.levels[-1] else 0.0
    
    def _is_better_criterion(self, new_value: float, current_value: float) -> bool:
        """Check if new criterion value is better than current."""
        if self.criterion in ["D", "A", "I"]:
            return new_value > current_value  # Maximize (or minimize negative)
        else:  # G-optimal
            return new_value > current_value  # Maximize (minimize negative)
    
    def validate_design(self) -> bool:
        """Validate optimal design parameters."""
        if len(self.factors) == 0:
            return False
        
        if self.n_runs < len(self.model_terms):
            return False
        
        if self.criterion not in ["D", "A", "G", "I"]:
            return False
        
        return True
    
    def design_efficiency(self, reference_design: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Calculate design efficiency metrics.
        
        Parameters:
        -----------
        reference_design : pd.DataFrame, optional
            Reference design for comparison. If None, uses orthogonal design
            
        Returns:
        --------
        Dict[str, float]
            Efficiency metrics
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")
        
        # Calculate current design criterion
        current_X = self._build_model_matrix(self.design_matrix)
        current_XtX = current_X.T @ current_X
        
        efficiencies = {}
        
        try:
            if self.criterion == "D":
                current_det = np.linalg.det(current_XtX)
                
                # D-efficiency relative to orthogonal design
                p = len(self.model_terms)
                max_det = (self.n_runs / p) ** p  # Theoretical maximum
                efficiencies['D_efficiency'] = (current_det / max_det) ** (1/p)
                
            elif self.criterion == "A":
                current_trace = np.trace(np.linalg.inv(current_XtX))
                
                # A-efficiency (simplified)
                p = len(self.model_terms)
                min_trace = p / self.n_runs  # Theoretical minimum
                efficiencies['A_efficiency'] = min_trace / current_trace
            
            # Relative efficiency compared to reference design
            if reference_design is not None:
                ref_X = self._build_model_matrix(reference_design)
                ref_XtX = ref_X.T @ ref_X
                
                if self.criterion == "D":
                    ref_det = np.linalg.det(ref_XtX)
                    efficiencies['Relative_D_efficiency'] = (current_det / ref_det) ** (1/p)
                
                elif self.criterion == "A":
                    ref_trace = np.trace(np.linalg.inv(ref_XtX))
                    efficiencies['Relative_A_efficiency'] = ref_trace / current_trace
        
        except np.linalg.LinAlgError:
            efficiencies['Error'] = "Singular information matrix"
        
        return efficiencies
    
    def prediction_variance_map(self, factor1: str, factor2: str, 
                               grid_size: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate prediction variance map for two factors.
        
        Parameters:
        -----------
        factor1, factor2 : str
            Factor names for the map
        grid_size : int, default=20
            Grid resolution
            
        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            X, Y, Z arrays for contour plotting
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")
        
        # Get factor objects
        factor1_obj = next(f for f in self.factors if f.name == factor1)
        factor2_obj = next(f for f in self.factors if f.name == factor2)
        
        # Create grid
        if factor1_obj.factor_type == "continuous":
            x_range = np.linspace(min(factor1_obj.levels), max(factor1_obj.levels), grid_size)
        else:
            x_range = factor1_obj.levels
        
        if factor2_obj.factor_type == "continuous":
            y_range = np.linspace(min(factor2_obj.levels), max(factor2_obj.levels), grid_size)
        else:
            y_range = factor2_obj.levels
        
        X, Y = np.meshgrid(x_range, y_range)
        Z = np.zeros_like(X)
        
        # Calculate information matrix
        design_X = self._build_model_matrix(self.design_matrix)
        XtX_inv = np.linalg.inv(design_X.T @ design_X)
        
        # Calculate prediction variance at each grid point
        for i in range(len(y_range)):
            for j in range(len(x_range)):
                # Create point with other factors at center
                point_data = {}
                for factor in self.factors:
                    if factor.name == factor1:
                        point_data[factor.name] = X[i, j]
                    elif factor.name == factor2:
                        point_data[factor.name] = Y[i, j]
                    else:
                        # Set other factors to center
                        if factor.factor_type == "continuous":
                            center = (min(factor.levels) + max(factor.levels)) / 2
                            point_data[factor.name] = center
                        else:
                            point_data[factor.name] = factor.levels[0]  # First level
                
                point = pd.Series(point_data)
                x_point = self._build_point_vector(point)
                variance = x_point.T @ XtX_inv @ x_point
                Z[i, j] = variance
        
        return X, Y, Z
    
    def augment_design(self, additional_runs: int, 
                      current_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Augment existing design with additional runs.
        
        Parameters:
        -----------
        additional_runs : int
            Number of additional runs to add
        current_data : pd.DataFrame, optional
            Current experimental data. If None, uses generated design
            
        Returns:
        --------
        pd.DataFrame
            Augmented design
        """
        if current_data is None:
            if self.design_matrix is None:
                raise ValueError("No current design available")
            current_data = self.design_matrix.copy()
        
        if self.candidate_set is None:
            self.generate_candidate_set()
        
        # Start with current design
        augmented_design = current_data.copy()
        current_n_runs = len(current_data)
        
        # Add runs one by one using exchange algorithm
        for new_run in range(additional_runs):
            best_addition = None
            best_criterion = float('-inf') if self.criterion in ['D', 'A'] else float('inf')
            
            # Try each candidate point
            for _, candidate in self.candidate_set.iterrows():
                # Create trial design with new point
                trial_design = augmented_design.copy()
                new_point = {'RunID': current_n_runs + new_run + 1}
                for factor in self.factors:
                    new_point[factor.name] = candidate[factor.name]
                
                trial_design = pd.concat([trial_design, pd.DataFrame([new_point])], 
                                       ignore_index=True)
                
                # Calculate criterion
                criterion_value = self._calculate_criterion(trial_design)
                
                if self._is_better_criterion(criterion_value, best_criterion):
                    best_addition = new_point
                    best_criterion = criterion_value
            
            # Add best point
            if best_addition is not None:
                augmented_design = pd.concat([augmented_design, pd.DataFrame([best_addition])], 
                                           ignore_index=True)
        
        return augmented_design
    
    def design_diagnostics(self) -> Dict[str, Any]:
        """
        Calculate design diagnostics and properties.
        
        Returns:
        --------
        Dict[str, Any]
            Diagnostic metrics
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")
        
        diagnostics = {}
        
        # Basic properties
        diagnostics['n_runs'] = len(self.design_matrix)
        diagnostics['n_factors'] = len(self.factors)
        diagnostics['n_model_terms'] = len(self.model_terms)
        diagnostics['criterion'] = self.criterion
        
        # Model matrix properties
        X = self._build_model_matrix(self.design_matrix)
        XtX = X.T @ X
        
        try:
            # Condition number
            eigenvalues = np.linalg.eigvals(XtX)
            condition_number = np.max(eigenvalues) / np.min(eigenvalues)
            diagnostics['condition_number'] = condition_number
            
            # Determinant
            diagnostics['determinant'] = np.linalg.det(XtX)
            
            # Trace
            diagnostics['trace'] = np.trace(XtX)
            
            # Minimum eigenvalue
            diagnostics['min_eigenvalue'] = np.min(eigenvalues)
            
            # Design criterion value
            diagnostics['criterion_value'] = self._calculate_criterion(self.design_matrix)
            
            # Correlation matrix
            correlation_matrix = np.corrcoef(X.T)
            diagnostics['max_correlation'] = np.max(np.abs(correlation_matrix - np.eye(len(self.model_terms))))
            
        except np.linalg.LinAlgError:
            diagnostics['error'] = "Singular information matrix"
        
        # Exchange algorithm convergence
        if self.exchange_history:
            diagnostics['exchange_iterations'] = len(self.exchange_history)
            diagnostics['final_improvement'] = self.exchange_history[-1]['improved']
            
            # Convergence plot data
            criterion_values = [h['criterion_value'] for h in self.exchange_history]
            diagnostics['convergence_history'] = criterion_values
        
        return diagnostics


class CustomOptimalDesign(OptimalDesign):
    """
    Custom optimal design with user-defined criterion function.
    """
    
    def __init__(self, factors: List[Factor], n_runs: int, 
                 criterion_function: Callable[[np.ndarray], float],
                 criterion_name: str = "Custom"):
        """
        Initialize custom optimal design.
        
        Parameters:
        -----------
        factors : List[Factor]
            List of experimental factors
        n_runs : int
            Number of experimental runs
        criterion_function : Callable[[np.ndarray], float]
            Function that takes model matrix X and returns criterion value
        criterion_name : str, default="Custom"
            Name for the custom criterion
        """
        super().__init__(factors, n_runs, criterion="D")  # Dummy criterion
        self.name = f"{criterion_name}-Optimal Design"
        self.criterion_function = criterion_function
        self.criterion_name = criterion_name
    
    def _calculate_criterion(self, design: pd.DataFrame) -> float:
        """Calculate custom criterion value."""
        X = self._build_model_matrix(design)
        try:
            return self.criterion_function(X)
        except:
            return float('-inf')  # Return bad value if function fails
