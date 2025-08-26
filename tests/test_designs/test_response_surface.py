import unittest

import numpy as np

from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign


class TestResponseSurfaceDesign(unittest.TestCase):
    def setUp(self):
        self.factors = [
            Factor("A", [0, 1], factor_type="continuous"),
            Factor("B", [0, 1], factor_type="continuous"),
            Factor("C", [0, 1], factor_type="continuous"),
        ]

    def test_bbd_requires_three_factors(self):
        with self.assertRaises(ValueError):
            design = ResponseSurfaceDesign(self.factors[:2], design_type="BBD")
            design.generate_design()

    def test_bbd_run_count_and_orthogonality(self):
        design = ResponseSurfaceDesign(self.factors, design_type="BBD", center_points=1)
        matrix = design.generate_design()
        self.assertEqual(len(matrix), 13)

        coded = design._get_design_matrix_coded()
        xtx = coded.T @ coded
        off_diag = xtx - np.diag(np.diag(xtx))
        self.assertTrue(np.allclose(off_diag, 0))

    def test_ccd_design_properties(self):
        factors = self.factors[:2]
        design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=2)
        matrix = design.generate_design()
        props = design.design_properties()

        self.assertEqual(props["n_factors"], 2)
        self.assertEqual(props["n_runs"], len(matrix))
        self.assertTrue(props["rotatable"])
        self.assertAlmostEqual(props["alpha"], np.sqrt(2), places=3)
        self.assertAlmostEqual(props["factorial_fraction"], 4 / len(matrix), places=5)
        self.assertAlmostEqual(props["axial_fraction"], 4 / len(matrix), places=5)
        self.assertAlmostEqual(props["center_fraction"], 2 / len(matrix), places=5)

    def test_bbd_design_properties(self):
        design = ResponseSurfaceDesign(self.factors, design_type="BBD", center_points=1)
        design.generate_design()
        props = design.design_properties()

        self.assertEqual(props["n_factors"], 3)
        self.assertEqual(props["n_runs"], 13)
        self.assertFalse(props["rotatable"])
        self.assertTrue(props["orthogonal"])


if __name__ == "__main__":
    unittest.main()
