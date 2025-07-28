import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doe_python.analysis.anova import ANOVAAnalysis
from doe_python.designs.base import Factor
from doe_python.designs.factorial import FactorialDesign


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


def test_mixed_effects_and_unbalanced():
    df = pd.DataFrame(
        {
            "Subject": [1, 1, 2, 2],
            "A": [0, 1, 0, 1],
            "Response": [1.0, 2.0, 1.1, 2.1],
        }
    )
    analysis = ANOVAAnalysis(df, "Response")
    mix_res = analysis.mixed_effects_model(["A"], ["Subject"])
    assert "aic" in mix_res

    # Unbalanced ANOVA
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
