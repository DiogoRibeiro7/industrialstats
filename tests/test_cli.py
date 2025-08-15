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
