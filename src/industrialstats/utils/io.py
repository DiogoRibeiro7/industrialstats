"""Structured data-loading helpers for external tabular inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from dataexcept import DataLoadingError


def load_csv(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Load a CSV file and expose operational failures through DataExcept.

    Parameters
    ----------
    path : str or pathlib.Path
        CSV source path.
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
    """
    try:
        return pd.read_csv(path, **kwargs)
    except (OSError, ValueError, UnicodeError) as exc:
        raise DataLoadingError(str(path), exc) from exc
