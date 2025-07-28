from __future__ import annotations

"""Screening designs such as Plackett-Burman."""

from typing import List
import pandas as pd
import numpy as np
from scipy.linalg import circulant

from .base import ExperimentalDesign, Factor


class PlackettBurmanDesign(ExperimentalDesign):
    """Basic Plackett-Burman design supporting up to 7 factors."""

    def __init__(self, factors: List[Factor], randomize: bool = True) -> None:
        """Initialize the design."""
        super().__init__("Plackett-Burman Design")
        self.factors = factors
        self.randomize_flag = randomize

        if not all(len(f.levels) == 2 for f in self.factors):
            raise ValueError("Plackett-Burman design requires 2-level factors")
        if len(self.factors) > 7:
            raise ValueError("This implementation supports at most 7 factors")

    def generate_design(self) -> pd.DataFrame:
        """Generate the design matrix."""
        first_row = [-1, -1, 1, -1, 1, 1, 1]
        base_matrix = circulant(first_row)[:7, :7]
        design_matrix = np.vstack([base_matrix, -np.ones(7)])
        design_matrix = design_matrix[:, : len(self.factors)]

        df = pd.DataFrame(design_matrix, columns=[f.name for f in self.factors])
        df.insert(0, "RunOrder", range(1, len(df) + 1))

        if self.randomize_flag:
            df = df.sample(frac=1).reset_index(drop=True)
            df.insert(0, "RunOrder", range(1, len(df) + 1))
            self.randomized = True

        self.design_matrix = df
        return df

    def validate_design(self) -> bool:
        """Validate the design parameters."""
        return len(self.factors) >= 2 and len(self.factors) <= 7

