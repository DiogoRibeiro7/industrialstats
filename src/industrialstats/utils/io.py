"""Structured data-loading helpers for external tabular inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from dataexcept import DataLoadingError, DtypeMismatchError, MissingColumnError


def load_csv(
    path: str | Path,
    *,
    required_columns: Sequence[str] | None = None,
    expected_dtypes: Mapping[str, Sequence[str]] | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Load a CSV file and expose operational failures through DataExcept.

    Parameters
    ----------
    path : str or pathlib.Path
        CSV source path.
    required_columns : sequence of str, optional
        Columns that must be present in the loaded table. Missing columns raise
        :class:`dataexcept.MissingColumnError` with the CSV source as context.
    expected_dtypes : mapping of str to sequence of str, optional
        Allowed pandas dtype names for selected columns. Missing columns raise
        :class:`dataexcept.MissingColumnError`; mismatches raise
        :class:`dataexcept.DtypeMismatchError`.
    **kwargs
        Additional arguments passed to :func:`pandas.read_csv`.

    Returns
    -------
    pandas.DataFrame
        Loaded tabular data.

    Raises
    ------
    DataLoadingError
        If pandas or the filesystem cannot load the CSV source.
    MissingColumnError
        If a required or dtype-constrained column is absent from the loaded table.
    DtypeMismatchError
        If a dtype-constrained column does not have an allowed dtype.
    TypeError
        If ``required_columns`` or ``expected_dtypes`` violates its API contract.
    """
    if required_columns is not None:
        if isinstance(required_columns, str) or not isinstance(
            required_columns, Sequence
        ):
            raise TypeError("required_columns must be a sequence of strings or None")
        if not all(isinstance(column, str) for column in required_columns):
            raise TypeError("required_columns must contain only strings")

    if expected_dtypes is not None:
        if not isinstance(expected_dtypes, Mapping):
            raise TypeError("expected_dtypes must be a mapping or None")
        for column, allowed in expected_dtypes.items():
            if not isinstance(column, str):
                raise TypeError("expected_dtypes keys must be strings")
            if isinstance(allowed, str) or not isinstance(allowed, Sequence):
                raise TypeError("expected_dtypes values must be sequences of strings")
            if not allowed or not all(isinstance(dtype, str) for dtype in allowed):
                raise TypeError(
                    "expected_dtypes values must be non-empty sequences of strings"
                )

    try:
        frame = pd.read_csv(path, **kwargs)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DataLoadingError(str(path), exc) from exc

    if required_columns is not None:
        for column in required_columns:
            if column not in frame.columns:
                raise MissingColumnError(column, dataframe=str(path))

    if expected_dtypes is not None:
        for column, allowed in expected_dtypes.items():
            if column not in frame.columns:
                raise MissingColumnError(column, dataframe=str(path))
            found = str(frame[column].dtype)
            if found not in allowed:
                raise DtypeMismatchError(column, expected=allowed, found=found)

    return frame
