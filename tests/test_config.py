"""Tests for global configuration management."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pytest
from dataexcept import ConfigurationError, FileReadError, ParsingError

from industrialstats import config
from industrialstats.config import load_config


def test_update_and_apply_changes_logging_level():
    original = logging.getLogger().level
    config.update(log_level="DEBUG", precision=2)
    try:
        assert logging.getLogger().level == logging.DEBUG
        assert np.get_printoptions()["precision"] == 2
    finally:
        config.update(log_level=logging.getLevelName(original), precision=4)


def test_load_config_from_json(tmp_path: Path):
    config_file = tmp_path / "cfg.json"
    config_file.write_text(json.dumps({"plot_style": "ggplot", "precision": 3}))
    load_config(config_file)
    assert config.plot_style == "ggplot"
    assert np.get_printoptions()["precision"] == 3


def test_unsupported_config_format_uses_structured_configuration_error(
    tmp_path: Path,
):
    config_file = tmp_path / "cfg.toml"
    config_file.write_text("precision = 3")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(config_file)

    error = exc_info.value
    assert error.option == str(config_file)
    assert ".toml" in str(error)


def test_missing_config_file_uses_structured_file_read_error(tmp_path: Path):
    config_file = tmp_path / "missing.json"

    with pytest.raises(FileReadError) as exc_info:
        load_config(config_file)

    error = exc_info.value
    assert error.path == str(config_file)
    assert isinstance(error.original, FileNotFoundError)
    assert error.__cause__ is error.original


def test_malformed_json_uses_path_only_parsing_context(tmp_path: Path):
    config_file = tmp_path / "cfg.json"
    secret = '"api_key": "do-not-retain"'
    config_file.write_text("{" + secret)

    with pytest.raises(ParsingError) as exc_info:
        load_config(config_file)

    error = exc_info.value
    assert error.text == str(config_file)
    assert secret not in str(error)
    assert isinstance(error.__cause__, json.JSONDecodeError)
