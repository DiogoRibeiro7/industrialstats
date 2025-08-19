import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm

from industrialstats.analysis.diagnostics import ModelDiagnostics


def _make_violating_model():
    n = 100
    x = np.linspace(0, 10, n)
    rng = np.random.default_rng(0)
    noise = np.zeros(n)
    for i in range(1, n):
        noise[i] = 0.8 * noise[i - 1] + rng.standard_t(df=2) * (1 + x[i])
    y = 2 * x + noise
    X = sm.add_constant(x)
    return sm.OLS(y, X).fit()


def test_assumption_tests_detects_violations():
    model = _make_violating_model()
    md = ModelDiagnostics(model)
    results = md.assumption_tests()
    assert not results.loc[results.assumption == "normality", "passed"].iloc[0]
    assert not results.loc[results.assumption == "homoscedasticity", "passed"].iloc[0]
    assert not results.loc[results.assumption == "independence", "passed"].iloc[0]


def test_detect_outliers_flags_points():
    rng = np.random.default_rng(1)
    x = np.linspace(0, 10, 50)
    y = 2 * x + rng.normal(size=50)
    y[0] += 30
    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    md = ModelDiagnostics(model)
    outliers = md.detect_outliers()
    assert outliers["is_outlier"].iloc[0]
    assert outliers["is_outlier"].sum() >= 1


def test_recommendations_and_plots(tmp_path):
    model = _make_violating_model()
    md = ModelDiagnostics(model)
    md.assumption_tests()
    md.detect_outliers()
    recs = md.recommendations()
    assert any("non-normal" in r for r in recs)
    fig = md.influence_plots()
    fig_path = tmp_path / "diag.png"
    fig.savefig(fig_path)
    assert fig_path.exists()
    plt.close(fig)
