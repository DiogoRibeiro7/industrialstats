import unittest

import numpy as np
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
    @staticmethod
    def _factors(count: int) -> list[Factor]:
        return [Factor(f"X{index}", [-1, 0, 1]) for index in range(1, count + 1)]

    def test_two_factor_design_preserves_five_run_base_case(self):
        design = DefinitiveScreeningDesign(self._factors(2), randomize=False)
        dm = design.generate_design()

        self.assertEqual(dm.shape, (5, 3))
        self.assertTrue(design.validate_design())

    def test_four_factor_design_has_minimal_nine_runs(self):
        design = DefinitiveScreeningDesign(self._factors(4), randomize=False)
        dm = design.generate_design()

        self.assertEqual(dm.shape, (9, 5))
        self.assertEqual(set(dm.columns), {"RunOrder", "X1", "X2", "X3", "X4"})
        self.assertTrue(design.validate_design())

    def test_nonminimal_factor_count_uses_next_conference_order(self):
        design = DefinitiveScreeningDesign(self._factors(5), randomize=False)
        dm = design.generate_design()

        # q = 5 is the smallest odd prime with q + 1 >= 5, hence 13 runs.
        self.assertEqual(dm.shape, (13, 6))

    def test_main_effects_are_mutually_orthogonal(self):
        design = DefinitiveScreeningDesign(self._factors(6), randomize=False)
        dm = design.generate_design()
        x = dm[[f"X{i}" for i in range(1, 7)]].to_numpy(dtype=float)

        cross_product = x.T @ x
        off_diagonal = cross_product - np.diag(np.diag(cross_product))
        np.testing.assert_allclose(off_diagonal, 0.0)

    def test_main_effects_are_orthogonal_to_quadratics_and_two_factor_interactions(
        self,
    ):
        design = DefinitiveScreeningDesign(self._factors(6), randomize=False)
        dm = design.generate_design()
        x = dm[[f"X{i}" for i in range(1, 7)]].to_numpy(dtype=float)

        np.testing.assert_allclose(x.T @ (x**2), 0.0)

        interactions = np.column_stack(
            [
                x[:, left] * x[:, right]
                for left in range(x.shape[1])
                for right in range(left + 1, x.shape[1])
            ]
        )
        np.testing.assert_allclose(x.T @ interactions, 0.0)

    def test_intercept_linear_and_pure_quadratic_terms_are_estimable(self):
        design = DefinitiveScreeningDesign(self._factors(6), randomize=False)
        dm = design.generate_design()
        x = dm[[f"X{i}" for i in range(1, 7)]].to_numpy(dtype=float)

        model_matrix = np.column_stack((np.ones(len(x)), x, x**2))
        self.assertEqual(np.linalg.matrix_rank(model_matrix), 13)

    def test_design_is_foldover_symmetric_with_single_center(self):
        design = DefinitiveScreeningDesign(self._factors(4), randomize=False)
        dm = design.generate_design()
        x = dm[["X1", "X2", "X3", "X4"]].to_numpy(dtype=int)

        noncenter = x[:-1]
        half = len(noncenter) // 2
        np.testing.assert_array_equal(noncenter[half:], -noncenter[:half])
        np.testing.assert_array_equal(x[-1], np.zeros(4, dtype=int))

    def test_seed_reproducibility(self):
        factors = self._factors(4)
        first = DefinitiveScreeningDesign(factors, seed=17)
        second = DefinitiveScreeningDesign(factors, seed=17)

        pd.testing.assert_frame_equal(first.generate_design(), second.generate_design())


if __name__ == "__main__":
    unittest.main()
