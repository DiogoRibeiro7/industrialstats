import pandas as pd

from industrialstats.designs.advanced import SplitPlotDesign
from industrialstats.designs.base import Factor


def test_split_plot_run_count_and_structure():
    wp = [Factor("Batch", [1, 2])]
    sp = [Factor("Temp", [100, 200])]
    design = SplitPlotDesign(wp, sp, randomize=False)
    df = design.generate_design()
    assert len(df) == 4
    assert set(df.columns) == {"StdOrder", "WholePlot", "Batch", "Temp"}
    # Whole plot levels appear in contiguous blocks
    for _, group in df.groupby("WholePlot"):
        positions = group.index.to_list()
        assert positions == list(range(min(positions), max(positions) + 1))


def test_split_plot_randomization_seed():
    wp = [Factor("A", [0, 1])]
    sp = [Factor("B", [-1, 1])]
    design1 = SplitPlotDesign(wp, sp, seed=5)
    df1 = design1.generate_design()
    design2 = SplitPlotDesign(wp, sp, seed=5)
    df2 = design2.generate_design()
    pd.testing.assert_frame_equal(df1, df2)
    # whole-plot groups remain contiguous
    for _, group in df1.groupby("WholePlot"):
        positions = group.index.to_list()
        assert positions == list(range(min(positions), max(positions) + 1))


def test_split_plot_three_level_factor():
    wp = [Factor("W", [1, 2])]
    sp = [Factor("C", [0, 1, 2])]
    design = SplitPlotDesign(wp, sp, randomize=False)
    df = design.generate_design()
    assert len(df) == 2 * 3
    assert sorted(df["C"].unique()) == [0, 1, 2]
