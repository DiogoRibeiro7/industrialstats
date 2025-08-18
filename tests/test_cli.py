import pandas as pd

from doe_python.cli import main


def test_cli_factorial(tmp_path):
    output = tmp_path / "design.csv"
    args = [
        "factorial",
        "-f",
        "A=0,1",
        "-f",
        "B=0,1",
        "-r",
        "1",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert len(df) == 4
    assert set(df.columns).issuperset({"A", "B"})


def test_cli_rcbd(tmp_path):
    output = tmp_path / "rcbd.csv"
    args = [
        "rcbd",
        "-t",
        "T1",
        "-t",
        "T2",
        "-b",
        "B1",
        "-b",
        "B2",
        "--seed",
        "1",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert set(df["Block"]) == {"B1", "B2"}


def test_cli_fractional(tmp_path):
    output = tmp_path / "frac.csv"
    args = [
        "fractional",
        "-f",
        "A=0,1",
        "-f",
        "B=0,1",
        "-f",
        "C=0,1",
        "--fraction",
        "1/2",
        "-g",
        "AB",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert set(df.columns).issuperset({"A", "B", "C"})


def test_cli_crd(tmp_path):
    output = tmp_path / "crd.csv"
    args = [
        "crd",
        "-t",
        "T1",
        "-t",
        "T2",
        "-r",
        "2",
        "--seed",
        "1",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert set(df["Treatment"]) == {"T1", "T2"}


def test_cli_screening(tmp_path):
    output = tmp_path / "screen.csv"
    args = [
        "screening",
        "-f",
        "A=1,-1",
        "-f",
        "B=1,-1",
        "--seed",
        "3",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert set(df.columns).issuperset({"A", "B"})


def test_cli_anova(tmp_path):
    data = tmp_path / "data.csv"
    pd.DataFrame({"Treatment": ["T1", "T1", "T2", "T2"], "y": [1, 2, 3, 4]}).to_csv(
        data, index=False
    )
    output = tmp_path / "anova.csv"
    args = [
        "anova",
        "--data",
        str(data),
        "--response",
        "y",
        "--formula",
        "y ~ Treatment",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "sum_sq" in df.columns


def test_cli_power(tmp_path):
    output = tmp_path / "power.csv"
    args = [
        "power",
        "--analysis",
        "t-test",
        "--effect-size",
        "0.5",
        "--power",
        "0.8",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "sample_size" in df.columns


def test_cli_model(tmp_path):
    data = tmp_path / "mf.csv"
    pd.DataFrame({"y": [1, 2, 3, 4], "A": [0, 0, 1, 1], "B": [0, 1, 0, 1]}).to_csv(
        data, index=False
    )
    output = tmp_path / "model.csv"
    args = [
        "model",
        "--data",
        str(data),
        "--response",
        "y",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "selected_terms" in df.columns
