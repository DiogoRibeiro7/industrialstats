from __future__ import annotations

"""Screening designs such as Plackett-Burman."""

from typing import List

import numpy as np
import pandas as pd
from scipy.linalg import hankel, toeplitz

from .base import ExperimentalDesign, Factor


class PlackettBurmanDesign(ExperimentalDesign):
    """Plackett-Burman screening design for two-level factors.

    Supports any number of factors using a Hadamard-based construction and
    optional randomization.
    """

    def __init__(self, factors: List[Factor], randomize: bool = True) -> None:
        """Initialize the design."""
        super().__init__("Plackett-Burman Design")
        self.factors = factors
        self.randomize_flag = randomize

        if not all(len(f.levels) == 2 for f in self.factors):
            raise ValueError("Plackett-Burman design requires 2-level factors")

    def _pb_matrix(self, n_factors: int) -> np.ndarray:
        """Generate a Plackett-Burman matrix using a Hadamard construction."""
        keep = int(n_factors)
        n = 4 * (int(n_factors / 4) + 1)
        f, e = np.frexp([n, n / 12.0, n / 20.0])
        k = [idx for idx, val in enumerate(np.logical_and(f == 0.5, e > 0)) if val]
        if not k:
            raise ValueError("n must be a multiple of 4")
        k = k[0]
        e = e[k] - 1

        if k == 0:
            H = np.ones((1, 1))
        elif k == 1:
            H = np.vstack(
                (
                    np.ones((1, 12)),
                    np.hstack(
                        (
                            np.ones((11, 1)),
                            toeplitz(
                                [-1, -1, 1, -1, -1, -1, 1, 1, 1, -1, 1],
                                [-1, 1, -1, 1, 1, 1, -1, -1, -1, 1, -1],
                            ),
                        )
                    ),
                )
            )
        elif k == 2:
            H = np.vstack(
                (
                    np.ones((1, 20)),
                    np.hstack(
                        (
                            np.ones((19, 1)),
                            hankel(
                                [
                                    -1,
                                    -1,
                                    1,
                                    1,
                                    -1,
                                    -1,
                                    -1,
                                    -1,
                                    1,
                                    -1,
                                    1,
                                    -1,
                                    1,
                                    1,
                                    1,
                                    1,
                                    -1,
                                    -1,
                                    1,
                                ],
                                [
                                    1,
                                    -1,
                                    -1,
                                    1,
                                    1,
                                    -1,
                                    -1,
                                    -1,
                                    -1,
                                    1,
                                    -1,
                                    1,
                                    -1,
                                    1,
                                    1,
                                    1,
                                    1,
                                    -1,
                                    -1,
                                ],
                            ),
                        )
                    ),
                )
            )
        else:
            raise ValueError("Design not supported for this many factors")

        for _ in range(e):
            H = np.vstack((np.hstack((H, H)), np.hstack((H, -H))))

        H = H[:, 1 : (keep + 1)]
        return np.flipud(H)

    def generate_design(self) -> pd.DataFrame:
        """Generate the design matrix."""
        design_matrix = self._pb_matrix(len(self.factors))
        df = pd.DataFrame(design_matrix, columns=[f.name for f in self.factors])
        df.insert(0, "RunOrder", range(1, len(df) + 1))

        if self.randomize_flag:
            df = df.sample(frac=1).reset_index(drop=True)
            df.insert(0, "RunOrder", range(1, len(df) + 1))
            self.randomized = True

        self.design_matrix = df
        return df

    def foldover(self) -> pd.DataFrame:
        """Create a foldover design to de-alias main effects."""
        if self.design_matrix is None:
            self.generate_design()

        fold_df = self.design_matrix.copy()
        for col in self.factors:
            fold_df[col.name] = -fold_df[col.name]

        fold_df["RunOrder"] = range(
            len(self.design_matrix) + 1, 2 * len(self.design_matrix) + 1
        )
        self.design_matrix = pd.concat([self.design_matrix, fold_df], ignore_index=True)
        return fold_df

    def validate_design(self) -> bool:
        """Validate the design parameters."""
        return len(self.factors) >= 2


class DefinitiveScreeningDesign(ExperimentalDesign):
    """Simple Definitive Screening Design implementation.

    This implementation generates a basic 3-level definitive screening design
    using :math:`-1`, ``0`` and ``1`` levels. It creates ``2 * n + 1`` runs,
    where ``n`` is the number of factors.

    References
    ----------
    .. [1] Jones, B., Nachtsheim, C. (2011). A Class of Three-Level Designs for
       Definitive Screening in the Presence of Second-Order Effects.
    """

    def __init__(self, factors: List[Factor], randomize: bool = True) -> None:
        """Initialize the design.

        Parameters
        ----------
        factors : List[Factor]
            Factors to include in the screening design. Each factor should have
            exactly three levels.
        randomize : bool, optional
            If ``True``, randomize the run order. Defaults to ``True``.
        """

        super().__init__("Definitive Screening Design")
        self.factors = factors
        self.randomize_flag = randomize

        if not all(len(f.levels) == 3 for f in self.factors):
            raise ValueError("Definitive screening requires 3-level factors")

    def generate_design(self) -> pd.DataFrame:
        """Generate the design matrix."""

        if len(self.factors) < 2:
            raise ValueError("At least two factors are required")

        design_rows = []
        run_id = 1
        base_levels = [-1, 1]

        for factor in self.factors:
            for level in base_levels:
                row = {f.name: 0 for f in self.factors}
                row[factor.name] = level
                design_rows.append({"RunID": run_id, **row})
                run_id += 1

        # Center run
        design_rows.append({"RunID": run_id, **{f.name: 0 for f in self.factors}})

        df = pd.DataFrame(design_rows)

        if self.randomize_flag:
            df = df.sample(frac=1).reset_index(drop=True)
            df.insert(0, "RunOrder", range(1, len(df) + 1))
            self.randomized = True
        else:
            df.insert(0, "RunOrder", range(1, len(df) + 1))

        self.design_matrix = df
        return df

    def validate_design(self) -> bool:
        """Validate design parameters."""

        return len(self.factors) >= 2 and all(len(f.levels) == 3 for f in self.factors)
