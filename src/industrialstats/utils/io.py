"""Structured data-loading helpers for external tabular inputs."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd
from dataexcept import DataLoadingError, MissingColumnError


def load_csv(
    path: str | Path,
    *,
    required_columns: Sequence[str] | None = None,
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
        If a required column is absent from the loaded table.
    TypeError
        If ``required_columns`` is not a sequence of strings.
    """
    if required_columns is not None:
        if isinstance(required_columns, str) or not isinstance(
            required_columns, Sequence
        ):
            raise TypeError("required_columns must be a sequence of strings or None")
        if not all(isinstance(column, str) for column in required_columns):
            raise TypeError("required_columns must contain only strings")

    try:
        frame = pd.read_csv(path, **kwargs)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DataLoadingError(str(path), exc) from exc

    if required_columns is not None:
        for column in required_columns:
            if column not in frame.columns:
                raise MissingColumnError(column, dataframe=str(path))

    return frame
