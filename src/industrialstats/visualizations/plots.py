"""Visualization functions for experimental designs and analysis."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from scipy import stats

from ..designs.base import ExperimentalDesign

# Set default style
plt.style.use("default")
sns.set_palette("husl")


class ExperimentPlotter:
    """Main plotting class for experimental designs and results."""

    def __init__(
        self,
        data: pd.DataFrame | None = None,
        design_matrix: pd.DataFrame | None = None,
    ):
        """Initialize the plotter.

        Parameters
        ----------
        data : pd.DataFrame, optional
            Data with responses.
        design_matrix : pd.DataFrame, optional
            Design matrix without responses.
        """
        self.data = data
        self.design_matrix = design_matrix

        if data is not None:
            self.factor_columns = [
                col
                for col in data.columns
                if col not in ["RunID", "RunOrder", "Replicate", "DesignPoint"]
            ]
        elif design_matrix is not None:
            self.factor_columns = [
                col
                for col in design_matrix.columns
                if col not in ["RunID", "RunOrder", "Replicate", "DesignPoint"]
            ]
        else:
            self.factor_columns = []

    def main_effects_plot(
        self, response_column: str, figsize: tuple[int, int] = (12, 8)
    ) -> plt.Figure:
        """Create a main-effects plot of factor level means.

        Parameters
        ----------
        response_column : str
            Column name of the response variable.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(12, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            Generated main-effects plot.

        Raises
        ------
        ValueError
            If data is missing or response column is invalid.
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
            factor_means = self.data.groupby(factor)[response_column].agg(
                ["mean", "std", "count"]
            )
            levels = factor_means.index
            means = factor_means["mean"]
            stds = factor_means["std"]
            counts = factor_means["count"]

            # Calculate standard errors
            std_errors = stds / np.sqrt(counts)

            # Plot means with error bars
            x_pos = range(len(levels))
            bars = ax.bar(x_pos, means, alpha=0.7, capsize=5)
            ax.errorbar(
                x_pos,
                means,
                yerr=std_errors,
                fmt="none",
                color="black",
                capsize=5,
                capthick=2,
            )

            # Customize plot
            ax.set_xlabel(factor)
            ax.set_ylabel(f"Mean {response_column}")
            ax.set_title(f"Main Effect: {factor}")
            ax.set_xticks(x_pos)
            ax.set_xticklabels(levels)
            ax.grid(True, alpha=0.3)

            # Add value labels on bars
            for idx, (bar, mean_val) in enumerate(zip(bars, means, strict=True)):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + std_errors.iloc[idx],
                    f"{mean_val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        # Hide unused subplots
        for i in range(n_factors, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        return fig

    @staticmethod
    def design_comparison_plot(
        designs: dict[str, ExperimentalDesign],
        figsize: tuple[int, int] = (12, 8),
    ) -> plt.Figure:
        """Compare multiple designs side by side.

        Parameters
        ----------
        designs : dict of str to ExperimentalDesign
            Mapping of design names to design instances with generated
            design matrices.
        figsize : tuple of int, optional
            Figure size for the plot grid. Defaults to ``(12, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            Figure containing design space plots and a metrics table.

        Raises
        ------
        ValueError
            If a design lacks a design matrix or has fewer than two factors.

        Examples
        --------
        >>> from industrialstats.designs.factorial import Factor, FactorialDesign
        >>> from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign
        >>> fd = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
        >>> fd.generate_design()
        >>> rcbd = RandomizedCompleteBlockDesign(["T1", "T2"], ["B1", "B2"])
        >>> rcbd.generate_design()
        >>> ExperimentPlotter.design_comparison_plot({"Factorial": fd, "RCBD": rcbd})
        <Figure size ...>
        """

        n_designs = len(designs)
        if n_designs == 0:
            raise ValueError("At least one design must be provided")

        fig = plt.figure(figsize=figsize)
        gs = fig.add_gridspec(2, n_designs, height_ratios=[3, 1])

        summary_rows: list[dict[str, Any]] = []

        for idx, (name, design) in enumerate(designs.items()):
            if design.design_matrix is None:
                raise ValueError(f"Design '{name}' has no design matrix")

            factors = [f.name for f in design.factors]
            if len(factors) < 2:
                raise ValueError(
                    f"Design '{name}' requires at least two factors for comparison"
                )

            ax = fig.add_subplot(gs[0, idx])
            x = design.design_matrix[factors[0]]
            y = design.design_matrix[factors[1]]
            ax.scatter(x, y, s=80, alpha=0.7, edgecolors="black")
            ax.set_xlabel(factors[0])
            ax.set_ylabel(factors[1])

            efficiency = design.design_efficiency.get("run_fraction", np.nan)
            run_count = len(design.design_matrix)

            ax.set_title(
                f"{name}\nRuns: {run_count} | Run frac: {efficiency:.2f}", fontsize=10
            )
            ax.grid(True, alpha=0.3)

            summary_rows.append(
                {
                    "Design": name,
                    "Runs": run_count,
                    "RunFraction": round(efficiency, 3),
                    "Factors": ", ".join(factors),
                    "Levels": ", ".join(
                        f"{f.name}:{len(f.levels)}" for f in design.factors
                    ),
                }
            )

        summary_df = pd.DataFrame(summary_rows)
        ax_table = fig.add_subplot(gs[1, :])
        ax_table.axis("off")
        table = ax_table.table(
            cellText=summary_df.astype(str).to_numpy().tolist(),
            colLabels=list(summary_df.columns),
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        ax_table.set_title("Design Comparison Metrics", pad=10)

        fig.tight_layout()
        return fig

    def interactive_design_explorer(
        self,
        response_column: str | None = None,
        filename: str | None = None,
    ) -> go.Figure:
        """Create an interactive design-space explorer using Plotly.

        Parameters
        ----------
        response_column : str, optional
            Column name of the response variable for color overlay.
        filename : str, optional
            Path to export the interactive plot as an HTML file.

        Returns
        -------
        plotly.graph_objects.Figure
            Generated interactive figure.

        Raises
        ------
        ValueError
            If neither data nor design matrix is available or fewer than two
            factors are present.

        Examples
        --------
        >>> from industrialstats.designs.factorial import Factor, FactorialDesign
        >>> design = FactorialDesign([Factor("A", [0, 1]), Factor("B", [0, 1])])
        >>> design.generate_design()
        >>> plotter = ExperimentPlotter(design_matrix=design.design_matrix)
        >>> fig = plotter.interactive_design_explorer()
        >>> isinstance(fig, go.Figure)
        True
        """

        dm = self.data if self.data is not None else self.design_matrix
        if dm is None:
            raise ValueError("Design matrix or data required for explorer")

        factors = [
            c
            for c in dm.columns
            if c not in ["RunID", "RunOrder", "Replicate", "DesignPoint"]
            and c != response_column
        ]
        if len(factors) < 2:
            raise ValueError("At least two factors are required")

        x_factor, y_factor = factors[:2]
        hover_cols = factors.copy()
        if response_column and response_column in dm.columns:
            hover_cols.append(response_column)

        marker_base: dict[str, Any] = {
            "size": 10,
            "line": {"width": 1, "color": "black"},
        }

        combos = dm[factors].drop_duplicates().reset_index(drop=True)
        traces = []
        for _, row in combos.iterrows():
            mask = (dm[factors] == row).all(axis=1)
            subset = dm[mask]
            marker_kwargs = marker_base.copy()
            if response_column and response_column in subset.columns:
                marker_kwargs.update(
                    color=subset[response_column],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar={"title": response_column},
                )
            hovertemplate = (
                "<br>".join(
                    [f"{col}: %{{customdata[{i}]}}" for i, col in enumerate(hover_cols)]
                )
                + "<extra></extra>"
            )
            traces.append(
                go.Scatter(
                    x=subset[x_factor],
                    y=subset[y_factor],
                    mode="markers",
                    customdata=subset[hover_cols].to_numpy(),
                    marker=marker_kwargs,
                    name=" | ".join(f"{f}={row[f]}" for f in factors),
                    hovertemplate=hovertemplate,
                )
            )

        fig = go.Figure(data=traces)

        updatemenus = []
        for idx, factor in enumerate(factors):
            buttons = []
            levels = ["All", *sorted(dm[factor].unique().tolist())]
            for level in levels:
                visibility = []
                for _, row in combos.iterrows():
                    if level == "All":
                        visibility.append(True)
                    else:
                        visibility.append(row[factor] == level)
                label = f"All {factor}" if level == "All" else f"{factor}={level}"
                buttons.append(
                    {
                        "label": label,
                        "method": "update",
                        "args": [{"visible": visibility}],
                    }
                )
            updatemenus.append(
                {
                    "buttons": buttons,
                    "direction": "down",
                    "x": 0.0,
                    "y": 1.15 - idx * 0.1,
                    "xanchor": "left",
                    "yanchor": "top",
                    "showactive": True,
                }
            )

        fig.update_layout(
            title="Interactive Design Explorer",
            xaxis_title=x_factor,
            yaxis_title=y_factor,
            updatemenus=updatemenus,
        )

        if filename:
            fig.write_html(filename)

        return fig

    def interaction_plot(
        self,
        factor1: str,
        factor2: str,
        response_column: str,
        figsize: tuple[int, int] = (10, 6),
    ) -> plt.Figure:
        """Create an interaction plot between two factors.

        Parameters
        ----------
        factor1 : str
            First factor name.
        factor2 : str
            Second factor name.
        response_column : str
            Response variable name.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(10, 6)``.

        Returns
        -------
        matplotlib.figure.Figure
            Interaction plot figure.
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
                subset = self.data[
                    (self.data[factor1] == level1) & (self.data[factor2] == level2)
                ]
                if len(subset) > 0:
                    interaction_data.append(
                        {
                            factor1: level1,
                            factor2: level2,
                            "mean": subset[response_column].mean(),
                            "std": subset[response_column].std(),
                            "count": len(subset),
                        }
                    )

        interaction_df = pd.DataFrame(interaction_data)

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        # Plot lines for each level of factor1
        for level1 in levels1:
            subset = interaction_df[interaction_df[factor1] == level1]
            if len(subset) > 0:
                x_vals = [levels2.index(val) for val in subset[factor2]]
                y_vals = subset["mean"].values

                ax.plot(
                    x_vals,
                    y_vals,
                    "o-",
                    label=f"{factor1} = {level1}",
                    linewidth=2,
                    markersize=8,
                )

        # Customize plot
        ax.set_xlabel(factor2)
        ax.set_ylabel(f"Mean {response_column}")
        ax.set_title(f"Interaction Plot: {factor1} × {factor2}")
        ax.set_xticks(range(len(levels2)))
        ax.set_xticklabels(levels2)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig

    def residual_plots(
        self, model_results: dict[str, np.ndarray], figsize: tuple[int, int] = (15, 10)
    ) -> plt.Figure:
        """Create comprehensive residual analysis plots.

        Parameters
        ----------
        model_results : dict[str, np.ndarray]
            Dictionary containing residuals, fitted values, etc.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(15, 10)``.

        Returns
        -------
        matplotlib.figure.Figure
            Residual analysis plots.
        """
        required_keys = ["residuals", "fitted_values"]
        for key in required_keys:
            if key not in model_results:
                raise ValueError(f"'{key}' not found in model_results")

        residuals = model_results["residuals"]
        fitted_values = model_results["fitted_values"]

        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=figsize)

        # 1. Residuals vs Fitted
        axes[0, 0].scatter(fitted_values, residuals, alpha=0.6)
        axes[0, 0].axhline(y=0, color="red", linestyle="--", alpha=0.7)
        axes[0, 0].set_xlabel("Fitted Values")
        axes[0, 0].set_ylabel("Residuals")
        axes[0, 0].set_title("Residuals vs Fitted")
        axes[0, 0].grid(True, alpha=0.3)

        # Add LOWESS smoother
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess

            smoothed = lowess(residuals, fitted_values, frac=0.3)
            axes[0, 0].plot(smoothed[:, 0], smoothed[:, 1], color="blue", linewidth=2)
        except ImportError:
            pass

        # 2. Q-Q Plot (Normal probability plot)
        stats.probplot(residuals, dist="norm", plot=axes[0, 1])
        axes[0, 1].set_title("Normal Q-Q Plot")
        axes[0, 1].grid(True, alpha=0.3)

        # 3. Scale-Location plot
        sqrt_abs_residuals = np.sqrt(np.abs(residuals))
        axes[1, 0].scatter(fitted_values, sqrt_abs_residuals, alpha=0.6)
        axes[1, 0].set_xlabel("Fitted Values")
        axes[1, 0].set_ylabel("√|Residuals|")
        axes[1, 0].set_title("Scale-Location Plot")
        axes[1, 0].grid(True, alpha=0.3)

        # Add LOWESS smoother
        try:
            smoothed = lowess(sqrt_abs_residuals, fitted_values, frac=0.3)
            axes[1, 0].plot(smoothed[:, 0], smoothed[:, 1], color="blue", linewidth=2)
        except ImportError:
            pass

        # 4. Residuals vs Leverage (if available)
        if "leverage" in model_results and "cooks_distance" in model_results:
            leverage = model_results["leverage"]
            cooks_d = model_results["cooks_distance"]

            scatter = axes[1, 1].scatter(
                leverage, residuals, c=cooks_d, alpha=0.6, cmap="Reds"
            )
            axes[1, 1].set_xlabel("Leverage")
            axes[1, 1].set_ylabel("Residuals")
            axes[1, 1].set_title("Residuals vs Leverage")
            axes[1, 1].grid(True, alpha=0.3)

            # Add Cook's distance contours
            x_range = np.linspace(leverage.min(), leverage.max(), 100)
            p = 2  # Simplified assumption

            for cook_level in [0.5, 1.0]:
                y_cook = np.sqrt(cook_level * p * (1 - x_range) / x_range)
                axes[1, 1].plot(
                    x_range, y_cook, "--", alpha=0.5, label=f"Cook's D = {cook_level}"
                )
                axes[1, 1].plot(x_range, -y_cook, "--", alpha=0.5)

            axes[1, 1].legend()
            plt.colorbar(scatter, ax=axes[1, 1], label="Cook's Distance")
        else:
            # Histogram of residuals
            axes[1, 1].hist(residuals, bins=20, alpha=0.7, edgecolor="black")
            axes[1, 1].set_xlabel("Residuals")
            axes[1, 1].set_ylabel("Frequency")
            axes[1, 1].set_title("Histogram of Residuals")
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    def design_space_plot(
        self,
        factor1: str,
        factor2: str,
        response_column: str | None = None,
        figsize: tuple[int, int] = (10, 8),
    ) -> plt.Figure:
        """Create design space plot showing experimental points.

        Parameters
        ----------
        factor1 : str
            Factor for the x-axis.
        factor2 : str
            Factor for the y-axis.
        response_column : str, optional
            Response variable for color coding.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(10, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            Design space plot.
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
            scatter = ax.scatter(
                x,
                y,
                c=data_to_use[response_column],
                s=100,
                alpha=0.7,
                cmap="viridis",
                edgecolors="black",
            )
            plt.colorbar(scatter, label=response_column)
        else:
            # Color by design point type if available
            if "DesignPoint" in data_to_use.columns:
                design_types = data_to_use["DesignPoint"].unique()
                colors = plt.get_cmap("Set1")(np.linspace(0, 1, len(design_types)))

                for design_type, color in zip(design_types, colors, strict=True):
                    mask = data_to_use["DesignPoint"] == design_type
                    ax.scatter(
                        x[mask],
                        y[mask],
                        c=[color],
                        label=design_type,
                        s=100,
                        alpha=0.7,
                        edgecolors="black",
                    )
                ax.legend()
            else:
                ax.scatter(x, y, s=100, alpha=0.7, edgecolors="black")

        # Add run numbers if available
        if "RunOrder" in data_to_use.columns:
            for _i, (xi, yi, run) in enumerate(
                zip(x, y, data_to_use["RunOrder"], strict=True)
            ):
                ax.annotate(
                    str(run),
                    (xi, yi),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8,
                    alpha=0.7,
                )

        ax.set_xlabel(factor1)
        ax.set_ylabel(factor2)
        ax.set_title(f"Design Space: {factor1} vs {factor2}")
        ax.grid(True, alpha=0.3)

        return fig

    def factorial_cube_plot(
        self,
        factors: list[str],
        response_column: str | None = None,
        figsize: tuple[int, int] = (10, 8),
    ) -> plt.Figure:
        """Create 3D cube plot for 3-factor designs.

        Parameters
        ----------
        factors : list[str]
            List of exactly three factor names.
        response_column : str, optional
            Response variable for color coding.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(10, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            3D factorial cube plot.
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
        ax = fig.add_subplot(111, projection="3d")

        x = data_to_use[factors[0]]
        y = data_to_use[factors[1]]
        z = data_to_use[factors[2]]

        if response_column and response_column in data_to_use.columns:
            # Color by response
            scatter = ax.scatter(
                x,
                y,
                z,
                c=data_to_use[response_column],
                s=100,
                alpha=0.7,
                cmap="viridis",
            )
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
                (0, 1),
                (2, 3),
                (4, 5),
                (6, 7),  # Parallel to factor 0
                (0, 2),
                (1, 3),
                (4, 6),
                (5, 7),  # Parallel to factor 1
                (0, 4),
                (1, 5),
                (2, 6),
                (3, 7),  # Parallel to factor 2
            ]

            for edge in edges:
                point1 = vertices[edge[0]]
                point2 = vertices[edge[1]]
                ax.plot(
                    [point1[0], point2[0]],
                    [point1[1], point2[1]],
                    [point1[2], point2[2]],
                    "k-",
                    alpha=0.3,
                )

        ax.set_xlabel(factors[0])
        ax.set_ylabel(factors[1])
        ax.set_zlabel(factors[2])
        ax.set_title(f"Factorial Cube: {' × '.join(factors)}")

        return fig

    def box_plots_by_factor(
        self, response_column: str, figsize: tuple[int, int] = (15, 8)
    ) -> plt.Figure:
        """Create box plots for each factor.

        Parameters
        ----------
        response_column : str
            Response variable name.
        figsize : tuple of int, optional
            Figure size. Defaults to ``(15, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            Box plots by factor.
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
            box_data = [
                self.data[self.data[factor] == level][response_column].values
                for level in factor_levels
            ]

            box_plot = ax.boxplot(box_data, labels=factor_levels, patch_artist=True)

            # Color the boxes
            colors = plt.get_cmap("Set3")(np.linspace(0, 1, len(factor_levels)))
            for patch, color in zip(box_plot["boxes"], colors, strict=True):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)

            ax.set_xlabel(factor)
            ax.set_ylabel(response_column)
            ax.set_title(f"Box Plot: {factor}")
            ax.grid(True, alpha=0.3)

        # Hide unused subplots
        for i in range(n_factors, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        return fig
