"""Response Surface Methodology (RSM) designs."""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np
from itertools import product
from .base import ExperimentalDesign, Factor


class ResponseSurfaceDesign(ExperimentalDesign):
    """
    Response Surface Design for optimization studies.
    
    Supports Central Composite Design (CCD), Box-Behnken Design (BBD),
    and custom response surface designs.
    """
    
    def __init__(self, factors: List[Factor], design_type: str = "CCD", 
                 alpha: Optional[float] = None, center_points: int = 5):
        """
        Initialize response surface design.
        
        Parameters:
        -----------
        factors : List[Factor]
            List of continuous factors (must be 2-level for coding)
        design_type : str, default="CCD"
            Type of design: "CCD" (Central Composite) or "BBD" (Box-Behnken)
        alpha : float, optional
            Alpha value for axial points (CCD only). If None, calculated for rotatability
        center_points : int, default=5
            Number of center point replicates
        """
        super().__init__(f"{design_type} Response Surface Design")
        
        if design_type not in ["CCD", "BBD"]:
            raise ValueError("design_type must be 'CCD' or 'BBD'")
        
        # Validate factors for RSM
        for factor in factors:
            if factor.factor_type != "continuous":
                raise ValueError("Response surface designs require continuous factors only")
            if len(factor.levels) != 2:
                raise ValueError("Factors must have exactly 2 levels for coding")
        
        self.factors = factors
        self.design_type = design_type
        self.center_points = center_points
        self.alpha = alpha
        
        if center_points < 1:
            raise ValueError("Must have at least 1 center point")
    
    def generate_design(self) -> pd.DataFrame:
        """Generate response surface design matrix."""
        if not self.validate_design():
            raise ValueError("Invalid design configuration")
        
        if self.design_type == "CCD":
            return self._generate_ccd()
        elif self.design_type == "BBD":
            return self._generate_bbd()
    
    def _generate_ccd(self) -> pd.DataFrame:
        """Generate Central Composite Design."""
        k = len(self.factors)  # Number of factors
        
        # Calculate alpha for rotatability if not specified
        if self.alpha is None:
            self.alpha = (2**k)**(1/4)  # Fourth root of 2^k
        
        design_points = []
        run_id = 1
        
        # 1. Factorial points (2^k)
        factorial_levels = [[-1, 1] for _ in range(k)]
        factorial_combinations = list(product(*factorial_levels))
        
        for combo in factorial_combinations:
            point = {
                'RunID': run_id,
                'DesignPoint': 'Factorial',
                'PointType': 'Factorial'
            }
            for i, factor in enumerate(self.factors):
                point[factor.name] = combo[i]
            design_points.append(point)
            run_id += 1
        
        # 2. Axial points (2k)
        for i in range(k):
            # Positive axial point
            point_pos = {
                'RunID': run_id,
                'DesignPoint': 'Axial',
                'PointType': 'Axial'
            }
            for j, factor in enumerate(self.factors):
                point_pos[factor.name] = self.alpha if i == j else 0
            design_points.append(point_pos)
            run_id += 1
            
            # Negative axial point
            point_neg = {
                'RunID': run_id,
                'DesignPoint': 'Axial',
                'PointType': 'Axial'
            }
            for j, factor in enumerate(self.factors):
                point_neg[factor.name] = -self.alpha if i == j else 0
            design_points.append(point_neg)
            run_id += 1
        
        # 3. Center points
        for cp in range(self.center_points):
            point = {
                'RunID': run_id,
                'DesignPoint': 'Center',
                'PointType': 'Center'
            }
            for factor in self.factors:
                point[factor.name] = 0  # Coded center
            design_points.append(point)
            run_id += 1
        
        # Convert to DataFrame
        self.design_matrix = pd.DataFrame(design_points)
        
        # Convert from coded to actual levels
        self._convert_to_actual_levels()
        
        return self.design_matrix
    
    def _generate_bbd(self) -> pd.DataFrame:
        """Generate Box-Behnken Design."""
        k = len(self.factors)
        
        if k < 3:
            raise ValueError("Box-Behnken design requires at least 3 factors")
        
        design_points = []
        run_id = 1
        
        # Box-Behnken points: each pair of factors at ±1, others at 0
        for i in range(k):
            for j in range(i + 1, k):
                # Four combinations for factors i and j
                for level_i in [-1, 1]:
                    for level_j in [-1, 1]:
                        point = {
                            'RunID': run_id,
                            'DesignPoint': 'BoxBehnken',
                            'PointType': 'BoxBehnken'
                        }
                        for idx, factor in enumerate(self.factors):
                            if idx == i:
                                point[factor.name] = level_i
                            elif idx == j:
                                point[factor.name] = level_j
                            else:
                                point[factor.name] = 0
                        design_points.append(point)
                        run_id += 1
        
        # Center points
        for cp in range(self.center_points):
            point = {
                'RunID': run_id,
                'DesignPoint': 'Center',
                'PointType': 'Center'
            }
            for factor in self.factors:
                point[factor.name] = 0
            design_points.append(point)
            run_id += 1
        
        # Convert to DataFrame
        self.design_matrix = pd.DataFrame(design_points)
        
        # Convert from coded to actual levels
        self._convert_to_actual_levels()
        
        return self.design_matrix
    
    def _convert_to_actual_levels(self):
        """Convert coded levels (-1, 0, +1, ±α) to actual factor levels."""
        for factor in self.factors:
            coded_values = self.design_matrix[factor.name].values
            
            # Calculate center and range
            low_level = factor.levels[0]
            high_level = factor.levels[1]
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2
            
            # Convert coded to actual
            actual_values = center + coded_values * half_range
            self.design_matrix[factor.name] = actual_values
    
    def validate_design(self) -> bool:
        """Validate response surface design parameters."""
        if len(self.factors) < 2:
            return False
        
        if self.design_type == "BBD" and len(self.factors) < 3:
            return False
        
        for factor in self.factors:
            if factor.factor_type != "continuous":
                return False
            if len(factor.levels) != 2:
                return False
        
        if self.center_points < 1:
            return False
        
        return True
    
    def n_runs(self) -> int:
        """Calculate total number of runs."""
        k = len(self.factors)
        
        if self.design_type == "CCD":
            factorial_runs = 2**k
            axial_runs = 2 * k
            return factorial_runs + axial_runs + self.center_points
        elif self.design_type == "BBD":
            # Box-Behnken: 2 * k * (k-1) + center points
            bbd_runs = 2 * k * (k - 1)
            return bbd_runs + self.center_points
    
    def design_properties(self) -> Dict[str, Any]:
        """Calculate design properties (rotatability, orthogonality, etc.)."""
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")
        
        k = len(self.factors)
        properties = {}
        
        # Basic properties
        properties['n_factors'] = k
        properties['n_runs'] = len(self.design_matrix)
        properties['design_type'] = self.design_type
        
        if self.design_type == "CCD":
            properties['alpha'] = self.alpha
            properties['rotatable'] = abs(self.alpha - (2**k)**(1/4)) < 0.001
            
            # Efficiency calculations
            factorial_runs = 2**k
            axial_runs = 2 * k
            center_runs = self.center_points
            
            properties['factorial_fraction'] = factorial_runs / self.n_runs()
            properties['axial_fraction'] = axial_runs / self.n_runs()
            properties['center_fraction'] = center_runs / self.n_runs()
        
        elif self.design_type == "BBD":
            properties['orthogonal'] = True  # Box-Behnken is always orthogonal
            properties['rotatable'] = False  # Box-Behnken is not rotatable
        
        return properties
    
    def prediction_variance(self, prediction_points: List[List[float]]) -> np.ndarray:
        """
        Calculate prediction variance at specified points.
        
        Parameters:
        -----------
        prediction_points : List[List[float]]
            Points where to calculate prediction variance (in coded units)
            
        Returns:
        --------
        np.ndarray
            Prediction variances
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")
        
        # Convert design matrix to coded units for calculation
        X_coded = self._get_design_matrix_coded()
        
        # Add intercept column
        X_coded = np.column_stack([np.ones(len(X_coded)), X_coded])
        
        # Add quadratic terms
        k = len(self.factors)
        for i in range(k):
            X_coded = np.column_stack([X_coded, X_coded[:, i+1]**2])
        
        # Add interaction terms
        for i in range(k):
            for j in range(i + 1, k):
                X_coded = np.column_stack([X_coded, X_coded[:, i+1] * X_coded[:, j+1]])
        
        # Calculate (X'X)^-1
        XtX_inv = np.linalg.inv(X_coded.T @ X_coded)
        
        # Calculate prediction variance for each point
        variances = []
        for point in prediction_points:
            # Create expanded point vector
            x_point = [1.0]  # intercept
            x_point.extend(point)  # linear terms
            x_point.extend([xi**2 for xi in point])  # quadratic terms
            
            # interaction terms
            for i in range(len(point)):
                for j in range(i + 1, len(point)):
                    x_point.append(point[i] * point[j])
            
            x_point = np.array(x_point)
            variance = x_point.T @ XtX_inv @ x_point
            variances.append(variance)
        
        return np.array(variances)
    
    def _get_design_matrix_coded(self) -> np.ndarray:
        """Get design matrix in coded units."""
        coded_matrix = np.zeros((len(self.design_matrix), len(self.factors)))
        
        for i, factor in enumerate(self.factors):
            actual_values = self.design_matrix[factor.name].values
            
            # Calculate coding parameters
            low_level = factor.levels[0]
            high_level = factor.levels[1]
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2
            
            # Convert to coded
            coded_matrix[:, i] = (actual_values - center) / half_range
        
        return coded_matrix
    
    def response_surface_analysis(self, response_data: List[float]) -> Dict[str, Any]:
        """
        Fit response surface model and analyze results.
        
        Parameters:
        -----------
        response_data : List[float]
            Response values for each design point
            
        Returns:
        --------
        Dict[str, Any]
            Analysis results including coefficients, model fit, optimum
        """
        if len(response_data) != len(self.design_matrix):
            raise ValueError("Response data length must match design matrix")
        
        # Get coded design matrix
        X_coded = self._get_design_matrix_coded()
        k = len(self.factors)
        
        # Build full quadratic model matrix
        # Intercept
        X_model = np.ones((len(X_coded), 1))
        term_names = ['Intercept']
        
        # Linear terms
        X_model = np.column_stack([X_model, X_coded])
        term_names.extend([f.name for f in self.factors])
        
        # Quadratic terms
        for i, factor in enumerate(self.factors):
            X_model = np.column_stack([X_model, X_coded[:, i]**2])
            term_names.append(f"{factor.name}²")
        
        # Interaction terms
        for i in range(k):
            for j in range(i + 1, k):
                X_model = np.column_stack([X_model, X_coded[:, i] * X_coded[:, j]])
                term_names.append(f"{self.factors[i].name}*{self.factors[j].name}")
        
        # Fit model using least squares
        y = np.array(response_data)
        
        try:
            # Calculate coefficients
            XtX_inv = np.linalg.inv(X_model.T @ X_model)
            coefficients = XtX_inv @ X_model.T @ y
            
            # Calculate fitted values and residuals
            y_fitted = X_model @ coefficients
            residuals = y - y_fitted
            
            # Calculate R-squared
            ss_total = np.sum((y - np.mean(y))**2)
            ss_residual = np.sum(residuals**2)
            r_squared = 1 - (ss_residual / ss_total)
            
            # Adjusted R-squared
            n = len(y)
            p = len(coefficients) - 1  # excluding intercept
            adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)
            
            # Standard errors
            mse = ss_residual / (n - len(coefficients))
            std_errors = np.sqrt(np.diag(XtX_inv) * mse)
            
            # t-statistics and p-values
            from scipy import stats
            t_stats = coefficients / std_errors
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - len(coefficients)))
            
            # Find optimum (coded units)
            optimum_coded = self._find_optimum_coded(coefficients, term_names)
            
            # Convert optimum to actual units
            optimum_actual = {}
            if optimum_coded is not None:
                for i, factor in enumerate(self.factors):
                    low_level = factor.levels[0]
                    high_level = factor.levels[1]
                    center = (low_level + high_level) / 2
                    half_range = (high_level - low_level) / 2
                    
                    actual_value = center + optimum_coded[i] * half_range
                    optimum_actual[factor.name] = actual_value
            
            # Prepare results
            results = {
                'coefficients': dict(zip(term_names, coefficients)),
                'std_errors': dict(zip(term_names, std_errors)),
                't_statistics': dict(zip(term_names, t_stats)),
                'p_values': dict(zip(term_names, p_values)),
                'r_squared': r_squared,
                'adj_r_squared': adj_r_squared,
                'rmse': np.sqrt(mse),
                'fitted_values': y_fitted,
                'residuals': residuals,
                'optimum_coded': optimum_coded,
                'optimum_actual': optimum_actual
            }
            
            return results
            
        except np.linalg.LinAlgError:
            raise ValueError("Unable to fit model - design matrix is singular")
    
    def _find_optimum_coded(self, coefficients: np.ndarray, term_names: List[str]) -> Optional[np.ndarray]:
        """Find stationary point (optimum) in coded units."""
        k = len(self.factors)
        
        # Extract linear coefficients (b vector)
        b = coefficients[1:k+1]
        
        # Extract quadratic coefficients (B matrix)
        B = np.zeros((k, k))
        
        # Diagonal elements (pure quadratic terms)
        for i in range(k):
            quad_term = f"{self.factors[i].name}²"
            if quad_term in term_names:
                idx = term_names.index(quad_term)
                B[i, i] = coefficients[idx]
        
        # Off-diagonal elements (interaction terms)
        for i in range(k):
            for j in range(i + 1, k):
                interaction_term = f"{self.factors[i].name}*{self.factors[j].name}"
                if interaction_term in term_names:
                    idx = term_names.index(interaction_term)
                    B[i, j] = B[j, i] = coefficients[idx] / 2  # Divide by 2 for symmetric matrix
        
        # Find stationary point: x_s = -0.5 * B^(-1) * b
        try:
            x_stationary = -0.5 * np.linalg.inv(B) @ b
            
            # Check if stationary point is within reasonable bounds
            if np.all(np.abs(x_stationary) <= 3):  # Within ±3 coded units
                return x_stationary
            else:
                return None  # Optimum outside reasonable region
                
        except np.linalg.LinAlgError:
            return None  # Singular matrix
    
    def contour_data(self, coefficients: Dict[str, float], 
                    factor1: str, factor2: str, 
                    grid_size: int = 20) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate contour plot data for two factors.
        
        Parameters:
        -----------
        coefficients : Dict[str, float]
            Model coefficients from response_surface_analysis
        factor1, factor2 : str
            Names of factors for contour plot
        grid_size : int, default=20
            Grid resolution
            
        Returns:
        --------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            X, Y, Z arrays for contour plotting
        """
        # Find factor indices
        factor1_idx = next(i for i, f in enumerate(self.factors) if f.name == factor1)
        factor2_idx = next(i for i, f in enumerate(self.factors) if f.name == factor2)
        
        # Create grid in coded units
        x_coded = np.linspace(-2, 2, grid_size)
        y_coded = np.linspace(-2, 2, grid_size)
        X_coded, Y_coded = np.meshgrid(x_coded, y_coded)
        
        # Calculate response surface
        Z = np.zeros_like(X_coded)
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Set other factors to center (0)
                point = np.zeros(len(self.factors))
                point[factor1_idx] = X_coded[i, j]
                point[factor2_idx] = Y_coded[i, j]
                
                # Calculate response using model
                response = coefficients['Intercept']
                
                # Linear terms
                for k, factor in enumerate(self.factors):
                    response += coefficients.get(factor.name, 0) * point[k]
                
                # Quadratic terms
                for k, factor in enumerate(self.factors):
                    response += coefficients.get(f"{factor.name}²", 0) * point[k]**2
                
                # Interaction terms
                for k in range(len(self.factors)):
                    for l in range(k + 1, len(self.factors)):
                        interaction_coef = coefficients.get(
                            f"{self.factors[k].name}*{self.factors[l].name}", 0
                        )
                        response += interaction_coef * point[k] * point[l]
                
                Z[i, j] = response
        
        # Convert grid to actual units
        factor1_obj = next(f for f in self.factors if f.name == factor1)
        factor2_obj = next(f for f in self.factors if f.name == factor2)
        
        # Factor 1 conversion
        center1 = (factor1_obj.levels[0] + factor1_obj.levels[1]) / 2
        range1 = (factor1_obj.levels[1] - factor1_obj.levels[0]) / 2
        X_actual = center1 + X_coded * range1
        
        # Factor 2 conversion
        center2 = (factor2_obj.levels[0] + factor2_obj.levels[1]) / 2
        range2 = (factor2_obj.levels[1] - factor2_obj.levels[0]) / 2
        Y_actual = center2 + Y_coded * range2
        
        return X_actual, Y_actual, Z
