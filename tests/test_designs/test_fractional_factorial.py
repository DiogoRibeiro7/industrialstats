import unittest

from doe_python.designs.base import Factor
from doe_python.designs.fractional_factorial import FractionalFactorialDesign


class TestFractionalFactorialDesign(unittest.TestCase):
    """Tests for FractionalFactorialDesign."""

    def setUp(self):
        self.factors = [
            Factor("A", [0, 1]),
            Factor("B", [0, 1]),
            Factor("C", [0, 1]),
            Factor("D", [0, 1]),
        ]

    def test_design_generation(self):
        design = FractionalFactorialDesign(
            self.factors,
            fraction="1/2",
            generators=["ABC"],
            replicates=1,
            randomize=False,
        )
        dm = design.generate_design()
        self.assertEqual(len(dm), 8)
        self.assertListEqual(
            sorted(dm.columns.tolist()),
            sorted(["RunID", "Replicate", "A", "B", "C", "D"]),
        )

    def test_alias_and_resolution(self):
        design = FractionalFactorialDesign(
            self.factors,
            fraction="1/2",
            generators=["ABC"],
            replicates=1,
            randomize=False,
        )
        alias = design.alias_structure()
        self.assertIn("A", alias)
        self.assertIn("ABC", alias["A"][0])
        res = design.resolution_analysis()
        self.assertEqual(res["resolution"], 4)


if __name__ == "__main__":
    unittest.main()
