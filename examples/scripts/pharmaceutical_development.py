"""Pharmaceutical formulation optimization using a mixture design.

This example demonstrates a realistic drug formulation workflow that
incorporates multiple response variables, regulatory compliance checks,
and risk assessment. Three formulation components are studied using a
simplex-lattice mixture design and the responses considered are efficacy,
stability, and cost. A Monte Carlo robustness analysis estimates the
probability of meeting regulatory targets for each candidate formulation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from industrialstats.designs.advanced import MixtureDesign
from industrialstats.designs.base import Factor
from industrialstats.utils.data_generation import DataSimulator

EFFICACY_THRESHOLD = 0.6
STABILITY_THRESHOLD = 0.3
COST_THRESHOLD = 0.8


def simulate_responses(design: pd.DataFrame, seed: int = 123) -> pd.DataFrame:
    """Simulate efficacy, stability, and cost responses for each run.

    Parameters
    ----------
    design : pandas.DataFrame
        Mixture design matrix with component proportions.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    pandas.DataFrame
        Design matrix with three response columns added.
    """
    sim = DataSimulator(seed)

    eff = sim.simulate_factorial_response(
        design,
        main_effects={"API": 1.0, "Stabilizer": 0.2, "Filler": -0.1},
        interactions={("API", "Stabilizer"): 0.4},
        noise_level=0.03,
    )

    stab = sim.simulate_factorial_response(
        design,
        main_effects={"API": -0.2, "Stabilizer": 0.8, "Filler": 0.1},
        interactions={("Stabilizer", "Filler"): 0.3},
        noise_level=0.03,
    )

    cost = design["API"] * 0.9 + design["Stabilizer"] * 0.3 + design["Filler"] * 0.1
    # small manufacturing variability
    rng = np.random.default_rng(seed)
    cost = cost + rng.normal(0, 0.01, size=len(cost))

    out = design.copy()
    out["Efficacy"] = eff
    out["Stability"] = stab
    out["Cost"] = cost
    return out


def assess_risk(
    design: pd.DataFrame, n_sim: int = 500, seed: int = 1234
) -> pd.DataFrame:
    """Estimate regulatory compliance risk for each candidate formulation.

    Parameters
    ----------
    design : pandas.DataFrame
        Design matrix with responses.
    n_sim : int, optional
        Number of Monte Carlo replicates for robustness analysis.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    pandas.DataFrame
        DataFrame with additional column ``Risk`` giving probability of
        violating any regulatory requirement.
    """
    rng = np.random.default_rng(seed)
    risks = []
    for _, row in design.iterrows():
        passes = 0
        base = row[["API", "Stabilizer", "Filler"]].to_numpy()
        for _ in range(n_sim):
            perturbed = base + rng.normal(0, 0.01, size=3)
            perturbed = np.clip(perturbed, 0, None)
            perturbed /= perturbed.sum()
            sim_design = pd.DataFrame(
                [perturbed], columns=["API", "Stabilizer", "Filler"]
            )
            sim = simulate_responses(sim_design, seed=rng.integers(0, 10_000))
            if (
                sim["Efficacy"].iat[0] >= EFFICACY_THRESHOLD
                and sim["Stability"].iat[0] >= STABILITY_THRESHOLD
                and sim["Cost"].iat[0] <= COST_THRESHOLD
            ):
                passes += 1
        risks.append(1 - passes / n_sim)
    out = design.copy()
    out["Risk"] = risks
    return out


def main() -> None:
    """Run the pharmaceutical development study."""
    factors = [
        Factor("API", [], "continuous"),
        Factor("Stabilizer", [], "continuous"),
        Factor("Filler", [], "continuous"),
    ]
    design = MixtureDesign(factors, order=2, randomize=True, seed=42)
    design_matrix = design.generate_design()

    design_with_resp = simulate_responses(design_matrix)
    assessed = assess_risk(design_with_resp)

    print("Design with responses and risk (first 10 rows):")
    print(assessed.head(10).to_string(index=False))

    compliant = assessed[
        (assessed["Efficacy"] >= EFFICACY_THRESHOLD)
        & (assessed["Stability"] >= STABILITY_THRESHOLD)
        & (assessed["Cost"] <= COST_THRESHOLD)
    ]
    if not compliant.empty:
        best = compliant.nsmallest(1, "Risk")
        print("\nRecommended formulation (minimum risk while meeting targets):")
        print(best.to_string(index=False))
    else:
        print("\nNo formulation met all regulatory thresholds in the nominal data.")


if __name__ == "__main__":
    main()
