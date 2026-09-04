"""Data export utilities for industrialstats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from dataexcept import FileWriteError


def export_to_csv(
    df: pd.DataFrame,
    path: str | Path,
    include_index: bool = False,
    **kwargs: Any,
) -> None:
    """Save a DataFrame to CSV.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to export.
    path : str or Path
        Destination file path.
    include_index : bool, optional
        Whether to include the DataFrame index. Defaults to ``False``.
    **kwargs
        Additional arguments passed to :func:`pandas.DataFrame.to_csv`.

    Raises
    ------
    FileWriteError
        If pandas or the filesystem cannot write the destination.
    """
    try:
        df.to_csv(path, index=include_index, **kwargs)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise FileWriteError(str(path), exc) from exc


def export_to_excel(
    df: pd.DataFrame,
    path: str | Path,
    include_index: bool = False,
    **kwargs: Any,
) -> None:
    """Save a DataFrame to an Excel workbook.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to export.
    path : str or Path
        Destination file path.
    include_index : bool, optional
        Whether to include the index column. Defaults to ``False``.
    **kwargs
        Additional arguments passed to :func:`pandas.DataFrame.to_excel`.

    Raises
    ------
    FileWriteError
        If pandas or the filesystem cannot write the destination.
    """
    try:
        df.to_excel(path, index=include_index, **kwargs)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise FileWriteError(str(path), exc) from exc


def export_to_json(df: pd.DataFrame, path: str | Path, **kwargs: Any) -> None:
    """Save a DataFrame and metadata to JSON.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to export.
    path : str or Path
        Destination file path.
    **kwargs
        Additional JSON ``dump`` options.

    Raises
    ------
    FileWriteError
        If serialization or filesystem writing fails.
    """
    data = {
        "data": df.to_dict(orient="records"),
        "columns": list(df.columns),
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, **kwargs)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise FileWriteError(str(path), exc) from exc
