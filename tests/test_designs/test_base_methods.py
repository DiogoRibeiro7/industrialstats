import json
import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


class TestBaseMethods(unittest.TestCase):
    def setUp(self):
        self.factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        self.design = FactorialDesign(self.factors, replicates=1, randomize=False)
        self.design.generate_design()

    def test_clone_creates_independent_copy(self):
        clone = self.design.clone()
        self.assertEqual(len(clone.design_matrix), len(self.design.design_matrix))
        clone.design_matrix.loc[0, "A"] = 99
        self.assertNotEqual(
            clone.design_matrix.iloc[0]["A"], self.design.design_matrix.iloc[0]["A"]
        )

    def test_merge_with_appends_and_aligns_columns(self):
        extended_factor = Factor("C", [0, 1])
        other_design = FactorialDesign(
            [self.factors[0], extended_factor], randomize=False
        )
        other_design.generate_design()

        merged = self.design.merge_with(other_design)
        self.assertEqual(
            merged.run_count,
            self.design.run_count + other_design.run_count,
        )
        self.assertIn("C", merged.design_matrix.columns)
        self.assertTrue(
            merged.design_matrix["C"].isna().head(self.design.run_count).all()
        )

    def test_merge_with_incompatible_factors_raises(self):
        other = self.design.clone()
        other.factors[0] = Factor("A", [0.0, 1.0], factor_type="continuous")
        with self.assertRaises(ValueError):
            self.design.merge_with(other)

    def test_to_excel_creates_summary_sheet(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.xlsx"
            self.design.to_excel(str(path))
            self.assertTrue(path.exists())
            with pd.ExcelFile(path) as xl:
                sheets = xl.sheet_names
                self.assertIn("Summary", sheets)
                summary_df = xl.parse("Summary", index_col=0)
                self.assertIn("Run Count", summary_df.index)
                self.assertIn("Balanced", summary_df.index)

    def test_to_excel_requires_valid_extension(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.csv"
            with self.assertRaises(ValueError):
                self.design.to_excel(path)

    def test_to_json_contains_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.json"
            self.design.to_json(path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], self.design.name)
            self.assertIn("design_efficiency", payload["metadata"])
            self.assertIn("design_matrix", payload)

    def test_to_json_extension_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "design.txt"
            with self.assertRaises(ValueError):
                self.design.to_json(path)

    def test_is_balanced_and_design_efficiency_metrics(self):
        self.assertTrue(self.design.is_balanced)
        efficiency = self.design.design_efficiency
        self.assertAlmostEqual(efficiency["run_fraction"], 1.0)
        self.assertAlmostEqual(efficiency["missing_rate"], 0.0)
        self.assertAlmostEqual(efficiency["balance_index"], 1.0)
        self.assertAlmostEqual(efficiency["replication_factor"], 1.0)

    def test_is_balanced_detects_missing_data(self):
        self.design.design_matrix.loc[0, "A"] = math.nan
        self.assertFalse(self.design.is_balanced)

    def test_is_balanced_missing_column_raises(self):
        matrix = self.design.design_matrix.drop(columns=["A"])
        self.design.design_matrix = matrix
        with self.assertRaises(ValueError):
            _ = self.design.is_balanced

    def test_design_efficiency_handles_missing_values(self):
        self.design.design_matrix.loc[0, "A"] = math.nan
        metrics = self.design.design_efficiency
        self.assertGreater(metrics["missing_rate"], 0)
        self.assertTrue(math.isnan(metrics["balance_index"]))

    def test_compare_to(self):
        other = FactorialDesign(self.factors, replicates=2, randomize=False)
        other.generate_design()
        comparison = self.design.compare_to(other)
        self.assertEqual(
            comparison["run_diff"], other.run_count - self.design.run_count
        )
        self.assertEqual(comparison["factor_diff"], [])

    def test_randomize_reproducible(self):
        design1 = FactorialDesign(self.factors, replicates=1, randomize=False)
        design1.generate_design()
        design1.randomize(seed=42)

        design2 = FactorialDesign(self.factors, replicates=1, randomize=False)
        design2.generate_design()
        design2.randomize(seed=42)

        pd.testing.assert_frame_equal(design1.design_matrix, design2.design_matrix)


if __name__ == "__main__":
    unittest.main()
