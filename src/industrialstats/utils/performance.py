"""Utilities for profiling code execution paths."""

from __future__ import annotations

import cProfile
import pstats
from collections.abc import Callable
from typing import Any


def profile_function(
    func: Callable[..., Any], *args: Any, **kwargs: Any
) -> pstats.Stats:
    """Profile a callable and return execution statistics.

    Parameters
    ----------
    func : Callable
        Function or method to profile.
    *args : Any
        Positional arguments passed to ``func``.
    **kwargs : Any
        Keyword arguments passed to ``func``.

    Returns
    -------
    pstats.Stats
        Profiling statistics sorted by cumulative time.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    func(*args, **kwargs)
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    return stats
