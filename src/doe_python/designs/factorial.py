"""Full factorial experimental designs."""

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from itertools import product
from .base import ExperimentalDesign, Factor


class FactorialDesign(ExperimentalDesign):
    """Full factorial experimental design (2^k, 3^k, mixed factorials)."""
    
    def __init__(self, factors: List[Factor], replicates: int = 1, 
                 center_points: int = 0, randomize: bool = True):
        """
        Initialize factorial design.
        
        Parameters:
        -----------
        factors : List[Factor]
            List of factors for the experiment
        replicates : int, default=1
            Number of replicates for each treatment combination
        center_points : int, default=0
            Number of center points to add (for continuous factors)
        randomize : bool, default=True
            Whether to randomize the run order automatically
        """
        super().__init__("Full Factorial Design")
        self.factors = factors
        self.replicates = replicates
        self.center_points = center_points
        self.randomize_flag = randomize
        
        if replicates < 1:
            raise ValueError("Number of replicates must be at least 1")
        if center_points < 0:
            raise ValueError("Number of center points cannot be negative")
    
    def generate_design(self) -> pd.DataFrame:
        """Generate full factorial design matrix."""
        if not self.validate_design():
            raise ValueError("Invalid design configuration")
            
        # Generate all factor level combinations
        factor_levels = [factor.levels for factor in self.factors]
        combinations_list = list(product(*factor_levels))
        
        # Create base design
        design_data = []
        run_id = 1
        
        # Add factorial points
        for rep in range(self.replicates):
            for combo in combinations_list:
                row = {
                    'RunID': run_id,
                    'Replicate': rep + 1,
                    'DesignPoint': 'Factorial'
                }
                for i, factor in enumerate(self.factors):
                    row[factor.name] = combo[i]
                design_data.append(row)
                run_id += 1
                
        # Add center points if specified
        if self.center_points > 0:
            center_values = self._calculate_center_points()
            for cp in range(self.center_points):
                row = {
                    'RunID': run_id,
                    'Replicate': 1,  # Center points typically in first replicate
                    'DesignPoint': 'Center'
                }
                for i, factor in enumerate(self.factors):
                    row[factor.name] = center_values[i]
                design_data.append(row)
                run_id += 1
                
        self.design_matrix = pd.DataFrame(design_data)
        
        # Randomize if requested
        if self.randomize_flag:
            self.randomize()
            
        return self.design_matrix
    
    def _calculate_center_points(self) -> List[float]:
        """Calculate center point values for continuous factors."""
        center_values = []
        for factor in self.factors:
            if factor.factor_type == 'continuous':
                # For continuous factors, use the mean of levels
                center_values.append(np.mean(factor.levels))
            else:
                # For categorical factors, use middle level or most common
                middle_idx = len(factor.levels) // 2
                center_values.append(factor.levels[middle_idx])
        return center_values
    
    def validate_design(self) -> bool:
        """Validate factorial design parameters."""
        if not self.factors:
            return False
            
        # Check that all factors have at least 2 levels
        for factor in self.factors:
            if len(factor.levels) < 2:
                return False
                
        if self.replicates < 1:
            return False
            
        return True
    
    def n_runs(self) -> int:
        """Calculate total number of experimental runs."""
        if not self.factors:
            return 0
        factorial_runs = np.prod([len(f.levels) for f in self.factors]) * self.replicates
        return factorial_runs + self.center_points
    
    def n_factorial_runs(self) -> int:
        """Calculate number of factorial runs (excluding center points)."""
        if not self.factors:
            return 0
        return np.prod([len(f.levels) for f in self.factors]) * self.replicates
    
    def degrees_of_freedom(self) -> Dict[str, int]:
        """Calculate degrees of freedom for ANOVA analysis."""
        if not self.factors:
            return {}
            
        dof = {}
        total_runs = self.n_runs()
        
        # Main effects
        for factor in self.factors:
            dof[factor.name] = len(factor.levels) - 1
            
        # Two-factor interactions
        for i in range(len(self.factors)):
            for j in range(i + 1, len(self.factors)):
                interaction_name = f"{self.factors[i].name}*{self.factors[j].name}"
                dof[interaction_name] = dof[self.factors[i].name] * dof[self.factors[j].name]
        
        # Three-factor interactions (for designs with 3+ factors)
        if len(self.factors) >= 3:
            for i in range(len(self.factors)):
                for j in range(i + 1, len(self.factors)):
                    for k in range(j + 1, len(self.factors)):
                        interaction_name = f"{self.factors[i].name}*{self.factors[j].name}*{self.factors[k].name}"
                        dof[interaction_name] = (dof[self.factors[i].name] * 
                                               dof[self.factors[j].name] * 
                                               dof[self.factors[k].name])
        
        # Error degrees of freedom
        model_dof = sum(dof.values()) + 1  # +1 for intercept
        dof['Error'] = total_runs - model_dof
        dof['Total'] = total_runs - 1
        
        return dof
    
    def calculate_effects(self, response_data: List[float]) -> Dict[str, float]:
        """
        Calculate main effects and interactions for 2-level factors.
        
        Parameters:
        -----------
        response_data : List[float]
            Response values corresponding to each row in design matrix
            
        Returns:
        --------
        Dict[str, float]
            Dictionary of effect names and their calculated values
        """
        if not self._is_two_level_design():
            raise ValueError("Effect calculation only supported for 2-level designs")
            
        if len(response_data) != len(self.design_matrix):
            raise ValueError("Response data length doesn't match design matrix")
            
        effects = {}
        n_factors = len(self.factors)
        
        # Convert to coded levels (-1, +1)
        coded_matrix = self._get_coded_matrix()
        
        # Main effects
        for i, factor in enumerate(self.factors):
            high_responses = [response_data[j] for j in range(len(response_data)) 
                            if coded_matrix.iloc[j, i] == 1]
            low_responses = [response_data[j] for j in range(len(response_data)) 
                           if coded_matrix.iloc[j, i] == -1]
            
            effect = np.mean(high_responses) - np.mean(low_responses)
            effects[factor.name] = effect
            
        # Two-factor interactions
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                interaction_column = coded_matrix.iloc[:, i] * coded_matrix.iloc[:, j]
                
                high_responses = [response_data[k] for k in range(len(response_data)) 
                                if interaction_column.iloc[k] == 1]
                low_responses = [response_data[k] for k in range(len(response_data)) 
                               if interaction_column.iloc[k] == -1]
                
                effect = np.mean(high_responses) - np.mean(low_responses)
                effects[f"{self.factors[i].name}*{self.factors[j].name}"] = effect
                
        return effects
    
    def _is_two_level_design(self) -> bool:
        """Check if all factors have exactly 2 levels."""
        return all(len(factor.levels) == 2 for factor in self.factors)
    
    def _get_coded_matrix(self) -> pd.DataFrame:
        """Convert factorial design to coded levels (-1, +1)."""
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")
            
        coded_data = []
        for _, row in self.design_matrix.iterrows():
            coded_row = {}
            for factor in self.factors:
                if len(factor.levels) == 2:
                    # For 2-level factors: low level = -1, high level = +1
                    coded_row[factor.name] = -1 if row[factor.name] == factor.levels[0] else 1
                else:
                    # For multi-level factors, normalize to [-1, 1] range
                    level_idx = factor.levels.index(row[factor.name])
                    coded_row[factor.name] = 2 * level_idx / (len(factor.levels) - 1) - 1
            coded_data.append(coded_row)
            
        return pd.DataFrame(coded_data)
    
    def power_analysis(self, effect_size: float, alpha: float = 0.05, 
                      power: float = 0.8) -> Dict[str, Any]:
        """
        Calculate power analysis for the factorial design.
        
        Parameters:
        -----------
        effect_size : float
            Expected effect size (Cohen's f)
        alpha : float, default=0.05
            Type I error rate
        power : float, default=0.8
            Desired statistical power
            
        Returns:
        --------
        Dict[str, Any]
            Power analysis results
        """
        from scipy.stats import f, ncf
        
        # Degrees of freedom calculation
        if not self.factors:
            raise ValueError("No factors defined")
            
        df_treatment = np.prod([len(f.levels) for f in self.factors]) - 1
        df_error = (np.prod([len(f.levels) for f in self.factors]) * 
                   self.replicates) - np.prod([len(f.levels) for f in self.factors])
        
        # Non-centrality parameter
        n_total = np.prod([len(f.levels) for f in self.factors]) * self.replicates
        lambda_nc = (effect_size ** 2) * n_total / len(self.factors)
        
        # Critical F-value
        f_critical = f.ppf(1 - alpha, df_treatment, df_error)
        
        # Power calculation
        calculated_power = 1 - ncf.cdf(f_critical, df_treatment, df_error, lambda_nc)
        
        return {
            'effect_size': effect_size,
            'alpha': alpha,
            'target_power': power,
            'calculated_power': calculated_power,
            'df_treatment': df_treatment,
            'df_error': df_error,
            'n_total': n_total,
            'f_critical': f_critical,
            'lambda_nc': lambda_nc
        }
