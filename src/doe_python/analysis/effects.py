"""Effect calculation and analysis for experimental designs."""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns


class EffectsAnalysis:
    """Calculate and analyze factorial effects."""
    
    def __init__(self, design_matrix: pd.DataFrame, response_data: List[float]):
        """
        Initialize effects analysis.
        
        Parameters:
        -----------
        design_matrix : pd.DataFrame
            Experimental design matrix
        response_data : List[float]
            Response values corresponding to each row in design matrix
        """
        if len(response_data) != len(design_matrix):
            raise ValueError("Response data length must match design matrix rows")
            
        self.design_matrix = design_matrix.copy()
        self.response_data = np.array(response_data)
        self.effects: Optional[Dict[str, float]] = None
        
        # Identify factor columns (exclude metadata columns)
        metadata_cols = ['RunID', 'Replicate', 'DesignPoint', 'RunOrder']
        self.factor_names = [col for col in design_matrix.columns 
                           if col not in metadata_cols]
        
        if not self.factor_names:
            raise ValueError("No factor columns found in design matrix")
    
    def calculate_main_effects(self) -> Dict[str, float]:
        """
        Calculate main effects for all factors.
        
        Returns:
        --------
        Dict[str, float]
            Main effects for each factor
        """
        effects = {}
        
        for factor in self.factor_names:
            factor_levels = sorted(self.design_matrix[factor].unique())
            
            if len(factor_levels) == 2:
                # Two-level factor - calculate simple effect
                low_responses = self.response_data[
                    self.design_matrix[factor] == factor_levels[0]
                ]
                high_responses = self.response_data[
                    self.design_matrix[factor] == factor_levels[1]
                ]
                effects[factor] = np.mean(high_responses) - np.mean(low_responses)
                
            else:
                # Multi-level factor - use range of means
                level_means = []
                for level in factor_levels:
                    level_responses = self.response_data[
                        self.design_matrix[factor] == level
                    ]
                    level_means.append(np.mean(level_responses))
                
                # Effect as range (max - min of level means)
                effects[factor] = np.max(level_means) - np.min(level_means)
                
        return effects
    
    def calculate_interaction_effects(self, max_order: int = 2) -> Dict[str, float]:
        """
        Calculate interaction effects up to specified order.
        
        Parameters:
        -----------
        max_order : int, default=2
            Maximum interaction order to calculate
            
        Returns:
        --------
        Dict[str, float]
            Interaction effects
        """
        interactions = {}
        
        if max_order >= 2:
            # Two-factor interactions
            for i, factor1 in enumerate(self.factor_names):
                for factor2 in self.factor_names[i+1:]:
                    interaction_name = f"{factor1}*{factor2}"
                    interaction_effect = self._calculate_two_factor_interaction(
                        factor1, factor2
                    )
                    interactions[interaction_name] = interaction_effect
                    
        if max_order >= 3:
            # Three-factor interactions
            for i, factor1 in enumerate(self.factor_names):
                for j, factor2 in enumerate(self.factor_names[i+1:], i+1):
                    for factor3 in self.factor_names[j+1:]:
                        interaction_name = f"{factor1}*{factor2}*{factor3}"
                        interaction_effect = self._calculate_three_factor_interaction(
                            factor1, factor2, factor3
                        )
                        interactions[interaction_name] = interaction_effect
                        
        return interactions
    
    def _calculate_two_factor_interaction(self, factor1: str, factor2: str) -> float:
        """Calculate two-factor interaction effect."""
        levels1 = sorted(self.design_matrix[factor1].unique())
        levels2 = sorted(self.design_matrix[factor2].unique())
        
        if len(levels1) == 2 and len(levels2) == 2:
            # 2x2 interaction - classical calculation
            cell_means = {}
            for level1 in levels1:
                for level2 in levels2:
                    mask = ((self.design_matrix[factor1] == level1) & 
                           (self.design_matrix[factor2] == level2))
                    if mask.any():
                        cell_means[(level1, level2)] = np.mean(self.response_data[mask])
                    else:
                        cell_means[(level1, level2)] = 0
                        
            # Interaction effect calculation
            # AB = [(high,high) + (low,low) - (high,low) - (low,high)] / 2
            interaction = ((cell_means[(levels1[1], levels2[1])] + 
                          cell_means[(levels1[0], levels2[0])]) - 
                         (cell_means[(levels1[1], levels2[0])] + 
                          cell_means[(levels1[0], levels2[1])]))
            
            return interaction / 2
            
        else:
            # Multi-level factors - use ANOVA approach
            return self._anova_interaction_effect(factor1, factor2)
    
    def _calculate_three_factor_interaction(self, factor1: str, factor2: str, 
                                          factor3: str) -> float:
        """Calculate three-factor interaction effect."""
        levels1 = sorted(self.design_matrix[factor1].unique())
        levels2 = sorted(self.design_matrix[factor2].unique())
        levels3 = sorted(self.design_matrix[factor3].unique())
        
        if all(len(levels) == 2 for levels in [levels1, levels2, levels3]):
            # 2x2x2 interaction
            cell_means = {}
            for l1 in levels1:
                for l2 in levels2:
                    for l3 in levels3:
                        mask = ((self.design_matrix[factor1] == l1) & 
                               (self.design_matrix[factor2] == l2) &
                               (self.design_matrix[factor3] == l3))
                        if mask.any():
                            cell_means[(l1, l2, l3)] = np.mean(self.response_data[mask])
                        else:
                            cell_means[(l1, l2, l3)] = 0
                            
            # Three-factor interaction calculation (simplified)
            # ABC = sum of ((-1)^(a+b+c) * mean(abc)) / 4
            interaction = 0
            for i, l1 in enumerate(levels1):
                for j, l2 in enumerate(levels2):
                    for k, l3 in enumerate(levels3):
                        sign = (-1) ** (i + j + k)
                        interaction += sign * cell_means[(l1, l2, l3)]
                        
            return interaction / 4
            
        else:
            # Multi-level factors - use ANOVA approach
            return self._anova_interaction_effect(factor1, factor2, factor3)
    
    def _anova_interaction_effect(self, *factors) -> float:
        """Calculate interaction effect using ANOVA approach."""
        try:
            from statsmodels.formula.api import ols
            from statsmodels.stats.anova import anova_lm
            
            # Create temporary dataframe
            temp_df = self.design_matrix.copy()
            temp_df['response'] = self.response_data
            
            # Create formula
            factor_terms = [f'C({factor})' for factor in factors]
            interaction_term = ' * '.join(factor_terms)
            formula = f'response ~ {interaction_term}'
            
            # Fit model and get ANOVA table
            model = ols(formula, data=temp_df).fit()
            anova_table = anova_lm(model, typ=2)
            
            # Find interaction term in ANOVA table
            interaction_key = ':'.join([f'C({factor})' for factor in factors])
            
            for index in anova_table.index:
                if all(f'C({factor})' in index for factor in factors) and ':' in index:
                    if 'F' in anova_table.columns:
                        return anova_table.loc[index, 'F']
                    else:
                        return anova_table.loc[index, 'sum_sq']
                        
            return 0.0
            
        except Exception:
            return 0.0
    
    def normal_probability_plot(self, effects: Dict[str, float], 
                              alpha: float = 0.05, figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create normal probability plot for effect screening.
        
        Parameters:
        -----------
        effects : Dict[str, float]
            Dictionary of effects to plot
        alpha : float, default=0.05
            Significance level for reference lines
        figsize : Tuple[int, int], default=(10, 6)
            Figure size
            
        Returns:
        --------
        plt.Figure
            Normal probability plot
        """
        if not effects:
            raise ValueError("No effects provided for plotting")
            
        effect_values = np.array(list(effects.values()))
        effect_names = list(effects.keys())
        
        # Calculate theoretical quantiles
        n = len(effect_values)
        theoretical_quantiles = stats.norm.ppf(np.arange(1, n + 1) / (n + 1))
        
        # Sort effects by magnitude
        sorted_indices = np.argsort(effect_values)
        sorted_effects = effect_values[sorted_indices]
        sorted_names = np.array(effect_names)[sorted_indices]
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot points
        scatter = ax.scatter(theoretical_quantiles, sorted_effects, 
                           alpha=0.7, s=50, c='steelblue', edgecolors='black')
        
        # Add labels
        for i, name in enumerate(sorted_names):
            ax.annotate(name, (half_normal_quantiles[i], sorted_abs_effects[i]), 
                       xytext=(5, 5), textcoords='offset points', 
                       fontsize=9, alpha=0.8)
        
        # Add reference line for inactive effects
        # Use smallest effects to estimate noise line
        n_inactive = max(2, len(abs_effects) // 3)  # Assume 1/3 are inactive
        inactive_effects = sorted_abs_effects[:n_inactive]
        inactive_quantiles = half_normal_quantiles[:n_inactive]
        
        if len(inactive_effects) > 1:
            slope, intercept, r_value, _, _ = stats.linregress(
                inactive_quantiles, inactive_effects
            )
            line_x = np.array([0, half_normal_quantiles.max()])
            line_y = slope * line_x + intercept
            ax.plot(line_x, line_y, 'r--', alpha=0.8, 
                   label=f'Inactive effects line (R² = {r_value**2:.3f})')
        
        ax.set_xlabel('Half-Normal Quantiles')
        ax.set_ylabel('|Effects|')
        ax.set_title('Half-Normal Plot of Effects')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return fig
    
    def interaction_plots(self, max_interactions: int = 3, 
                         figsize: Tuple[int, int] = (15, 10)) -> plt.Figure:
        """
        Create interaction plots for significant two-factor interactions.
        
        Parameters:
        -----------
        max_interactions : int, default=3
            Maximum number of interaction plots to create
        figsize : Tuple[int, int], default=(15, 10)
            Figure size
            
        Returns:
        --------
        plt.Figure
            Interaction plots
        """
        # Calculate interaction effects
        interactions = self.calculate_interaction_effects()
        
        # Filter for two-factor interactions only
        two_factor_interactions = {
            name: effect for name, effect in interactions.items() 
            if name.count('*') == 1
        }
        
        if not two_factor_interactions:
            raise ValueError("No two-factor interactions found")
        
        # Sort by effect magnitude and take top interactions
        sorted_interactions = sorted(
            two_factor_interactions.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )[:max_interactions]
        
        # Create subplots
        n_plots = len(sorted_interactions)
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_plots == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for i, (interaction_name, effect) in enumerate(sorted_interactions):
            factor1, factor2 = interaction_name.split('*')
            
            # Get factor levels
            levels1 = sorted(self.design_matrix[factor1].unique())
            levels2 = sorted(self.design_matrix[factor2].unique())
            
            # Calculate cell means
            means_by_f1 = {}
            for level1 in levels1:
                means_by_f2 = []
                for level2 in levels2:
                    mask = ((self.design_matrix[factor1] == level1) & 
                           (self.design_matrix[factor2] == level2))
                    if mask.any():
                        means_by_f2.append(np.mean(self.response_data[mask]))
                    else:
                        means_by_f2.append(np.nan)
                means_by_f1[level1] = means_by_f2
            
            # Plot interaction
            ax = axes[i]
            for j, level1 in enumerate(levels1):
                valid_indices = ~np.isnan(means_by_f1[level1])
                if valid_indices.any():
                    x_vals = np.array(range(len(levels2)))[valid_indices]
                    y_vals = np.array(means_by_f1[level1])[valid_indices]
                    ax.plot(x_vals, y_vals, 'o-', label=f'{factor1}={level1}', 
                           linewidth=2, markersize=6)
            
            ax.set_xlabel(factor2)
            ax.set_ylabel('Response Mean')
            ax.set_title(f'{interaction_name}\nEffect = {effect:.3f}')
            ax.set_xticks(range(len(levels2)))
            ax.set_xticklabels(levels2)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # Hide unused subplots
        for i in range(len(sorted_interactions), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        return fig
    
    def effect_hierarchy_plot(self, figsize: Tuple[int, int] = (12, 8)) -> plt.Figure:
        """
        Create hierarchical plot showing main effects and interactions.
        
        Parameters:
        -----------
        figsize : Tuple[int, int], default=(12, 8)
            Figure size
            
        Returns:
        --------
        plt.Figure
            Effect hierarchy plot
        """
        # Get all effects
        main_effects = self.calculate_main_effects()
        interaction_effects = self.calculate_interaction_effects()
        
        # Organize by hierarchy
        effects_by_order = {1: main_effects}
        
        for name, effect in interaction_effects.items():
            order = name.count('*') + 1
            if order not in effects_by_order:
                effects_by_order[order] = {}
            effects_by_order[order][name] = effect
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        colors = ['steelblue', 'orange', 'green', 'red', 'purple']
        y_positions = []
        labels = []
        values = []
        colors_list = []
        
        y_pos = 0
        for order in sorted(effects_by_order.keys()):
            effects = effects_by_order[order]
            order_name = 'Main Effects' if order == 1 else f'{order}-Factor Interactions'
            
            # Add order separator
            if y_pos > 0:
                y_pos += 0.5
                
            # Sort effects within order
            sorted_effects = sorted(effects.items(), key=lambda x: abs(x[1]), reverse=True)
            
            for name, effect in sorted_effects:
                y_positions.append(y_pos)
                labels.append(name)
                values.append(effect)
                colors_list.append(colors[(order - 1) % len(colors)])
                y_pos += 1
            
            # Add order label
            ax.text(-max(abs(v) for v in values) * 1.1, y_pos - len(sorted_effects)/2 - 0.5, 
                   order_name, rotation=90, ha='center', va='center', 
                   fontsize=12, fontweight='bold')
        
        # Create horizontal bar plot
        bars = ax.barh(y_positions, values, color=colors_list, alpha=0.7)
        
        # Add value labels
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width + np.sign(width) * max(abs(v) for v in values) * 0.02, 
                   bar.get_y() + bar.get_height()/2, f'{value:.3f}',
                   ha='left' if width >= 0 else 'right', va='center', fontsize=9)
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel('Effect Size')
        ax.set_title('Effect Hierarchy Plot')
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig for points
        for i, name in enumerate(sorted_names):
            ax.annotate(name, (theoretical_quantiles[i], sorted_effects[i]), 
                       xytext=(5, 5), textcoords='offset points', 
                       fontsize=9, alpha=0.8)
        
        # Add reference line through center points
        center_indices = len(theoretical_quantiles) // 4, 3 * len(theoretical_quantiles) // 4
        if len(theoretical_quantiles) > 4:
            x_ref = theoretical_quantiles[center_indices[0]:center_indices[1]]
            y_ref = sorted_effects[center_indices[0]:center_indices[1]]
            
            if len(x_ref) > 1:
                slope, intercept, r_value, _, _ = stats.linregress(x_ref, y_ref)
                line_x = np.array([theoretical_quantiles.min(), theoretical_quantiles.max()])
                line_y = slope * line_x + intercept
                ax.plot(line_x, line_y, 'r--', alpha=0.8, 
                       label=f'Reference Line (R² = {r_value**2:.3f})')
        
        # Add significance bounds (rough estimate)
        if len(effect_values) > 3:
            # Use median absolute deviation for robust estimate
            mad = np.median(np.abs(sorted_effects - np.median(sorted_effects)))
            threshold = 2.5 * mad  # Rough significance threshold
            
            ax.axhline(y=threshold, color='orange', linestyle=':', alpha=0.6, 
                      label=f'Approximate significance threshold')
            ax.axhline(y=-threshold, color='orange', linestyle=':', alpha=0.6)
        
        ax.set_xlabel('Normal Quantiles')
        ax.set_ylabel('Effects')
        ax.set_title('Normal Probability Plot of Effects')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        return fig
    
    def pareto_chart(self, effects: Dict[str, float], 
                    figsize: Tuple[int, int] = (12, 6)) -> plt.Figure:
        """
        Create Pareto chart of effects.
        
        Parameters:
        -----------
        effects : Dict[str, float]
            Dictionary of effects to plot
        figsize : Tuple[int, int], default=(12, 6)
            Figure size
            
        Returns:
        --------
        plt.Figure
            Pareto chart
        """
        if not effects:
            raise ValueError("No effects provided for plotting")
            
        # Calculate absolute effects
        abs_effects = {name: abs(effect) for name, effect in effects.items()}
        
        # Sort by magnitude
        sorted_effects = sorted(abs_effects.items(), key=lambda x: x[1], reverse=True)
        names, values = zip(*sorted_effects)
        
        # Calculate cumulative percentage
        total = sum(values)
        cumulative_pct = np.cumsum(values) / total * 100
        
        # Create plot
        fig, ax1 = plt.subplots(figsize=figsize)
        
        # Bar chart
        bars = ax1.bar(range(len(names)), values, alpha=0.7, color='steelblue')
        ax1.set_xlabel('Effects')
        ax1.set_ylabel('Absolute Effect Size', color='steelblue')
        ax1.set_xticks(range(len(names)))
        ax1.set_xticklabels(names, rotation=45, ha='right')
        
        # Add effect values on bars
        for i, (bar, value) in enumerate(zip(bars, values)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.2f}', ha='center', va='bottom', fontsize=9)
        
        # Cumulative percentage line
        ax2 = ax1.twinx()
        line = ax2.plot(range(len(names)), cumulative_pct, 'ro-', 
                       color='red', alpha=0.7, linewidth=2, markersize=6)
        ax2.set_ylabel('Cumulative Percentage', color='red')
        ax2.set_ylim(0, 105)
        
        # Add percentage labels
        for i, pct in enumerate(cumulative_pct):
            ax2.text(i, pct + 2, f'{pct:.1f}%', ha='center', va='bottom', 
                    fontsize=8, color='red')
        
        # Add 80% line (Pareto principle)
        ax2.axhline(y=80, color='orange', linestyle='--', alpha=0.7, 
                   label='80% Line')
        ax2.legend(loc='lower right')
        
        plt.title('Pareto Chart of Effects')
        plt.tight_layout()
        
        return fig
    
    def effects_summary_table(self) -> pd.DataFrame:
        """
        Create comprehensive effects summary table.
        
        Returns:
        --------
        pd.DataFrame
            Summary of all calculated effects
        """
        # Calculate all effects
        main_effects = self.calculate_main_effects()
        interaction_effects = self.calculate_interaction_effects()
        
        all_effects = {**main_effects, **interaction_effects}
        
        if not all_effects:
            return pd.DataFrame()
        
        # Create summary
        summary_data = []
        for name, effect in all_effects.items():
            effect_type = 'Main' if '*' not in name else 'Interaction'
            order = name.count('*') + 1
            
            summary_data.append({
                'Effect': name,
                'Estimate': effect,
                'Abs_Estimate': abs(effect),
                'Type': effect_type,
                'Order': order
            })
            
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Abs_Estimate', ascending=False)
        
        # Add rankings
        summary_df['Rank'] = range(1, len(summary_df) + 1)
        
        # Add percentage contribution
        total_abs_effect = summary_df['Abs_Estimate'].sum()
        summary_df['Percent_Contribution'] = (
            summary_df['Abs_Estimate'] / total_abs_effect * 100
        ).round(2)
        
        # Add cumulative percentage
        summary_df['Cumulative_Percent'] = summary_df['Percent_Contribution'].cumsum()
        
        return summary_df
    
    def half_normal_plot(self, effects: Dict[str, float], 
                        figsize: Tuple[int, int] = (10, 6)) -> plt.Figure:
        """
        Create half-normal plot for effect screening.
        
        Parameters:
        -----------
        effects : Dict[str, float]
            Dictionary of effects to plot
        figsize : Tuple[int, int], default=(10, 6)
            Figure size
            
        Returns:
        --------
        plt.Figure
            Half-normal plot
        """
        if not effects:
            raise ValueError("No effects provided for plotting")
            
        # Use absolute values of effects
        abs_effects = np.array([abs(effect) for effect in effects.values()])
        effect_names = list(effects.keys())
        
        # Sort by magnitude
        sorted_indices = np.argsort(abs_effects)
        sorted_abs_effects = abs_effects[sorted_indices]
        sorted_names = np.array(effect_names)[sorted_indices]
        
        # Calculate half-normal quantiles
        n = len(abs_effects)
        half_normal_quantiles = stats.norm.ppf(0.5 + 0.5 * np.arange(1, n + 1) / (n + 1))
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot points
        ax.scatter(half_normal_quantiles, sorted_abs_effects, 
                  alpha=0.7, s=50, c='steelblue', edgecolors='black')
        
        # Add labels
