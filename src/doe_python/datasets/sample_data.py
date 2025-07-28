"""Small example datasets shipped with DOE Python."""

from __future__ import annotations

from io import StringIO

import pandas as pd

_MANUFACTURING_CSV = """Temperature,Pressure,Strength
150,200,55
160,210,57
170,220,63
180,230,65
"""


def load_manufacturing() -> pd.DataFrame:
    """Load a toy manufacturing dataset.

    Returns:
        DataFrame with process conditions and response.
    """
    return pd.read_csv(StringIO(_MANUFACTURING_CSV))
