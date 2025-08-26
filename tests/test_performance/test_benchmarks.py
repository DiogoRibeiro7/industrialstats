"""Performance benchmarks for industrialstats.

These tests provide simple regression checks on the performance of
key design generation and analysis routines. The thresholds are
conservative to avoid false positives while still detecting major
regressions.
"""

from __future__ import annotations

import time
from typing import List

import pytest

from industrialstats.analysis.power_analysis import PowerAnalysis
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign
from industrialstats.designs.optimal import OptimalDesign
from industrialstats.utils.data_generation import DataSimulator
from industrialstats.utils.performance import profile_function


def _build_factors(n: int) -> List[Factor]:
    """Create ``n`` two-level continuous factors."""
    return [
        Factor(name=f"F{i}", levels=[-1, 1], factor_type="continuous") for i in range(n)
    ]


@pytest.mark.parametrize(
    "n_factors,max_time", [(3, 0.05), (5, 0.2), (7, 0.5), (9, 1.0), (11, 2.0)]
)
def test_factorial_generation_benchmark(n_factors: int, max_time: float) -> None:
    """Factorial design generation stays within time limits."""
    factors = _build_factors(n_factors)
    design = FactorialDesign(factors, randomize=False)
    start = time.perf_counter()
    design.generate_design()
    elapsed = time.perf_counter() - start
    assert elapsed < max_time


def test_large_design_memory_usage() -> None:
    """Large factorial design remains below memory threshold."""
    factors = _build_factors(8)  # 256 runs
    design = FactorialDesign(factors, replicates=2, randomize=False)
    design.generate_design()
    mem_mb = design.design_matrix.memory_usage(deep=True).sum() / (1024**2)
    assert mem_mb < 5  # MB


def test_power_analysis_performance() -> None:
    """Power analysis executes quickly for moderate designs."""
    pa = PowerAnalysis()
    start = time.perf_counter()
    pa.factorial_power(effect_size=0.25, power=0.8, factor_levels=[2, 2, 2])
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5


def test_high_dimensional_simulation_performance() -> None:
    """Simulation scales to many factors without excessive runtime."""
    factors = _build_factors(10)
    design = FactorialDesign(factors, randomize=False)
    X = design.generate_design()
    effects = {f.name: 0.5 for f in factors}
    start = time.perf_counter()
    sim = DataSimulator(seed=0)
    sim.simulate_factorial_response(
        X, main_effects=effects, interactions={}, noise_level=1.0
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_optimal_design_scalability() -> None:
    """Coordinate exchange converges within time limit."""
    factors = _build_factors(3)
    opt = OptimalDesign(factors, n_runs=8)
    opt.generate_candidate_set()
    start = time.perf_counter()
    # Use systematic start to avoid singular initial designs
    opt.generate_design(max_iterations=20, random_start=False, n_random_starts=1)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0


def test_performance_regression_detection() -> None:
    """Repeated runs have comparable execution times."""
    factors = _build_factors(4)

    def _generate() -> None:
        design = FactorialDesign(factors, randomize=False)
        design.generate_design()

    stats1 = profile_function(_generate)
    stats2 = profile_function(_generate)
    # Ensure subsequent run does not exceed 150% of initial time
    assert stats2.total_tt <= stats1.total_tt * 1.5
