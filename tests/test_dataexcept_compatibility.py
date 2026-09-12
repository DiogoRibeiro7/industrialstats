from pathlib import Path

import pandas as pd
import pytest
from dataexcept import DataLoadingError, FileWriteError

import industrialstats
from industrialstats.utils.export import export_to_csv
from industrialstats.utils.io import load_csv


def test_dataexcept_runtime_compatibility_contract(tmp_path: Path) -> None:
    """Exercise the DataExcept surface required by industrialstats."""
    assert industrialstats.__version__

    missing = tmp_path / "missing.csv"
    with pytest.raises(DataLoadingError) as load_exc:
        load_csv(missing)

    load_error = load_exc.value
    assert load_error.source == str(missing)
    assert isinstance(load_error.original, FileNotFoundError)
    assert load_error.__cause__ is load_error.original

    target = tmp_path / "missing-parent" / "design.csv"
    frame = pd.DataFrame({"x": [1.0]})
    with pytest.raises(FileWriteError) as write_exc:
        export_to_csv(frame, target)

    write_error = write_exc.value
    assert write_error.path == str(target)
    assert isinstance(write_error.original, OSError)
    assert write_error.__cause__ is write_error.original
