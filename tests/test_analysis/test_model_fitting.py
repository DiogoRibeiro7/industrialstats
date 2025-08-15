import logging

import pandas as pd
import pytest

from doe_python.analysis.model_fitting import ModelFitting


def test_hierarchical_fitting_logging_and_errors(caplog, capsys, monkeypatch):
    df = pd.DataFrame(
        {
            "A": [0, 1, 0, 1],
            "B": [0, 0, 1, 1],
            "Y": [1.0, 2.0, 3.0, 4.0],
        }
    )
    fitter = ModelFitting(df, "Y")

    def mock_fit_terms(self, terms):
        if "A" in terms:
            raise ValueError("bad")
        return {
            "p_values": {t: 0.01 for t in terms if t != "Intercept"},
            "coefficients": {t: 1.0 for t in terms if t != "Intercept"},
        }

    monkeypatch.setattr(ModelFitting, "_fit_terms", mock_fit_terms)

    with caplog.at_level(logging.DEBUG):
        fitter.hierarchical_fitting(max_order=1)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error fitting term" in caplog.text
