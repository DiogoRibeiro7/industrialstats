import unittest
import pandas as pd
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from doe_python.utils.validation import DesignValidator
from doe_python.designs.base import Factor


class TestDesignValidator(unittest.TestCase):
    def test_validate_factors(self):
        factors = [Factor("A", [0, 1]), Factor("B", [1])]
        warnings = DesignValidator.validate_factors(factors)
        self.assertIn("fewer than 2 levels", warnings[0])

    def test_validate_design_matrix(self):
        df = pd.DataFrame({"A": [0, 1, 0], "B": [1, 0, 2]})
        result = DesignValidator.validate_design_matrix(df)
        self.assertFalse(result["missing_values"])
        self.assertFalse(result["duplicate_rows"])

    def test_check_confounding(self):
        df = pd.DataFrame({"A": [0, 1, 0, 1], "B": [0, 1, 0, 1]})
        confounding = DesignValidator.check_confounding(df)
        self.assertIn("A", confounding)

    def test_estimate_power(self):
        df = pd.DataFrame({"A": [0, 1, 0, 1], "B": [0, 0, 1, 1]})
        power = DesignValidator.estimate_power(df, 1.0)
        self.assertGreater(power, 0)
        self.assertLess(power, 1)


if __name__ == "__main__":
    unittest.main()
