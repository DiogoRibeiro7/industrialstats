from __future__ import annotations

"""Utilities for profiling code execution paths."""

import cProfile
import pstats
from typing import Any, Callable


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
