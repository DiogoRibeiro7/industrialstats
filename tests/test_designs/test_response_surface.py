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


class TestResponseSurfaceOptimisation(unittest.TestCase):
    def setUp(self) -> None:
        self.factors = [
            Factor("x1", [0, 1], factor_type="continuous"),
            Factor("x2", [0, 1], factor_type="continuous"),
        ]
        self.design = ResponseSurfaceDesign(
            self.factors, design_type="CCD", center_points=3
        )
        self.design.generate_design()
        self.coded = self.design._get_design_matrix_coded()

        # Define quadratic model coefficients for reproducible case study
        self.intercept = 12.5
        self.B = np.array([[0.6, 0.2], [0.2, 0.4]])
        self.b = np.array([1.2, -0.8])
        self.y = (
            self.intercept
            + self.coded @ self.b
            + np.sum((self.coded @ self.B) * self.coded, axis=1)
        )
        self.results = self.design.response_surface_analysis(self.y.tolist())

    def test_steepest_ascent_path_follows_gradient(self):
        path = self.design.steepest_ascent(self.results, step_length=0.5, n_steps=2)
        path_df = path["path"]
        gradient = self.b
        gradient /= np.linalg.norm(gradient)
        first_step = (
            path_df.loc[1, ["coded_x1", "coded_x2"]].to_numpy()
            - path_df.loc[0, ["coded_x1", "coded_x2"]].to_numpy()
        )
        np.testing.assert_allclose(first_step, 0.5 * gradient, rtol=1e-5, atol=1e-5)

    def test_ridge_analysis_matches_radius(self):
        radii = [0.8, 1.0]
        ridge = self.design.ridge_analysis(self.results, radii)
        solutions = ridge["solutions"]
        for radius, (_, row) in zip(radii, solutions.iterrows()):
            coded_point = row[["coded_x1", "coded_x2"]].to_numpy()
            self.assertAlmostEqual(np.linalg.norm(coded_point), radius, places=3)
            gradient = self.B @ coded_point + 0.5 * self.b
            if np.linalg.norm(coded_point) > 1e-8:
                lam = -float(
                    np.dot(gradient, coded_point) / np.dot(coded_point, coded_point)
                )
                np.testing.assert_allclose(
                    self.B @ coded_point + 0.5 * self.b + lam * coded_point,
                    np.zeros_like(coded_point),
                    atol=1e-5,
                )

    def test_canonical_analysis_detects_minimum(self):
        analysis = self.design.canonical_analysis(self.results)
        expected_stationary = -0.5 * np.linalg.solve(self.B, self.b)
        np.testing.assert_allclose(
            analysis["stationary_point_coded"], expected_stationary, atol=1e-5
        )
        self.assertEqual(analysis["surface_type"], "minimum")
        self.assertTrue(
            all(np.isfinite(ax) for ax in analysis["confidence_region"]["axes"])
        )

    def test_multiple_response_optimization_returns_pareto(self):
        # Build a second response surface with different trade-offs
        intercept2 = 9.0
        B2 = np.array([[0.4, -0.1], [-0.1, 0.3]])
        b2 = np.array([-0.6, 0.9])
        y2 = (
            intercept2
            + self.coded @ b2
            + np.sum((self.coded @ B2) * self.coded, axis=1)
        )
        results2 = self.design.response_surface_analysis(y2.tolist())

        optimisation = self.design.multiple_response_optimization(
            {"yield": self.results, "purity": {**results2, "goal": "max"}},
            weights={"yield": 0.6, "purity": 0.4},
            constraint_functions=[lambda point: point[0] - 1.2],
        )

        optimum = optimisation["optimum"]
        self.assertEqual(set(optimum["responses"]), {"yield", "purity"})
        self.assertGreater(optimum["overall_desirability"], 0.0)
        pareto = optimisation["pareto_frontier"]
        self.assertTrue(pareto)
        for point in pareto:
            responses = point["responses"]
            for other in pareto:
                if other is point:
                    continue
                other_resp = other["responses"]
                if (
                    other_resp["yield"] >= responses["yield"]
                    and other_resp["purity"] >= responses["purity"]
                ):
                    self.assertFalse(
                        other_resp["yield"] > responses["yield"]
                        or other_resp["purity"] > responses["purity"]
                    )
        sensitivity = optimisation["weight_sensitivity"]
        self.assertEqual(len(sensitivity), 4)
        for entry in sensitivity:
            self.assertIn("responses", entry)


if __name__ == "__main__":
    unittest.main()
