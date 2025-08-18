"""Data transformation helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def center(df: pd.DataFrame) -> pd.DataFrame:
    """Center numeric columns around zero.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    Returns
    -------
    pandas.DataFrame
        Centered DataFrame.
    """
    centered = df.copy()
    for col in centered.select_dtypes(include=[np.number]).columns:
        centered[col] = centered[col] - centered[col].mean()
    return centered


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize numeric columns to unit variance.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.

    Returns
    -------
    pandas.DataFrame
        Standardized DataFrame.
    """
    standardized = df.copy()
    for col in standardized.select_dtypes(include=[np.number]).columns:
        std = standardized[col].std(ddof=0)
        if std != 0:
            standardized[col] = (standardized[col] - standardized[col].mean()) / std
    return standardized


def log_transform(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply natural logarithm to specified columns.

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.
    columns : list[str]
        Columns to transform.

    Returns
    -------
    pandas.DataFrame
        DataFrame with transformed columns.
    """
    transformed = df.copy()
    for col in columns:
        transformed[col] = np.log(transformed[col])
    return transformed
