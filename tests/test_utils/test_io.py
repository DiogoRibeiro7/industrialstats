from pathlib import Path

import pandas as pd
import pytest
from dataexcept import DataLoadingError

from industrialstats.utils.io import load_csv


def test_load_csv_reads_valid_file(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_csv(path, index=False)

    loaded = load_csv(path)

    pd.testing.assert_frame_equal(loaded, pd.DataFrame({"x": [1, 2], "y": [3, 4]}))


def test_load_csv_wraps_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.csv"

    with pytest.raises(DataLoadingError) as exc_info:
        load_csv(path)

    error = exc_info.value
    assert error.source == str(path)
    assert isinstance(error.original, FileNotFoundError)
    assert error.__cause__ is error.original
