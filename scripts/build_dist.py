"""Build distribution artifacts for the industrialstats package.

This script creates source and wheel distributions in the ``dist`` directory
using the PEP 517 build backend.
"""

# mypy: ignore-errors

from __future__ import annotations

import subprocess
from pathlib import Path


def build_dist(output_dir: str = "dist") -> None:
    """Build wheel and sdist artifacts.

    Parameters
    ----------
    output_dir : str, optional
        Directory where the artifacts will be written. Defaults to ``"dist"``.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    subprocess.run(["python", "-m", "build", "--outdir", output_dir], check=True)


if __name__ == "__main__":  # pragma: no cover - script entry
    build_dist()
