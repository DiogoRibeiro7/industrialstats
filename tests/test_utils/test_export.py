import os
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
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f_csv:
            export_to_csv(self.df, f_csv.name)
            self.assertTrue(os.path.exists(f_csv.name))
            os.unlink(f_csv.name)

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f_xls:
            export_to_excel(self.df, f_xls.name)
            self.assertTrue(os.path.exists(f_xls.name))
            os.unlink(f_xls.name)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f_json:
            export_to_json(self.df, f_json.name)
            self.assertTrue(os.path.exists(f_json.name))
            os.unlink(f_json.name)

    def test_export_to_csv_wraps_filesystem_failure(self):
        path = Path("missing-parent") / "output.csv"

        with self.assertRaises(FileWriteError) as ctx:
            export_to_csv(self.df, path)

        error = ctx.exception
        self.assertEqual(error.path, str(path))
        self.assertIsInstance(error.original, OSError)
        self.assertIs(error.__cause__, error.original)

    def test_export_to_json_wraps_serialization_failure(self):
        path = Path(tempfile.gettempdir()) / "industrialstats-invalid.json"
        df = pd.DataFrame({"value": [object()]})

        with self.assertRaises(FileWriteError) as ctx:
            export_to_json(df, path)

        error = ctx.exception
        self.assertEqual(error.path, str(path))
        self.assertIsInstance(error.original, TypeError)
        self.assertIs(error.__cause__, error.original)


if __name__ == "__main__":
    unittest.main()
