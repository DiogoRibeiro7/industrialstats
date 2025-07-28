import unittest
import pandas as pd
import os
import sys

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from doe_python.utils.data_generation import DataSimulator
from doe_python.designs.factorial import FactorialDesign
from doe_python.designs.base import Factor


class TestDataSimulator(unittest.TestCase):
    def test_simulate_factorial_response(self):
        factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        design = FactorialDesign(factors, replicates=1)
        dm = design.generate_design()
        simulator = DataSimulator(seed=123)
        response = simulator.simulate_factorial_response(dm)
        self.assertEqual(len(response), len(dm))


if __name__ == "__main__":
    unittest.main()
