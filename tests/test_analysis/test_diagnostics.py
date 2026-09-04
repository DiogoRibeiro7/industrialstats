import math

import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm
from matplotlib.figure import Figure

from industrialstats.analysis.diagnostics import ModelDiagnostics


def _build_model(normal: bool = True):
    rng = np.random.default_rng(123 if normal else 321)
    n = 120
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    if normal:
        noise = rng.normal(scale=0.5, size=n)
    else:
        noise = rng.standard_t(df=2, size=n) * (1 + x1)
        for i in range(1, n):
            noise[i] += 0.6 * noise[i - 1]
    y = 2.5 + 1.8 * x1 - 1.2 * x2 + noise
    data = pd.DataFrame({"y": y, "x1": x1, "x2": x2})
    model = sm.OLS(data["y"], sm.add_constant(data[["x1", "x2"]])).fit()
    model_result = {
        "model_object": model,
        "residuals": model.resid,
        "fitted_values": model.fittedvalues,
        "model_metrics": {
            "R2": model.rsquared,
            "RMSE": math.sqrt(model.mse_resid),
        },
    }
    return data, model_result


def test_assumption_tests_flag_violations():
    data, model_result = _build_model(normal=False)
    diagnostics = ModelDiagnostics(model_result, data)
    results = diagnostics.assumption_tests()
    assert not results["normality"]["passes"]
    assert not results["homoscedasticity"]["passes"]
    assert not results["independence"]["passes"]


def test_influence_and_outlier_detection_identifies_points():
    data, model_result = _build_model(normal=True)
    data = data.copy()
    data.loc[5, "y"] += 10
    model = sm.OLS(data["y"], sm.add_constant(data[["x1", "x2"]])).fit()
    model_result["model_object"] = model
    model_result["residuals"] = model.resid
    model_result["fitted_values"] = model.fittedvalues

    diagnostics = ModelDiagnostics(model_result, data)
    influence = diagnostics.influence_analysis()
    assert influence["studentized_residuals"].shape[0] == data.shape[0]
    outliers = diagnostics.outlier_detection()
    assert 5 in outliers["studentized_residuals"] or 5 in outliers["cooks_distance"]


def test_model_adequacy_reports_summary_and_plots():
    data, model_result = _build_model(normal=True)
    diagnostics = ModelDiagnostics(model_result, data)
    summary = diagnostics.model_adequacy()
    assert set(summary.keys()) == {
        "assumptions",
        "outliers",
        "influence",
        "model_metrics",
        "overall_pass",
        "plots",
    }
    assert all(isinstance(fig, Figure) for fig in summary["plots"].values())


def test_recommendation_system_returns_guidance():
    data, model_result = _build_model(normal=False)
    diagnostics = ModelDiagnostics(model_result, data)
    recs = diagnostics.recommendation_system()
    assert any("transformation" in rec.lower() for rec in recs)
    assert len(recs) >= 2


def test_invalid_model_result_raises():
    data, model_result = _build_model()
    with pytest.raises(KeyError):
        ModelDiagnostics({"residuals": model_result["residuals"]}, data)
    with pytest.raises(ValueError):
        ModelDiagnostics(
            {
                "model_object": model_result["model_object"],
                "residuals": model_result["residuals"],
                "fitted_values": model_result["fitted_values"][1:],
            },
            data.iloc[:-1],
        )
