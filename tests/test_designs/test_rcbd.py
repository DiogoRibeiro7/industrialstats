import unittest

import pandas as pd

from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign


class TestRCBD(unittest.TestCase):
    def setUp(self):
        self.treatments = ["T1", "T2", "T3"]
        self.blocks = ["B1", "B2"]
        self.design = RandomizedCompleteBlockDesign(self.treatments, self.blocks)

    def test_generate_design(self):
        dm = self.design.generate_design()
        self.assertEqual(len(dm), 6)
        # each block contains all treatments
        for block in self.blocks:
            subset = dm[dm["Block"] == block]
            self.assertEqual(set(subset["Treatment"]), set(self.treatments))

    def test_efficiency_vs_crd(self):
        eff = self.design.efficiency_vs_crd(block_variance=2.0, error_variance=1.0)
        self.assertLess(eff, 1.0)

    def test_missing_plot_analysis(self):
        self.design.generate_design()
        result = self.design.missing_plot_analysis([("B1", "T1")])
        self.assertEqual(result["missing_count"], 1)
        self.assertEqual(result["remaining_runs"], 5)

    def test_latin_square_option(self):
        design2 = RandomizedCompleteBlockDesign(["A", "B", "C"], ["R1", "R2", "R3"])
        latin = design2.latin_square_option()
        self.assertIsNotNone(latin)
        self.assertEqual(len(latin), 9)

    def test_seed_reproducibility(self):
        design1 = RandomizedCompleteBlockDesign(self.treatments, self.blocks)
        dm1 = design1.generate_design(seed=123)

        design2 = RandomizedCompleteBlockDesign(self.treatments, self.blocks)
        dm2 = design2.generate_design(seed=123)

        pd.testing.assert_frame_equal(dm1, dm2)


if __name__ == "__main__":
    unittest.main()
