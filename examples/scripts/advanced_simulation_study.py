"""Advanced manufacturing simulation study using :class:`DataSimulator`.

This script demonstrates how the :class:`industrialstats.utils.data_generation.DataSimulator`
class can be used to reproduce multi-response process behaviours with complex
noise structures, measurement error, and missing data. The scenario mirrors the
guidelines in Montgomery [1]_ for factorial settings and Box & Jenkins [2]_ for
process dynamics.

References
----------
.. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed.
       Wiley.
.. [2] Box, G.E.P., Jenkins, G.M., Reinsel, G.C., & Ljung, G.M. (2015).
       *Time Series Analysis: Forecasting and Control*, 5th ed. Wiley.
.. [3] Carroll, R.J., Ruppert, D., Stefanski, L.A., & Crainiceanu, C.M. (2006).
       *Measurement Error in Nonlinear Models*, 2nd ed. Chapman & Hall/CRC.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.utils.data_generation import DataSimulator


def build_design() -> pd.DataFrame:
    """Construct a :math:`2^3` factorial design with replicates."""

    factors = [
        Factor("Temperature", levels=[-1, 1]),
        Factor("Pressure", levels=[-1, 1]),
        Factor("Catalyst", levels=[-1, 1]),
    ]
    design = FactorialDesign(factors, replicates=2, randomize=False)
    return design.generate_design()


def main() -> None:
    """Simulate continuous, binary, and count responses with diagnostics."""

    design_matrix = build_design()
    simulator = DataSimulator(seed=2024)

    def continuous_model(df: pd.DataFrame) -> np.ndarray:
        return (
            3.0
            + 1.5 * df["Temperature"].to_numpy()
            - 1.0 * df["Pressure"].to_numpy()
            + 0.8 * df["Temperature"].to_numpy() * df["Catalyst"].to_numpy()
        )

    def binary_model(df: pd.DataFrame) -> np.ndarray:
        return -1.0 + 0.75 * df["Pressure"].to_numpy()

    def count_model(df: pd.DataFrame) -> np.ndarray:
        return 0.2 * df["Catalyst"].to_numpy()

    covariance = np.array(
        [
            [1.0, 0.2, 0.1],
            [0.2, 1.0, 0.15],
            [0.1, 0.15, 0.8],
        ]
    )

    multi_response = simulator.simulate_multi_response(
        design_matrix,
        [continuous_model, binary_model, count_model],
        covariance,
        response_types=["continuous", "categorical", "count"],
        measurement_error=[
            {"scale": 0.1, "distribution": "normal"},
            {"scale": 0.05, "distribution": "laplace"},
            None,
        ],
    )

    process = simulator.simulate_process_data(
        n_periods=120,
        model=lambda df: 5 + 0.4 * np.sin(2 * np.pi * df["t"] / 12),
        trend={"type": "linear", "slope": -0.01},
        seasonality={"period": 12, "amplitude": 0.6},
        ar_params=[0.5],
        ma_params=[-0.2],
        heteroskedastic=np.linspace(0.2, 0.6, 120),
        outliers={"leverage": {"fraction": 0.05, "magnitude": 8}},
        missing={"mechanism": "MNAR", "rate": 0.1},
        measurement_error={"scale": 0.05, "distribution": "normal"},
        return_components=True,
    )

    output_dir = Path(__file__).resolve().parent / ".." / ".." / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    multi_response.to_csv(output_dir / "advanced_multi_response.csv", index=False)
    process.to_csv(output_dir / "advanced_process_series.csv", index=False)

    comparison = simulator.validate_against_real_data(
        multi_response[["Y1"]], multi_response[["Y1"]]
    )
    print("Similarity diagnostics:", comparison)


if __name__ == "__main__":
    main()
