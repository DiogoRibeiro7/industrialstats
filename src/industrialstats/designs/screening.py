"""Screening designs such as Plackett-Burman and definitive screening."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import hankel, toeplitz

from .base import ExperimentalDesign, Factor


class PlackettBurmanDesign(ExperimentalDesign):
    """Plackett--Burman screening design for two-level factors.

    The implemented Hadamard catalogue contains Sylvester orders and the
    standard 12- and 20-run Plackett--Burman base designs together with all
    powers-of-two doublings of those bases. For ``k`` factors, the constructor
    selects the smallest supported run size ``N`` satisfying ``N > k``.

    Parameters
    ----------
    factors : list of Factor
        Factors to include in the design. Each factor must have two levels.
    randomize : bool, optional
        If ``True``, randomize the run order. Defaults to ``True``.
    seed : int, optional
        Random seed for deterministic run-order shuffling.
    """

    _BASE_ORDERS = (1, 12, 20)

    def __init__(
        self, factors: list[Factor], randomize: bool = True, seed: int | None = None
    ) -> None:
        super().__init__("Plackett-Burman Design")
        self.factors = factors
        self.randomize_flag = randomize
        self.seed = seed

        if len(self.factors) < 2:
            raise ValueError("At least two factors are required")
        if not all(len(f.levels) == 2 for f in self.factors):
            raise ValueError("Plackett-Burman design requires 2-level factors")

    @staticmethod
    def _is_power_of_two(value: int) -> bool:
        """Return whether ``value`` is a positive power of two."""
        return value > 0 and value & (value - 1) == 0

    @classmethod
    def is_supported_run_size(cls, n_runs: int) -> bool:
        """Return whether ``n_runs`` belongs to the implemented PB catalogue."""
        if isinstance(n_runs, bool) or not isinstance(n_runs, int) or n_runs < 4:
            return False
        return any(
            n_runs % base == 0 and cls._is_power_of_two(n_runs // base)
            for base in cls._BASE_ORDERS
        )

    @classmethod
    def supported_run_sizes(cls, max_runs: int) -> tuple[int, ...]:
        """Return implemented Plackett--Burman run sizes up to ``max_runs``."""
        if isinstance(max_runs, bool) or not isinstance(max_runs, int):
            raise ValueError("max_runs must be an integer >= 4")
        if max_runs < 4:
            raise ValueError("max_runs must be >= 4")

        sizes: set[int] = set()
        for base in cls._BASE_ORDERS:
            order = base
            while order < 4:
                order *= 2
            while order <= max_runs:
                sizes.add(order)
                order *= 2
        return tuple(sorted(sizes))

    @classmethod
    def run_size_for_factors(cls, n_factors: int) -> int:
        """Return the smallest implemented run size able to hold ``n_factors``."""
        if isinstance(n_factors, bool) or not isinstance(n_factors, int):
            raise ValueError("n_factors must be an integer >= 2")
        if n_factors < 2:
            raise ValueError("n_factors must be >= 2")

        upper = 4
        while upper <= n_factors:
            upper *= 2
        candidates = cls.supported_run_sizes(upper)
        return min(order for order in candidates if order > n_factors)

    def run_size(self) -> int:
        """Return the number of runs generated for this factor set."""
        return self.run_size_for_factors(len(self.factors))

    def _pb_matrix(self, n_factors: int) -> np.ndarray:
        """Generate a Plackett-Burman matrix using the implemented catalogue."""
        keep = int(n_factors)
        n = self.run_size_for_factors(keep)
        f, e = np.frexp([n, n / 12.0, n / 20.0])
        candidates = [
            idx for idx, val in enumerate(np.logical_and(f == 0.5, e > 0)) if val
        ]
        if not candidates:
            raise ValueError(f"Run size {n} is not in the implemented PB catalogue")
        k = candidates[0]
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
            raise ValueError(f"Run size {n} is not in the implemented PB catalogue")

        for _ in range(e):
            H = np.vstack((np.hstack((H, H)), np.hstack((H, -H))))

        H = H[:, 1 : (keep + 1)]
        return np.flipud(H)

    def generate_design(self) -> pd.DataFrame:
        """Generate the design matrix."""
        design_matrix = self._pb_matrix(len(self.factors))
        df = pd.DataFrame(design_matrix, columns=[f.name for f in self.factors])

        self.design_matrix = df
        if self.randomize_flag:
            self.randomize(seed=self.seed)
        else:
            self.design_matrix.insert(
                0, "RunOrder", range(1, len(self.design_matrix) + 1)
            )
        return self.design_matrix

    def foldover(self) -> pd.DataFrame:
        """Create a foldover design to de-alias main effects.

        Returns
        -------
        pandas.DataFrame
            Foldover design matrix appended to the existing design.
        """
        design_matrix = self.design_matrix
        if design_matrix is None:
            design_matrix = self.generate_design()

        fold_df = design_matrix.copy()
        for col in self.factors:
            fold_df[col.name] = -fold_df[col.name]

        fold_df["RunOrder"] = range(len(design_matrix) + 1, 2 * len(design_matrix) + 1)
        self.design_matrix = pd.concat([design_matrix, fold_df], ignore_index=True)
        return fold_df

    def validate_design(self) -> bool:
        """Validate the design parameters and main-effect orthogonality."""
        if len(self.factors) < 2 or not all(len(f.levels) == 2 for f in self.factors):
            return False
        matrix = self._pb_matrix(len(self.factors)).astype(float)
        cross_product = matrix.T @ matrix
        return np.allclose(cross_product, len(matrix) * np.eye(len(self.factors)))


class DefinitiveScreeningDesign(ExperimentalDesign):
    """Conference-matrix definitive screening design for three-level factors.

    This implementation follows the conference-matrix construction of Xiao,
    Lin, and Bai (2012). It uses the smallest Paley conference order large
    enough for the requested number of factors, takes the required columns,
    appends their foldover, and adds one center run.

    For ``m`` factors, let ``q`` be the smallest supported value, either 1 or
    an odd prime, satisfying ``q + 1 >= m``. The design then has
    ``2 * (q + 1) + 1`` runs. Consequently, designs are minimal ``2m + 1``
    constructions when ``m = q + 1`` and may contain additional runs when a
    larger conference order is required.

    Factor columns are returned in coded levels ``-1, 0, 1``. Three-level
    factors are interpreted as quantitative/continuous for the statistical
    construction even when legacy ``Factor`` metadata leaves ``factor_type``
    at its default value. Mixed continuous/two-level categorical DSDs are not
    yet implemented.

    Parameters
    ----------
    factors : list of Factor
        Factors to include; each must have exactly three levels.
    randomize : bool, optional
        If ``True``, shuffle the run order. Defaults to ``True``.
    seed : int, optional
        Random seed controlling the shuffle.

    References
    ----------
    .. [1] Jones, B., Nachtsheim, C. J. (2011). A Class of Three-Level Designs
       for Definitive Screening in the Presence of Second-Order Effects.
       Journal of Quality Technology, 43(1), 1-15.
    .. [2] Xiao, L., Lin, D. K. J., Bai, F. (2012). Constructing Definitive
       Screening Designs Using Conference Matrices. Journal of Quality
       Technology, 44(1), 2-8.
    """

    def __init__(
        self, factors: list[Factor], randomize: bool = True, seed: int | None = None
    ) -> None:
        super().__init__("Definitive Screening Design")
        self.factors = factors
        self.randomize_flag = randomize
        self.seed = seed

        if len(self.factors) < 2:
            raise ValueError("At least two factors are required")
        if not all(len(f.levels) == 3 for f in self.factors):
            raise ValueError("Definitive screening requires 3-level factors")

    @staticmethod
    def _is_prime(value: int) -> bool:
        """Return whether ``value`` is prime."""
        if value < 2:
            return False
        if value == 2:
            return True
        if value % 2 == 0:
            return False
        return all(value % divisor != 0 for divisor in range(3, int(value**0.5) + 1, 2))

    @classmethod
    def _conference_prime(cls, n_factors: int) -> int:
        """Return the smallest supported Paley parameter fitting the factors."""
        if n_factors <= 2:
            return 1

        candidate = n_factors - 1
        if candidate % 2 == 0:
            candidate += 1
        while not cls._is_prime(candidate):
            candidate += 2
        return candidate

    @staticmethod
    def _paley_conference_matrix(prime: int) -> np.ndarray:
        """Construct a Paley conference matrix of order ``prime + 1``.

        The returned matrix ``C`` has zero diagonal, off-diagonal entries in
        ``{-1, 1}``, and satisfies ``C.T @ C = prime * I``. ``prime = 1`` is
        the two-factor base case.
        """
        if prime == 1:
            return np.array([[0, 1], [1, 0]], dtype=int)

        quadratic_residues = {(value * value) % prime for value in range(1, prime)}
        character = np.zeros(prime, dtype=int)
        for value in range(1, prime):
            character[value] = 1 if value in quadratic_residues else -1

        core = np.array(
            [
                [character[(column - row) % prime] for column in range(prime)]
                for row in range(prime)
            ],
            dtype=int,
        )

        order = prime + 1
        conference = np.zeros((order, order), dtype=int)
        conference[0, 1:] = 1
        conference[1:, 0] = 1 if prime % 4 == 1 else -1
        conference[1:, 1:] = core
        return conference

    @classmethod
    def _coded_matrix(cls, n_factors: int) -> np.ndarray:
        """Construct the coded DSD matrix before run-order annotation."""
        prime = cls._conference_prime(n_factors)
        conference = cls._paley_conference_matrix(prime)
        selected = conference[:, :n_factors]
        center = np.zeros((1, n_factors), dtype=int)
        return np.vstack((selected, -selected, center))

    def generate_design(self) -> pd.DataFrame:
        """Generate the coded definitive screening design matrix."""
        coded = self._coded_matrix(len(self.factors))
        df = pd.DataFrame(coded, columns=[factor.name for factor in self.factors])

        self.design_matrix = df
        if self.randomize_flag:
            self.randomize(seed=self.seed)
        else:
            self.design_matrix.insert(
                0, "RunOrder", range(1, len(self.design_matrix) + 1)
            )
        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate both inputs and defining algebraic DSD properties."""
        if len(self.factors) < 2:
            return False
        if not all(len(f.levels) == 3 for f in self.factors):
            return False

        coded = self._coded_matrix(len(self.factors)).astype(float)
        n_runs, n_factors = coded.shape

        # Linear main effects are mutually orthogonal.
        cross_product = coded.T @ coded
        diagonal = np.diag(np.diag(cross_product))
        if not np.allclose(cross_product, diagonal):
            return False

        # Foldover symmetry makes linear effects orthogonal to pure quadratics.
        quadratics = coded**2
        if not np.allclose(coded.T @ quadratics, 0.0):
            return False

        # Main effects must be orthogonal to every two-factor interaction.
        interactions = np.column_stack(
            [
                coded[:, left] * coded[:, right]
                for left in range(n_factors)
                for right in range(left + 1, n_factors)
            ]
        )
        if interactions.size and not np.allclose(coded.T @ interactions, 0.0):
            return False

        # Intercept + all linear + all pure quadratic terms are estimable.
        second_order_main_model = np.column_stack((np.ones(n_runs), coded, quadratics))
        return np.linalg.matrix_rank(second_order_main_model) == 1 + 2 * n_factors
