import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doe_python.datasets.sample_data import load_manufacturing


class TestSampleData(unittest.TestCase):
    def test_load_manufacturing(self):
        df = load_manufacturing()
        self.assertEqual(df.shape, (4, 3))
        self.assertIn("Strength", df.columns)


if __name__ == "__main__":
    unittest.main()
