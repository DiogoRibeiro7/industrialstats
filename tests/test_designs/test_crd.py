import pandas as pd
import pytest
from dataexcept import DtypeMismatchError, MissingColumnError, MissingDataError

from industrialstats.designs.crd import CompletelyRandomizedDesign


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


def test_crd_missing_response_uses_structured_schema_error():
    design = CompletelyRandomizedDesign(["A", "B"], replicates=2, seed=0)
    data = design.generate_design()

    with pytest.raises(MissingColumnError) as exc_info:
        design.summary_statistics(data, ["Response"])

    error = exc_info.value
    assert error.column == "Response"
    assert error.dataframe == "response_data"


def test_crd_non_numeric_response_uses_structured_dtype_error():
    design = CompletelyRandomizedDesign(["A", "B"], replicates=2, seed=0)
    data = design.generate_design()
    data["Response"] = ["low", "high", "low", "high"]

    with pytest.raises(DtypeMismatchError) as exc_info:
        design.summary_statistics(data, ["Response"])

    error = exc_info.value
    assert error.column == "Response"
    assert error.expected == ["numeric"]
    assert error.found == str(data["Response"].dtype)


def test_crd_missing_values_use_structured_missing_data_error():
    design = CompletelyRandomizedDesign(["A", "B"], replicates=2, seed=0)
    data = design.generate_design()
    data["Response"] = [1.0, None, 3.0, 4.0]

    with pytest.raises(MissingDataError) as exc_info:
        design.summary_statistics(data, ["Response"])

    error = exc_info.value
    assert error.feature == "Response"
    assert "Missing values detected" in str(error)
