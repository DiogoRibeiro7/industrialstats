import logging

import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.model_fitting import ModelFitting


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


def test_regularized_fitting_agrees_with_sklearn():
    from sklearn.datasets import make_regression
    from sklearn.linear_model import ElasticNetCV, LassoCV, RidgeCV

    X, y = make_regression(
        n_samples=60, n_features=5, n_informative=3, noise=0.1, random_state=0
    )
    df = pd.DataFrame(X, columns=[f"x{i}" for i in range(5)])
    df["y"] = y
    fitter = ModelFitting(df, "y")

    # LASSO
    res_lasso = fitter.regularized_fitting(method="lasso", cv=3, random_state=0)
    sk_lasso = LassoCV(cv=3, random_state=0).fit(df.drop(columns="y"), y)
    assert res_lasso["best_alpha"] == pytest.approx(sk_lasso.alpha_)
    assert np.allclose(
        [res_lasso["coefficients"][f"x{i}"] for i in range(5)], sk_lasso.coef_
    )

    # Ridge
    ridge_alphas = np.logspace(-6, 6, 100)
    res_ridge = fitter.regularized_fitting(method="ridge", cv=3, alphas=ridge_alphas)
    sk_ridge = RidgeCV(alphas=ridge_alphas, cv=3).fit(df.drop(columns="y"), y)
    assert res_ridge["best_alpha"] == pytest.approx(sk_ridge.alpha_)
    assert np.allclose(
        [res_ridge["coefficients"][f"x{i}"] for i in range(5)], sk_ridge.coef_
    )

    # Elastic Net
    res_enet = fitter.regularized_fitting(
        method="elasticnet", cv=3, random_state=0, l1_ratio=0.5
    )
    sk_enet = ElasticNetCV(cv=3, random_state=0, l1_ratio=0.5).fit(
        df.drop(columns="y"), y
    )
    assert res_enet["best_alpha"] == pytest.approx(sk_enet.alpha_)
    assert np.allclose(
        [res_enet["coefficients"][f"x{i}"] for i in range(5)], sk_enet.coef_
    )
    selected = res_lasso["selected_features"]
    expected = [f"x{i}" for i, c in enumerate(sk_lasso.coef_) if not np.isclose(c, 0)]
    assert selected == expected
