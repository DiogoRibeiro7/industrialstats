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
from typing import Any, Dict, Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover
    yaml = None


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


def load_config(path: Union[str, Path]) -> None:
    """Load configuration from a JSON or YAML file.

    Parameters
    ----------
    path : str or Path
        Path to the configuration file.

    Raises
    ------
    ValueError
        If the file format is unsupported or PyYAML is required but not
        installed.
    """
    path = Path(path)
    if path.suffix.lower() == ".json":
        data: Dict[str, Any] = json.loads(path.read_text())
    elif path.suffix.lower() in {".yml", ".yaml"}:
        if yaml is None:  # pragma: no cover - handled above
            raise ValueError("PyYAML is required for YAML configuration files")
        data = yaml.safe_load(path.read_text())
    else:  # pragma: no cover - defensive
        raise ValueError("Unsupported configuration file format")

    config.update(**data)
