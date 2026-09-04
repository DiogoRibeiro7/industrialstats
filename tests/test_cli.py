"""Comprehensive tests for the command line interface.

These tests exercise the ``industrialstats`` CLI across its subcommands,
covering parameter combinations, error handling, help text, and basic
integration workflows.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pytest
from dataexcept import DataLoadingError

from industrialstats.cli import main


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Top-level help text should be displayed."""
    with pytest.raises(SystemExit):
        main(["--help"])
    captured = capsys.readouterr()
    assert "industrialstats command line interface" in captured.out


def test_cli_factorial(tmp_path: Path) -> None:
    """Generate a factorial design with replicates and center points."""
    output = tmp_path / "design.csv"
    args = [
        "factorial",
        "-f",
        "A=0,1",
        "-f",
        "B=0,1",
        "-r",
        "2",
        "-c",
        "1",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert len(df) == 9  # 2 factors -> 4 runs * 2 replicates + 1 center point
    assert set(df.columns).issuperset({"A", "B"})


def test_cli_rcbd_deterministic(tmp_path: Path) -> None:
    """RCBD shuffling should be reproducible with a seed and custom factor name."""
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
        "--blocking-factor",
        "Group",
        "--seed",
        "1",
    ]
    out1 = tmp_path / "rcbd1.csv"
    out2 = tmp_path / "rcbd2.csv"
    main([*args, "-o", str(out1)])
    main([*args, "-o", str(out2)])
    df1 = pd.read_csv(out1)
    df2 = pd.read_csv(out2)
    pd.testing.assert_frame_equal(df1, df2)
    assert set(df1["Group"]) == {"B1", "B2"}


def test_cli_fractional(tmp_path: Path) -> None:
    """Fractional factorial design generation with replicates."""
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
        "-r",
        "2",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert len(df) == 8
    assert set(df.columns).issuperset({"A", "B", "C"})


def test_cli_crd(tmp_path: Path) -> None:
    """CRD generation with replicates and seeded randomization."""
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


def test_cli_screening_pb(tmp_path: Path) -> None:
    """Plackett–Burman screening design generation."""
    output = tmp_path / "screen_pb.csv"
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


def test_cli_screening_dsd(tmp_path: Path) -> None:
    """Definitive screening design generation."""
    output = tmp_path / "screen_dsd.csv"
    args = [
        "screening",
        "-f",
        "A=-1,0,1",
        "-f",
        "B=-1,0,1",
        "--design",
        "dsd",
        "--seed",
        "2",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert set(df.columns).issuperset({"A", "B"})


def test_cli_anova(tmp_path: Path) -> None:
    """ANOVA analysis on CSV input with explicit type selection."""
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
        "--typ",
        "3",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "sum_sq" in df.columns


def test_cli_anova_missing_file(tmp_path: Path) -> None:
    """ANOVA should expose missing input files through DataExcept."""
    with pytest.raises(DataLoadingError) as exc_info:
        main(
            [
                "anova",
                "--data",
                str(tmp_path / "missing.csv"),
                "--response",
                "y",
                "--formula",
                "y ~ 1",
            ]
        )

    assert isinstance(exc_info.value.original, FileNotFoundError)
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


def test_cli_power_ttest(tmp_path: Path) -> None:
    """Power analysis for a t-test."""
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


def test_cli_power_anova(tmp_path: Path) -> None:
    """Power analysis for ANOVA."""
    output = tmp_path / "power_anova.csv"
    args = [
        "power",
        "--analysis",
        "anova",
        "--effect-size",
        "0.3",
        "--power",
        "0.8",
        "--n-groups",
        "4",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "sample_size" in df.columns


def test_cli_model(tmp_path: Path) -> None:
    """Stepwise model fitting with custom thresholds."""
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
        "--entry-threshold",
        "0.01",
        "--removal-threshold",
        "0.2",
        "-o",
        str(output),
    ]
    main(args)
    df = pd.read_csv(output)
    assert "selected_terms" in df.columns


def test_cli_invalid_factor_spec() -> None:
    """Invalid factor strings should raise an ``ArgumentTypeError``."""
    with pytest.raises(argparse.ArgumentTypeError):
        main(["factorial", "-f", "A0,1"])


def test_cli_power_invalid_analysis() -> None:
    """Invalid power analysis type should raise ``SystemExit``."""
    with pytest.raises(SystemExit):
        main(["power", "--analysis", "unknown"])


def test_cli_subcommand_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Subcommand help should be displayed."""
    with pytest.raises(SystemExit):
        main(["factorial", "--help"])
    captured = capsys.readouterr()
    assert "usage: industrialstats factorial" in captured.out


def test_cli_workflow_factorial_anova(tmp_path: Path) -> None:
    """Integration test: generate design then run ANOVA on the data."""
    design_file = tmp_path / "design.csv"
    main(
        [
            "factorial",
            "-f",
            "A=0,1",
            "-f",
            "B=0,1",
            "-o",
            str(design_file),
        ]
    )
    design_df = pd.read_csv(design_file)
    design_df["y"] = [1, 2, 3, 4]
    data_file = tmp_path / "data.csv"
    design_df.to_csv(data_file, index=False)
    output = tmp_path / "anova.csv"
    main(
        [
            "anova",
            "--data",
            str(data_file),
            "--response",
            "y",
            "--formula",
            "y ~ A + B",
            "-o",
            str(output),
        ]
    )
    df = pd.read_csv(output)
    assert "sum_sq" in df.columns
