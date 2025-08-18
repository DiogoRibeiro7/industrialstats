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


if __name__ == "__main__":
    unittest.main()
