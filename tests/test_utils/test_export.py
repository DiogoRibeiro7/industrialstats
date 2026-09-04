import tempfile
import unittest
from pathlib import Path

import pandas as pd
from dataexcept import FileWriteError

from industrialstats.utils.export import export_to_csv, export_to_excel, export_to_json


class TestExportUtilities(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    def test_export_csv_excel_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)

            csv_path = tmp / "design.csv"
            export_to_csv(self.df, csv_path)
            self.assertTrue(csv_path.exists())

            excel_path = tmp / "design.xlsx"
            export_to_excel(self.df, excel_path)
            self.assertTrue(excel_path.exists())

            json_path = tmp / "design.json"
            export_to_json(self.df, json_path)
            self.assertTrue(json_path.exists())

    def test_export_to_csv_wraps_filesystem_failure(self):
        path = Path("missing-parent") / "output.csv"

        with self.assertRaises(FileWriteError) as ctx:
            export_to_csv(self.df, path)

        error = ctx.exception
        self.assertEqual(error.path, str(path))
        self.assertIsInstance(error.original, OSError)
        self.assertIs(error.__cause__, error.original)

    def test_export_to_json_wraps_serialization_failure(self):
        df = pd.DataFrame({"value": [object()]})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            with self.assertRaises(FileWriteError) as ctx:
                export_to_json(df, path)

            error = ctx.exception
            self.assertEqual(error.path, str(path))
            self.assertIsInstance(error.original, TypeError)
            self.assertIs(error.__cause__, error.original)


if __name__ == "__main__":
    unittest.main()
