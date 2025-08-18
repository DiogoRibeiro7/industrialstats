import unittest

from industrialstats.datasets.sample_data import load_manufacturing


class TestSampleData(unittest.TestCase):
    def test_load_manufacturing(self):
        df = load_manufacturing()
        self.assertEqual(df.shape, (4, 3))
        self.assertIn("Strength", df.columns)


if __name__ == "__main__":
    unittest.main()
