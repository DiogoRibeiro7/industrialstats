from pathlib import Path

import pandas as pd
import pytest
from dataexcept import (
    DataLoadingError,
    DtypeMismatchError,
    MissingColumnError,
    SchemaMismatchError,
)

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


def test_load_csv_raises_missing_column_error_for_required_schema(
    tmp_path: Path,
) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(MissingColumnError) as exc_info:
        load_csv(path, required_columns=["x", "response"])

    error = exc_info.value
    assert error.column == "response"
    assert error.dataframe == str(path)


def test_load_csv_rejects_invalid_required_columns_contract(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(TypeError, match="sequence of strings"):
        load_csv(path, required_columns="x")

    with pytest.raises(TypeError, match="contain only strings"):
        load_csv(path, required_columns=["x", 1])  # type: ignore[list-item]


def test_load_csv_accepts_exact_schema(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_csv(path, index=False)

    loaded = load_csv(path, exact_columns=["x", "y"])

    assert list(loaded.columns) == ["x", "y"]


@pytest.mark.parametrize(
    "exact_columns",
    [
        ["x"],
        ["x", "y", "z"],
        ["y", "x"],
    ],
)
def test_load_csv_raises_schema_mismatch_for_non_exact_columns(
    tmp_path: Path,
    exact_columns: list[str],
) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2], "y": [3, 4]}).to_csv(path, index=False)

    with pytest.raises(SchemaMismatchError) as exc_info:
        load_csv(path, exact_columns=exact_columns)

    error = exc_info.value
    assert error.expected == f"columns={exact_columns!r}"
    assert error.found == "columns=['x', 'y']"


def test_load_csv_rejects_invalid_exact_columns_contract(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(TypeError, match="sequence of strings"):
        load_csv(path, exact_columns="x")

    with pytest.raises(TypeError, match="contain only strings"):
        load_csv(path, exact_columns=["x", 1])  # type: ignore[list-item]

    with pytest.raises(TypeError, match="must not contain duplicates"):
        load_csv(path, exact_columns=["x", "x"])


def test_load_csv_accepts_allowed_dtype_contract(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2], "label": ["a", "b"]}).to_csv(path, index=False)

    loaded = load_csv(
        path,
        expected_dtypes={"x": ["int64"], "label": ["object", "string", "str"]},
    )

    assert str(loaded["x"].dtype) == "int64"


def test_load_csv_raises_dtype_mismatch_error(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(DtypeMismatchError) as exc_info:
        load_csv(path, expected_dtypes={"x": ["float64"]})

    error = exc_info.value
    assert error.column == "x"
    assert error.expected == ["float64"]
    assert error.found == "int64"


def test_load_csv_dtype_contract_requires_existing_column(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(MissingColumnError) as exc_info:
        load_csv(path, expected_dtypes={"response": ["float64"]})

    error = exc_info.value
    assert error.column == "response"
    assert error.dataframe == str(path)


def test_load_csv_rejects_invalid_dtype_contract(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    pd.DataFrame({"x": [1, 2]}).to_csv(path, index=False)

    with pytest.raises(TypeError, match="mapping"):
        load_csv(path, expected_dtypes=["int64"])  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="keys must be strings"):
        load_csv(path, expected_dtypes={1: ["int64"]})  # type: ignore[dict-item]

    with pytest.raises(TypeError, match="sequences of strings"):
        load_csv(path, expected_dtypes={"x": "int64"})  # type: ignore[dict-item]

    with pytest.raises(TypeError, match="non-empty sequences of strings"):
        load_csv(path, expected_dtypes={"x": []})
