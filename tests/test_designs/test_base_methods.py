import os
import sys
import tempfile
import unittest

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doe_python.designs.base import Factor
from doe_python.designs.factorial import FactorialDesign


class TestBaseMethods(unittest.TestCase):
    def setUp(self):
        self.factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        self.design = FactorialDesign(self.factors, replicates=1)
        self.design.generate_design()

    def test_clone_and_merge(self):
        clone = self.design.clone()
        self.assertEqual(len(clone.design_matrix), len(self.design.design_matrix))
        clone.design_matrix.loc[0, "A"] = 99
        self.assertNotEqual(
            clone.design_matrix.iloc[0]["A"], self.design.design_matrix.iloc[0]["A"]
        )

        merged = self.design.merge_with(clone)
        self.assertEqual(len(merged.design_matrix), 2 * len(self.design.design_matrix))

    def test_export_methods(self):
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            self.design.to_excel(f.name)
            self.assertTrue(os.path.exists(f.name))
            os.unlink(f.name)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            self.design.to_json(f.name)
            self.assertTrue(os.path.exists(f.name))
            os.unlink(f.name)

    def test_properties(self):
        self.assertTrue(self.design.is_balanced)
        eff = self.design.design_efficiency
        self.assertIn("run_fraction", eff)
        self.assertEqual(self.design.run_count, len(self.design.design_matrix))
        self.assertEqual(self.design.factor_names, ["A", "B"])

    def test_compare_to(self):
        other = FactorialDesign(self.factors, replicates=2)
        other.generate_design()
        comparison = self.design.compare_to(other)
        self.assertEqual(comparison["run_diff"], other.run_count - self.design.run_count)
        self.assertEqual(comparison["factor_diff"], [])


if __name__ == "__main__":
    unittest.main()
