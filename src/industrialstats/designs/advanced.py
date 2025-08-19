from __future__ import annotations

"""Advanced experimental designs."""

from itertools import product
from typing import List, Optional

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


class SplitPlotDesign(ExperimentalDesign):
    """Basic split-plot experimental design.

    The design handles hard-to-change *whole-plot* factors and easier-to-change
    *sub-plot* factors. Randomization is restricted so that sub-plot runs are
    shuffled only within each whole plot.

    Parameters
    ----------
    whole_plot_factors : list[Factor]
        Factors applied to whole plots (hard-to-change factors).
    sub_plot_factors : list[Factor]
        Factors applied within whole plots (easy-to-change factors).
    replicates : int, optional
        Number of replicates for each whole-plot/sub-plot combination. Defaults
        to ``1``.
    randomize : bool, optional
        Whether to randomize run order. Defaults to ``True``.
    seed : int, optional
        Random seed for reproducible shuffling.

    Examples
    --------
    Generate a split-plot design with one whole-plot factor and one sub-plot
    factor::

        >>> from industrialstats.designs.base import Factor
        >>> from industrialstats.designs.advanced import SplitPlotDesign
        >>> wp = [Factor("Oven", [1, 2])]
        >>> sp = [Factor("Temperature", [150, 200, 250])]
        >>> design = SplitPlotDesign(wp, sp, seed=123)
        >>> design.generate_design().head()
           RunOrder  WholePlot  Oven  Temperature
        0         1          2     2          200
        1         2          2     2          150
        2         3          2     2          250
        3         4          1     1          250
        4         5          1     1          200
    """

    def __init__(
        self,
        whole_plot_factors: List[Factor],
        sub_plot_factors: List[Factor],
        replicates: int = 1,
        randomize: bool = True,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__("Split-Plot Design")
        if not whole_plot_factors:
            raise ValueError("At least one whole-plot factor is required")
        if not sub_plot_factors:
            raise ValueError("At least one sub-plot factor is required")
        if replicates < 1:
            raise ValueError("replicates must be >= 1")

        self.whole_plot_factors = whole_plot_factors
        self.sub_plot_factors = sub_plot_factors
        self.replicates = replicates
        self.randomize_flag = randomize
        self.seed = seed
        self.factors = whole_plot_factors + sub_plot_factors

    def generate_design(self) -> pd.DataFrame:
        """Generate the split-plot design matrix.

        Returns
        -------
        pandas.DataFrame
            Generated design matrix with ``WholePlot`` identifiers.
        """
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        design_rows = []
        run_id = 1
        whole_plot_id = 1
        wp_levels = [f.levels for f in self.whole_plot_factors]
        sp_levels = [f.levels for f in self.sub_plot_factors]
        for wp_combo in product(*wp_levels):
            for rep in range(self.replicates):
                for sp_combo in product(*sp_levels):
                    row = {
                        "StdOrder": run_id,
                        "WholePlot": whole_plot_id,
                    }
                    for i, factor in enumerate(self.whole_plot_factors):
                        row[factor.name] = wp_combo[i]
                    for j, factor in enumerate(self.sub_plot_factors):
                        row[factor.name] = sp_combo[j]
                    design_rows.append(row)
                    run_id += 1
            whole_plot_id += 1

        self.design_matrix = pd.DataFrame(design_rows)

        if self.randomize_flag:
            rng = np.random.default_rng(self.seed)
            hp_ids = self.design_matrix["WholePlot"].unique().tolist()
            rng.shuffle(hp_ids)
            randomized = []
            for hp in hp_ids:
                df_hp = self.design_matrix[self.design_matrix["WholePlot"] == hp]
                df_hp = df_hp.sample(
                    frac=1,
                    random_state=int(rng.integers(0, np.iinfo("int32").max)),
                ).reset_index(drop=True)
                randomized.append(df_hp)
            self.design_matrix = pd.concat(randomized, ignore_index=True)
            self.design_matrix.insert(
                0, "RunOrder", range(1, len(self.design_matrix) + 1)
            )
            self.randomized = True

        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate split-plot design parameters."""
        return (
            bool(self.whole_plot_factors)
            and bool(self.sub_plot_factors)
            and self.replicates >= 1
        )
