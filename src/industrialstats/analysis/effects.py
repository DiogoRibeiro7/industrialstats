"""Effect calculation and analysis for experimental designs."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class EffectsAnalysis:
    """Calculate and analyze factorial effects."""

    def __init__(self, design_matrix: pd.DataFrame, response_data: list[float]):
        """Initialize effects analysis.

        Parameters
        ----------
        design_matrix : pd.DataFrame
            Experimental design matrix.
        response_data : list[float]
            Responses for each design row.

        Raises
        ------
        ValueError
            If the response length does not match the design matrix or if no
            factor columns are found.
        """
        if len(response_data) != len(design_matrix):
            raise ValueError("Response data length must match design matrix rows")

        self.design_matrix = design_matrix.copy()
        self.response_data = np.array(response_data)
        self.effects: dict[str, float] | None = None

        # Identify factor columns (exclude metadata columns)
        metadata_cols = ["RunID", "Replicate", "DesignPoint", "RunOrder"]
        self.factor_names = [
            col for col in design_matrix.columns if col not in metadata_cols
        ]

        if not self.factor_names:
            raise ValueError("No factor columns found in design matrix")

    def calculate_main_effects(self) -> dict[str, float]:
        """Calculate main effects for all factors.

        Returns
        -------
        dict[str, float]
            Mapping of factor names to effect estimates.
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

    def calculate_interaction_effects(self, max_order: int = 2) -> dict[str, float]:
        """Calculate interaction effects.

        Parameters
        ----------
        max_order : int, optional
            Maximum interaction order to compute. Defaults to 2.

        Returns
        -------
        dict[str, float]
            Interaction effect estimates keyed by name.
        """
        interactions = {}

        if max_order >= 2:
            # Two-factor interactions
            for i, factor1 in enumerate(self.factor_names):
                for factor2 in self.factor_names[i + 1 :]:
                    interaction_name = f"{factor1}*{factor2}"
                    interaction_effect = self._calculate_two_factor_interaction(
                        factor1, factor2
                    )
                    interactions[interaction_name] = interaction_effect

        if max_order >= 3:
            # Three-factor interactions
            for i, factor1 in enumerate(self.factor_names):
                for j, factor2 in enumerate(self.factor_names[i + 1 :], i + 1):
                    for factor3 in self.factor_names[j + 1 :]:
                        interaction_name = f"{factor1}*{factor2}*{factor3}"
                        interaction_effect = self._calculate_three_factor_interaction(
                            factor1, factor2, factor3
                        )
                        interactions[interaction_name] = interaction_effect

        return interactions

    def _calculate_two_factor_interaction(self, factor1: str, factor2: str) -> float:
        """Calculate a two-factor interaction effect.

        Parameters
        ----------
        factor1 : str
            First factor name.
        factor2 : str
            Second factor name.

        Returns
        -------
        float
            Estimated interaction effect.
        """
        levels1 = sorted(self.design_matrix[factor1].unique())
        levels2 = sorted(self.design_matrix[factor2].unique())

        if len(levels1) == 2 and len(levels2) == 2:
            # 2x2 interaction - classical calculation
            cell_means = {}
            for level1 in levels1:
                for level2 in levels2:
                    mask = (self.design_matrix[factor1] == level1) & (
                        self.design_matrix[factor2] == level2
                    )
                    if mask.any():
                        cell_means[(level1, level2)] = np.mean(self.response_data[mask])
                    else:
                        cell_means[(level1, level2)] = 0

            # Interaction effect calculation
            # AB = [(high,high) + (low,low) - (high,low) - (low,high)] / 2
            interaction = (
                cell_means[(levels1[1], levels2[1])]
                + cell_means[(levels1[0], levels2[0])]
            ) - (
                cell_means[(levels1[1], levels2[0])]
                + cell_means[(levels1[0], levels2[1])]
            )

            return interaction / 2

        # Multi-level factors - use ANOVA approach
        return self._anova_interaction_effect(factor1, factor2)

    def _calculate_three_factor_interaction(
        self, factor1: str, factor2: str, factor3: str
    ) -> float:
        """Calculate a three-factor interaction effect.

        Parameters
        ----------
        factor1 : str
            First factor name.
        factor2 : str
            Second factor name.
        factor3 : str
            Third factor name.

        Returns
        -------
        float
            Estimated interaction effect.
        """
        levels1 = sorted(self.design_matrix[factor1].unique())
        levels2 = sorted(self.design_matrix[factor2].unique())
        levels3 = sorted(self.design_matrix[factor3].unique())

        if all(len(levels) == 2 for levels in [levels1, levels2, levels3]):
            # 2x2x2 interaction
            cell_means = {}
            for l1 in levels1:
                for l2 in levels2:
                    for l3 in levels3:
                        mask = (
                            (self.design_matrix[factor1] == l1)
                            & (self.design_matrix[factor2] == l2)
                            & (self.design_matrix[factor3] == l3)
                        )
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

        # Multi-level factors - use ANOVA approach
        return self._anova_interaction_effect(factor1, factor2, factor3)

    def _anova_interaction_effect(self, *factors) -> float:
        """Calculate interaction effect using an ANOVA approach.

        Parameters
        ----------
        *factors
            Factor names involved in the interaction.

        Returns
        -------
        float
            F statistic for the interaction term or 0.0 if unavailable.
        """
        try:
            from statsmodels.formula.api import ols
            from statsmodels.stats.anova import anova_lm

            # Create temporary dataframe
            temp_df = self.design_matrix.copy()
            temp_df["response"] = self.response_data

            # Create formula
            factor_terms = [f"C({factor})" for factor in factors]
            interaction_term = " * ".join(factor_terms)
            formula = f"response ~ {interaction_term}"

            # Fit model and get ANOVA table
            model = ols(formula, data=temp_df).fit()
            anova_table = anova_lm(model, typ=2)

            # Find interaction term in ANOVA table
            for index in anova_table.index:
                if all(f"C({factor})" in index for factor in factors) and ":" in index:
                    if "F" in anova_table.columns:
                        return anova_table.loc[index, "F"]
                    return anova_table.loc[index, "sum_sq"]

            return 0.0

        except (ValueError, np.linalg.LinAlgError, ImportError) as e:
            logger.debug(
                "Failed to compute interaction effect for factors %s: %s", factors, e
            )
            return 0.0

    def normal_probability_plot(
        self, effects: dict[str, float], figsize: tuple[int, int] = (10, 6)
    ) -> plt.Figure:
        """Create a normal probability plot for effect screening.

        Parameters
        ----------
        effects : dict[str, float]
            Dictionary of effect estimates.
        figsize : tuple of int, optional
            Size of the figure. Defaults to ``(10, 6)``.

        Returns
        -------
        matplotlib.figure.Figure
            Matplotlib figure with the probability plot.

        Raises
        ------
        ValueError
            If ``effects`` is empty.
        """
        if not effects:
            raise ValueError("No effects provided for plotting")

        effect_values = np.array(list(effects.values()))
        effect_names = list(effects.keys())
        sorted_indices = np.argsort(effect_values)
        sorted_effects = effect_values[sorted_indices]
        sorted_names = np.array(effect_names)[sorted_indices]
        n = len(sorted_effects)
        quantiles = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
        fig, ax = plt.subplots(figsize=figsize)
        ax.scatter(
            quantiles,
            sorted_effects,
            alpha=0.7,
            s=50,
            c="steelblue",
            edgecolors="black",
        )
        for i, name in enumerate(sorted_names):
            ax.annotate(
                name,
                (quantiles[i], sorted_effects[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                alpha=0.8,
            )
        ax.set_xlabel("Normal Quantiles")
        ax.set_ylabel("Effects")
        ax.set_title("Normal Probability Plot of Effects")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def interaction_plots(
        self, max_interactions: int = 3, figsize: tuple[int, int] = (15, 10)
    ) -> plt.Figure:
        """Plot selected two-factor interactions.

        Parameters
        ----------
        max_interactions : int, optional
            Number of interactions to display. Defaults to 3.
        figsize : tuple of int, optional
            Size of the figure grid. Defaults to ``(15, 10)``.

        Returns
        -------
        matplotlib.figure.Figure
            Figure containing the interaction plots.

        Raises
        ------
        ValueError
            If no two-factor interactions are present.
        """
        # Calculate interaction effects
        interactions = self.calculate_interaction_effects()

        # Filter for two-factor interactions only
        two_factor_interactions = {
            name: effect
            for name, effect in interactions.items()
            if name.count("*") == 1
        }

        if not two_factor_interactions:
            raise ValueError("No two-factor interactions found")

        # Sort by effect magnitude and take top interactions
        sorted_interactions = sorted(
            two_factor_interactions.items(), key=lambda x: abs(x[1]), reverse=True
        )[:max_interactions]

        # Create subplots
        n_plots = len(sorted_interactions)
        n_cols = min(3, n_plots)
        n_rows = (n_plots + n_cols - 1) // n_cols

        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        # subplots returns a bare Axes for a 1x1 grid, a 1-D array for a single
        # row, and a 2-D array otherwise; normalise all three to a flat list.
        axes = np.atleast_1d(axes).ravel()

        for i, (interaction_name, effect) in enumerate(sorted_interactions):
            factor1, factor2 = interaction_name.split("*")

            # Get factor levels
            levels1 = sorted(self.design_matrix[factor1].unique())
            levels2 = sorted(self.design_matrix[factor2].unique())

            # Calculate cell means
            means_by_f1 = {}
            for level1 in levels1:
                means_by_f2 = []
                for level2 in levels2:
                    mask = (self.design_matrix[factor1] == level1) & (
                        self.design_matrix[factor2] == level2
                    )
                    if mask.any():
                        means_by_f2.append(np.mean(self.response_data[mask]))
                    else:
                        means_by_f2.append(np.nan)
                means_by_f1[level1] = means_by_f2

            # Plot interaction
            ax = axes[i]
            for _j, level1 in enumerate(levels1):
                valid_indices = ~np.isnan(means_by_f1[level1])
                if valid_indices.any():
                    x_vals = np.array(range(len(levels2)))[valid_indices]
                    y_vals = np.array(means_by_f1[level1])[valid_indices]
                    ax.plot(
                        x_vals,
                        y_vals,
                        "o-",
                        label=f"{factor1}={level1}",
                        linewidth=2,
                        markersize=6,
                    )

            ax.set_xlabel(factor2)
            ax.set_ylabel("Response Mean")
            ax.set_title(f"{interaction_name}\nEffect = {effect:.3f}")
            ax.set_xticks(range(len(levels2)))
            ax.set_xticklabels(levels2)
            ax.legend()
            ax.grid(True, alpha=0.3)

        # Hide unused subplots
        for i in range(len(sorted_interactions), len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        return fig

    def effect_hierarchy_plot(self, figsize: tuple[int, int] = (12, 8)) -> plt.Figure:
        """Plot a hierarchy diagram of effects.

        Parameters
        ----------
        figsize : tuple of int, optional
            Figure size. Defaults to ``(12, 8)``.

        Returns
        -------
        matplotlib.figure.Figure
            Matplotlib figure with the hierarchy plot.
        """
        # Get all effects
        main_effects = self.calculate_main_effects()
        interaction_effects = self.calculate_interaction_effects()

        # Organize by hierarchy
        effects_by_order = {1: main_effects}

        for name, effect in interaction_effects.items():
            order = name.count("*") + 1
            if order not in effects_by_order:
                effects_by_order[order] = {}
            effects_by_order[order][name] = effect

        # Create plot
        fig, ax = plt.subplots(figsize=figsize)

        colors = ["steelblue", "orange", "green", "red", "purple"]
        y_positions = []
        labels = []
        values = []
        colors_list = []

        y_pos = 0.0
        for order in sorted(effects_by_order.keys()):
            effects = effects_by_order[order]
            order_name = (
                "Main Effects" if order == 1 else f"{order}-Factor Interactions"
            )

            # Add order separator
            if y_pos > 0:
                y_pos += 0.5

            # Sort effects within order
            sorted_effects = sorted(
                effects.items(), key=lambda x: abs(x[1]), reverse=True
            )

            for name, effect in sorted_effects:
                y_positions.append(y_pos)
                labels.append(name)
                values.append(effect)
                colors_list.append(colors[(order - 1) % len(colors)])
                y_pos += 1

            # Add order label
            ax.text(
                -max(abs(v) for v in values) * 1.1,
                y_pos - len(sorted_effects) / 2 - 0.5,
                order_name,
                rotation=90,
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold",
            )

        # Create horizontal bar plot
        bars = ax.barh(y_positions, values, color=colors_list, alpha=0.7)

        # Add value labels
        for bar, value in zip(bars, values, strict=True):
            width = bar.get_width()
            ax.text(
                width + np.sign(width) * max(abs(v) for v in values) * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{value:.3f}",
                ha="left" if width >= 0 else "right",
                va="center",
                fontsize=9,
            )

        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Effect Size")
        ax.set_title("Effect Hierarchy Plot")
        ax.axvline(x=0, color="black", linestyle="-", alpha=0.5)
        ax.grid(True, alpha=0.3, axis="x")

        plt.tight_layout()
        return fig

    def pareto_chart(
        self, effects: dict[str, float], figsize: tuple[int, int] = (12, 6)
    ) -> plt.Figure:
        """Plot a Pareto chart of effect magnitudes.

        Parameters
        ----------
        effects : dict[str, float]
            Effects to visualize.
        figsize : tuple of int, optional
            Size of the figure. Defaults to ``(12, 6)``.

        Returns
        -------
        matplotlib.figure.Figure
            Pareto chart figure.

        Raises
        ------
        ValueError
            If ``effects`` is empty.
        """
        if not effects:
            raise ValueError("No effects provided for plotting")

        # Calculate absolute effects
        abs_effects = {name: abs(effect) for name, effect in effects.items()}

        # Sort by magnitude
        sorted_effects = sorted(abs_effects.items(), key=lambda x: x[1], reverse=True)
        names, values = zip(*sorted_effects, strict=True)

        # Calculate cumulative percentage
        total = sum(values)
        cumulative_pct = np.cumsum(values) / total * 100

        # Create plot
        fig, ax1 = plt.subplots(figsize=figsize)

        # Bar chart
        bars = ax1.bar(range(len(names)), values, alpha=0.7, color="steelblue")
        ax1.set_xlabel("Effects")
        ax1.set_ylabel("Absolute Effect Size", color="steelblue")
        ax1.set_xticks(range(len(names)))
        ax1.set_xticklabels(names, rotation=45, ha="right")

        # Add effect values on bars
        for bar, value in zip(bars, values, strict=True):
            height = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + height * 0.01,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

        # Cumulative percentage line
        ax2 = ax1.twinx()
        ax2.plot(
            range(len(names)),
            cumulative_pct,
            "ro-",
            color="red",
            alpha=0.7,
            linewidth=2,
            markersize=6,
        )
        ax2.set_ylabel("Cumulative Percentage", color="red")
        ax2.set_ylim(0, 105)

        # Add percentage labels
        for i, pct in enumerate(cumulative_pct):
            ax2.text(
                i,
                pct + 2,
                f"{pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                color="red",
            )

        # Add 80% line (Pareto principle)
        ax2.axhline(y=80, color="orange", linestyle="--", alpha=0.7, label="80% Line")
        ax2.legend(loc="lower right")

        plt.title("Pareto Chart of Effects")
        plt.tight_layout()

        return fig

    def effects_summary_table(self) -> pd.DataFrame:
        """Create a summary table of all effects.

        Returns
        -------
        pd.DataFrame
            Table with effect estimates, rankings, and percentages.
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
            effect_type = "Main" if "*" not in name else "Interaction"
            order = name.count("*") + 1

            summary_data.append(
                {
                    "Effect": name,
                    "Estimate": effect,
                    "Abs_Estimate": abs(effect),
                    "Type": effect_type,
                    "Order": order,
                }
            )

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values("Abs_Estimate", ascending=False)

        # Add rankings
        summary_df["Rank"] = range(1, len(summary_df) + 1)

        # Add percentage contribution
        total_abs_effect = summary_df["Abs_Estimate"].sum()
        summary_df["Percent_Contribution"] = (
            summary_df["Abs_Estimate"] / total_abs_effect * 100
        ).round(2)

        # Add cumulative percentage
        summary_df["Cumulative_Percent"] = summary_df["Percent_Contribution"].cumsum()

        return summary_df

    def half_normal_plot(
        self,
        effects: dict[str, float],
        figsize: tuple[int, int] = (10, 6),
        interactive: bool = True,
    ) -> tuple[plt.Figure, list[str]]:
        """Create a half-normal probability plot for effect screening.

        Parameters
        ----------
        effects : dict[str, float]
            Dictionary of effect estimates.
        figsize : tuple of int, optional
            Size of the figure. Defaults to ``(10, 6)``.
        interactive : bool, optional
            If ``True``, enable interactive point identification using
            ``mplcursors`` when available. Defaults to ``True``.

        Returns
        -------
        tuple of (matplotlib.figure.Figure, list[str])
            The generated figure and a list of effect names deemed significant
            by Lenth's method.

        Raises
        ------
        ValueError
            If ``effects`` is empty.
        """
        if not effects:
            raise ValueError("No effects provided for plotting")

        effect_values = np.abs(np.array(list(effects.values())))
        effect_names = np.array(list(effects.keys()))

        # Lenth's method for effect significance
        s0 = 1.5 * np.median(effect_values)
        threshold = 2.5 * s0
        filtered = effect_values[effect_values <= threshold]
        s = 1.5 * np.median(filtered) if filtered.size else s0
        me = 2.5 * s
        sme = 3.5 * s
        significant = list(effect_names[effect_values > sme])

        # Half-normal quantiles
        sorted_idx = np.argsort(effect_values)
        sorted_effects = effect_values[sorted_idx]
        sorted_names = effect_names[sorted_idx]
        n = len(sorted_effects)
        probs = (np.arange(1, n + 1) - 0.5) / n
        quantiles = stats.norm.ppf(0.5 + probs / 2)

        fig, ax = plt.subplots(figsize=figsize)
        points = ax.scatter(
            quantiles,
            sorted_effects,
            alpha=0.7,
            s=50,
            c="steelblue",
            edgecolors="black",
        )

        if interactive:
            try:  # pragma: no cover - interactive features not tested
                import mplcursors

                cursor = mplcursors.cursor(points, hover=True)
                cursor.connect(
                    "add", lambda sel: sel.annotation.set_text(sorted_names[sel.index])
                )
            except ImportError:  # pragma: no cover
                logger.debug("mplcursors not available; interactive mode disabled")

        ax.axhline(me, color="red", linestyle="--", linewidth=1, label="ME")
        ax.axhline(sme, color="green", linestyle="--", linewidth=1, label="SME")

        ax.set_xlabel("Half-Normal Quantiles")
        ax.set_ylabel("Absolute Effects")
        ax.set_title("Half-Normal Plot of Effects")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig, significant
