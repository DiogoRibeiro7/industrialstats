"""Advanced experimental designs."""

from __future__ import annotations

from collections.abc import Callable
from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

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
        whole_plot_factors: list[Factor],
        sub_plot_factors: list[Factor],
        replicates: int = 1,
        randomize: bool = True,
        seed: int | None = None,
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
            for _rep in range(self.replicates):
                for sp_combo in product(*sp_levels):
                    row: dict[str, Any] = {
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


class MixtureDesign(ExperimentalDesign):
    """Simplex-lattice mixture design.

    Parameters
    ----------
    factors : list[Factor]
        Mixture components. Must contain at least three continuous factors.
    order : int, optional
        Simplex-lattice degree :math:`m`. Defaults to ``2``.
    constraints : list[Callable[[numpy.ndarray], bool]], optional
        Constraint functions applied to candidate mixtures. Each function
        receives an array of component proportions and returns ``True`` if the
        point satisfies the constraint. Defaults to ``None``.
    randomize : bool, optional
        Whether to randomize run order. Defaults to ``False``.
    seed : int, optional
        Random seed for reproducible randomization.

    Examples
    --------
    Generate a simplex-lattice design for a three-component mixture::

        >>> from industrialstats.designs.base import Factor
        >>> from industrialstats.designs.advanced import MixtureDesign
        >>> comps = [
        ...     Factor("A", [], "continuous"),
        ...     Factor("B", [], "continuous"),
        ...     Factor("C", [], "continuous"),
        ... ]
        >>> design = MixtureDesign(comps, order=2)
        >>> design.generate_design()
             A    B    C
        0  1.0  0.0  0.0
        1  0.0  1.0  0.0
        2  0.0  0.0  1.0
        3  0.5  0.5  0.0
        4  0.5  0.0  0.5
        5  0.0  0.5  0.5

    References
    ----------
    .. [1] Cornell, J. A. (2011). *Experiments with Mixtures*.
    """

    def __init__(
        self,
        factors: list[Factor],
        order: int = 2,
        constraints: list[Callable[[np.ndarray], bool]] | None = None,
        randomize: bool = False,
        seed: int | None = None,
    ) -> None:
        super().__init__("Mixture Design")
        if len(factors) < 3:
            raise ValueError("MixtureDesign requires at least three factors")
        self.factors = factors
        self.order = order
        self.constraints = constraints or []
        self.randomize_flag = randomize
        self.seed = seed

    def _generate_simplex_lattice(self) -> np.ndarray:
        q = len(self.factors)
        m = self.order
        grids = [np.arange(m + 1) for _ in range(q)]
        combos = np.stack(np.meshgrid(*grids), -1).reshape(-1, q)
        combos = combos[combos.sum(axis=1) == m]
        points = combos / m
        return points

    def generate_design(self) -> pd.DataFrame:
        """Generate the mixture design matrix."""
        if not self.validate_design():
            raise ValueError("Invalid mixture design configuration")

        points = self._generate_simplex_lattice()
        valid_points = []
        for pt in points:
            if all(constraint(pt) for constraint in self.constraints):
                if not np.isclose(pt.sum(), 1.0):
                    raise ValueError("Mixture components must sum to 1")
                valid_points.append(pt)

        design = pd.DataFrame(valid_points, columns=[f.name for f in self.factors])

        if self.randomize_flag:
            rng = np.random.default_rng(self.seed)
            design = design.sample(
                frac=1,
                random_state=int(rng.integers(0, np.iinfo("int32").max)),
            ).reset_index(drop=True)
            design.insert(0, "RunOrder", range(1, len(design) + 1))
            self.randomized = True

        self.design_matrix = design
        return design

    def plot_simplex(self, ax: Axes | None = None) -> Axes:
        """Plot mixture design points for three components.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Axes object to plot on. Created if ``None``.

        Returns
        -------
        matplotlib.axes.Axes
            Axes containing the simplex plot.

        Raises
        ------
        ValueError
            If the design has not been generated or the number of factors is
            not three.
        """
        if self.design_matrix is None:
            raise ValueError("Generate design before plotting")
        if len(self.factors) != 3:
            raise ValueError("Simplex plot currently supports three factors")

        import matplotlib.pyplot as plt

        if ax is None:
            _, ax = plt.subplots()

        data = self.design_matrix[[f.name for f in self.factors]].to_numpy()
        x = data[:, 1] + 0.5 * data[:, 2]
        y = (np.sqrt(3) / 2) * data[:, 2]
        ax.scatter(x, y)
        ax.set_xlabel(self.factors[1].name)
        ax.set_ylabel(self.factors[2].name)
        ax.set_title("Mixture Simplex")
        ax.set_aspect("equal")
        return ax

    def validate_design(self) -> bool:
        """Validate mixture design parameters."""
        return len(self.factors) >= 3 and self.order >= 1
