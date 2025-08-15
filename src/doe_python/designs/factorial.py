"""Full factorial experimental designs."""

from itertools import product
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


class FactorialDesign(ExperimentalDesign):
    """Full factorial experimental design (2^k, 3^k, mixed factorials)."""

    def __init__(
        self,
        factors: List[Factor],
        replicates: int = 1,
        center_points: int = 0,
        randomize: bool = True,
        blocks: int | None = None,
        seed: int | None = None,
    ) -> None:
        """Create a full factorial design.

        Parameters
        ----------
        factors : list[Factor]
            Factors included in the experiment.
        replicates : int, optional
            Number of replicates. Defaults to 1.
        center_points : int, optional
            Number of center points for continuous factors. Defaults to 0.
        randomize : bool, optional
            Whether to randomize run order. Defaults to ``True``.
        blocks : int, optional
            Number of blocks for the design. If ``None`` no blocking is
            applied.
        seed : int, optional
            Random seed used for run order shuffling.

        Raises
        ------
        ValueError
            If ``center_points`` is negative.
        """
        super().__init__("Full Factorial Design")
        self.factors = factors
        self.replicates = replicates
        self.center_points = center_points
        self.randomize_flag = randomize
        self.blocks = blocks
        self.seed = seed

        if center_points < 0:
            raise ValueError("Number of center points cannot be negative")

    def generate_design(self) -> pd.DataFrame:
        """Generate the full factorial design matrix.

        Returns
        -------
        pd.DataFrame
            Generated design matrix.

        Raises
        ------
        ValueError
            If the design configuration is invalid.
        """
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        # Generate all factor level combinations
        factor_levels = [factor.levels for factor in self.factors]
        combinations_list = list(product(*factor_levels))

        # Create base design
        design_data = []
        run_id = 1

        # Add factorial points
        for rep in range(self.replicates):
            for combo in combinations_list:
                row = {
                    "RunID": run_id,
                    "Replicate": rep + 1,
                    "DesignPoint": "Factorial",
                    "StdOrder": run_id,
                }
                for i, factor in enumerate(self.factors):
                    row[factor.name] = combo[i]
                design_data.append(row)
                run_id += 1

        # Add center points if specified
        if self.center_points > 0:
            center_values = self._calculate_center_points()
            for cp in range(self.center_points):
                row = {
                    "RunID": run_id,
                    "Replicate": 1,  # Center points typically in first replicate
                    "DesignPoint": "Center",
                    "StdOrder": run_id,
                }
                for i, factor in enumerate(self.factors):
                    row[factor.name] = center_values[i]
                design_data.append(row)
                run_id += 1

        self.design_matrix = pd.DataFrame(design_data)
        # Apply blocking if requested
        if self.blocks and self.blocks > 1:
            blocks = [i % self.blocks + 1 for i in range(len(self.design_matrix))]
            self.design_matrix["Block"] = blocks

        # Randomize if requested
        if self.randomize_flag:
            if self.blocks and self.blocks > 1:
                rng = np.random.default_rng(self.seed)
                self.design_matrix = (
                    self.design_matrix.groupby("Block", group_keys=False)
                    .apply(
                        lambda df: df.sample(
                            frac=1,
                            random_state=int(rng.integers(0, np.iinfo("int32").max)),
                        )
                    )
                    .reset_index(drop=True)
                )
                self.design_matrix.insert(
                    0, "RunOrder", range(1, len(self.design_matrix) + 1)
                )
                self.randomized = True
            else:
                self.randomize(self.seed)

        return self.design_matrix

    def _calculate_center_points(self) -> List[float]:
        """Calculate center point values for continuous factors.

        Returns
        -------
        list[float]
            Center values for each factor.
        """
        center_values = []
        for factor in self.factors:
            if factor.factor_type == "continuous":
                # For continuous factors, use the mean of levels
                center_values.append(np.mean(factor.levels))
            else:
                # For categorical factors, use middle level or most common
                middle_idx = len(factor.levels) // 2
                center_values.append(factor.levels[middle_idx])
        return center_values

    def validate_design(self) -> bool:
        """Validate factorial design parameters.

        Returns
        -------
        bool
            ``True`` if the configuration is valid.
        """
        if not self.factors:
            return False

        # Check that all factors have at least 2 levels
        for factor in self.factors:
            if len(factor.levels) < 2:
                return False

        if self.replicates < 1:
            return False

        return True

    def n_runs(self) -> int:
        """Calculate total number of experimental runs.

        Returns
        -------
        int
            Total run count including center points.
        """
        if not self.factors:
            return 0
        factorial_runs = (
            np.prod([len(f.levels) for f in self.factors]) * self.replicates
        )
        return factorial_runs + self.center_points

    def n_factorial_runs(self) -> int:
        """Calculate number of factorial runs (excluding center points).

        Returns
        -------
        int
            Count of factorial runs.
        """
        if not self.factors:
            return 0
        return np.prod([len(f.levels) for f in self.factors]) * self.replicates

    def degrees_of_freedom(self) -> Dict[str, int]:
        """Calculate degrees of freedom for ANOVA analysis.

        Returns
        -------
        dict[str, int]
            Degrees of freedom by effect name.
        """
        if not self.factors:
            return {}

        dof = {}
        total_runs = self.n_runs()

        # Main effects
        for factor in self.factors:
            dof[factor.name] = len(factor.levels) - 1

        # Two-factor interactions
        for i in range(len(self.factors)):
            for j in range(i + 1, len(self.factors)):
                interaction_name = f"{self.factors[i].name}*{self.factors[j].name}"
                dof[interaction_name] = (
                    dof[self.factors[i].name] * dof[self.factors[j].name]
                )

        # Three-factor interactions (for designs with 3+ factors)
        if len(self.factors) >= 3:
            for i in range(len(self.factors)):
                for j in range(i + 1, len(self.factors)):
                    for k in range(j + 1, len(self.factors)):
                        interaction_name = f"{self.factors[i].name}*{self.factors[j].name}*{self.factors[k].name}"
                        dof[interaction_name] = (
                            dof[self.factors[i].name]
                            * dof[self.factors[j].name]
                            * dof[self.factors[k].name]
                        )

        # Error degrees of freedom
        model_dof = sum(dof.values()) + 1  # +1 for intercept
        dof["Error"] = total_runs - model_dof
        dof["Total"] = total_runs - 1

        return dof

    def calculate_effects(self, response_data: List[float]) -> Dict[str, float]:
        """Calculate main effects and interactions for 2-level factors.

        Parameters
        ----------
        response_data : list[float]
            Response values for each run.

        Returns
        -------
        dict[str, float]
            Calculated effect estimates.

        Raises
        ------
        ValueError
            If the design is not two-level or lengths mismatch.
        """
        if not self._is_two_level_design():
            raise ValueError("Effect calculation only supported for 2-level designs")

        if len(response_data) != len(self.design_matrix):
            raise ValueError("Response data length doesn't match design matrix")

        effects: Dict[str, float] = {}
        n_factors = len(self.factors)

        # Build design matrix with 0/1 coding for regression
        X = pd.DataFrame()
        for factor in self.factors:
            X[factor.name] = (
                self.design_matrix[factor.name] == factor.levels[1]
            ).astype(int)

        # Add two-factor interactions
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                col = f"{self.factors[i].name}*{self.factors[j].name}"
                X[col] = X[self.factors[i].name] * X[self.factors[j].name]

        X.insert(0, "Intercept", 1)
        y = np.asarray(response_data)

        beta = np.linalg.lstsq(X.values, y, rcond=None)[0]

        for idx, factor in enumerate(self.factors):
            effects[factor.name] = float(beta[idx + 1])

        offset = n_factors + 1
        for i in range(n_factors):
            for j in range(i + 1, n_factors):
                col = f"{self.factors[i].name}*{self.factors[j].name}"
                effects[col] = float(beta[offset])
                offset += 1

        return effects

    def _is_two_level_design(self) -> bool:
        """Check if all factors have exactly two levels.

        Returns
        -------
        bool
            ``True`` if every factor has two levels.
        """
        return all(len(factor.levels) == 2 for factor in self.factors)

    def _get_coded_matrix(self) -> pd.DataFrame:
        """Convert the design matrix to coded levels (-1, +1).

        Returns
        -------
        pd.DataFrame
            Coded design matrix.

        Raises
        ------
        ValueError
            If the design matrix is not available.
        """
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")

        coded_data = []
        for _, row in self.design_matrix.iterrows():
            coded_row = {}
            for factor in self.factors:
                if len(factor.levels) == 2:
                    # For 2-level factors: low level = -1, high level = +1
                    coded_row[factor.name] = (
                        -1 if row[factor.name] == factor.levels[0] else 1
                    )
                else:
                    # For multi-level factors, normalize to [-1, 1] range
                    level_idx = factor.levels.index(row[factor.name])
                    coded_row[factor.name] = (
                        2 * level_idx / (len(factor.levels) - 1) - 1
                    )
            coded_data.append(coded_row)

        return pd.DataFrame(coded_data)

    def power_analysis(
        self, effect_size: float, alpha: float = 0.05, power: float = 0.8
    ) -> Dict[str, Any]:
        """Calculate power analysis for the factorial design.

        Parameters
        ----------
        effect_size : float
            Expected effect size (Cohen's ``f``).
        alpha : float, optional
            Type I error rate. Defaults to 0.05.
        power : float, optional
            Desired statistical power. Defaults to 0.8.

        Returns
        -------
        dict[str, Any]
            Power analysis results.

        Raises
        ------
        ValueError
            If no factors are defined.
        """
        from scipy.stats import f, ncf

        # Degrees of freedom calculation
        if not self.factors:
            raise ValueError("No factors defined")

        df_treatment = np.prod([len(f.levels) for f in self.factors]) - 1
        df_error = (
            np.prod([len(f.levels) for f in self.factors]) * self.replicates
        ) - np.prod([len(f.levels) for f in self.factors])

        # Non-centrality parameter
        n_total = np.prod([len(f.levels) for f in self.factors]) * self.replicates
        lambda_nc = (effect_size**2) * n_total / len(self.factors)

        # Critical F-value
        f_critical = f.ppf(1 - alpha, df_treatment, df_error)

        # Power calculation
        calculated_power = 1 - ncf.cdf(f_critical, df_treatment, df_error, lambda_nc)

        return {
            "effect_size": effect_size,
            "alpha": alpha,
            "target_power": power,
            "calculated_power": calculated_power,
            "df_treatment": df_treatment,
            "df_error": df_error,
            "n_total": n_total,
            "f_critical": f_critical,
            "lambda_nc": lambda_nc,
        }

    def add_star_points(self, alpha: float | None = None) -> pd.DataFrame:
        r"""Add star points to convert to a central composite design.

        Parameters
        ----------
        alpha : float, optional
            Distance of star points from the center. If ``None``, a default of
            :math:`\sqrt{k}` is used where ``k`` is the number of factors.

        Returns
        -------
        pd.DataFrame
            Newly generated star points that were appended to the design matrix.

        Raises
        ------
        ValueError
            If the design matrix has not been generated or factors are not all
            continuous.
        """
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")

        if not all(f.factor_type == "continuous" for f in self.factors):
            raise ValueError("Star points only supported for continuous factors")

        k = len(self.factors)
        if alpha is None:
            alpha = float(np.sqrt(k))

        center = self._calculate_center_points()
        run_id = int(self.design_matrix["RunID"].max()) + 1
        star_rows = []
        for i, factor in enumerate(self.factors):
            span = max(factor.levels) - min(factor.levels)
            for sign in (-1, 1):
                row: Dict[str, Any] = {
                    "RunID": run_id,
                    "Replicate": 1,
                    "DesignPoint": "Star",
                    "StdOrder": run_id,
                }
                for j, other in enumerate(self.factors):
                    if i == j:
                        row[other.name] = center[j] + sign * (alpha * span / 2)
                    else:
                        row[other.name] = center[j]
                star_rows.append(row)
                run_id += 1

        star_df = pd.DataFrame(star_rows)
        self.design_matrix = pd.concat([self.design_matrix, star_df], ignore_index=True)
        return star_df

    def generate_foldover(self) -> pd.DataFrame:
        """Generate a foldover design for de-aliasing effects.

        Returns
        -------
        pd.DataFrame
            Foldover design appended to the current design matrix.

        Raises
        ------
        ValueError
            If the design matrix has not been generated.
        """
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")

        fold_rows = []
        run_id = int(self.design_matrix["RunID"].max()) + 1
        for _, row in self.design_matrix.iterrows():
            new_row = {
                "RunID": run_id,
                "Replicate": row.get("Replicate", 1),
                "DesignPoint": "Foldover",
                "StdOrder": run_id,
            }
            for factor in self.factors:
                levels = factor.levels
                if len(levels) == 2:
                    new_row[factor.name] = (
                        levels[0] if row[factor.name] == levels[1] else levels[1]
                    )
                else:
                    new_row[factor.name] = row[factor.name]
            fold_rows.append(new_row)
            run_id += 1

        fold_df = pd.DataFrame(fold_rows)
        self.design_matrix = pd.concat([self.design_matrix, fold_df], ignore_index=True)
        return fold_df

    def blocking_scheme(self, block_size: int) -> pd.DataFrame:
        """Create a simple blocking scheme column.

        Parameters
        ----------
        block_size : int
            Number of runs per block.

        Returns
        -------
        pd.DataFrame
            Design matrix with an added ``Block`` column.

        Raises
        ------
        ValueError
            If the design matrix has not been generated.
        """
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")

        n_runs = len(self.design_matrix)
        blocks = [i // block_size + 1 for i in range(n_runs)]
        self.design_matrix["Block"] = blocks
        return self.design_matrix

    def confounding_pattern(self) -> Dict[str, List[str]]:
        """Return confounding pattern based on alias correlations.

        Returns
        -------
        dict[str, list[str]]
            Mapping of factor names to aliased terms.
        """
        corr = self.alias_matrix().abs()
        confound: Dict[str, List[str]] = {}
        cols = list(corr.columns)
        for i, c1 in enumerate(cols):
            for j in range(i + 1, len(cols)):
                c2 = cols[j]
                if corr.loc[c1, c2] > 0.99:
                    confound.setdefault(c1, []).append(c2)
        return confound

    def design_generators(self) -> List[str]:
        """Return generator strings for fractional factorial designs.

        Returns
        -------
        list[str]
            Generator expressions or an empty list for full factorials.
        """
        return []

    def alias_matrix(self) -> pd.DataFrame:
        """Calculate alias matrix showing confounding between effects.

        Returns
        -------
        pandas.DataFrame
            Correlation matrix of coded factor columns.

        Raises
        ------
        ValueError
            If the design matrix has not been generated.
        """
        coded = self._get_coded_matrix()
        return coded.corr()
