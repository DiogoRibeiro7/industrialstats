import unittest

import numpy as np

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.utils.data_generation import DataSimulator


class TestDataSimulator(unittest.TestCase):
    def test_simulate_factorial_response(self):
        factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        design = FactorialDesign(factors, replicates=1)
        dm = design.generate_design()
        simulator = DataSimulator(seed=123)
        response = simulator.simulate_factorial_response(
            dm, interactions={("A", "B"): 0.5}, noise_dist="laplace"
        )
        self.assertEqual(len(response), len(dm))

    def test_response_types(self):
        factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        design = FactorialDesign(factors, replicates=1)
        dm = design.generate_design()
        simulator = DataSimulator(seed=123)
        bin_resp = simulator.simulate_factorial_response(dm, response_type="binomial")
        self.assertTrue(set(np.unique(bin_resp)).issubset({0, 1}))
        pois_resp = simulator.simulate_factorial_response(dm, response_type="poisson")
        self.assertTrue((pois_resp >= 0).all())

    def test_multiple_interactions(self):
        factors = [Factor("A", [0, 1]), Factor("B", [0, 1]), Factor("C", [0, 1])]
        design = FactorialDesign(factors, replicates=1)
        dm = design.generate_design()
        simulator = DataSimulator(seed=42)
        response = simulator.simulate_factorial_response(
            dm,
            interactions={("A", "B"): 1.0, ("B", "C"): -0.5},
            noise_level=0.0,
        )
        self.assertEqual(len(response), len(dm))

    def test_random_effects_and_correlated_noise(self):
        factors = [Factor("A", [0, 1])]
        design = FactorialDesign(factors, replicates=2)
        dm = design.generate_design()
        dm["Batch"] = [1, 1, 2, 2]
        simulator = DataSimulator(seed=7)
        response = simulator.simulate_factorial_response(
            dm,
            random_effects={"Batch": 0.5},
            corr=0.3,
        )
        self.assertEqual(len(response), len(dm))

    def test_heteroskedastic_and_drift(self):
        factors = [Factor("A", [0, 1])]
        design = FactorialDesign(factors, replicates=10)
        dm = design.generate_design()
        hetero = np.linspace(0.1, 1.0, len(dm))
        simulator = DataSimulator(seed=5)
        response = simulator.simulate_factorial_response(
            dm, heteroskedastic=hetero, drift=0.5
        )
        self.assertGreater(response.iloc[-1], response.iloc[0])
        first_var = np.nanvar(response[:10])
        last_var = np.nanvar(response[-10:])
        self.assertNotAlmostEqual(first_var, last_var)

    def test_missing_data(self):
        factors = [Factor("A", [0, 1])]
        design = FactorialDesign(factors, replicates=5)
        dm = design.generate_design()
        simulator = DataSimulator(seed=1)
        response = simulator.simulate_factorial_response(dm, missing_rate=0.2)
        self.assertAlmostEqual(response.isna().mean(), 0.2, delta=0.1)

    def test_correlated_responses(self):
        factors = [Factor("A", [0, 1])]
        design = FactorialDesign(factors, replicates=20)
        dm = design.generate_design()
        sim = DataSimulator(seed=0)
        cov = np.array([[1.0, 0.8], [0.8, 1.0]])
        df = sim.simulate_correlated_responses(dm, [{"A": 1}, {"A": 1}], cov)
        corr = df.corr().iloc[0, 1]
        self.assertAlmostEqual(corr, 0.8, delta=0.15)

    def test_validation_against_real_data(self):
        factors = [Factor("A", [0, 1])]
        design = FactorialDesign(factors, replicates=1)
        dm = design.generate_design()
        sim = DataSimulator(seed=2)
        simulated = sim.simulate_factorial_response(dm, noise_level=0.0)
        stats = sim.validate_against_real_data(simulated, simulated.copy())
        self.assertLess(stats["Response"]["mean_diff"], 1e-9)


if __name__ == "__main__":
    unittest.main()
