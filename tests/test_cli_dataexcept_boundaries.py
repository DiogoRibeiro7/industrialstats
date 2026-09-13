"""Structured operational-boundary tests for the command-line interface."""

from pathlib import Path

import pytest
from dataexcept import DataLoadingError

from industrialstats.cli import main


@pytest.mark.parametrize(
    "argv",
    [
        ["anova", "--response", "y", "--formula", "y ~ A"],
        ["model", "--response", "y"],
    ],
)
def test_cli_data_commands_preserve_structured_loading_error(
    tmp_path: Path,
    argv: list[str],
) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(DataLoadingError) as exc_info:
        main([*argv[:1], "--data", str(missing), *argv[1:]])

    error = exc_info.value
    assert error.source == str(missing)
    assert isinstance(error.original, FileNotFoundError)
    assert error.__cause__ is error.original
