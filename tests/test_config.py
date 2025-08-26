"""Tests for global configuration management."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

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
