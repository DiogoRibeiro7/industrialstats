from pathlib import Path

import pytest

import industrialstats.cli as cli


def test_console_cli_renders_dataexcept_as_argument_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing = tmp_path / "missing.csv"
    monkeypatch.setattr(
        "sys.argv",
        [
            "industrialstats",
            "anova",
            "--data",
            str(missing),
            "--response",
            "y",
            "--formula",
            "y ~ 1",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "DataLoadingError" in captured.err
    assert str(missing) in captured.err


def test_programmatic_cli_preserves_dataexcept_contract(tmp_path: Path) -> None:
    missing = tmp_path / "missing.csv"

    from dataexcept import DataLoadingError

    with pytest.raises(DataLoadingError):
        cli.main(
            [
                "anova",
                "--data",
                str(missing),
                "--response",
                "y",
                "--formula",
                "y ~ 1",
            ]
        )


def test_cli_does_not_hide_unexpected_programmer_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_unexpectedly(_args: object) -> None:
        raise ValueError("unexpected programmer failure")

    monkeypatch.setattr(cli, "anova_command", fail_unexpectedly)

    with pytest.raises(ValueError, match="unexpected programmer failure"):
        cli.main(
            [
                "anova",
                "--data",
                "unused.csv",
                "--response",
                "y",
                "--formula",
                "y ~ 1",
            ]
        )
