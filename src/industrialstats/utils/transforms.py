"""Data transformation helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataexcept import DataTransformationError, DtypeMismatchError, MissingColumnError


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
    """Apply natural logarithm to specified positive numeric columns.

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

    Raises
    ------
    MissingColumnError
        If a requested column is absent from the input DataFrame.
    DtypeMismatchError
        If a requested column is not numeric.
    DataTransformationError
        If a requested column contains zero or negative values.
    """
    transformed = df.copy()
    for col in columns:
        if col not in transformed.columns:
            raise MissingColumnError(col, dataframe="transform_input")
        if not pd.api.types.is_numeric_dtype(transformed[col]):
            raise DtypeMismatchError(
                col,
                expected=["numeric"],
                found=str(transformed[col].dtype),
            )
        if (transformed[col] <= 0).any():
            raise DataTransformationError(
                "log_transform",
                f"Column '{col}' must contain only strictly positive values",
            )
        transformed[col] = np.log(transformed[col])
    return transformed
