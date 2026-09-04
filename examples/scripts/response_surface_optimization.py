"""
Response Surface Methodology Example for Process Optimization.

This script demonstrates how to use RSM for finding optimal operating
conditions in a chemical reaction optimization study.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign


def main():
    """Run the complete response surface optimization study."""

    print("=" * 80)
    print("RESPONSE SURFACE METHODOLOGY FOR PROCESS OPTIMIZATION")
    print("=" * 80)

    # ========================================================================
    # PROBLEM DEFINITION
    # ========================================================================

    print("\n🎯 OPTIMIZATION PROBLEM:")
    print("-" * 40)
    print("Objective: Maximize yield of a chemical reaction")
    print("Process: Catalytic synthesis reaction")
    print("Response: Reaction yield (%)")
    print("Goal: Find optimal temperature and pressure conditions")

    # Define factors for RSM study
    factors = [
        Factor("Temperature", [250, 350], "continuous"),  # °C
        Factor("Pressure", [2, 8], "continuous"),  # bar
    ]

    print("\n📊 PROCESS FACTORS:")
    print("-" * 25)
    for factor in factors:
        range_str = f"{factor.levels[0]} - {factor.levels[1]}"
        print(f"  {factor.name:12} : {range_str:10} {get_units(factor.name)}")

    # ========================================================================
    # EXPERIMENTAL DESIGN
    # ========================================================================

    print("\n🔬 RESPONSE SURFACE DESIGN:")
    print("-" * 35)

    # Create Central Composite Design
    rsm_design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=6)
    design_matrix = rsm_design.generate_design()

    # Display design properties
    properties = rsm_design.design_properties()
    print(f"Design Type: {properties['design_type']}")
    print(f"Number of Factors: {properties['n_factors']}")
    print(f"Total Runs: {properties['n_runs']}")
    print(f"Alpha (rotatability): {properties['alpha']:.3f}")
    print(f"Rotatable Design: {properties['rotatable']}")

    print("\nDesign Point Distribution:")
    point_counts = design_matrix["PointType"].value_counts()
    for point_type, count in point_counts.items():
        print(f"  {point_type:10} : {count:2d} runs")

    print("\n📋 EXPERIMENTAL DESIGN MATRIX:")
    print("-" * 40)
    print(design_matrix.round(1).to_string(index=False))

    # ========================================================================
    # DATA COLLECTION (Simulation)
    # ========================================================================

    print("\n🧪 CONDUCTING EXPERIMENTS...")
    print("-" * 35)

    # Simulate realistic chemical reaction data
    rng = np.random.default_rng(42)  # For reproducible results
    yields = simulate_chemical_reaction_yield(design_matrix, rng=rng)
    design_matrix["Yield"] = yields

    print("Experimental data collected!")
    print("Yield Statistics:")
    print(f"  Mean: {np.mean(yields):.1f}%")
    print(f"  Std Dev: {np.std(yields):.1f}%")
    print(f"  Range: {np.min(yields):.1f} - {np.max(yields):.1f}%")

    print("\n📊 EXPERIMENTAL RESULTS:")
    print("-" * 30)
    results_display = design_matrix[
        ["Temperature", "Pressure", "Yield", "PointType"]
    ].round(1)
    print(results_display.to_string(index=False))

    # ========================================================================
    # RESPONSE SURFACE ANALYSIS
    # ========================================================================

    print("\n📈 RESPONSE SURFACE ANALYSIS:")
    print("=" * 40)

    # Fit quadratic response surface model
    response_analysis = rsm_design.response_surface_analysis(yields)

    print("\n🔍 MODEL COEFFICIENTS:")
    print("-" * 30)
    coefficients = response_analysis["coefficients"]
    for term, coeff in coefficients.items():
        significance = "*" if response_analysis["p_values"][term] < 0.05 else ""
        print(f"  {term:20} : {coeff:+8.3f} {significance}")

    print("\n📊 MODEL STATISTICS:")
    print("-" * 25)
    print(f"  R-squared        : {response_analysis['r_squared']:.4f}")
    print(f"  Adj R-squared    : {response_analysis['adj_r_squared']:.4f}")
    print(f"  RMSE             : {response_analysis['rmse']:.3f}")

    print("\n🎯 STATISTICAL SIGNIFICANCE:")
    print("-" * 35)
    significant_terms = []
    for term, p_val in response_analysis["p_values"].items():
        significance_level = get_significance_level(p_val)
        print(f"  {term:20} : p = {p_val:.4f} {significance_level}")
        if p_val < 0.05:
            significant_terms.append(term)

    print(f"\nSignificant terms (p < 0.05): {', '.join(significant_terms)}")

    # ========================================================================
    # OPTIMIZATION
    # ========================================================================

    print("\n🎯 OPTIMIZATION RESULTS:")
    print("-" * 30)

    optimum_actual = response_analysis["optimum_actual"]

    if optimum_actual:
        print("OPTIMAL CONDITIONS:")
        for factor_name, optimal_value in optimum_actual.items():
            units = get_units(factor_name)
            print(f"  {factor_name:12} : {optimal_value:.1f} {units}")

        # Predict optimal response
        optimal_yield = predict_yield_at_conditions(optimum_actual, coefficients)
        print(f"\nPredicted Optimal Yield: {optimal_yield:.1f}%")

        # Check if optimum is within experimental region
        temp_range = factors[0].levels
        pressure_range = factors[1].levels

        temp_within = temp_range[0] <= optimum_actual["Temperature"] <= temp_range[1]
        pressure_within = (
            pressure_range[0] <= optimum_actual["Pressure"] <= pressure_range[1]
        )

        if temp_within and pressure_within:
            print("✅ Optimum is within the experimental region")
        else:
            print("⚠️  Optimum is outside the experimental region")
            print("   Consider expanding the design space or using steepest ascent")
    else:
        print("❌ No stationary point found within reasonable bounds")
        print("   Consider using steepest ascent method or expanding design space")

    # ========================================================================
    # SENSITIVITY ANALYSIS
    # ========================================================================

    print("\n🔄 SENSITIVITY ANALYSIS:")
    print("-" * 30)

    # Calculate relative importance of factors
    factor_importance = calculate_factor_importance(coefficients, factors)

    print("Factor Importance (relative contribution to response):")
    for factor, importance in factor_importance.items():
        print(f"  {factor:12} : {importance:.1f}%")

    # Identify critical factors
    critical_factors = [f for f, imp in factor_importance.items() if imp > 20]
    print(f"\nCritical factors (>20% contribution): {', '.join(critical_factors)}")

    # ========================================================================
    # ROBUSTNESS ANALYSIS
    # ========================================================================

    print("\n🛡️  ROBUSTNESS ANALYSIS:")
    print("-" * 30)

    if optimum_actual:
        robustness_results = analyze_robustness(optimum_actual, coefficients, factors)

        print("Response sensitivity to ±5% changes in factors:")
        for factor, sensitivity in robustness_results.items():
            print(f"  {factor:12} : ±{abs(sensitivity):.2f}% yield change")

        # Recommendations for robust operation
        print("\n💡 ROBUSTNESS RECOMMENDATIONS:")
        print("-" * 35)
        most_sensitive = max(robustness_results.items(), key=lambda x: abs(x[1]))
        print(f"• Maintain tight control on {most_sensitive[0]} (highest sensitivity)")

        least_sensitive = min(robustness_results.items(), key=lambda x: abs(x[1]))
        print(f"• {least_sensitive[0]} is less critical (lowest sensitivity)")

        print("• Implement process monitoring for all critical factors")
        print("• Consider operating slightly away from optimum for robustness")

    # ========================================================================
    # VISUALIZATION
    # ========================================================================

    print("\n📊 CREATING VISUALIZATIONS...")
    print("-" * 35)

    try:
        create_rsm_visualizations(
            design_matrix, rsm_design, coefficients, optimum_actual, factors
        )
        print("✅ All plots saved successfully!")

        plot_files = [
            "rsm_design_space.png",
            "rsm_response_surface.png",
            "rsm_contour_plot.png",
            "rsm_residual_analysis.png",
            "rsm_prediction_variance.png",
        ]

        print("\nGenerated visualizations:")
        for plot_file in plot_files:
            print(f"  📈 {plot_file}")

    except Exception as e:
        print(f"Note: Visualization encountered an issue: {e}")

    # ========================================================================
    # VALIDATION RECOMMENDATIONS
    # ========================================================================

    print("\n✅ VALIDATION RECOMMENDATIONS:")
    print("-" * 40)

    if optimum_actual:
        print("1. CONFIRMATION EXPERIMENTS:")
        print("   • Run 3-5 replicates at optimal conditions")
        print(f"   • Expected yield: {optimal_yield:.1f} ± 2.0%")

        print("\n2. ROBUSTNESS VALIDATION:")
        print("   • Test small deviations from optimal point")
        print("   • Verify process stability over time")

        print("\n3. SCALE-UP CONSIDERATIONS:")
        print("   • Validate model at pilot scale")
        print("   • Monitor for scale-dependent effects")
        print("   • Update model with production data")

    print("\n4. PROCESS CONTROL:")
    print("   • Implement SPC charts for critical factors")
    print("   • Establish control limits based on sensitivity analysis")
    print("   • Regular model validation with new data")

    # ========================================================================
    # ECONOMIC ANALYSIS
    # ========================================================================

    print("\n💰 ECONOMIC IMPACT ANALYSIS:")
    print("-" * 35)

    if optimum_actual:
        # Simple economic analysis
        current_yield = np.mean(yields)  # Assume current average as baseline
        optimal_yield_pred = optimal_yield

        improvement = optimal_yield_pred - current_yield
        relative_improvement = (improvement / current_yield) * 100

        print(f"Current Average Yield: {current_yield:.1f}%")
        print(f"Predicted Optimal Yield: {optimal_yield_pred:.1f}%")
        print(f"Absolute Improvement: +{improvement:.1f} percentage points")
        print(f"Relative Improvement: +{relative_improvement:.1f}%")

        # Hypothetical economic impact (example values)
        annual_production = 1000  # tons per year
        product_value = 5000  # $/ton

        annual_value_increase = annual_production * product_value * (improvement / 100)

        print("\nHypothetical Economic Impact (example):")
        print(f"  Annual Production: {annual_production:,} tons/year")
        print(f"  Product Value: ${product_value:,}/ton")
        print(f"  Annual Value Increase: ${annual_value_increase:,.0f}/year")

    # ========================================================================
    # SUMMARY AND CONCLUSIONS
    # ========================================================================

    print("\n📝 EXECUTIVE SUMMARY:")
    print("=" * 40)

    print("\n🔑 KEY FINDINGS:")
    print("-" * 20)

    # Model adequacy
    r2 = response_analysis["r_squared"]
    if r2 > 0.8:
        model_quality = "Excellent"
    elif r2 > 0.6:
        model_quality = "Good"
    else:
        model_quality = "Poor"

    print(f"1. Model Quality: {model_quality} (R² = {r2:.3f})")

    # Significant factors
    main_effects = [t for t in significant_terms if "*" not in t and t != "Intercept"]
    interactions = [t for t in significant_terms if "*" in t]

    print(
        f"2. Significant Main Effects: {', '.join(main_effects) if main_effects else 'None'}"
    )
    print(
        f"3. Significant Interactions: {', '.join(interactions) if interactions else 'None'}"
    )

    # Optimization result
    if optimum_actual:
        print(f"4. Optimization: Successful - {optimal_yield:.1f}% yield predicted")
    else:
        print("4. Optimization: Stationary point not found in region")

    print("\n💡 STRATEGIC RECOMMENDATIONS:")
    print("-" * 35)

    if optimum_actual and improvement > 2:
        print("• HIGH PRIORITY: Implement optimal conditions immediately")
        print(f"• Expected yield improvement: +{improvement:.1f} percentage points")
    elif optimum_actual:
        print("• MODERATE PRIORITY: Consider optimization implementation")
        print(f"• Modest improvement expected: +{improvement:.1f} percentage points")
    else:
        print("• EXPLORATION NEEDED: Expand experimental region")
        print("• Current region may not contain optimum")

    print("• Establish robust process control for critical factors")
    print("• Validate model predictions with confirmation experiments")
    print("• Consider advanced optimization techniques if needed")

    print("\n🚀 NEXT STEPS:")
    print("-" * 15)
    print("1. Conduct confirmation experiments at optimal conditions")
    print("2. Implement process changes in controlled manner")
    print("3. Monitor process performance and update model")
    print("4. Train operators on optimal operating procedures")
    print("5. Document standard operating procedures")

    print("\n" + "=" * 80)
    print("RESPONSE SURFACE OPTIMIZATION COMPLETE!")
    print("Check generated visualizations for detailed insights.")
    print("=" * 80)


def simulate_chemical_reaction_yield(
    design_matrix: pd.DataFrame, rng: np.random.Generator | None = None
) -> np.ndarray:
    """
    Simulate realistic chemical reaction yield data.

    Models a catalytic reaction where:
    - Higher temperature generally increases yield (up to a point)
    - Higher pressure increases yield
    - There's an optimal temperature around 300°C
    - Temperature and pressure interact

    Pass a seeded ``rng`` for reproducible output; a fresh unseeded generator
    is used by default.
    """
    if rng is None:
        rng = np.random.default_rng()

    yields = []

    for _, row in design_matrix.iterrows():
        temp = row["Temperature"]
        pressure = row["Pressure"]

        # Base yield model (quadratic response surface)
        # Optimal around 300°C and 6 bar

        # Convert to coded variables for easier modeling
        temp_coded = (temp - 300) / 50  # Center at 300°C, scale by 50
        pressure_coded = (pressure - 5) / 1.5  # Center at 5 bar, scale by 1.5

        # Quadratic response surface
        yield_response = (
            75  # Baseline yield
            + 8 * temp_coded  # Linear temperature effect
            + 12 * pressure_coded  # Linear pressure effect
            + -3 * temp_coded**2  # Quadratic temperature (optimum)
            + -2 * pressure_coded**2  # Quadratic pressure
            + 4 * temp_coded * pressure_coded  # Interaction
            + rng.normal(0, 2.5)  # Experimental error
        )

        # Ensure realistic bounds
        yield_response = max(min(yield_response, 95), 40)
        yields.append(yield_response)

    return np.array(yields)


def get_units(factor_name: str) -> str:
    """Get units for factors."""
    units_map = {
        "Temperature": "°C",
        "Pressure": "bar",
        "Time": "min",
        "Concentration": "mol/L",
    }
    return units_map.get(factor_name, "")


def get_significance_level(p_value: float) -> str:
    """Get significance level indicator."""
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    if p_value < 0.1:
        return "."
    return ""


def predict_yield_at_conditions(conditions: dict, coefficients: dict) -> float:
    """Predict yield at given conditions using response surface model."""
    temp = conditions["Temperature"]
    pressure = conditions["Pressure"]

    # Convert to coded variables (same as in simulation)
    temp_coded = (temp - 300) / 50
    pressure_coded = (pressure - 5) / 1.5

    # Calculate prediction using model coefficients
    prediction = coefficients["Intercept"]

    # Linear terms
    prediction += coefficients.get("Temperature", 0) * temp_coded
    prediction += coefficients.get("Pressure", 0) * pressure_coded

    # Quadratic terms
    prediction += coefficients.get("Temperature²", 0) * temp_coded**2
    prediction += coefficients.get("Pressure²", 0) * pressure_coded**2

    # Interaction term
    prediction += (
        coefficients.get("Temperature*Pressure", 0) * temp_coded * pressure_coded
    )

    return prediction


def calculate_factor_importance(coefficients: dict, factors: list) -> dict:
    """Calculate relative importance of factors."""
    importance = {}

    # Get coefficient magnitudes for main effects
    main_effects = {}
    for factor in factors:
        coeff = coefficients.get(factor.name, 0)
        main_effects[factor.name] = abs(coeff)

    # Calculate relative importance
    total_effect = sum(main_effects.values())

    if total_effect > 0:
        for factor_name, effect in main_effects.items():
            importance[factor_name] = (effect / total_effect) * 100
    else:
        for factor in factors:
            importance[factor.name] = 0

    return importance


def analyze_robustness(
    optimal_conditions: dict, coefficients: dict, factors: list
) -> dict:
    """Analyze response sensitivity to changes in optimal conditions."""
    sensitivities = {}

    for factor in factors:
        factor_name = factor.name
        optimal_value = optimal_conditions[factor_name]

        # Calculate range (5% of factor range)
        factor_range = factor.levels[1] - factor.levels[0]
        delta = 0.05 * factor_range

        # Calculate yield at optimal ± delta
        conditions_plus = optimal_conditions.copy()
        conditions_minus = optimal_conditions.copy()

        conditions_plus[factor_name] = optimal_value + delta
        conditions_minus[factor_name] = optimal_value - delta

        yield_plus = predict_yield_at_conditions(conditions_plus, coefficients)
        yield_minus = predict_yield_at_conditions(conditions_minus, coefficients)

        # Sensitivity = change in yield per unit change in factor
        sensitivity = (yield_plus - yield_minus) / (2 * delta) * delta
        sensitivities[factor_name] = sensitivity

    return sensitivities


def create_rsm_visualizations(
    design_matrix: pd.DataFrame,
    rsm_design,
    coefficients: dict,
    optimum_actual: dict,
    factors: list,
):
    """Create comprehensive RSM visualization suite."""

    # 1. Design space plot
    fig1, ax1 = plt.subplots(figsize=(10, 8))

    # Plot design points by type
    point_types = design_matrix["PointType"].unique()
    colors = {"Factorial": "blue", "Axial": "red", "Center": "green"}
    markers = {"Factorial": "o", "Axial": "s", "Center": "^"}

    for point_type in point_types:
        subset = design_matrix[design_matrix["PointType"] == point_type]
        ax1.scatter(
            subset["Temperature"],
            subset["Pressure"],
            c=colors[point_type],
            marker=markers[point_type],
            s=100,
            alpha=0.7,
            label=point_type,
            edgecolors="black",
        )

    # Add optimum if found
    if optimum_actual:
        ax1.scatter(
            optimum_actual["Temperature"],
            optimum_actual["Pressure"],
            c="gold",
            marker="*",
            s=300,
            edgecolors="black",
            linewidth=2,
            label="Optimum",
            zorder=5,
        )

    ax1.set_xlabel("Temperature (°C)")
    ax1.set_ylabel("Pressure (bar)")
    ax1.set_title("Response Surface Design Space")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    fig1.savefig("rsm_design_space.png", dpi=300, bbox_inches="tight")
    plt.close(fig1)

    # 2. Response surface 3D plot
    fig2 = plt.figure(figsize=(12, 9))
    ax2 = fig2.add_subplot(111, projection="3d")

    # Create contour data
    X, Y, Z = rsm_design.contour_data(
        coefficients, "Temperature", "Pressure", grid_size=25
    )

    # 3D surface
    surface = ax2.plot_surface(X, Y, Z, cmap="viridis", alpha=0.8, linewidth=0)

    # Add experimental points
    ax2.scatter(
        design_matrix["Temperature"],
        design_matrix["Pressure"],
        design_matrix["Yield"],
        c="red",
        s=50,
        alpha=0.8,
    )

    # Add optimum
    if optimum_actual:
        optimal_yield = predict_yield_at_conditions(optimum_actual, coefficients)
        ax2.scatter(
            optimum_actual["Temperature"],
            optimum_actual["Pressure"],
            optimal_yield,
            c="gold",
            marker="*",
            s=200,
        )

    ax2.set_xlabel("Temperature (°C)")
    ax2.set_ylabel("Pressure (bar)")
    ax2.set_zlabel("Yield (%)")
    ax2.set_title("3D Response Surface")

    # Add colorbar
    fig2.colorbar(surface, shrink=0.5, aspect=5, label="Yield (%)")

    fig2.savefig("rsm_response_surface.png", dpi=300, bbox_inches="tight")
    plt.close(fig2)

    # 3. Contour plot
    fig3, ax3 = plt.subplots(figsize=(10, 8))

    # Contour plot
    contour = ax3.contour(X, Y, Z, levels=15, colors="black", alpha=0.4, linewidths=0.5)
    ax3.clabel(contour, inline=True, fontsize=8)
    contourf = ax3.contourf(X, Y, Z, levels=15, cmap="viridis", alpha=0.8)

    # Add experimental points
    ax3.scatter(
        design_matrix["Temperature"],
        design_matrix["Pressure"],
        c=design_matrix["Yield"],
        s=100,
        cmap="viridis",
        edgecolors="white",
        linewidth=1,
        zorder=5,
    )

    # Add optimum
    if optimum_actual:
        ax3.scatter(
            optimum_actual["Temperature"],
            optimum_actual["Pressure"],
            c="gold",
            marker="*",
            s=300,
            edgecolors="black",
            linewidth=2,
            zorder=6,
        )

    ax3.set_xlabel("Temperature (°C)")
    ax3.set_ylabel("Pressure (bar)")
    ax3.set_title("Response Surface Contour Plot")

    # Add colorbar
    plt.colorbar(contourf, label="Yield (%)")

    fig3.savefig("rsm_contour_plot.png", dpi=300, bbox_inches="tight")
    plt.close(fig3)

    # 4. Residual analysis (if we have a fitted model)
    try:
        fig4, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Calculate residuals (simplified)
        predicted_yields = []
        for _, row in design_matrix.iterrows():
            conditions = {
                "Temperature": row["Temperature"],
                "Pressure": row["Pressure"],
            }
            pred = predict_yield_at_conditions(conditions, coefficients)
            predicted_yields.append(pred)

        residuals = design_matrix["Yield"] - np.array(predicted_yields)

        # Residuals vs fitted
        axes[0, 0].scatter(predicted_yields, residuals, alpha=0.7)
        axes[0, 0].axhline(y=0, color="red", linestyle="--")
        axes[0, 0].set_xlabel("Fitted Values")
        axes[0, 0].set_ylabel("Residuals")
        axes[0, 0].set_title("Residuals vs Fitted")
        axes[0, 0].grid(True, alpha=0.3)

        # Normal Q-Q plot
        from scipy import stats

        stats.probplot(residuals, dist="norm", plot=axes[0, 1])
        axes[0, 1].set_title("Normal Q-Q Plot")
        axes[0, 1].grid(True, alpha=0.3)

        # Histogram of residuals
        axes[1, 0].hist(residuals, bins=8, alpha=0.7, edgecolor="black")
        axes[1, 0].set_xlabel("Residuals")
        axes[1, 0].set_ylabel("Frequency")
        axes[1, 0].set_title("Histogram of Residuals")
        axes[1, 0].grid(True, alpha=0.3)

        # Residuals vs run order
        axes[1, 1].plot(residuals, "o-", alpha=0.7)
        axes[1, 1].axhline(y=0, color="red", linestyle="--")
        axes[1, 1].set_xlabel("Run Order")
        axes[1, 1].set_ylabel("Residuals")
        axes[1, 1].set_title("Residuals vs Run Order")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        fig4.savefig("rsm_residual_analysis.png", dpi=300, bbox_inches="tight")
        plt.close(fig4)

    except Exception as e:
        print(f"Could not create residual plots: {e}")

    # 5. Prediction variance map (simplified)
    try:
        fig5, ax5 = plt.subplots(figsize=(10, 8))

        # Create a simple prediction variance visualization
        # This is a simplified version - full implementation would use design matrix
        temp_range = np.linspace(250, 350, 20)
        pressure_range = np.linspace(2, 8, 20)
        T_grid, P_grid = np.meshgrid(temp_range, pressure_range)

        # Simple variance model (higher variance away from center and design points)
        center_temp, center_pressure = 300, 5
        variance_grid = np.sqrt(
            (T_grid - center_temp) ** 2 / 2500 + (P_grid - center_pressure) ** 2 / 9
        )

        contour_var = ax5.contour(
            T_grid, P_grid, variance_grid, levels=10, colors="black", alpha=0.4
        )
        ax5.clabel(contour_var, inline=True, fontsize=8)
        contourf_var = ax5.contourf(
            T_grid, P_grid, variance_grid, levels=10, cmap="Reds", alpha=0.7
        )

        # Add design points
        ax5.scatter(
            design_matrix["Temperature"],
            design_matrix["Pressure"],
            c="blue",
            s=80,
            alpha=0.8,
            edgecolors="white",
            linewidth=1,
        )

        ax5.set_xlabel("Temperature (°C)")
        ax5.set_ylabel("Pressure (bar)")
        ax5.set_title("Prediction Variance Map (Relative)")

        plt.colorbar(contourf_var, label="Relative Prediction Variance")

        fig5.savefig("rsm_prediction_variance.png", dpi=300, bbox_inches="tight")
        plt.close(fig5)

    except Exception as e:
        print(f"Could not create prediction variance plot: {e}")


if __name__ == "__main__":
    main()
