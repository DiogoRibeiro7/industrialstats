"""Power analysis and sample size determination for experimental designs."""

from typing import List, Dict, Optional, Any, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class PowerAnalysisResult:
    """Container for power analysis results."""
    effect_size: float
    alpha: float
    power: float
    sample_size: int
    test_type: str
    additional_info: Dict[str, Any]


class PowerAnalysis:
    """
    Comprehensive power analysis for experimental designs.
    
    Supports power calculations for t-tests, ANOVA, factorial designs,
    and regression models.
    """
    
    def __init__(self):
        """Initialize power analysis."""
        self.results_history: List[PowerAnalysisResult] = []
    
    def t_test_power(self, effect_size: Optional[float] = None,
                    alpha: float = 0.05, power: Optional[float] = None,
                    sample_size: Optional[int] = None,
                    test_type: str = "two_sample") -> PowerAnalysisResult:
        """
        Power analysis for t-tests.
        
        Parameters:
        -----------
        effect_size : float, optional
            Cohen's d effect size
        alpha : float, default=0.05
            Type I error rate
        power : float, optional
            Statistical power (1 - β)
        sample_size : int, optional
            Sample size per group
        test_type : str, default="two_sample"
            Type of t-test: "one_sample", "two_sample", "paired"
            
        Returns:
        --------
        PowerAnalysisResult
            Power analysis results
        """
        # Validate inputs
        non_none_params = sum(x is not None for x in [effect_size, power, sample_size])
        if non_none_params != 2:
            raise ValueError("Exactly two of effect_size, power, sample_size must be specified")
        
        if test_type not in ["one_sample", "two_sample", "paired"]:
            raise ValueError("test_type must be 'one_sample', 'two_sample', or 'paired'")
        
        # Calculate missing parameter
        if effect_size is None:
            effect_size = self._solve_for_effect_size_t_test(
                alpha, power, sample_size, test_type
            )
        elif power is None:
            power = self._calculate_power_t_test(
                effect_size, alpha, sample_size, test_type
            )
        elif sample_size is None:
            sample_size = self._solve_for_sample_size_t_test(
                effect_size, alpha, power, test_type
            )
        
        # Additional calculations
        additional_info = {
            'critical_value': stats.t.ppf(1 - alpha/2, sample_size - 1),
            'degrees_of_freedom': sample_size - 1 if test_type != "two_sample" else 2 * sample_size - 2,
            'minimum_detectable_difference': effect_size,
            'test_description': self._get_test_description(test_type)
        }
        
        result = PowerAnalysisResult(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            sample_size=sample_size,
            test_type=f"t_test_{test_type}",
            additional_info=additional_info
        )
        
        self.results_history.append(result)
        return result
    
    def anova_power(self, effect_size: Optional[float] = None,
                   alpha: float = 0.05, power: Optional[float] = None,
                   sample_size: Optional[int] = None,
                   n_groups: int = 3) -> PowerAnalysisResult:
        """
        Power analysis for one-way ANOVA.
        
        Parameters:
        -----------
        effect_size : float, optional
            Cohen's f effect size
        alpha : float, default=0.05
            Type I error rate
        power : float, optional
            Statistical power
        sample_size : int, optional
            Sample size per group
        n_groups : int, default=3
            Number of groups
            
        Returns:
        --------
        PowerAnalysisResult
            Power analysis results
        """
        # Validate inputs
        non_none_params = sum(x is not None for x in [effect_size, power, sample_size])
        if non_none_params != 2:
            raise ValueError("Exactly two of effect_size, power, sample_size must be specified")
        
        if n_groups < 2:
            raise ValueError("n_groups must be at least 2")
        
        # Calculate missing parameter
        if effect_size is None:
            effect_size = self._solve_for_effect_size_anova(
                alpha, power, sample_size, n_groups
            )
        elif power is None:
            power = self._calculate_power_anova(
                effect_size, alpha, sample_size, n_groups
            )
        elif sample_size is None:
            sample_size = self._solve_for_sample_size_anova(
                effect_size, alpha, power, n_groups
            )
        
        # Calculate additional metrics
        df_between = n_groups - 1
        df_within = n_groups * (sample_size - 1)
        total_n = n_groups * sample_size
        
        additional_info = {
            'n_groups': n_groups,
            'total_sample_size': total_n,
            'df_between': df_between,
            'df_within': df_within,
            'critical_f': stats.f.ppf(1 - alpha, df_between, df_within),
            'eta_squared': effect_size**2 / (1 + effect_size**2)
        }
        
        result = PowerAnalysisResult(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            sample_size=sample_size,
            test_type="one_way_anova",
            additional_info=additional_info
        )
        
        self.results_history.append(result)
        return result
    
    def factorial_power(self, effect_size: Optional[float] = None,
                       alpha: float = 0.05, power: Optional[float] = None,
                       replicates: Optional[int] = None,
                       factor_levels: List[int] = [2, 2]) -> PowerAnalysisResult:
        """
        Power analysis for factorial designs.
        
        Parameters:
        -----------
        effect_size : float, optional
            Cohen's f effect size for main effects
        alpha : float, default=0.05
            Type I error rate
        power : float, optional
            Statistical power
        replicates : int, optional
            Number of replicates
        factor_levels : List[int], default=[2, 2]
            Number of levels for each factor
            
        Returns:
        --------
        PowerAnalysisResult
            Power analysis results
        """
        # Validate inputs
        non_none_params = sum(x is not None for x in [effect_size, power, replicates])
        if non_none_params != 2:
            raise ValueError("Exactly two of effect_size, power, replicates must be specified")
        
        if len(factor_levels) < 1:
            raise ValueError("At least one factor required")
        
        # Calculate design parameters
        n_treatment_combinations = np.prod(factor_levels)
        
        # Calculate missing parameter
        if effect_size is None:
            effect_size = self._solve_for_effect_size_factorial(
                alpha, power, replicates, factor_levels
            )
        elif power is None:
            power = self._calculate_power_factorial(
                effect_size, alpha, replicates, factor_levels
            )
        elif replicates is None:
            replicates = self._solve_for_replicates_factorial(
                effect_size, alpha, power, factor_levels
            )
        
        # Calculate degrees of freedom for main effects
        main_effect_dfs = [levels - 1 for levels in factor_levels]
        
        # Calculate error degrees of freedom
        df_error = n_treatment_combinations * (replicates - 1)
        total_n = n_treatment_combinations * replicates
        
        additional_info = {
            'factor_levels': factor_levels,
            'n_factors': len(factor_levels),
            'n_treatment_combinations': n_treatment_combinations,
            'total_sample_size': total_n,
            'main_effect_dfs': main_effect_dfs,
            'df_error': df_error,
            'design_type': f"{len(factor_levels)}-factor factorial",
            'design_notation': 'x'.join(map(str, factor_levels))
        }
        
        result = PowerAnalysisResult(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            sample_size=replicates,
            test_type="factorial_design",
            additional_info=additional_info
        )
        
        self.results_history.append(result)
        return result
    
    def regression_power(self, effect_size: Optional[float] = None,
                        alpha: float = 0.05, power: Optional[float] = None,
                        sample_size: Optional[int] = None,
                        n_predictors: int = 1) -> PowerAnalysisResult:
        """
        Power analysis for multiple regression.
        
        Parameters:
        -----------
        effect_size : float, optional
            Cohen's f² effect size
        alpha : float, default=0.05
            Type I error rate
        power : float, optional
            Statistical power
        sample_size : int, optional
            Total sample size
        n_predictors : int, default=1
            Number of predictors in the model
            
        Returns:
        --------
        PowerAnalysisResult
            Power analysis results
        """
        # Validate inputs
        non_none_params = sum(x is not None for x in [effect_size, power, sample_size])
        if non_none_params != 2:
            raise ValueError("Exactly two of effect_size, power, sample_size must be specified")
        
        if n_predictors < 1:
            raise ValueError("n_predictors must be at least 1")
        
        # Calculate missing parameter
        if effect_size is None:
            effect_size = self._solve_for_effect_size_regression(
                alpha, power, sample_size, n_predictors
            )
        elif power is None:
            power = self._calculate_power_regression(
                effect_size, alpha, sample_size, n_predictors
            )
        elif sample_size is None:
            sample_size = self._solve_for_sample_size_regression(
                effect_size, alpha, power, n_predictors
            )
        
        # Calculate additional metrics
        df_model = n_predictors
        df_error = sample_size - n_predictors - 1
        
        if df_error <= 0:
            raise ValueError("Sample size too small for the number of predictors")
        
        r_squared = effect_size / (1 + effect_size)
        
        additional_info = {
            'n_predictors': n_predictors,
            'df_model': df_model,
            'df_error': df_error,
            'r_squared': r_squared,
            'adjusted_r_squared': 1 - (1 - r_squared) * (sample_size - 1) / df_error,
            'critical_f': stats.f.ppf(1 - alpha, df_model, df_error)
        }
        
        result = PowerAnalysisResult(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            sample_size=sample_size,
            test_type="multiple_regression",
            additional_info=additional_info
        )
        
        self.results_history.append(result)
        return result
    
    def power_curve(self, test_type: str, fixed_params: Dict[str, Any],
                   varying_param: str, param_range: List[float]) -> Dict[str, Any]:
        """
        Generate power curve by varying one parameter.
        
        Parameters:
        -----------
        test_type : str
            Type of test: "t_test", "anova", "factorial", "regression"
        fixed_params : Dict[str, Any]
            Fixed parameters for the analysis
        varying_param : str
            Parameter to vary: "effect_size", "sample_size", "alpha", "power"
        param_range : List[float]
            Range of values for the varying parameter
            
        Returns:
        --------
        Dict[str, Any]
            Power curve data and plot
        """
        results = []
        
        for param_value in param_range:
            # Set up parameters
            params = fixed_params.copy()
            params[varying_param] = param_value
            
            try:
                # Call appropriate power analysis method
                if test_type == "t_test":
                    result = self.t_test_power(**params)
                elif test_type == "anova":
                    result = self.anova_power(**params)
                elif test_type == "factorial":
                    result = self.factorial_power(**params)
                elif test_type == "regression":
                    result = self.regression_power(**params)
                else:
                    raise ValueError(f"Unknown test_type: {test_type}")
                
                results.append({
                    varying_param: param_value,
                    'effect_size': result.effect_size,
                    'alpha': result.alpha,
                    'power': result.power,
                    'sample_size': result.sample_size
                })
                
            except Exception as e:
                # Skip invalid parameter combinations
                continue
        
        if not results:
            raise ValueError("No valid parameter combinations found")
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_values = [r[varying_param] for r in results]
        
        if varying_param == "power":
            y_values = [r['effect_size'] for r in results]
            ax.set_ylabel('Effect Size')
        elif varying_param == "effect_size":
            y_values = [r['power'] for r in results]
            ax.set_ylabel('Statistical Power')
        elif varying_param == "sample_size":
            y_values = [r['power'] for r in results]
            ax.set_ylabel('Statistical Power')
        elif varying_param == "alpha":
            y_values = [r['power'] for r in results]
            ax.set_ylabel('Statistical Power')
        else:
            y_values = [r['power'] for r in results]
            ax.set_ylabel('Statistical Power')
        
        ax.plot(x_values, y_values, 'b-', linewidth=2, marker='o', markersize=4)
        ax.set_xlabel(varying_param.replace('_', ' ').title())
        ax.set_title(f'Power Curve: {test_type.replace("_", " ").title()}')
        ax.grid(True, alpha=0.3)
        
        # Add reference lines
        if varying_param != "power":
            ax.axhline(y=0.8, color='red', linestyle='--', alpha=0.7, label='Power = 0.8')
            ax.axhline(y=0.9, color='orange', linestyle='--', alpha=0.7, label='Power = 0.9')
            ax.legend()
        
        plt.tight_layout()
        
        return {
            'results': results,
            'figure': fig,
            'varying_param': varying_param,
            'test_type': test_type
        }
    
    def sample_size_table(self, test_type: str, effect_sizes: List[float],
                         powers: List[float] = [0.8, 0.9, 0.95],
                         alpha: float = 0.05, **kwargs) -> pd.DataFrame:
        """
        Generate sample size table for different effect sizes and powers.
        
        Parameters:
        -----------
        test_type : str
            Type of test
        effect_sizes : List[float]
            Effect sizes to include
        powers : List[float], default=[0.8, 0.9, 0.95]
            Power levels to include
        alpha : float, default=0.05
            Type I error rate
        **kwargs
            Additional parameters for specific tests
            
        Returns:
        --------
        pd.DataFrame
            Sample size table
        """
        table_data = []
        
        for effect_size in effect_sizes:
            row = {'Effect_Size': effect_size}
            
            for power in powers:
                try:
                    # Calculate sample size
                    if test_type == "t_test":
                        result = self.t_test_power(
                            effect_size=effect_size, alpha=alpha, power=power, **kwargs
                        )
                    elif test_type == "anova":
                        result = self.anova_power(
                            effect_size=effect_size, alpha=alpha, power=power, **kwargs
                        )
                    elif test_type == "factorial":
                        result = self.factorial_power(
                            effect_size=effect_size, alpha=alpha, power=power, **kwargs
                        )
                    elif test_type == "regression":
                        result = self.regression_power(
                            effect_size=effect_size, alpha=alpha, power=power, **kwargs
                        )
                    else:
                        raise ValueError(f"Unknown test_type: {test_type}")
                    
                    row[f'Power_{power}'] = result.sample_size
                    
                except Exception:
                    row[f'Power_{power}'] = np.nan
            
            table_data.append(row)
        
        return pd.DataFrame(table_data)
    
    def minimum_detectable_effect(self, test_type: str, alpha: float = 0.05,
                                 power: float = 0.8, sample_size: int = 20,
                                 **kwargs) -> PowerAnalysisResult:
        """
        Calculate minimum detectable effect for given design.
        
        Parameters:
        -----------
        test_type : str
            Type of test
        alpha : float, default=0.05
            Type I error rate
        power : float, default=0.8
            Statistical power
        sample_size : int, default=20
            Sample size
        **kwargs
            Additional parameters for specific tests
            
        Returns:
        --------
        PowerAnalysisResult
            Analysis with minimum detectable effect
        """
        if test_type == "t_test":
            return self.t_test_power(
                alpha=alpha, power=power, sample_size=sample_size, **kwargs
            )
        elif test_type == "anova":
            return self.anova_power(
                alpha=alpha, power=power, sample_size=sample_size, **kwargs
            )
        elif test_type == "factorial":
            return self.factorial_power(
                alpha=alpha, power=power, replicates=sample_size, **kwargs
            )
        elif test_type == "regression":
            return self.regression_power(
                alpha=alpha, power=power, sample_size=sample_size, **kwargs
            )
        else:
            raise ValueError(f"Unknown test_type: {test_type}")
    
    # Helper methods for calculations
    def _calculate_power_t_test(self, effect_size: float, alpha: float,
                               sample_size: int, test_type: str) -> float:
        """Calculate power for t-test."""
        if test_type == "one_sample":
            df = sample_size - 1
            ncp = effect_size * np.sqrt(sample_size)
        elif test_type == "two_sample":
            df = 2 * sample_size - 2
            ncp = effect_size * np.sqrt(sample_size / 2)
        elif test_type == "paired":
            df = sample_size - 1
            ncp = effect_size * np.sqrt(sample_size)
        
        critical_t = stats.t.ppf(1 - alpha/2, df)
        
        # Calculate power using non-central t-distribution
        from scipy.stats import nct
        power = 1 - nct.cdf(critical_t, df, ncp) + nct.cdf(-critical_t, df, ncp)
        
        return power
    
    def _calculate_power_anova(self, effect_size: float, alpha: float,
                              sample_size: int, n_groups: int) -> float:
        """Calculate power for ANOVA."""
        df_between = n_groups - 1
        df_within = n_groups * (sample_size - 1)
        
        # Non-centrality parameter
        ncp = effect_size**2 * n_groups * sample_size
        
        # Critical F-value
        critical_f = stats.f.ppf(1 - alpha, df_between, df_within)
        
        # Calculate power using non-central F-distribution
        from scipy.stats import ncf
        power = 1 - ncf.cdf(critical_f, df_between, df_within, ncp)
        
        return power
    
    def _calculate_power_factorial(self, effect_size: float, alpha: float,
                                  replicates: int, factor_levels: List[int]) -> float:
        """Calculate power for factorial design."""
        n_treatment_combinations = np.prod(factor_levels)
        df_error = n_treatment_combinations * (replicates - 1)
        
        # Use first factor for main effect calculation
        df_factor = factor_levels[0] - 1
        
        # Non-centrality parameter
        ncp = effect_size**2 * n_treatment_combinations * replicates
        
        # Critical F-value
        critical_f = stats.f.ppf(1 - alpha, df_factor, df_error)
        
        # Calculate power
        from scipy.stats import ncf
        power = 1 - ncf.cdf(critical_f, df_factor, df_error, ncp)
        
        return power
    
    def _calculate_power_regression(self, effect_size: float, alpha: float,
                                   sample_size: int, n_predictors: int) -> float:
        """Calculate power for regression."""
        df_model = n_predictors
        df_error = sample_size - n_predictors - 1
        
        # Non-centrality parameter
        ncp = effect_size * sample_size
        
        # Critical F-value
        critical_f = stats.f.ppf(1 - alpha, df_model, df_error)
        
        # Calculate power
        from scipy.stats import ncf
        power = 1 - ncf.cdf(critical_f, df_model, df_error, ncp)
        
        return power
    
    def _solve_for_sample_size_t_test(self, effect_size: float, alpha: float,
                                     power: float, test_type: str) -> int:
        """Solve for sample size in t-test."""
        # Use iterative search
        for n in range(2, 10000):
            calculated_power = self._calculate_power_t_test(effect_size, alpha, n, test_type)
            if calculated_power >= power:
                return n
        
        raise ValueError("Could not find adequate sample size")
    
    def _solve_for_sample_size_anova(self, effect_size: float, alpha: float,
                                    power: float, n_groups: int) -> int:
        """Solve for sample size in ANOVA."""
        # Use iterative search
        for n in range(2, 10000):
            calculated_power = self._calculate_power_anova(effect_size, alpha, n, n_groups)
            if calculated_power >= power:
                return n
        
        raise ValueError("Could not find adequate sample size")
    
    def _solve_for_replicates_factorial(self, effect_size: float, alpha: float,
                                       power: float, factor_levels: List[int]) -> int:
        """Solve for replicates in factorial design."""
        # Use iterative search
        for r in range(1, 1000):
            calculated_power = self._calculate_power_factorial(effect_size, alpha, r, factor_levels)
            if calculated_power >= power:
                return r
        
        raise ValueError("Could not find adequate number of replicates")
    
    def _solve_for_sample_size_regression(self, effect_size: float, alpha: float,
                                         power: float, n_predictors: int) -> int:
        """Solve for sample size in regression."""
        # Use iterative search
        for n in range(n_predictors + 2, 10000):
            calculated_power = self._calculate_power_regression(effect_size, alpha, n, n_predictors)
            if calculated_power >= power:
                return n
        
        raise ValueError("Could not find adequate sample size")
    
    def _solve_for_effect_size_t_test(self, alpha: float, power: float,
                                     sample_size: int, test_type: str) -> float:
        """Solve for effect size in t-test."""
        # Use binary search
        low, high = 0.01, 5.0
        tolerance = 1e-6
        
        while high - low > tolerance:
            mid = (low + high) / 2
            calculated_power = self._calculate_power_t_test(mid, alpha, sample_size, test_type)
            
            if calculated_power < power:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def _solve_for_effect_size_anova(self, alpha: float, power: float,
                                    sample_size: int, n_groups: int) -> float:
        """Solve for effect size in ANOVA."""
        # Use binary search
        low, high = 0.01, 5.0
        tolerance = 1e-6
        
        while high - low > tolerance:
            mid = (low + high) / 2
            calculated_power = self._calculate_power_anova(mid, alpha, sample_size, n_groups)
            
            if calculated_power < power:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def _solve_for_effect_size_factorial(self, alpha: float, power: float,
                                        replicates: int, factor_levels: List[int]) -> float:
        """Solve for effect size in factorial design."""
        # Use binary search
        low, high = 0.01, 5.0
        tolerance = 1e-6
        
        while high - low > tolerance:
            mid = (low + high) / 2
            calculated_power = self._calculate_power_factorial(mid, alpha, replicates, factor_levels)
            
            if calculated_power < power:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def _solve_for_effect_size_regression(self, alpha: float, power: float,
                                         sample_size: int, n_predictors: int) -> float:
        """Solve for effect size in regression."""
        # Use binary search
        low, high = 0.01, 5.0
        tolerance = 1e-6
        
        while high - low > tolerance:
            mid = (low + high) / 2
            calculated_power = self._calculate_power_regression(mid, alpha, sample_size, n_predictors)
            
            if calculated_power < power:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def _get_test_description(self, test_type: str) -> str:
        """Get description of test type."""
        descriptions = {
            "one_sample": "One-sample t-test (compare mean to known value)",
            "two_sample": "Two-sample t-test (compare two independent groups)",
            "paired": "Paired t-test (compare paired observations)"
        }
        return descriptions.get(test_type, "Unknown test type")
    
    def summary_report(self) -> str:
        """Generate summary report of all power analyses performed."""
        if not self.results_history:
            return "No power analyses performed yet."
        
        report = "POWER ANALYSIS SUMMARY REPORT\n"
        report += "=" * 50 + "\n\n"
        
        for i, result in enumerate(self.results_history, 1):
            report += f"Analysis {i}: {result.test_type.replace('_', ' ').title()}\n"
            report += "-" * 30 + "\n"
            report += f"Effect Size: {result.effect_size:.4f}\n"
            report += f"Alpha: {result.alpha}\n"
            report += f"Power: {result.power:.4f}\n"
            report += f"Sample Size: {result.sample_size}\n"
            
            # Add test-specific information
            if 'n_groups' in result.additional_info:
                report += f"Number of Groups: {result.additional_info['n_groups']}\n"
            if 'n_factors' in result.additional_info:
                report += f"Number of Factors: {result.additional_info['n_factors']}\n"
            if 'n_predictors' in result.additional_info:
                report += f"Number of Predictors: {result.additional_info['n_predictors']}\n"
            
            report += "\n"
        
        return report
