"""ANOVA analysis for experimental designs."""

from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
import warnings


class ANOVAAnalysis:
    """Perform ANOVA analysis on experimental data."""
    
    def __init__(self, data: pd.DataFrame, response_column: str):
        """
        Initialize ANOVA analysis.
        
        Parameters:
        -----------
        data : pd.DataFrame
            Experimental data
        response_column : str
            Name of the response variable column
        """
        if response_column not in data.columns:
            raise ValueError(f"Response column '{response_column}' not found in data")
            
        self.data = data.copy()
        self.response = response_column
        self.model: Optional[sm.regression.linear_model.RegressionResultsWrapper] = None
        self.anova_table: Optional[pd.DataFrame] = None
        
        # Remove any rows with missing response values
        self.data = self.data.dropna(subset=[response_column])
        
        if len(self.data) == 0:
            raise ValueError("No valid data rows after removing missing values")
    
    def fit_model(self, formula: str) -> sm.regression.linear_model.RegressionResultsWrapper:
        """
        Fit linear model using R-style formula.
        
        Parameters:
        -----------
        formula : str
            Model formula in R-style syntax (e.g., 'response ~ factor1 * factor2')
            
        Returns:
        --------
        RegressionResultsWrapper
            Fitted model object
        """
        try:
            self.model = ols(formula, data=self.data).fit()
            return self.model
        except Exception as e:
            raise ValueError(f"Error fitting model with formula '{formula}': {str(e)}")
    
    def anova_table_calculation(self, typ: int = 2) -> pd.DataFrame:
        """
        Calculate ANOVA table.
        
        Parameters:
        -----------
        typ : int, default=2
            Type of ANOVA (1, 2, or 3)
            
        Returns:
        --------
        pd.DataFrame
            ANOVA table with Sum of Squares, degrees of freedom, Mean Squares, F-statistics, and p-values
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        try:
            self.anova_table = anova_lm(self.model, typ=typ)
            
            # Add additional columns for clarity
            self.anova_table['Mean_Square'] = (
                self.anova_table['sum_sq'] / self.anova_table['df']
            )
            
            # Calculate effect sizes (eta-squared and partial eta-squared)
            total_ss = self.anova_table['sum_sq'].sum()
            self.anova_table['Eta_Squared'] = (
                self.anova_table['sum_sq'] / total_ss
            )
            
            # Partial eta-squared (for Type II and III)
            if typ in [2, 3]:
                error_ss = self.anova_table.loc['Residual', 'sum_sq'] if 'Residual' in self.anova_table.index else 0
                self.anova_table['Partial_Eta_Squared'] = (
                    self.anova_table['sum_sq'] / 
                    (self.anova_table['sum_sq'] + error_ss)
                )
            
            # Add significance stars
            def add_significance_stars(p_value):
                if pd.isna(p_value):
                    return ''
                elif p_value < 0.001:
                    return '***'
                elif p_value < 0.01:
                    return '**'
                elif p_value < 0.05:
                    return '*'
                elif p_value < 0.1:
                    return '.'
                else:
                    return ''
            
            self.anova_table['Significance'] = self.anova_table['PR(>F)'].apply(add_significance_stars)
            
            return self.anova_table
            
        except Exception as e:
            raise ValueError(f"Error calculating ANOVA table: {str(e)}")
    
    def multiple_comparisons(self, factor: str, method: str = 'tukey', 
                           alpha: float = 0.05) -> pd.DataFrame:
        """
        Perform multiple comparison tests.
        
        Parameters:
        -----------
        factor : str
            Factor name for pairwise comparisons
        method : str, default='tukey'
            Multiple comparison method ('tukey', 'bonferroni', 'holm')
        alpha : float, default=0.05
            Family-wise error rate
            
        Returns:
        --------
        pd.DataFrame
            Pairwise comparison results
        """
        if factor not in self.data.columns:
            raise ValueError(f"Factor '{factor}' not found in data")
        
        if method.lower() == 'tukey':
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
            
            mc_result = pairwise_tukeyhsd(
                self.data[self.response], 
                self.data[factor],
                alpha=alpha
            )
            
            # Convert to DataFrame
            mc_df = pd.DataFrame({
                'Group1': mc_result.groupsunique[mc_result._multicomp.pairindices[0]],
                'Group2': mc_result.groupsunique[mc_result._multicomp.pairindices[1]], 
                'Mean_Diff': mc_result.meandiffs,
                'P_adj': mc_result.pvalues,
                'Lower_CI': mc_result.confint[:, 0],
                'Upper_CI': mc_result.confint[:, 1],
                'Reject_H0': mc_result.reject
            })
            
            return mc_df
            
        elif method.lower() == 'bonferroni':
            # Bonferroni correction
            groups = self.data[factor].unique()
            n_comparisons = len(groups) * (len(groups) - 1) // 2
            bonferroni_alpha = alpha / n_comparisons
            
            results = []
            for i, group1 in enumerate(groups):
                for group2 in groups[i+1:]:
                    data1 = self.data[self.data[factor] == group1][self.response]
                    data2 = self.data[self.data[factor] == group2][self.response]
                    
                    # Perform t-test
                    t_stat, p_val = stats.ttest_ind(data1, data2)
                    
                    # Bonferroni adjusted p-value
                    p_adj = min(p_val * n_comparisons, 1.0)
                    
                    # Confidence interval for difference
                    diff = data1.mean() - data2.mean()
                    pooled_se = np.sqrt((data1.var()/len(data1)) + (data2.var()/len(data2)))
                    df = len(data1) + len(data2) - 2
                    t_critical = stats.t.ppf(1 - bonferroni_alpha/2, df)
                    margin_error = t_critical * pooled_se
                    
                    results.append({
                        'Group1': group1,
                        'Group2': group2,
                        'Mean_Diff': diff,
                        'P_adj': p_adj,
                        'Lower_CI': diff - margin_error,
                        'Upper_CI': diff + margin_error,
                        'Reject_H0': p_adj < alpha
                    })
            
            return pd.DataFrame(results)
            
        else:
            raise NotImplementedError(f"Method '{method}' not implemented")
    
    def residual_analysis(self) -> Dict[str, np.ndarray]:
        """
        Perform comprehensive residual analysis.
        
        Returns:
        --------
        Dict[str, np.ndarray]
            Dictionary containing various residual statistics
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        residuals = self.model.resid
        fitted_values = self.model.fittedvalues
        
        # Standardized residuals
        mse = self.model.mse_resid
        standardized_residuals = residuals / np.sqrt(mse)
        
        # Studentized residuals
        influence = self.model.get_influence()
        leverage = influence.hat_matrix_diag
        studentized_residuals = residuals / (np.sqrt(mse * (1 - leverage)))
        
        # Externally studentized residuals
        externally_studentized = influence.resid_studentized_external
        
        # Cook's distance
        cooks_d = influence.cooks_distance[0]
        
        return {
            'residuals': residuals,
            'fitted_values': fitted_values,
            'standardized_residuals': standardized_residuals,
            'studentized_residuals': studentized_residuals,
            'externally_studentized_residuals': externally_studentized,
            'leverage': leverage,
            'cooks_distance': cooks_d
        }
    
    def assumptions_tests(self) -> Dict[str, Dict[str, Any]]:
        """
        Test ANOVA assumptions.
        
        Returns:
        --------
        Dict[str, Dict[str, Any]]
            Test results for normality, homogeneity of variance, and independence
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        residuals = self.model.resid
        results = {}
        
        # 1. Normality test (Shapiro-Wilk)
        try:
            shapiro_stat, shapiro_p = stats.shapiro(residuals)
            results['normality'] = {
                'test': 'Shapiro-Wilk',
                'statistic': shapiro_stat,
                'p_value': shapiro_p,
                'assumption_met': shapiro_p > 0.05,
                'interpretation': 'Residuals are normally distributed' if shapiro_p > 0.05 else 'Residuals may not be normally distributed'
            }
        except Exception as e:
            results['normality'] = {
                'test': 'Shapiro-Wilk',
                'error': str(e),
                'assumption_met': None
            }
        
        # 2. Homogeneity of variance (Levene's test)
        try:
            # Get factor columns (exclude response and metadata)
            factor_cols = [col for col in self.data.columns 
                          if col not in [self.response, 'RunID', 'RunOrder', 'Replicate']]
            
            if factor_cols:
                # Use first factor for Levene's test
                main_factor = factor_cols[0]
                groups = [self.data[self.data[main_factor] == level][self.response].values 
                         for level in self.data[main_factor].unique()]
                
                levene_stat, levene_p = stats.levene(*groups)
                results['homogeneity'] = {
                    'test': 'Levene',
                    'statistic': levene_stat,
                    'p_value': levene_p,
                    'assumption_met': levene_p > 0.05,
                    'interpretation': 'Variances are homogeneous' if levene_p > 0.05 else 'Variances may be heterogeneous'
                }
            else:
                results['homogeneity'] = {
                    'test': 'Levene',
                    'error': 'No factors found for testing',
                    'assumption_met': None
                }
        except Exception as e:
            results['homogeneity'] = {
                'test': 'Levene',
                'error': str(e),
                'assumption_met': None
            }
        
        # 3. Independence test (Durbin-Watson)
        try:
            from statsmodels.stats.diagnostic import durbin_watson
            dw_stat = durbin_watson(residuals)
            
            # DW statistic interpretation
            if 1.5 <= dw_stat <= 2.5:
                independence_met = True
                interpretation = 'No evidence of autocorrelation'
            else:
                independence_met = False
                interpretation = 'Possible autocorrelation detected'
            
            results['independence'] = {
                'test': 'Durbin-Watson',
                'statistic': dw_stat,
                'assumption_met': independence_met,
                'interpretation': interpretation,
                'note': 'Values around 2 indicate no autocorrelation'
            }
        except Exception as e:
            results['independence'] = {
                'test': 'Durbin-Watson',
                'error': str(e),
                'assumption_met': None
            }
        
        return results
    
    def model_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive model summary.
        
        Returns:
        --------
        Dict[str, Any]
            Model fit statistics and summary information
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        return {
            'r_squared': self.model.rsquared,
            'adj_r_squared': self.model.rsquared_adj,
            'f_statistic': self.model.fvalue,
            'f_pvalue': self.model.f_pvalue,
            'mse': self.model.mse_resid,
            'rmse': np.sqrt(self.model.mse_resid),
            'aic': self.model.aic,
            'bic': self.model.bic,
            'n_observations': self.model.nobs,
            'df_residuals': self.model.df_resid,
            'df_model': self.model.df_model
        }
    
    def contrast_analysis(self, contrasts: Dict[str, List[float]], 
                         factor: str) -> pd.DataFrame:
        """
        Perform contrast analysis.
        
        Parameters:
        -----------
        contrasts : Dict[str, List[float]]
            Dictionary of contrast names and coefficient vectors
        factor : str
            Factor name for contrasts
            
        Returns:
        --------
        pd.DataFrame
            Contrast analysis results
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_model() first.")
        
        if factor not in self.data.columns:
            raise ValueError(f"Factor '{factor}' not found in data")
        
        # Get factor levels and means
        factor_levels = sorted(self.data[factor].unique())
        group_means = [self.data[self.data[factor] == level][self.response].mean() 
                      for level in factor_levels]
        group_ns = [len(self.data[self.data[factor] == level]) 
                   for level in factor_levels]
        
        mse = self.model.mse_resid
        results = []
        
        for contrast_name, coefficients in contrasts.items():
            if len(coefficients) != len(factor_levels):
                raise ValueError(f"Contrast '{contrast_name}' must have {len(factor_levels)} coefficients")
            
            # Calculate contrast value
            contrast_value = sum(c * m for c, m in zip(coefficients, group_means))
            
            # Calculate standard error
            se_squared = mse * sum(c**2 / n for c, n in zip(coefficients, group_ns))
            se = np.sqrt(se_squared)
            
            # Calculate t-statistic and p-value
            t_stat = contrast_value / se
            df = self.model.df_resid
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
            
            # Confidence interval
            t_critical = stats.t.ppf(0.975, df)
            ci_lower = contrast_value - t_critical * se
            ci_upper = contrast_value + t_critical * se
            
            results.append({
                'Contrast': contrast_name,
                'Value': contrast_value,
                'SE': se,
                't_statistic': t_stat,
                'p_value': p_value,
                'CI_Lower': ci_lower,
                'CI_Upper': ci_upper,
                'Significant': p_value < 0.05
            })
        
        return pd.DataFrame(results)
    
    def power_analysis_post_hoc(self, alpha: float = 0.05) -> Dict[str, float]:
        """
        Calculate observed power for each effect in the model.
        
        Parameters:
        -----------
        alpha : float, default=0.05
            Significance level
            
        Returns:
        --------
        Dict[str, float]
            Observed power for each effect
        """
        if self.anova_table is None:
            raise ValueError("ANOVA table not calculated. Call anova_table_calculation() first.")
        
        from scipy.stats import ncf
        
        powers = {}
        
        for effect in self.anova_table.index:
            if effect != 'Residual' and 'F' in self.anova_table.columns:
                f_stat = self.anova_table.loc[effect, 'F']
                df1 = self.anova_table.loc[effect, 'df']
                df2 = self.anova_table.loc['Residual', 'df'] if 'Residual' in self.anova_table.index else 1
                
                if not pd.isna(f_stat) and f_stat > 0:
                    # Non-centrality parameter
                    lambda_nc = f_stat * df1
                    
                    # Critical F-value
                    f_critical = stats.f.ppf(1 - alpha, df1, df2)
                    
                    # Observed power
                    power = 1 - ncf.cdf(f_critical, df1, df2, lambda_nc)
                    powers[effect] = power
        
        return powers
