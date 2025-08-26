import numpy as np
import pandas as pd
import pytest

from industrialstats.analysis.anova import ANOVAAnalysis
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign


def test_anova_analysis_basic():
    factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
    design = FactorialDesign(factors, replicates=2, randomize=False)
    dm = design.generate_design()
    dm["Response"] = [1, 2, 1, 2, 1, 2, 1, 2]
    analysis = ANOVAAnalysis(dm, "Response")
    model = analysis.fit_model("Response ~ A + B + A:B")
    assert model is not None
    table = analysis.anova_table_calculation()
    assert set(["sum_sq", "df"]).issubset(table.columns)
    tests = analysis.assumptions_tests()
    assert "normality" in tests


def _simulate_nested_data() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    records = []
    for subj in range(4):
        subj_eff = rng.normal(0, 1.0)
        for batch in range(2):
            batch_eff = rng.normal(0, 0.5)
            for trt in [0, 1]:
                for _ in range(2):
                    y = 2 * trt + subj_eff + batch_eff + rng.normal(0, 0.1)
                    records.append(
                        {
                            "Subject": f"S{subj}",
                            "Batch": f"S{subj}B{batch}",
                            "Treatment": trt,
                            "Response": y,
                        }
                    )
    return pd.DataFrame(records)


def test_mixed_effects_model_with_nested_random_effects():
    df = _simulate_nested_data()
    analysis = ANOVAAnalysis(df, "Response")
    res = analysis.mixed_effects_model(
        ["Treatment"], ["Subject"], nested_effects=["Batch"]
    )
    assert pytest.approx(res["random_effects_var"]["Subject"], rel=0.3) == 0.5
    assert pytest.approx(res["random_effects_var"]["Batch"], rel=0.4) == 0.3
    assert res["lrt"]["Subject"]["p_value"] < 0.05
    assert res["lrt"]["Batch"]["p_value"] < 0.05


def test_unbalanced_anova():
    factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
    design = FactorialDesign(factors, replicates=2, randomize=False)
    dm = design.generate_design().iloc[:-1]
    dm["Response"] = list(range(1, len(dm) + 1))
    analysis2 = ANOVAAnalysis(dm, "Response")
    analysis2.fit_model("Response ~ A + B")
    ua = analysis2.unbalanced_anova()
    assert "anova_table" in ua


def test_nested_and_repeated():
    df = pd.DataFrame(
        {
            "Day": ["Mon", "Mon", "Mon", "Mon", "Tue", "Tue", "Tue", "Tue"],
            "Batch": ["B1", "B1", "B2", "B2", "B1", "B1", "B2", "B2"],
            "Response": [1, 2, 1.5, 2.5, 1.2, 2.1, 1.8, 2.8],
            "Subject": [1, 2, 1, 2, 1, 2, 1, 2],
            "Time": ["Pre", "Pre", "Pre", "Pre", "Post", "Post", "Post", "Post"],
        }
    )
    analysis = ANOVAAnalysis(df, "Response")
    nested = analysis.nested_anova({"Batch": "Day"})
    assert "anova_table" in nested

    rm_df = pd.DataFrame(
        {
            "Subject": [1, 1, 2, 2],
            "Time": ["Pre", "Post", "Pre", "Post"],
            "Response": [1.0, 1.2, 1.1, 1.3],
        }
    )
    rm_analysis = ANOVAAnalysis(rm_df, "Response")
    repeated = rm_analysis.repeated_measures_anova("Subject", ["Time"])
    assert "anova_table" in repeated
