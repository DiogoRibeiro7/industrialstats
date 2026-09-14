"""Structured data-boundary tests for split-plot analysis."""

import numpy as np
import pandas as pd
import pytest
from dataexcept import MissingColumnError, MissingDataError

from industrialstats.analysis.split_plot import SplitPlotAnalysis


def _valid_split_plot_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "WholePlot": [1, 1, 2, 2],
            "Replicate": [1, 1, 1, 1],
            "A": [-1, -1, 1, 1],
            "B": [-1, 1, -1, 1],
            "y": [1.0, 2.0, 3.0, 4.0],
        }
    )


def test_split_plot_missing_required_column_uses_dataexcept() -> None:
    data = _valid_split_plot_frame().drop(columns=["B"])

    with pytest.raises(MissingColumnError) as exc_info:
        SplitPlotAnalysis(data, "y", ["A"], ["B"])

    assert exc_info.value.column == "B"
    assert exc_info.value.dataframe == "split_plot_input"


def test_split_plot_all_missing_responses_use_dataexcept() -> None:
    data = _valid_split_plot_frame()
    data["y"] = np.nan

    with pytest.raises(MissingDataError) as exc_info:
        SplitPlotAnalysis(data, "y", ["A"], ["B"])

    assert exc_info.value.feature == "y"
    assert "No valid data rows" in str(exc_info.value)
