import unittest

import pandas as pd
from dataexcept import DataTransformationError, DtypeMismatchError, MissingColumnError

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

    def test_log_transform_missing_column_uses_structured_schema_error(self):
        with self.assertRaises(MissingColumnError) as context:
            log_transform(self.df, ["missing"])

        error = context.exception
        self.assertEqual(error.column, "missing")
        self.assertEqual(error.dataframe, "transform_input")

    def test_log_transform_non_numeric_column_uses_structured_dtype_error(self):
        frame = self.df.assign(label=["a", "b", "c"])

        with self.assertRaises(DtypeMismatchError) as context:
            log_transform(frame, ["label"])

        error = context.exception
        self.assertEqual(error.column, "label")
        self.assertEqual(error.expected, ["numeric"])
        self.assertEqual(error.found, str(frame["label"].dtype))

    def test_log_transform_non_positive_values_use_transformation_error(self):
        frame = self.df.copy()
        frame["A"] = [1.0, 0.0, -1.0]

        with self.assertRaises(DataTransformationError) as context:
            log_transform(frame, ["A"])

        error = context.exception
        self.assertEqual(error.step, "log_transform")
        self.assertIn("strictly positive", error.details or "")


if __name__ == "__main__":
    unittest.main()
