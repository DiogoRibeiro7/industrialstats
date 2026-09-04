from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.utils.data_generation import DataSimulator


class TestDataSimulator(unittest.TestCase):
    def setUp(self) -> None:
        self.factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        self.design = FactorialDesign(self.factors, replicates=2, randomize=False)
        self.dm = self.design.generate_design()
        self.simulator = DataSimulator(seed=1234)

    def test_simulate_factorial_response_supports_heavy_tails(self) -> None:
        response = self.simulator.simulate_factorial_response(
            self.dm,
            main_effects={"A": 1.0, "B": -0.5},
            noise_dist="t",
            noise_params={"df": 7},
            heteroskedastic=lambda df: np.linspace(0.5, 1.5, len(df)),
        )
        self.assertEqual(len(response), len(self.dm))
        self.assertAlmostEqual(response.iloc[0], -0.828109, places=6)
        self.assertGreater(np.nanmax(np.abs(response)), 1.0)

    def test_measurement_error_increases_variability(self) -> None:
        base_sim = DataSimulator(seed=1234)
        base = base_sim.simulate_factorial_response(
            self.dm,
            noise_level=0.0,
            measurement_error={"scale": 0.2, "distribution": "normal"},
        )
        reference_sim = DataSimulator(seed=1234)
        without_error = reference_sim.simulate_factorial_response(
            self.dm,
            noise_level=0.0,
            measurement_error=None,
        )
        self.assertGreater(np.nanvar(base), np.nanvar(without_error))

    def test_missing_mechanisms_mar_and_mnar(self) -> None:
        dm = self.dm.copy()
        dm["Covariate"] = np.linspace(0.0, 1.0, len(dm))
        ordered_cols = ["Covariate"] + [c for c in dm.columns if c != "Covariate"]
        dm = dm[ordered_cols]
        mar = self.simulator.simulate_factorial_response(
            dm,
            missing_rate=0.5,
            missing_pattern="MAR",
        )
        mnar = self.simulator.simulate_factorial_response(
            dm,
            missing_rate=0.5,
            missing_pattern="MNAR",
        )
        self.assertGreater(mar.isna().mean(), 0.0)
        self.assertGreater(mnar.isna().mean(), 0.0)

    def test_simulate_process_data_with_trend_and_seasonality(self) -> None:
        def model(df: pd.DataFrame) -> np.ndarray:
            return np.sin(df["t"]) * 0.1

        result = self.simulator.simulate_process_data(
            n_periods=50,
            model=model,
            trend={"type": "linear", "slope": 0.05, "intercept": 1.0},
            seasonality={"period": 12, "amplitude": 0.5},
            heteroskedastic=np.linspace(0.2, 0.5, 50),
            return_components=True,
        )
        self.assertIn("deterministic", result.columns)
        self.assertIn("stochastic", result.columns)
        self.assertEqual(len(result), 50)
        self.assertFalse(result["deterministic"].is_monotonic_increasing)

    def test_simulate_process_data_autocorrelation(self) -> None:
        series = self.simulator.simulate_process_data(
            n_periods=200,
            model=lambda df: np.zeros(len(df)),
            ar_params=[0.6],
            noise_dist="normal",
        )
        values = series["response"].dropna().to_numpy()
        acorr = np.corrcoef(values[1:], values[:-1])[0, 1]
        self.assertGreater(acorr, 0.4)

    def test_simulate_process_data_outliers_and_missing(self) -> None:
        series = self.simulator.simulate_process_data(
            n_periods=80,
            model=lambda df: np.zeros(len(df)),
            outliers={"random": {"fraction": 0.1, "magnitude": 10}},
            missing={"mechanism": "MCAR", "rate": 0.2},
        )
        missing_share = series["response"].isna().mean()
        self.assertAlmostEqual(missing_share, 0.2, delta=0.1)
        finite_values = series["response"].dropna()
        self.assertGreater(finite_values.abs().max(), 5.0)

    def test_simulate_multi_response_handles_varied_types(self) -> None:
        models = [
            lambda df: df["A"].to_numpy(),
            lambda df: -0.5 * df["B"].to_numpy(),
            lambda df: 0.2 * df["A"].to_numpy(),
        ]
        covariance = np.array(
            [
                [1.0, 0.2, 0.1],
                [0.2, 1.5, 0.3],
                [0.1, 0.3, 1.0],
            ]
        )
        df = self.simulator.simulate_multi_response(
            self.dm,
            models,
            covariance,
            response_types=["continuous", "categorical", "count"],
            measurement_error=[None, None, None],
        )
        self.assertEqual(len(df), len(self.dm))
        self.assertTrue(set(np.unique(df["Y2"])) <= {0, 1})
        self.assertTrue((df["Y3"] >= 0).all())
        corr = df[["Y1", "Y2"]].corr().iloc[0, 1]
        self.assertFalse(np.isnan(corr))

    def test_validate_against_real_data_reports_statistics(self) -> None:
        simulated = self.simulator.simulate_factorial_response(self.dm, noise_level=0.0)
        stats = self.simulator.validate_against_real_data(simulated, simulated.copy())
        expected: dict[str, float] = stats["Response"]
        self.assertLess(expected["mean_diff"], 1e-9)
        self.assertIn("ks_like", expected)


if __name__ == "__main__":
    unittest.main()
