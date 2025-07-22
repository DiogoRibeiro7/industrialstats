"""Visualization functions for experimental designs and analysis."""

from typing import List, Dict, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings

# Set default style
plt.style.use('default')
sns.set_palette("husl")


class ExperimentPlotter:
    """Main plotting class for experimental designs and results."""
    
    def __init__(self, data: Optional[pd.DataFrame] = None, 
                 design_matrix: Optional[pd.DataFrame] = None):
        """
        Initialize the plotter.
        
        Parameters:
        -----------
        data : pd.DataFrame, optional
            Experimental data with results
        design_matrix : pd.DataFrame, optional
            Design matrix without results
        """
        self.data = data
        self.design_matrix = design_matrix
        
        if data is not None:
            self.factor_columns = [col for col in data.columns 
                                 if col not in ['RunID', 'RunOrder', 'Replicate', 'DesignPoint']]
        elif design_matrix is not None:
            self.factor_columns = [col for col in design_matrix.columns 
                                 if col not in ['RunID', 'RunOrder', 'Replicate', 'DesignPoint']]
        else:
            self.factor_columns = []
    
    def main_effects_plot(self, response_column: str, 
                         figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Create main effects plot showing factor level means.
        
        Parameters:
        -----------
        response_column : str
            Name of response variable column
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            Main effects plot
        """
        if self.data is None:
            raise ValueError("Data required for main effects plot")
        
        if response_column not in self.data.columns:
            raise ValueError(f"Response column '{response_column}' not found")
        
        # Get factor columns (exclude response and metadata)
        factors = [col for col in self.factor_columns if col != response_column]
        
        if not factors:
            raise ValueError("No factors found for plotting")
        
        # Calculate subplot arrangement
        n_factors = len(factors)
        n_cols = min(3, n_factors)
        n_rows = (n_factors + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_factors == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes if isinstance(axes, (list, np.ndarray)) else [axes]
        else:
            axes = axes.flatten()
        
        for i, factor in enumerate(factors):
            ax = axes[i]
            
            # Calculate factor level means
            factor_means = self.data.groupby(factor)[response_column].agg(['mean', 'std', 'count'])
            levels = factor_means.index
            means = factor_means['mean']
            stds = factor_means['std']
            counts = factor_means['count']
            
            # Calculate standard errors
            std_errors = stds / np.sqrt(counts)
            
            # Plot means with error bars
            x_pos = range(len(levels))
            bars = ax.bar(x_pos, means, alpha=0.7, capsize=5)
            ax.errorbar(x_pos, means, yerr=std_errors, fmt='none', 
                       color='black', capsize=5, capthick=2)
            
            # Customize plot
            ax.set_xlabel(factor)
            ax.set_ylabel(f'Mean {response_column}')
            ax.set_title(f'Main Effect: {factor}')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(levels)
            ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar, mean_val in zip(bars, means):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + std_errors[bar.get_x()],
                       f'{mean_val:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Hide unused subplots
        for i in range(n_factors, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    def interaction_plot(self, factor1: str, factor2: str, response_column: str,
                        figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create interaction plot between two factors.
        
        Parameters:
        -----------
        factor1 : str
            First factor name
        factor2 : str
            Second factor name
        response_column : str
            Response variable name
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            Interaction plot
        """
        if self.data is None:
            raise ValueError("Data required for interaction plot")
        
        # Validate inputs
        for factor in [factor1, factor2, response_column]:
            if factor not in self.data.columns:
                raise ValueError(f"Column '{factor}' not found in data")
        
        # Get factor levels
        levels1 = sorted(self.data[factor1].unique())
        levels2 = sorted(self.data[factor2].unique())
        
        # Calculate interaction means
        interaction_data = []
        for level1 in levels1:
            for level2 in levels2:
                subset = self.data[(self.data[factor1] == level1) & 
                                 (self.data[factor2] == level2)]
                if len(subset) > 0:
                    interaction_data.append({
                        factor1: level1,
                        factor2: level2,
                        'mean': subset[response_column].mean(),
                        'std': subset[response_column].std(),
                        'count': len(subset)
                    })
        
        interaction_df = pd.DataFrame(interaction_data)
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot lines for each level of factor1
        for level1 in levels1:
            subset = interaction_df[interaction_df[factor1] == level1]
            if len(subset) > 0:
                x_vals = [levels2.index(val) for val in subset[factor2]]
                y_vals = subset['mean'].values
                
                ax.plot(x_vals, y_vals, 'o-', label=f'{factor1} = {level1}', 
                       linewidth=2, markersize=8)
        
        # Customize plot
        ax.set_xlabel(factor2)
        ax.set_ylabel(f'Mean {response_column}')
        ax.set_title(f'Interaction Plot: {factor1} × {factor2}')
        ax.set_xticks(range(len(levels2)))
        ax.set_xticklabels(levels2)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def residual_plots(self, model_results: Dict[str, np.ndarray],
                      figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
        """
        Create comprehensive residual analysis plots.
        
        Parameters:
        -----------
        model_results : Dict[str, np.ndarray]
            Dictionary containing residuals, fitted values, etc.
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            Residual analysis plots
        """
        required_keys = ['residuals', 'fitted_values']
        for key in required_keys:
            if key not in model_results:
                raise ValueError(f"'{key}' not found in model_results")
        
        residuals = model_results['residuals']
        fitted_values = model_results['fitted_values']
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        # 1. Residuals vs Fitted
        axes[0, 0].scatter(fitted_values, residuals, alpha=0.6)
        axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        axes[0, 0].set_xlabel('Fitted Values')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].set_title('Residuals vs Fitted')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Add LOWESS smoother
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess
            smoothed = lowess(residuals, fitted_values, frac=0.3)
            axes[0, 0].plot(smoothed[:, 0], smoothed[:, 1], color='blue', linewidth=2)
        except ImportError:
            pass
        
        # 2. Q-Q Plot (Normal probability plot)
        stats.probplot(residuals, dist="norm", plot=axes[0, 1])
        axes[0, 1].set_title('Normal Q-Q Plot')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Scale-Location plot
        sqrt_abs_residuals = np.sqrt(np.abs(residuals))
        axes[1, 0].scatter(fitted_values, sqrt_abs_residuals, alpha=0.6)
        axes[1, 0].set_xlabel('Fitted Values')
        axes[1, 0].set_ylabel('√|Residuals|')
        axes[1, 0].set_title('Scale-Location Plot')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Add LOWESS smoother
        try:
            smoothed = lowess(sqrt_abs_residuals, fitted_values, frac=0.3)
            axes[1, 0].plot(smoothed[:, 0], smoothed[:, 1], color='blue', linewidth=2)
        except ImportError:
            pass
        
        # 4. Residuals vs Leverage (if available)
        if 'leverage' in model_results and 'cooks_distance' in model_results:
            leverage = model_results['leverage']
            cooks_d = model_results['cooks_distance']
            
            scatter = axes[1, 1].scatter(leverage, residuals, c=cooks_d, 
                                       alpha=0.6, cmap='Reds')
            axes[1, 1].set_xlabel('Leverage')
            axes[1, 1].set_ylabel('Residuals')
            axes[1, 1].set_title("Residuals vs Leverage")
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add Cook's distance contours
            x_range = np.linspace(leverage.min(), leverage.max(), 100)
            n = len(residuals)
            p = 2  # Simplified assumption
            
            for cook_level in [0.5, 1.0]:
                y_cook = np.sqrt(cook_level * p * (1 - x_range) / x_range)
                axes[1, 1].plot(x_range, y_cook, '--', alpha=0.5, 
                               label=f"Cook's D = {cook_level}")
                axes[1, 1].plot(x_range, -y_cook, '--', alpha=0.5)
            
            axes[1, 1].legend()
            plt.colorbar(scatter, ax=axes[1, 1], label="Cook's Distance")
        else:
            # Histogram of residuals
            axes[1, 1].hist(residuals, bins=20, alpha=0.7, edgecolor='black')
            axes[1, 1].set_xlabel('Residuals')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].set_title('Histogram of Residuals')
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def design_space_plot(self, factor1: str, factor2: str, 
                         response_column: Optional[str] = None,
                         figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """
        Create design space plot showing experimental points.
        
        Parameters:
        -----------
        factor1 : str
            First factor for x-axis
        factor2 : str
            Second factor for y-axis
        response_column : str, optional
            Response variable for color coding
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            Design space plot
        """
        data_to_use = self.data if self.data is not None else self.design_matrix
        
        if data_to_use is None:
            raise ValueError("Either data or design_matrix required")
        
        # Validate factors
        for factor in [factor1, factor2]:
            if factor not in data_to_use.columns:
                raise ValueError(f"Factor '{factor}' not found")
        
        fig, ax = plt.subplots(figsize=figsize)
        
        x = data_to_use[factor1]
        y = data_to_use[factor2]
        
        if response_column and response_column in data_to_use.columns:
            # Color by response
            scatter = ax.scatter(x, y, c=data_to_use[response_column], 
                               s=100, alpha=0.7, cmap='viridis', edgecolors='black')
            plt.colorbar(scatter, label=response_column)
        else:
            # Color by design point type if available
            if 'DesignPoint' in data_to_use.columns:
                design_types = data_to_use['DesignPoint'].unique()
                colors = plt.cm.Set1(np.linspace(0, 1, len(design_types)))
                
                for design_type, color in zip(design_types, colors):
                    mask = data_to_use['DesignPoint'] == design_type
                    ax.scatter(x[mask], y[mask], c=[color], label=design_type,
                             s=100, alpha=0.7, edgecolors='black')
                ax.legend()
            else:
                ax.scatter(x, y, s=100, alpha=0.7, edgecolors='black')
        
        # Add run numbers if available
        if 'RunOrder' in data_to_use.columns:
            for i, (xi, yi, run) in enumerate(zip(x, y, data_to_use['RunOrder'])):
                ax.annotate(str(run), (xi, yi), xytext=(5, 5), 
                          textcoords='offset points', fontsize=8, alpha=0.7)
        
        ax.set_xlabel(factor1)
        ax.set_ylabel(factor2)
        ax.set_title(f'Design Space: {factor1} vs {factor2}')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def factorial_cube_plot(self, factors: List[str], response_column: Optional[str] = None,
                           figsize: Tuple[int, int] = (10, 8)) -> plt.Figure:
        """
        Create 3D cube plot for 3-factor designs.
        
        Parameters:
        -----------
        factors : List[str]
            List of 3 factor names
        response_column : str, optional
            Response variable for color coding
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            3D factorial cube plot
        """
        if len(factors) != 3:
            raise ValueError("Exactly 3 factors required for cube plot")
        
        data_to_use = self.data if self.data is not None else self.design_matrix
        
        if data_to_use is None:
            raise ValueError("Either data or design_matrix required")
        
        # Validate factors
        for factor in factors:
            if factor not in data_to_use.columns:
                raise ValueError(f"Factor '{factor}' not found")
        
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        x = data_to_use[factors[0]]
        y = data_to_use[factors[1]]
        z = data_to_use[factors[2]]
        
        if response_column and response_column in data_to_use.columns:
            # Color by response
            scatter = ax.scatter(x, y, z, c=data_to_use[response_column], 
                               s=100, alpha=0.7, cmap='viridis')
            plt.colorbar(scatter, label=response_column, shrink=0.5)
        else:
            ax.scatter(x, y, z, s=100, alpha=0.7)
        
        # Add cube edges for 2-level factors
        factor_levels = {}
        for factor in factors:
            levels = sorted(data_to_use[factor].unique())
            if len(levels) == 2:
                factor_levels[factor] = levels
        
        if len(factor_levels) == 3:
            # Draw cube edges
            from itertools import product
            
            vertices = list(product(*[factor_levels[f] for f in factors]))
            
            # Define cube edges
            edges = [
                (0, 1), (2, 3), (4, 5), (6, 7),  # Parallel to factor 0
                (0, 2), (1, 3), (4, 6), (5, 7),  # Parallel to factor 1
                (0, 4), (1, 5), (2, 6), (3, 7)   # Parallel to factor 2
            ]
            
            for edge in edges:
                point1 = vertices[edge[0]]
                point2 = vertices[edge[1]]
                ax.plot([point1[0], point2[0]], [point1[1], point2[1]], 
                       [point1[2], point2[2]], 'k-', alpha=0.3)
        
        ax.set_xlabel(factors[0])
        ax.set_ylabel(factors[1])
        ax.set_zlabel(factors[2])
        ax.set_title(f'Factorial Cube: {" × ".join(factors)}')
        
        return fig
    
    def box_plots_by_factor(self, response_column: str, 
                           figsize: Tuple[int, int] = (15, 8)) -> plt.Figure:
        """
        Create box plots for each factor.
        
        Parameters:
        -----------
        response_column : str
            Response variable name
        figsize : Tuple[int, int]
            Figure size
            
        Returns:
        --------
        plt.Figure
            Box plots by factor
        """
        if self.data is None:
            raise ValueError("Data required for box plots")
        
        if response_column not in self.data.columns:
            raise ValueError(f"Response column '{response_column}' not found")
        
        factors = [col for col in self.factor_columns if col != response_column]
        
        if not factors:
            raise ValueError("No factors found for plotting")
        
        # Calculate subplot arrangement
        n_factors = len(factors)
        n_cols = min(3, n_factors)
        n_rows = (n_factors + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_factors == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes if isinstance(axes, (list, np.ndarray)) else [axes]
        else:
            axes = axes.flatten()
        
        for i, factor in enumerate(factors):
            ax = axes[i]
            
            # Create box plot
            factor_levels = sorted(self.data[factor].unique())
            box_data = [self.data[self.data[factor] == level][response_column].values 
                       for level in factor_levels]
            
            box_plot = ax.boxplot(box_data, labels=factor_levels, patch_artist=True)
            
            # Color the boxes
            colors = plt.cm.Set3(np.linspace(0, 1, len(factor_levels)))
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            ax.set_xlabel(factor)
            ax.set_ylabel(response_column)
            ax.set_title(f'Box Plot: {factor}')
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(n_factors, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return fig
