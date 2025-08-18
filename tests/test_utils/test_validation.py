import unittest

import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.utils.validation import DesignValidator


class TestDesignValidator(unittest.TestCase):
    def test_validate_factors(self):
        factors = [Factor("A", [0, 1]), Factor("B", [1])]
        warnings = DesignValidator.validate_factors(factors)
        self.assertTrue(any("fewer than 2 levels" in w for w in warnings))

    def test_validate_design_matrix(self):
        df = pd.DataFrame({"A": [0, 1, 0], "B": [1, 0, 2]})
        result = DesignValidator.validate_design_matrix(df)
        self.assertFalse(result["missing_values"])
        self.assertFalse(result["duplicate_rows"])
        self.assertEqual(result["missing_counts"], {"A": 0, "B": 0})

    def test_check_confounding(self):
        df = pd.DataFrame({"A": [0, 1, 0, 1], "B": [0, 1, 0, 1]})
        confounding = DesignValidator.check_confounding(df)
        self.assertIn("A", confounding["high_correlation"])

    def test_estimate_power(self):
        df = pd.DataFrame({"A": [0, 1, 0, 1], "B": [0, 0, 1, 1]})
        power = DesignValidator.estimate_power(df, 1.0)
        self.assertGreater(power, 0)
        self.assertLess(power, 1)


if __name__ == "__main__":
    unittest.main()
