"""Global configuration management for industrialstats.

This module provides a simple configuration system that controls plotting
preferences, numerical precision, and logging levels across the package.
Configuration values can be loaded from a JSON or YAML file and are applied to
relevant third-party libraries.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from dataexcept import ConfigurationError, FileReadError, ParsingError

try:  # pragma: no cover - optional dependency
    import yaml
except ImportError:  # pragma: no cover
    # Sentinel for the optional dependency; guarded at every use site.
    yaml = None  # type: ignore[assignment]


@dataclass
class Config:
    """Package configuration settings.

    Parameters
    ----------
    plot_style : str, default="ggplot"
        Matplotlib style to apply for plots.
    theme : str, default="whitegrid"
        Seaborn theme used to style figures.
    precision : int, default=4
        Number of decimal places for NumPy printing.
    log_level : str, default="INFO"
        Logging level applied to the root logger.
    """

    plot_style: str = "ggplot"
    theme: str = "whitegrid"
    precision: int = 4
    log_level: str = "INFO"
    _applied: bool = field(default=False, init=False)

    def apply(self) -> None:
        """Apply configuration to third-party libraries."""
        plt.style.use(self.plot_style)
        sns.set_theme(style=self.theme)
        np.set_printoptions(precision=self.precision)
        logging.getLogger().setLevel(self.log_level.upper())
        self._applied = True

    def update(self, **kwargs: Any) -> None:
        """Update configuration values and reapply settings.

        Parameters
        ----------
        **kwargs
            Configuration fields to update.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.apply()


config = Config()


def _read_config_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as exc:
        raise FileReadError(str(path), exc) from exc


def load_config(path: str | Path) -> None:
    """Load configuration from a JSON or YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the configuration file.

    Raises
    ------
    ConfigurationError
        If the configuration file format is unsupported.
    FileReadError
        If the configuration file cannot be read.
    ParsingError
        If JSON or YAML content cannot be parsed.
    ValueError
        If PyYAML is required but not installed.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix not in {".json", ".yml", ".yaml"}:
        raise ConfigurationError(
            str(path),
            f"Unsupported configuration file format: {path.suffix or '<none>'}",
        )

    text = _read_config_text(path)

    if suffix == ".json":
        try:
            data: dict[str, Any] = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParsingError(
                str(path), f"Failed to parse JSON configuration: {exc.msg}"
            ) from exc
    else:
        if yaml is None:  # pragma: no cover - handled above
            raise ValueError("PyYAML is required for YAML configuration files")
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ParsingError(
                str(path), f"Failed to parse YAML configuration: {exc}"
            ) from exc

    config.update(**data)
