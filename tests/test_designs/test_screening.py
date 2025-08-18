import unittest

import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.screening import (
    DefinitiveScreeningDesign,
    PlackettBurmanDesign,
)


class TestPlackettBurmanDesign(unittest.TestCase):
    def test_generate_design(self):
        factors = [Factor("A", [1, -1]), Factor("B", [1, -1]), Factor("C", [1, -1])]
        design = PlackettBurmanDesign(factors, randomize=False)
        dm = design.generate_design()
        self.assertEqual(dm.shape, (4, 4))
        self.assertTrue({"A", "B", "C"}.issubset(dm.columns))
        # Check orthogonality
        mat = dm[["A", "B", "C"]].to_numpy()
        prod = mat.T @ mat
        for i in range(prod.shape[0]):
            for j in range(prod.shape[1]):
                if i == j:
                    self.assertEqual(prod[i, j], 4)
                else:
                    self.assertEqual(prod[i, j], 0)

    def test_more_factors(self):
        factors = [Factor(name, [1, -1]) for name in ["A", "B", "C", "D", "E"]]
        design = PlackettBurmanDesign(factors, randomize=False)
        dm = design.generate_design()
        self.assertEqual(dm.shape, (8, 6))
        mat = dm[[f.name for f in factors]].to_numpy()
        prod = mat.T @ mat
        for i in range(prod.shape[0]):
            for j in range(prod.shape[1]):
                if i == j:
                    self.assertEqual(prod[i, j], 8)
                else:
                    self.assertEqual(prod[i, j], 0)

    def test_foldover(self):
        factors = [Factor("A", [1, -1]), Factor("B", [1, -1])]
        design = PlackettBurmanDesign(factors, randomize=False)
        dm = design.generate_design()
        fold = design.foldover()
        self.assertEqual(len(design.design_matrix), 2 * len(dm))
        self.assertTrue((fold["A"] == -dm["A"]).all())

    def test_seed_reproducibility(self):
        factors = [Factor("A", [1, -1]), Factor("B", [1, -1])]
        d1 = PlackettBurmanDesign(factors, seed=5)
        d2 = PlackettBurmanDesign(factors, seed=5)
        pd.testing.assert_frame_equal(d1.generate_design(), d2.generate_design())


class TestDefinitiveScreeningDesign(unittest.TestCase):
    def test_basic_design(self):
        factors = [Factor("A", [-1, 0, 1]), Factor("B", [-1, 0, 1])]
        design = DefinitiveScreeningDesign(factors, randomize=False)
        dm = design.generate_design()
        # Expect 2 * n + 1 runs
        self.assertEqual(dm.shape[0], 2 * len(factors) + 1)
        self.assertTrue({"A", "B"}.issubset(dm.columns))


if __name__ == "__main__":
    unittest.main()
