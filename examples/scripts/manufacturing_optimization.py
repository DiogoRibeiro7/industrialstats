"""
Complete Manufacturing Optimization Example using DOE.

This script demonstrates a comprehensive DOE analysis for optimizing
an injection molding process for plastic parts.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from industrialstats.analysis.anova import ANOVAAnalysis
from industrialstats.analysis.effects import EffectsAnalysis
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.visualizations.plots import ExperimentPlotter


def main():
    """Run the complete manufacturing optimization study."""

    print("=" * 80)
    print("MANUFACTURING PROCESS OPTIMIZATION USING DESIGN OF EXPERIMENTS")
    print("=" * 80)
    sns.set_theme(style="whitegrid")

    # ========================================================================
    # PROBLEM DEFINITION
    # ========================================================================

    print("\n🎯 PROBLEM STATEMENT:")
    print("-" * 40)
    print("Objective: Optimize injection molding process for maximum tensile strength")
    print("Response: Tensile strength (MPa)")
    print("Goal: Identify optimal factor settings and significant effects")

    # Define experimental factors
    factors = [
        Factor("Temperature", [180, 220], "continuous"),  # °C
        Factor("Pressure", [80, 120], "continuous"),  # Bar
        Factor("Cooling_Time", [10, 20], "continuous"),  # Seconds
        Factor("Material", ["ABS", "PP"], "categorical"),  # Plastic type
    ]

    print("\n📊 EXPERIMENTAL FACTORS:")
    print("-" * 40)
    for factor in factors:
        levels_str = (
            f"{factor.levels[0]} - {factor.levels[1]}"
            if factor.factor_type == "continuous"
            else ", ".join(map(str, factor.levels))
        )
        print(f"  {factor.name:15} : {levels_str:15} ({factor.factor_type})")

    # ========================================================================
    # EXPERIMENTAL DESIGN
    # ========================================================================

    print("\n🔬 EXPERIMENTAL DESIGN:")
    print("-" * 40)

    # Create 2^4 factorial design with replicates
    design = FactorialDesign(factors, replicates=2, center_points=4)
    design_matrix = design.generate_design()

    print(f"Design Type: {design.name}")
    print(f"Total Runs: {len(design_matrix)}")
    print(f"Factorial Points: {design.n_factorial_runs()}")
    print(f"Center Points: {design.center_points}")
    print(f"Replicates: {design.replicates}")

    # Show degrees of freedom
    dof = design.degrees_of_freedom()
    print("\nDegrees of Freedom:")
    for effect, df in dof.items():
        print(f"  {effect:20}: {df}")

    print("\n📋 FIRST 10 EXPERIMENTAL RUNS:")
    print("-" * 40)
    print(design_matrix.head(10).to_string(index=False))

    # ========================================================================
    # DATA SIMULATION (In practice, this would be real experimental data)
    # ========================================================================

    print("\n🧪 COLLECTING EXPERIMENTAL DATA...")
    print("-" * 40)

    # Simulate realistic response data with known effects
    rng = np.random.default_rng(42)  # For reproducible results
    responses = simulate_tensile_strength_data(design_matrix, rng=rng)
    design_matrix["Tensile_Strength"] = responses

    print("Data Collection Complete!")
    print("Response Statistics:")
    print(f"  Mean: {np.mean(responses):.2f} MPa")
    print(f"  Std Dev: {np.std(responses):.2f} MPa")
    print(f"  Range: {np.min(responses):.2f} - {np.max(responses):.2f} MPa")

    # ========================================================================
    # EFFECTS ANALYSIS
    # ========================================================================

    print("\n📈 EFFECTS ANALYSIS:")
    print("=" * 50)

    # Calculate factorial effects
    effects_analyzer = EffectsAnalysis(design_matrix, responses)
    main_effects = effects_analyzer.calculate_main_effects()
    interaction_effects = effects_analyzer.calculate_interaction_effects()

    print("\n🔍 MAIN EFFECTS:")
    print("-" * 30)
    sorted_main = sorted(main_effects.items(), key=lambda x: abs(x[1]), reverse=True)
    for effect, value in sorted_main:
        direction = "↑" if value > 0 else "↓"
        print(f"  {effect:15} : {value:+7.2f} MPa {direction}")

    print("\n🔄 TWO-FACTOR INTERACTIONS:")
    print("-" * 35)
    two_factor = {k: v for k, v in interaction_effects.items() if k.count("*") == 1}
    sorted_interactions = sorted(
        two_factor.items(), key=lambda x: abs(x[1]), reverse=True
    )
    for effect, value in sorted_interactions:
        direction = "↑" if value > 0 else "↓"
        print(f"  {effect:15} : {value:+7.2f} MPa {direction}")

    # Create effects summary table
    effects_summary = effects_analyzer.effects_summary_table()
    print("\n📊 EFFECTS SUMMARY TABLE:")
    print("-" * 40)
    print(effects_summary.head(10).to_string(index=False))

    # ========================================================================
    # STATISTICAL ANALYSIS (ANOVA)
    # ========================================================================

    print("\n📊 STATISTICAL ANALYSIS (ANOVA):")
    print("=" * 50)

    # Perform ANOVA
    anova_analyzer = ANOVAAnalysis(design_matrix, "Tensile_Strength")

    # Fit full factorial model
    model_formula = (
        "Tensile_Strength ~ C(Temperature) * C(Pressure) * "
        + "C(Cooling_Time) * C(Material)"
    )

    try:
        model = anova_analyzer.fit_model(model_formula)
        anova_table = anova_analyzer.anova_table_calculation()

        print("\n📋 ANOVA TABLE:")
        print("-" * 60)
        # Display key columns
        display_cols = ["sum_sq", "df", "Mean_Square", "F", "PR(>F)", "Significance"]
        available_cols = [col for col in display_cols if col in anova_table.columns]
        print(anova_table[available_cols].round(4).to_string())

        # Model summary
        model_summary = anova_analyzer.model_summary()
        print("\n📈 MODEL SUMMARY:")
        print("-" * 25)
        print(f"  R-squared      : {model_summary['r_squared']:.4f}")
        print(f"  Adj R-squared  : {model_summary['adj_r_squared']:.4f}")
        print(f"  F-statistic    : {model_summary['f_statistic']:.2f}")
        print(f"  P-value        : {model_summary['f_pvalue']:.4f}")
        print(f"  RMSE           : {model_summary['rmse']:.3f}")

    except Exception as e:
        print(f"Note: ANOVA analysis encountered an issue: {e}")
        print("Proceeding with effects analysis...")
        anova_table = None
        model = None

    # ========================================================================
    # ASSUMPTION TESTING
    # ========================================================================

    if model is not None:
        print("\n🔍 ASSUMPTION TESTING:")
        print("-" * 30)

        try:
            assumptions = anova_analyzer.assumptions_tests()

            for assumption, results in assumptions.items():
                print(f"\n{assumption.title()} Test:")
                if "error" in results:
                    print(f"  Error: {results['error']}")
                else:
                    print(f"  Test: {results['test']}")
                    if "p_value" in results:
                        print(f"  P-value: {results['p_value']:.4f}")
                    if "statistic" in results:
                        print(f"  Statistic: {results['statistic']:.4f}")
                    print(f"  Result: {results['interpretation']}")

        except Exception as e:
            print(f"Note: Assumption testing encountered an issue: {e}")

    # ========================================================================
    # OPTIMIZATION RECOMMENDATIONS
    # ========================================================================

    print("\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    print("=" * 50)

    # Find optimal conditions based on effects
    optimal_conditions = find_optimal_conditions(main_effects, factors)

    print("\n🏆 RECOMMENDED OPTIMAL CONDITIONS:")
    print("-" * 40)
    for factor_name, optimal_level in optimal_conditions.items():
        print(f"  {factor_name:15} : {optimal_level}")

    # Predict response at optimal conditions
    predicted_response = predict_optimal_response(
        optimal_conditions, main_effects, interaction_effects
    )
    print(f"\n📊 PREDICTED TENSILE STRENGTH: {predicted_response:.2f} MPa")

    # Calculate improvement
    current_best = np.max(responses)
    improvement = predicted_response - current_best
    improvement_pct = (improvement / current_best) * 100

    print(f"Current Best Result: {current_best:.2f} MPa")
    if improvement > 0:
        print(f"Expected Improvement: +{improvement:.2f} MPa ({improvement_pct:+.1f}%)")
    else:
        print("Note: Predicted optimum is within current experimental range")

    # ========================================================================
    # STATISTICAL VALIDATION
    # ========================================================================

    print("\n📊 STATISTICAL VALIDATION:")
    print("-" * 40)
    baseline_conditions = design_matrix.loc[
        responses.argmax(), [f.name for f in factors]
    ]
    baseline_df = pd.DataFrame([baseline_conditions.to_dict()] * 5)
    optimal_df = pd.DataFrame([optimal_conditions] * 5)
    baseline_vals = simulate_tensile_strength_data(baseline_df, rng=rng)
    optimal_vals = simulate_tensile_strength_data(optimal_df, rng=rng)
    t_stat, p_val = stats.ttest_ind(optimal_vals, baseline_vals, equal_var=False)
    print(f"Mean at baseline: {baseline_vals.mean():.2f} MPa")
    print(f"Mean at optimal : {optimal_vals.mean():.2f} MPa")
    print(f"t-statistic     : {t_stat:.2f}")
    print(f"p-value         : {p_val:.4f}")

    # ========================================================================
    # ECONOMIC IMPACT ANALYSIS
    # ========================================================================

    print("\n💰 ECONOMIC IMPACT ANALYSIS:")
    print("-" * 40)
    annual_volume = 50_000
    cost_per_part = 2.5
    baseline_scrap_rate = 0.05
    scrap_reduction_per_mpa = 0.003
    new_scrap_rate = max(baseline_scrap_rate - improvement * scrap_reduction_per_mpa, 0)
    baseline_cost = baseline_scrap_rate * annual_volume * cost_per_part
    new_cost = new_scrap_rate * annual_volume * cost_per_part
    savings = baseline_cost - new_cost
    print(f"Estimated annual scrap cost savings: ${savings:,.0f}")

    fig_cost = plt.figure(figsize=(6, 4))
    sns.barplot(
        x=["Current", "Optimized"],
        y=[baseline_cost, new_cost],
        palette=["#d62728", "#2ca02c"],
    )
    plt.ylabel("Annual Scrap Cost ($)")
    plt.title("Economic Impact of Optimization")
    fig_cost.savefig("manufacturing_economic_impact.png", dpi=300, bbox_inches="tight")
    plt.close(fig_cost)

    # ========================================================================
    # SENSITIVITY ANALYSIS
    # ========================================================================

    print("\n🔄 SENSITIVITY ANALYSIS:")
    print("-" * 30)

    # Rank factors by effect magnitude
    all_effects = {**main_effects, **two_factor}
    sorted_all_effects = sorted(
        all_effects.items(), key=lambda x: abs(x[1]), reverse=True
    )

    print("\nFactor Importance Ranking:")
    for i, (effect, value) in enumerate(sorted_all_effects[:8], 1):
        effect_type = "Main" if "*" not in effect else "Interaction"
        print(f"  {i}. {effect:20} ({effect_type:11}) : {abs(value):6.2f} MPa")

    # Control recommendations
    print("\n💡 PROCESS CONTROL RECOMMENDATIONS:")
    print("-" * 45)

    # Most important factors for tight control
    critical_factors = [
        effect for effect, _ in sorted_all_effects[:3] if "*" not in effect
    ]
    print("Critical factors requiring tight control:")
    for factor in critical_factors:
        print(f"  • {factor}")

    # Robust settings
    print("\nFor robust operation (less sensitive to variation):")
    robust_recommendations = get_robust_recommendations(
        main_effects, interaction_effects
    )
    for recommendation in robust_recommendations:
        print(f"  • {recommendation}")

    # ========================================================================
    # VISUALIZATION
    # ========================================================================

    print("\n📊 CREATING VISUALIZATIONS...")
    print("-" * 35)

    try:
        create_comprehensive_plots(
            design_matrix, effects_analyzer, main_effects, interaction_effects, model
        )
        print("✅ All plots saved successfully!")

        print("\nGenerated plots:")
        plot_files = [
            "manufacturing_main_effects.png",
            "manufacturing_interaction_plots.png",
            "manufacturing_pareto_chart.png",
            "manufacturing_normal_plot.png",
            "manufacturing_design_space.png",
            "manufacturing_economic_impact.png",
        ]

        for plot_file in plot_files:
            print(f"  📈 {plot_file}")

    except Exception as e:
        print(f"Note: Visualization encountered an issue: {e}")

    # ========================================================================
    # SUMMARY AND CONCLUSIONS
    # ========================================================================

    print("\n📝 EXECUTIVE SUMMARY:")
    print("=" * 50)

    # Key findings
    most_important = sorted_main[0]
    most_important_interaction = sorted_interactions[0] if sorted_interactions else None

    print("\n🔑 KEY FINDINGS:")
    print("-" * 20)
    print(
        f"1. Most important factor: {most_important[0]} ({most_important[1]:+.1f} MPa effect)"
    )

    if most_important_interaction:
        print(
            f"2. Strongest interaction: {most_important_interaction[0]} "
            + f"({most_important_interaction[1]:+.1f} MPa effect)"
        )

    print(
        f"3. Optimal settings identified for {predicted_response:.1f} MPa tensile strength"
    )

    print(f"4. Estimated annual scrap cost savings: ${savings:,.0f}")

    # Process insights
    print("\n💡 PROCESS INSIGHTS:")
    print("-" * 25)

    # Temperature effect
    temp_effect = main_effects.get("Temperature", 0)
    if abs(temp_effect) > 2:
        temp_direction = "higher" if temp_effect > 0 else "lower"
        print(f"• Temperature has strong effect - use {temp_direction} temperatures")

    # Material effect
    material_effect = main_effects.get("Material", 0)
    if abs(material_effect) > 2:
        better_material = "ABS" if material_effect > 0 else "PP"
        print(f"• Material choice is critical - {better_material} performs better")

    # Interaction insights
    if "Temperature*Material" in interaction_effects:
        temp_mat_interaction = interaction_effects["Temperature*Material"]
        if abs(temp_mat_interaction) > 1:
            print("• Temperature effect depends on material choice")

    print("\n🎯 NEXT STEPS:")
    print("-" * 15)
    print("1. Confirm optimal settings with confirmation runs")
    print("2. Investigate process robustness around optimal point")
    print("3. Consider economic factors in final setting selection")
    print("4. Implement statistical process control for critical factors")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE - Check generated visualizations for detailed insights!")
    print("=" * 80)


def simulate_tensile_strength_data(
    design_matrix: pd.DataFrame, rng: np.random.Generator | None = None
) -> np.ndarray:
    """Simulate realistic tensile strength data with known factor effects.

    Parameters
    ----------
    design_matrix : pd.DataFrame
        Experimental design matrix containing factor settings.
    rng : numpy.random.Generator, optional
        Random generator used for the simulated noise. Pass a seeded generator
        for reproducible output; a fresh unseeded one is used by default.

    Returns
    -------
    np.ndarray
        Simulated tensile strength responses in MPa.
    """
    if rng is None:
        rng = np.random.default_rng()

    responses: list[float] = []

    for _, row in design_matrix.iterrows():
        base_strength = 45.0  # MPa

        temp_effect = (row["Temperature"] - 200) * 0.15
        pressure_effect = (row["Pressure"] - 100) * 0.10
        cooling_effect = (row["Cooling_Time"] - 15) * -0.08
        material_effect = 8.0 if row["Material"] == "ABS" else 0.0

        temp_pressure = ((row["Temperature"] - 200) * (row["Pressure"] - 100)) * 0.003
        temp_material = (
            4.0 if (row["Temperature"] > 200 and row["Material"] == "ABS") else 0.0
        )
        pressure_cooling = (
            (row["Pressure"] - 100) * (row["Cooling_Time"] - 15)
        ) * -0.002

        total_response = (
            base_strength
            + temp_effect
            + pressure_effect
            + cooling_effect
            + material_effect
            + temp_pressure
            + temp_material
            + pressure_cooling
        )

        machine_effect = rng.normal(0, 0.5)
        noise_scale = 1.2 if row["Material"] == "PP" else 0.8
        noise = rng.normal(0, noise_scale)
        final_response = total_response + machine_effect + noise

        final_response = max(final_response, 25.0)
        final_response = min(final_response, 70.0)

        responses.append(final_response)

    return np.array(responses)


def find_optimal_conditions(main_effects: dict, factors: list) -> dict:
    """Determine optimal factor levels from main effects.

    Parameters
    ----------
    main_effects : dict
        Mapping of factor names to estimated main effects.
    factors : list
        List of :class:`~industrialstats.designs.base.Factor` objects defining the design.

    Returns
    -------
    dict
        Dictionary of factor names and recommended levels.
    """
    optimal = {}

    for factor in factors:
        if factor.name in main_effects:
            effect = main_effects[factor.name]

            if factor.factor_type == "categorical":
                # For categorical factors, effect sign indicates better level
                if factor.name == "Material":
                    optimal[factor.name] = "ABS" if effect > 0 else "PP"
            else:
                # For continuous factors, choose high/low based on effect sign
                optimal[factor.name] = (
                    factor.levels[1] if effect > 0 else factor.levels[0]
                )
        else:
            # Default to high level if no effect calculated
            optimal[factor.name] = (
                factor.levels[1]
                if factor.factor_type == "continuous"
                else factor.levels[0]
            )

    return optimal


def predict_optimal_response(
    optimal_conditions: dict, main_effects: dict, interaction_effects: dict
) -> float:
    """Estimate tensile strength at the proposed optimal settings.

    Parameters
    ----------
    optimal_conditions : dict
        Selected factor levels representing the optimum.
    main_effects : dict
        Dictionary of main-effect estimates.
    interaction_effects : dict
        Dictionary of interaction-effect estimates.

    Returns
    -------
    float
        Predicted tensile strength in MPa.
    """
    # Base prediction (typical process average)
    prediction = 45.0

    # Add main effects (simplified calculation)
    for factor, level in optimal_conditions.items():
        if factor in main_effects:
            effect = main_effects[factor]
            # Simplified: add half effect if high level selected
            if factor == "Material":
                if level == "ABS" and effect > 0:
                    prediction += abs(effect) / 2
            else:
                # For continuous factors
                if level > 150:  # Assume "high" level
                    prediction += abs(effect) / 2 if effect > 0 else -abs(effect) / 2

    # Add significant interactions (simplified)
    temp_high = optimal_conditions.get("Temperature", 180) > 200
    material_abs = optimal_conditions.get("Material", "PP") == "ABS"

    if temp_high and material_abs and "Temperature*Material" in interaction_effects:
        interaction_effect = interaction_effects["Temperature*Material"]
        prediction += abs(interaction_effect) / 2

    return prediction


def get_robust_recommendations(main_effects: dict, interaction_effects: dict) -> list:
    """Generate recommendations for robust process operation.

    Parameters
    ----------
    main_effects : dict
        Dictionary of main-effect estimates.
    interaction_effects : dict
        Dictionary of interaction-effect estimates.

    Returns
    -------
    list
        Human-readable recommendations for maintaining robustness.
    """
    recommendations = []

    # Check for strong interactions that indicate sensitivity
    strong_interactions = [
        name
        for name, effect in interaction_effects.items()
        if abs(effect) > 2 and name.count("*") == 1
    ]

    if strong_interactions:
        recommendations.append(
            f"Monitor {strong_interactions[0].replace('*', ' and ')} interaction closely"
        )

    # Temperature recommendations
    if "Temperature" in main_effects and abs(main_effects["Temperature"]) > 3:
        recommendations.append("Maintain tight temperature control (±2°C)")

    # Material recommendations
    if "Material" in main_effects and abs(main_effects["Material"]) > 5:
        recommendations.append("Use consistent material batches and suppliers")

    # Process stability
    recommendations.append("Implement pre-production warm-up procedures")
    recommendations.append("Monitor process stability with control charts")

    return recommendations


def create_comprehensive_plots(
    design_matrix: pd.DataFrame,
    effects_analyzer,
    main_effects: dict,
    interaction_effects: dict,
    model=None,
):
    """Create all visualization plots for the analysis.

    Parameters
    ----------
    design_matrix : pd.DataFrame
        Experimental design with responses.
    effects_analyzer : EffectsAnalysis
        Fitted effects analyzer instance.
    main_effects : dict
        Dictionary of main-effect estimates.
    interaction_effects : dict
        Dictionary of interaction-effect estimates.
    model : statsmodels.regression.linear_model.RegressionResultsWrapper, optional
        Fitted regression model for residual diagnostics, by default ``None``.

    Returns
    -------
    None
    """

    # Initialize plotter
    plotter = ExperimentPlotter(design_matrix)

    # 1. Main effects plot
    try:
        fig1 = plotter.main_effects_plot("Tensile_Strength", figsize=(15, 10))
        fig1.savefig("manufacturing_main_effects.png", dpi=300, bbox_inches="tight")
        plt.close(fig1)
    except Exception as e:
        print(f"Main effects plot error: {e}")

    # 2. Key interaction plots
    try:
        fig2 = plt.figure(figsize=(15, 10))

        # Temperature vs Material interaction
        plt.subplot(2, 2, 1)
        create_interaction_subplot(
            design_matrix, "Temperature", "Material", "Tensile_Strength"
        )

        # Temperature vs Pressure interaction
        plt.subplot(2, 2, 2)
        create_interaction_subplot(
            design_matrix, "Temperature", "Pressure", "Tensile_Strength"
        )

        # Pressure vs Cooling Time interaction
        plt.subplot(2, 2, 3)
        create_interaction_subplot(
            design_matrix, "Pressure", "Cooling_Time", "Tensile_Strength"
        )

        # Material vs Pressure interaction
        plt.subplot(2, 2, 4)
        create_interaction_subplot(
            design_matrix, "Material", "Pressure", "Tensile_Strength"
        )

        plt.tight_layout()
        fig2.savefig(
            "manufacturing_interaction_plots.png", dpi=300, bbox_inches="tight"
        )
        plt.close(fig2)
    except Exception as e:
        print(f"Interaction plots error: {e}")

    # 3. Pareto chart of effects
    try:
        all_effects = {
            **main_effects,
            **{k: v for k, v in interaction_effects.items() if k.count("*") == 1},
        }
        fig3 = effects_analyzer.pareto_chart(all_effects, figsize=(12, 6))
        fig3.savefig("manufacturing_pareto_chart.png", dpi=300, bbox_inches="tight")
        plt.close(fig3)
    except Exception as e:
        print(f"Pareto chart error: {e}")

    # 4. Normal probability plot
    try:
        all_effects = {**main_effects, **interaction_effects}
        fig4 = effects_analyzer.normal_probability_plot(all_effects, figsize=(10, 6))
        fig4.savefig("manufacturing_normal_plot.png", dpi=300, bbox_inches="tight")
        plt.close(fig4)
    except Exception as e:
        print(f"Normal plot error: {e}")

    # 5. Design space plot
    try:
        fig5 = plotter.design_space_plot(
            "Temperature", "Pressure", "Tensile_Strength", figsize=(10, 8)
        )
        fig5.savefig("manufacturing_design_space.png", dpi=300, bbox_inches="tight")
        plt.close(fig5)
    except Exception as e:
        print(f"Design space plot error: {e}")


def create_interaction_subplot(
    data: pd.DataFrame, factor1: str, factor2: str, response: str
):
    """Create a single interaction plot subplot.

    Parameters
    ----------
    data : pd.DataFrame
        Data containing factor levels and response.
    factor1 : str
        Name of the first factor.
    factor2 : str
        Name of the second factor.
    response : str
        Response column name.

    Returns
    -------
    None
    """
    levels1 = sorted(data[factor1].unique())
    levels2 = sorted(data[factor2].unique())

    for level1 in levels1:
        means = []
        for level2 in levels2:
            subset = data[(data[factor1] == level1) & (data[factor2] == level2)]
            if len(subset) > 0:
                means.append(subset[response].mean())
            else:
                means.append(None)

        # Remove None values for plotting
        valid_indices = [i for i, m in enumerate(means) if m is not None]
        if valid_indices:
            x_vals = list(valid_indices)
            y_vals = [means[i] for i in valid_indices]
            [levels2[i] for i in valid_indices]

            plt.plot(
                x_vals,
                y_vals,
                "o-",
                label=f"{factor1}={level1}",
                linewidth=2,
                markersize=6,
            )

    plt.xlabel(factor2)
    plt.ylabel(f"Mean {response}")
    plt.title(f"{factor1} × {factor2}")
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Set x-axis labels
    plt.xticks(range(len(levels2)), levels2)


if __name__ == "__main__":
    main()
