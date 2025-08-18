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
