"""Release metadata consistency checks."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import industrialstats

ROOT = Path(__file__).resolve().parents[1]


def test_release_versions_match() -> None:
    """Package, build metadata, and citation metadata must share one version."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_version = pyproject["tool"]["poetry"]["version"]

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    match = re.search(r'^version:\s*["\']?([^"\'\n]+)["\']?\s*$', citation, re.MULTILINE)
    assert match is not None, "CITATION.cff must contain a version field"
    citation_version = match.group(1).strip()

    assert industrialstats.__version__ == package_version
    assert citation_version == package_version
