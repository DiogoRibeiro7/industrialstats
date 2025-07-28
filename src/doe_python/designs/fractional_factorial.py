from __future__ import annotations

"""Fractional factorial design implementation."""

from itertools import product
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


class FractionalFactorialDesign(ExperimentalDesign):
    """Fractional factorial design implementation."""

    def __init__(
        self,
        factors: List[Factor],
        fraction: str = "1/2",
        generators: Optional[List[str]] = None,
        resolution: Optional[int] = None,
        replicates: int = 1,
        randomize: bool = True,
    ) -> None:
        """Initialize fractional factorial design.

        Args:
            factors: Factors in the experiment. Must all have two levels.
            fraction: Fraction of the full design, e.g. ``"1/2"`` or ``"1/4"``.
            generators: Optional generator strings using factor names.
            resolution: Desired design resolution (for reference only).
            replicates: Number of replicates.
            randomize: Whether to randomize run order.
        """
        super().__init__("Fractional Factorial Design")
        self.factors = factors
        self.fraction = fraction
        self.generators = generators or []
        self.resolution = resolution
        self.replicates = replicates
        self.randomize_flag = randomize

        if not all(len(f.levels) == 2 for f in factors):
            raise ValueError("All factors must have exactly two levels")

        denom = int(fraction.split("/")[1])
        p = int(np.log2(denom))
        if 2**p != denom:
            raise ValueError("Fraction denominator must be a power of 2")
        self.p = p

        if not self.generators:
            base_names = [f.name for f in factors[: len(factors) - p]]
            for i in range(p):
                self.generators.append("".join(base_names))

    def _coded_levels(self) -> Dict[str, List[int]]:
        coded = {}
        for f in self.factors:
            coded[f.name] = [-1, 1]
        return coded

    def _evaluate_generator(self, gen: str, row: Dict[str, int]) -> int:
        val = 1
        for name in gen:
            val *= row[name]
        return val

    def generate_design(self) -> pd.DataFrame:
        """Generate fractional factorial design matrix."""
        coded_levels = self._coded_levels()
        base_factors = self.factors[: len(self.factors) - self.p]
        alias_factors = self.factors[len(self.factors) - self.p :]

        base_names = [f.name for f in base_factors]
        runs = list(product([-1, 1], repeat=len(base_names)))
        data = []
        run_id = 1
        for rep in range(1, self.replicates + 1):
            for run in runs:
                row = dict(zip(base_names, run))
                for name, gen in zip([f.name for f in alias_factors], self.generators):
                    row[name] = self._evaluate_generator(gen, row)
                data.append({"RunID": run_id, "Replicate": rep, **row})
                run_id += 1

        df = pd.DataFrame(data)
        for f in self.factors:
            mapping = {-1: f.levels[0], 1: f.levels[1]}
            df[f.name] = df[f.name].map(mapping)

        if self.randomize_flag:
            df = df.sample(frac=1, random_state=None).reset_index(drop=True)
            df.insert(0, "RunOrder", range(1, len(df) + 1))
            self.randomized = True
        self.design_matrix = df
        return df

    def validate_design(self) -> bool:
        """Validate fractional factorial parameters."""
        return all(len(f.levels) == 2 for f in self.factors) and self.replicates > 0

    def alias_structure(self) -> Dict[str, List[str]]:
        """Calculate complete alias structure."""
        structure: Dict[str, List[str]] = {}
        for f in self.factors:
            aliases = [f"{f.name}{gen}" for gen in self.generators]
            structure[f.name] = aliases
        return structure

    def resolution_analysis(self) -> Dict[str, Any]:
        """Analyze design resolution and clarity."""
        if not self.generators:
            return {"resolution": None}
        lengths = [len(gen) + 1 for gen in self.generators]
        return {"resolution": min(lengths)}

    def foldover_options(self) -> List[Dict[str, Any]]:
        """Suggest foldover strategies."""
        options = []
        for gen in self.generators:
            options.append({"generator": gen, "strategy": f"reverse {gen}"})
        return options
