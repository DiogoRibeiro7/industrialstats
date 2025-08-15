import unittest

import pandas as pd

from doe_python.utils.transforms import center, log_transform, standardize


class TestTransforms(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0]})

    def test_center(self):
        centered = center(self.df)
        self.assertAlmostEqual(centered["A"].mean(), 0.0)

    def test_standardize(self):
        standardized = standardize(self.df)
        self.assertAlmostEqual(float(standardized["B"].std(ddof=0)), 1.0)

    def test_log_transform(self):
        transformed = log_transform(self.df, ["A"])
        self.assertTrue(
            all(
                transformed["A"]
                == self.df["A"].apply(lambda x: __import__("math").log(x))
            )
        )


if __name__ == "__main__":
    unittest.main()
