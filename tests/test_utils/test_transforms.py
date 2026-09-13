import unittest

import pandas as pd
from dataexcept import FeaturePreprocessingError, MissingColumnError

from industrialstats.utils.transforms import center, log_transform, standardize


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

    def test_log_transform_raises_missing_column_error(self):
        with self.assertRaises(MissingColumnError) as ctx:
            log_transform(self.df, ["missing"])

        self.assertEqual(ctx.exception.column, "missing")
        self.assertEqual(ctx.exception.dataframe, "log_transform input")

    def test_log_transform_rejects_non_numeric_column(self):
        frame = pd.DataFrame({"label": ["a", "b"]})

        with self.assertRaises(FeaturePreprocessingError) as ctx:
            log_transform(frame, ["label"])

        self.assertEqual(ctx.exception.feature, "label")
        self.assertEqual(
            ctx.exception.reason, "log transform requires a numeric column"
        )

    def test_log_transform_rejects_non_positive_values(self):
        frame = pd.DataFrame({"A": [1.0, 0.0, -1.0]})

        with self.assertRaises(FeaturePreprocessingError) as ctx:
            log_transform(frame, ["A"])

        self.assertEqual(ctx.exception.feature, "A")
        self.assertEqual(
            ctx.exception.reason,
            "log transform requires strictly positive values",
        )


if __name__ == "__main__":
    unittest.main()
