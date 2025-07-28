from __future__ import annotations

"""Randomized Complete Block Design implementation."""

from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from .base import ExperimentalDesign, Factor


class RandomizedCompleteBlockDesign(ExperimentalDesign):
    """Randomized Complete Block Design."""

    def __init__(
        self,
        treatments: List[str],
        blocks: List[str],
        blocking_factor: str = "Block",
    ) -> None:
        """Initialize RCBD.

        Args:
            treatments (List[str]): List of treatment names or levels.
            blocks (List[str]): Names of blocking levels.
            blocking_factor (str): Column name for blocks in the design matrix.
        """
        super().__init__("Randomized Complete Block Design")
        if len(treatments) < 2:
            raise ValueError("Must have at least 2 treatments")
        if len(blocks) < 2:
            raise ValueError("Must have at least 2 blocks")

        self.treatments = treatments
        self.blocks = blocks
        self.blocking_factor = blocking_factor

        self.factors = [
            Factor("Treatment", treatments, "categorical"),
            Factor(blocking_factor, blocks, "categorical"),
        ]

    def generate_design(self) -> pd.DataFrame:
        """Generate RCBD matrix with proper randomization."""
        design_rows = []
        run_id = 1
        for block in self.blocks:
            block_rows = []
            for treatment in self.treatments:
                block_rows.append(
                    {
                        "RunID": run_id,
                        self.blocking_factor: block,
                        "Treatment": treatment,
                    }
                )
                run_id += 1
            # Randomize within block
            block_df = pd.DataFrame(block_rows).sample(frac=1).reset_index(drop=True)
            design_rows.extend(block_df.to_dict(orient="records"))

        self.design_matrix = pd.DataFrame(design_rows)
        self.design_matrix.insert(0, "RunOrder", range(1, len(self.design_matrix) + 1))
        self.randomized = True
        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate RCBD parameters."""
        return len(self.treatments) >= 2 and len(self.blocks) >= 2

    def efficiency_vs_crd(
        self, block_variance: float, error_variance: float = 1.0
    ) -> float:
        """Calculate relative efficiency compared to CRD."""
        if block_variance < 0 or error_variance <= 0:
            raise ValueError("variances must be positive")
        rcbd_error_ms = error_variance
        crd_error_ms = error_variance + block_variance
        return rcbd_error_ms / crd_error_ms

    def missing_plot_analysis(
        self, missing_positions: List[Tuple[str, str]]
    ) -> Dict[str, Any]:
        """Analyze impact of missing plots."""
        if self.design_matrix is None:
            self.generate_design()

        dm = self.design_matrix.copy()
        for block, treatment in missing_positions:
            mask = (dm[self.blocking_factor] == block) & (dm["Treatment"] == treatment)
            dm = dm.loc[~mask]

        balanced = (
            dm.groupby(self.blocking_factor)["Treatment"].nunique().nunique() == 1
        )
        return {
            "missing_count": len(missing_positions),
            "remaining_runs": len(dm),
            "balanced_after_missing": balanced,
        }

    def latin_square_option(self) -> Optional[pd.DataFrame]:
        """Generate Latin Square if conditions allow."""
        if len(self.treatments) != len(self.blocks) or len(self.treatments) < 3:
            return None

        treatments = self.treatments
        blocks = self.blocks
        n = len(treatments)
        ls_rows = []
        for i, row in enumerate(blocks):
            for j in range(n):
                treatment = treatments[(i + j) % n]
                ls_rows.append({"Row": row, "Column": j + 1, "Treatment": treatment})
        return pd.DataFrame(ls_rows)
