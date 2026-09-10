import pandas as pd
import pytest

from industrialstats.designs.advanced import SplitPlotDesign
from industrialstats.designs.base import Factor


def test_split_plot_run_count_and_structure():
    wp = [Factor("Batch", [1, 2])]
    sp = [Factor("Temp", [100, 200])]
    design = SplitPlotDesign(wp, sp, randomize=False)
    df = design.generate_design()

    assert len(df) == 4
    assert design.n_whole_plots() == 2
    assert design.n_runs() == 4
    assert set(df.columns) == {
        "StdOrder",
        "Replicate",
        "WholePlot",
        "SubPlot",
        "Batch",
        "Temp",
    }
    for _, group in df.groupby("WholePlot"):
        assert len(group) == 2
        assert group["SubPlot"].tolist() == [1, 2]
        positions = group.index.to_list()
        assert positions == list(range(min(positions), max(positions) + 1))


def test_replicates_create_distinct_whole_plot_experimental_units():
    wp = [Factor("Batch", [1, 2])]
    sp = [Factor("Temp", [100, 200, 300])]
    design = SplitPlotDesign(wp, sp, replicates=2, randomize=False)
    df = design.generate_design()

    assert design.n_whole_plots() == 4
    assert design.n_runs() == 12
    assert df["WholePlot"].nunique() == 4
    assert df.groupby("WholePlot").size().to_dict() == {1: 3, 2: 3, 3: 3, 4: 3}

    whole_plot_units = df.groupby("WholePlot").agg(
        Replicate=("Replicate", "first"),
        Batch=("Batch", "first"),
        replicate_count=("Replicate", "nunique"),
        batch_count=("Batch", "nunique"),
    )
    assert whole_plot_units["replicate_count"].eq(1).all()
    assert whole_plot_units["batch_count"].eq(1).all()
    assert set(map(tuple, whole_plot_units[["Replicate", "Batch"]].to_numpy())) == {
        (1, 1),
        (1, 2),
        (2, 1),
        (2, 2),
    }


def test_multiple_whole_plot_factors_have_one_unit_per_replicate_and_combination():
    wp = [
        Factor("Batch", [1, 2]),
        Factor("Pressure", [10, 20, 30]),
    ]
    sp = [Factor("Temp", [100, 200])]
    design = SplitPlotDesign(wp, sp, replicates=2, randomize=False)
    df = design.generate_design()

    assert design.n_whole_plots() == 2 * 2 * 3
    assert design.n_runs() == 2 * 2 * 3 * 2
    assert df["WholePlot"].nunique() == 12
    assert (df.groupby("WholePlot").size() == 2).all()

    units = df.drop_duplicates("WholePlot")
    assert len(units) == 12
    assert len(units[["Replicate", "Batch", "Pressure"]].drop_duplicates()) == 12


def test_split_plot_randomization_seed_and_restriction():
    wp = [Factor("A", [0, 1])]
    sp = [Factor("B", [-1, 1]), Factor("C", [10, 20])]
    design1 = SplitPlotDesign(wp, sp, replicates=2, seed=5)
    df1 = design1.generate_design()
    design2 = SplitPlotDesign(wp, sp, replicates=2, seed=5)
    df2 = design2.generate_design()

    pd.testing.assert_frame_equal(df1, df2)
    assert df1["RunOrder"].tolist() == list(range(1, len(df1) + 1))

    for _, group in df1.groupby("WholePlot"):
        positions = group.index.to_list()
        assert positions == list(range(min(positions), max(positions) + 1))
        assert group["A"].nunique() == 1
        assert group["Replicate"].nunique() == 1
        assert len(group[["B", "C"]].drop_duplicates()) == 4
        assert sorted(group["SubPlot"].tolist()) == [1, 2, 3, 4]


def test_split_plot_three_level_factor():
    wp = [Factor("W", [1, 2])]
    sp = [Factor("C", [0, 1, 2])]
    design = SplitPlotDesign(wp, sp, randomize=False)
    df = design.generate_design()

    assert len(df) == 2 * 3
    assert sorted(df["C"].unique()) == [0, 1, 2]


@pytest.mark.parametrize("replicates", [0, -1, True, 1.5])
def test_invalid_replicate_count_is_rejected(replicates):
    wp = [Factor("A", [0, 1])]
    sp = [Factor("B", [-1, 1])]

    with pytest.raises(ValueError, match="replicates"):
        SplitPlotDesign(wp, sp, replicates=replicates)


def test_empty_factor_levels_make_mutated_design_invalid():
    wp = [Factor("A", [0, 1])]
    sp = [Factor("B", [-1, 1])]
    design = SplitPlotDesign(wp, sp, randomize=False)
    design.sub_plot_factors[0].levels = []

    assert design.validate_design() is False
    with pytest.raises(ValueError, match="Invalid design configuration"):
        design.generate_design()
