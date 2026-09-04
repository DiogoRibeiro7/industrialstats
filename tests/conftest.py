"""Shared pytest configuration for the industrialstats test suite.

This module runs before any test module is imported, which makes it the
correct place to pin global state that individual tests must not have to
re-establish for themselves.
"""

from __future__ import annotations

import os

import matplotlib
from hypothesis import HealthCheck, settings

# Select a non-interactive backend before any test module imports pyplot.
# Test modules previously called ``matplotlib.use("Agg")`` individually, which
# made correctness depend on import order and left modules that import pyplot
# directly relying on some other module having run first.
matplotlib.use("Agg")


# Hypothesis health checks and deadlines are wall-clock based, so they report
# failures when the machine is merely busy rather than when the code is wrong.
# Shared CI runners are routinely loaded enough to trip them, so the profiles
# below trade that timing sensitivity for deterministic results.
settings.register_profile(
    "dev",
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.register_profile(
    "ci",
    deadline=None,
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    print_blob=True,
)

settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
