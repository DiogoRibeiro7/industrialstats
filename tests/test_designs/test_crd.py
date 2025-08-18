import pandas as pd

from doe_python.designs.crd import CompletelyRandomizedDesign


def test_crd_seed_reproducibility():
    design1 = CompletelyRandomizedDesign(["A", "B"], replicates=2, seed=1)
    dm1 = design1.generate_design()
    design2 = CompletelyRandomizedDesign(["A", "B"], replicates=2, seed=1)
    dm2 = design2.generate_design()
    pd.testing.assert_frame_equal(dm1, dm2)


def test_crd_degrees_of_freedom():
    design = CompletelyRandomizedDesign(["A", "B", "C"], replicates=3, seed=0)
    _ = design.generate_design()
    dfs = design.degrees_of_freedom()
    assert dfs["Total"] == design.n_runs() - 1


def test_crd_multi_response_summary():
    design = CompletelyRandomizedDesign(
        ["A", "B"], replicates=2, seed=0, response_variables=["y1", "y2"]
    )
    dm = design.generate_design()
    data = dm.copy()
    data["y1"] = [1.0, 2.0, 3.0, 4.0]
    data["y2"] = [2.0, 3.0, 4.0, 5.0]
    stats = design.summary_statistics(data, ["y1", "y2"])
    assert set(stats.keys()) == {"y1", "y2"}
    assert "mean" in stats["y1"].columns
