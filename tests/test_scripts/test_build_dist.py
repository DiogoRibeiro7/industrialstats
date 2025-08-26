"""Tests for the build_dist utility."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "build_dist",
    Path(__file__).resolve().parents[2] / "scripts" / "build_dist.py",
)
_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_build)


def test_build_dist_invokes_build(monkeypatch):
    """build_dist should invoke the build module with outdir."""
    called = {}

    def fake_run(cmd, check):  # type: ignore[override]
        called["cmd"] = cmd
        called["check"] = check

    monkeypatch.setattr(subprocess, "run", fake_run)
    _build.build_dist(output_dir="tmpdist")
    assert called["cmd"][:3] == ["python", "-m", "build"]
    assert "--outdir" in called["cmd"]
    assert called["check"] is True
