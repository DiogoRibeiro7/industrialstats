"""Data export utilities for DOE Python."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def export_to_csv(df: pd.DataFrame, path: str | Path, **kwargs: Any) -> None:
    """Save a DataFrame to CSV.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to export.
    path : str or Path
        Destination file path.
    **kwargs
        Additional arguments passed to :func:`pandas.DataFrame.to_csv`.
    """
    df.to_csv(path, index=False, **kwargs)


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
    """
    df.to_excel(path, index=include_index, **kwargs)


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
    """
    data = {
        "data": df.to_dict(orient="records"),
        "columns": list(df.columns),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, **kwargs)
