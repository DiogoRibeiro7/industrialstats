"""Dependency-boundary tests for configuration loading."""

from pathlib import Path

import pytest
from dataexcept import DependencyError

import industrialstats.config as config_module
from industrialstats.config import load_config


def test_yaml_without_pyyaml_uses_structured_dependency_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_file = tmp_path / "cfg.yaml"
    config_file.write_text("precision: 3\n")
    monkeypatch.setattr(config_module, "yaml", None)

    with pytest.raises(DependencyError) as exc_info:
        load_config(config_file)

    error = exc_info.value
    assert error.dependency_name == "PyYAML"
    assert "YAML configuration files" in str(error)
