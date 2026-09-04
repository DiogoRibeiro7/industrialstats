"""Optimal experimental designs using algorithmic approaches."""

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


class OptimalDesign(ExperimentalDesign):
    """
    Generate optimal experimental designs using exchange algorithms.

    Supports D-optimal, A-optimal, G-optimal, and I-optimal criteria.
    """

    def __init__(
        self,
        factors: list[Factor],
        n_runs: int,
        criterion: str = "D",
        model_terms: list[str] | None = None,
    ) -> None:
        """Initialize optimal design.

        Parameters
        ----------
        factors : list[Factor]
            Experimental factors.
        n_runs : int
            Number of experimental runs.
        criterion : str, optional
            Optimality criterion (``"D"``, ``"A"``, ``"G"``, or ``"I"``). Defaults to ``"D"``.
        model_terms : list[str], optional
            Model terms to include. Defaults to main effects and interactions.
        """
        super().__init__(f"{criterion}-Optimal Design")

        if criterion not in ["D", "A", "G", "I"]:
            raise ValueError("criterion must be 'D', 'A', 'G', or 'I'")

        if n_runs < len(factors) + 1:
            raise ValueError("n_runs must be greater than number of factors")

        self.factors = factors
        self.n_runs = n_runs
        self.criterion = criterion
        self.model_terms = model_terms or self._default_model_terms()
        self.candidate_set: pd.DataFrame | None = None
        self.candidate_model_matrix: np.ndarray | None = None
        self.exchange_history: list[dict[str, Any]] = []

    def _default_model_terms(self) -> list[str]:
        """Generate default model terms (main effects + two-factor interactions)."""
        terms = ["Intercept"]

        # Main effects
        for factor in self.factors:
            terms.append(factor.name)

        # Two-factor interactions
        for i, factor1 in enumerate(self.factors):
            for factor2 in self.factors[i + 1 :]:
                terms.append(f"{factor1.name}*{factor2.name}")

        return terms

    def generate_candidate_set(self, grid_density: int = 5) -> pd.DataFrame:
        """Generate candidate set of all possible design points.

        Parameters
        ----------
        grid_density : int, optional
            Number of levels for continuous factors. Defaults to ``5``.

        Returns
        -------
        pd.DataFrame
            Candidate set of design points.
        """
        candidate_points = []

        # Generate levels for each factor
        factor_levels = []
        for factor in self.factors:
            if factor.factor_type == "categorical":
                factor_levels.append(factor.levels)
            else:
                # Create grid for continuous factors
                min_val = min(factor.levels)
                max_val = max(factor.levels)
                levels = np.linspace(min_val, max_val, grid_density)
                factor_levels.append(levels.tolist())

        # Generate all combinations
        from itertools import product

        for i, combination in enumerate(product(*factor_levels)):
            point = {"CandidateID": i + 1}
            for j, factor in enumerate(self.factors):
                point[factor.name] = combination[j]
            candidate_points.append(point)

        self.candidate_set = pd.DataFrame(candidate_points)
        return self.candidate_set

    def generate_design(
        self,
        max_iterations: int = 1000,
        random_start: bool = True,
        n_random_starts: int = 5,
        improvement_threshold: float = 1e-6,
    ) -> pd.DataFrame:
        """Generate optimal design using coordinate exchange algorithm.

        Parameters
        ----------
        max_iterations : int, optional
            Maximum number of exchange iterations. Defaults to ``1000``.
        random_start : bool, optional
            Whether to use random starting design. Defaults to ``True``.
        n_random_starts : int, optional
            Number of random starts to try. Defaults to ``5``.
        improvement_threshold : float, optional
            Minimum improvement in the criterion required to continue
            iterations. Defaults to ``1e-6``.

        Returns
        -------
        pd.DataFrame
            Optimal design matrix.
        """
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        if self.candidate_set is None:
            self.generate_candidate_set()
        # Precompute candidate model matrix for faster evaluation
        self.candidate_model_matrix = self._build_model_matrix(self.candidate_set)

        best_design = None
        best_criterion_value = float("-inf")

        # Try multiple random starts
        for _start in range(n_random_starts):
            design = self._coordinate_exchange(
                max_iterations, random_start, improvement_threshold
            )
            criterion_value = self._calculate_criterion(design)

            if self._is_better_criterion(criterion_value, best_criterion_value):
                best_design = design.copy()
                best_criterion_value = criterion_value

        self.design_matrix = best_design
        return self.design_matrix

    def _coordinate_exchange(
        self, max_iterations: int, random_start: bool, improvement_threshold: float
    ) -> pd.DataFrame:
        """Perform coordinate exchange algorithm.

        Parameters
        ----------
        max_iterations : int
            Maximum number of exchange iterations.
        random_start : bool
            Whether to use a random starting design.
        improvement_threshold : float
            Minimum improvement required to continue iterating.

        Returns
        -------
        pd.DataFrame
            Optimized design matrix.
        """
        if random_start:
            current_design = self._random_initial_design()
        else:
            current_design = self._systematic_initial_design()

        current_X = self._build_model_matrix(current_design)
        XtX = current_X.T @ current_X
        self._validate_nonsingular(XtX)
        current_criterion = self._criterion_from_xtx(XtX)

        for iteration in range(max_iterations):
            prev_criterion = current_criterion
            improved = False

            for run_idx in range(self.n_runs):
                x_current = current_X[run_idx]
                best_value = current_criterion
                best_candidate_idx: int | None = None

                for cand_idx in self.candidate_set.index:
                    x_cand = self.candidate_model_matrix[cand_idx]
                    new_XtX = (
                        XtX - np.outer(x_current, x_current) + np.outer(x_cand, x_cand)
                    )
                    if self._is_singular(new_XtX):
                        continue
                    trial_criterion = self._criterion_from_xtx(new_XtX)
                    if self._is_better_criterion(trial_criterion, best_value):
                        best_value = trial_criterion
                        best_candidate_idx = cand_idx

                if best_candidate_idx is not None:
                    candidate = self.candidate_set.iloc[best_candidate_idx]
                    for factor in self.factors:
                        current_design.loc[run_idx, factor.name] = candidate[
                            factor.name
                        ]
                    XtX = (
                        XtX
                        - np.outer(x_current, x_current)
                        + np.outer(
                            self.candidate_model_matrix[best_candidate_idx],
                            self.candidate_model_matrix[best_candidate_idx],
                        )
                    )
                    current_X[run_idx] = self.candidate_model_matrix[best_candidate_idx]
                    current_criterion = best_value
                    improved = True

            improvement = current_criterion - prev_criterion
            self.exchange_history.append(
                {
                    "iteration": iteration,
                    "criterion_value": current_criterion,
                    "improvement": improvement,
                }
            )
            if not improved or improvement < improvement_threshold:
                break

        if self._is_singular(XtX):
            raise ValueError("Singular design matrix encountered")

        return current_design

    def _random_initial_design(self) -> pd.DataFrame:
        """Generate random initial design."""
        rng = np.random.default_rng()

        design_points = []
        for run in range(self.n_runs):
            candidate_idx = rng.integers(0, len(self.candidate_set))
            candidate = self.candidate_set.iloc[candidate_idx]

            point = {"RunID": run + 1}
            for factor in self.factors:
                point[factor.name] = candidate[factor.name]
            design_points.append(point)

        return pd.DataFrame(design_points)

    def _systematic_initial_design(self) -> pd.DataFrame:
        """Generate systematic initial design (space-filling)."""
        design_points = []

        # Use evenly spaced points from candidate set
        indices = np.linspace(0, len(self.candidate_set) - 1, self.n_runs, dtype=int)

        for i, run in enumerate(range(self.n_runs)):
            candidate = self.candidate_set.iloc[indices[i]]

            point = {"RunID": run + 1}
            for factor in self.factors:
                point[factor.name] = candidate[factor.name]
            design_points.append(point)

        return pd.DataFrame(design_points)

    def _calculate_criterion(self, design: pd.DataFrame) -> float:
        """Calculate optimality criterion value."""
        X = self._build_model_matrix(design)
        XtX = X.T @ X
        return self._criterion_from_xtx(XtX)

    def _criterion_from_xtx(self, XtX: np.ndarray) -> float:
        """Compute criterion value from information matrix."""
        try:
            if self.criterion == "D":
                sign, logdet = np.linalg.slogdet(XtX)
                return logdet if sign > 0 else float("-inf")

            XtX_inv = np.linalg.inv(XtX)

            if self.criterion == "A":
                return -np.trace(XtX_inv)

            variances = np.einsum(
                "ij,jk,ik->i",
                self.candidate_model_matrix,
                XtX_inv,
                self.candidate_model_matrix,
            )
            if self.criterion == "G":
                return -float(np.max(variances))
            if self.criterion == "I":
                return -float(np.mean(variances))

        except np.linalg.LinAlgError:
            return float("-inf")

    def _is_singular(self, XtX: np.ndarray) -> bool:
        """Check if information matrix is singular."""
        return np.linalg.matrix_rank(XtX) < XtX.shape[0]

    def _validate_nonsingular(self, XtX: np.ndarray) -> None:
        """Validate that the information matrix is non-singular."""
        if self._is_singular(XtX):
            raise ValueError("Singular design matrix encountered")

    def _build_model_matrix(self, design: pd.DataFrame) -> np.ndarray:
        """Build model matrix X from design."""
        n_runs = len(design)
        n_terms = len(self.model_terms)
        X = np.zeros((n_runs, n_terms))

        for i, run in design.iterrows():
            for j, term in enumerate(self.model_terms):
                X[i, j] = self._evaluate_term(term, run)

        return X

    def _build_point_vector(self, point: pd.Series) -> np.ndarray:
        """Build model vector for a single point."""
        x = np.zeros(len(self.model_terms))

        for j, term in enumerate(self.model_terms):
            x[j] = self._evaluate_term(term, point)

        return x

    def _evaluate_term(self, term: str, point: pd.Series) -> float:
        """Evaluate model term at a point."""
        if term == "Intercept":
            return 1.0

        if "*" in term:
            # Interaction term
            factors = term.split("*")
            value = 1.0
            for factor_name in factors:
                factor_value = point[factor_name]

                # Convert to coded value if continuous
                factor_obj = next(f for f in self.factors if f.name == factor_name)
                if factor_obj.factor_type == "continuous":
                    # Code as -1/+1
                    min_val = min(factor_obj.levels)
                    max_val = max(factor_obj.levels)
                    coded_value = 2 * (factor_value - min_val) / (max_val - min_val) - 1
                    value *= coded_value
                else:
                    # Categorical: use 0/1 coding
                    value *= 1.0 if factor_value == factor_obj.levels[-1] else 0.0

            return value

        # Main effect
        factor_obj = next(f for f in self.factors if f.name == term)
        factor_value = point[term]

        if factor_obj.factor_type == "continuous":
            # Code as -1/+1
            min_val = min(factor_obj.levels)
            max_val = max(factor_obj.levels)
            return 2 * (factor_value - min_val) / (max_val - min_val) - 1
        # Categorical: use 0/1 coding
        return 1.0 if factor_value == factor_obj.levels[-1] else 0.0

    def _is_better_criterion(self, new_value: float, current_value: float) -> bool:
        """Check if new criterion value is better than current."""
        if self.criterion in ["D", "A", "I"]:
            return new_value > current_value  # Maximize (or minimize negative)
        # G-optimal
        return new_value > current_value  # Maximize (minimize negative)

    def validate_design(self) -> bool:
        """Validate optimal design parameters."""
        if len(self.factors) == 0:
            return False

        if self.n_runs < len(self.model_terms):
            return False

        return self.criterion in ["D", "A", "G", "I"]

    def design_efficiency(
        self, reference_design: pd.DataFrame | None = None
    ) -> dict[str, float]:
        """Calculate design efficiency metrics.

        Parameters
        ----------
        reference_design : pd.DataFrame, optional
            Reference design for comparison. Defaults to an orthogonal design.

        Returns
        -------
        dict[str, float]
            Efficiency metrics.
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")

        # Calculate current design criterion
        current_X = self._build_model_matrix(self.design_matrix)
        current_XtX = current_X.T @ current_X

        efficiencies = {}

        try:
            if self.criterion == "D":
                current_det = np.linalg.det(current_XtX)

                # D-efficiency relative to orthogonal design
                p = len(self.model_terms)
                max_det = (self.n_runs / p) ** p  # Theoretical maximum
                efficiencies["D_efficiency"] = (current_det / max_det) ** (1 / p)

            elif self.criterion == "A":
                current_trace = np.trace(np.linalg.inv(current_XtX))

                # A-efficiency (simplified)
                p = len(self.model_terms)
                min_trace = p / self.n_runs  # Theoretical minimum
                efficiencies["A_efficiency"] = min_trace / current_trace

            # Relative efficiency compared to reference design
            if reference_design is not None:
                ref_X = self._build_model_matrix(reference_design)
                ref_XtX = ref_X.T @ ref_X

                if self.criterion == "D":
                    ref_det = np.linalg.det(ref_XtX)
                    efficiencies["Relative_D_efficiency"] = (current_det / ref_det) ** (
                        1 / p
                    )

                elif self.criterion == "A":
                    ref_trace = np.trace(np.linalg.inv(ref_XtX))
                    efficiencies["Relative_A_efficiency"] = ref_trace / current_trace

        except np.linalg.LinAlgError:
            efficiencies["Error"] = "Singular information matrix"

        return efficiencies

    def prediction_variance_map(
        self, factor1: str, factor2: str, grid_size: int = 20
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate prediction variance map for two factors.

        Parameters
        ----------
        factor1 : str
            First factor name.
        factor2 : str
            Second factor name.
        grid_size : int, optional
            Grid resolution. Defaults to ``20``.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            X, Y, Z arrays for contour plotting.
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")

        # Get factor objects
        factor1_obj = next(f for f in self.factors if f.name == factor1)
        factor2_obj = next(f for f in self.factors if f.name == factor2)

        # Create grid
        if factor1_obj.factor_type == "continuous":
            x_range = np.linspace(
                min(factor1_obj.levels), max(factor1_obj.levels), grid_size
            )
        else:
            x_range = factor1_obj.levels

        if factor2_obj.factor_type == "continuous":
            y_range = np.linspace(
                min(factor2_obj.levels), max(factor2_obj.levels), grid_size
            )
        else:
            y_range = factor2_obj.levels

        X, Y = np.meshgrid(x_range, y_range)
        Z = np.zeros_like(X)

        # Calculate information matrix
        design_X = self._build_model_matrix(self.design_matrix)
        XtX_inv = np.linalg.inv(design_X.T @ design_X)

        # Calculate prediction variance at each grid point
        for i in range(len(y_range)):
            for j in range(len(x_range)):
                # Create point with other factors at center
                point_data = {}
                for factor in self.factors:
                    if factor.name == factor1:
                        point_data[factor.name] = X[i, j]
                    elif factor.name == factor2:
                        point_data[factor.name] = Y[i, j]
                    else:
                        # Set other factors to center
                        if factor.factor_type == "continuous":
                            center = (min(factor.levels) + max(factor.levels)) / 2
                            point_data[factor.name] = center
                        else:
                            point_data[factor.name] = factor.levels[0]  # First level

                point = pd.Series(point_data)
                x_point = self._build_point_vector(point)
                variance = x_point.T @ XtX_inv @ x_point
                Z[i, j] = variance

        return X, Y, Z

    def augment_design(
        self, additional_runs: int, current_data: pd.DataFrame | None = None
    ) -> pd.DataFrame:
        """Augment existing design with additional runs.

        Parameters
        ----------
        additional_runs : int
            Number of additional runs to add.
        current_data : pd.DataFrame, optional
            Current experimental data. If ``None``, uses the generated design.

        Returns
        -------
        pd.DataFrame
            Augmented design.
        """
        if current_data is None:
            if self.design_matrix is None:
                raise ValueError("No current design available")
            current_data = self.design_matrix.copy()

        if self.candidate_set is None:
            self.generate_candidate_set()

        # Start with current design
        augmented_design = current_data.copy()
        current_n_runs = len(current_data)

        # Add runs one by one using exchange algorithm
        for new_run in range(additional_runs):
            best_addition = None
            best_criterion = (
                float("-inf") if self.criterion in ["D", "A"] else float("inf")
            )

            # Try each candidate point
            for _, candidate in self.candidate_set.iterrows():
                # Create trial design with new point
                trial_design = augmented_design.copy()
                new_point = {"RunID": current_n_runs + new_run + 1}
                for factor in self.factors:
                    new_point[factor.name] = candidate[factor.name]

                trial_design = pd.concat(
                    [trial_design, pd.DataFrame([new_point])], ignore_index=True
                )

                # Calculate criterion
                criterion_value = self._calculate_criterion(trial_design)

                if self._is_better_criterion(criterion_value, best_criterion):
                    best_addition = new_point
                    best_criterion = criterion_value

            # Add best point
            if best_addition is not None:
                augmented_design = pd.concat(
                    [augmented_design, pd.DataFrame([best_addition])], ignore_index=True
                )

        return augmented_design

    def design_diagnostics(self) -> dict[str, Any]:
        """Calculate design diagnostics and properties.

        Returns
        -------
        dict[str, Any]
            Diagnostic metrics for the current design.

        Raises
        ------
        ValueError
            If the design has not been generated.
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")

        diagnostics = {}

        # Basic properties
        diagnostics["n_runs"] = len(self.design_matrix)
        diagnostics["n_factors"] = len(self.factors)
        diagnostics["n_model_terms"] = len(self.model_terms)
        diagnostics["criterion"] = self.criterion

        # Model matrix properties
        X = self._build_model_matrix(self.design_matrix)
        XtX = X.T @ X

        try:
            # Condition number
            eigenvalues = np.linalg.eigvals(XtX)
            condition_number = np.max(eigenvalues) / np.min(eigenvalues)
            diagnostics["condition_number"] = condition_number

            # Determinant
            diagnostics["determinant"] = np.linalg.det(XtX)

            # Trace
            diagnostics["trace"] = np.trace(XtX)

            # Minimum eigenvalue
            diagnostics["min_eigenvalue"] = np.min(eigenvalues)

            # Design criterion value
            diagnostics["criterion_value"] = self._calculate_criterion(
                self.design_matrix
            )

            # Correlation matrix
            correlation_matrix = np.corrcoef(X.T)
            diagnostics["max_correlation"] = np.max(
                np.abs(correlation_matrix - np.eye(len(self.model_terms)))
            )

        except np.linalg.LinAlgError:
            diagnostics["error"] = "Singular information matrix"

        # Exchange algorithm convergence
        if self.exchange_history:
            diagnostics["exchange_iterations"] = len(self.exchange_history)
            diagnostics["final_improvement"] = self.exchange_history[-1]["improved"]

            # Convergence plot data
            criterion_values = [h["criterion_value"] for h in self.exchange_history]
            diagnostics["convergence_history"] = criterion_values

        return diagnostics


class CustomOptimalDesign(OptimalDesign):
    """
    Custom optimal design with user-defined criterion function.
    """

    def __init__(
        self,
        factors: list[Factor],
        n_runs: int,
        criterion_function: Callable[[np.ndarray], float],
        criterion_name: str = "Custom",
    ) -> None:
        """Initialize custom optimal design.

        Parameters
        ----------
        factors : list[Factor]
            Experimental factors.
        n_runs : int
            Number of experimental runs.
        criterion_function : Callable[[np.ndarray], float]
            Function that takes the model matrix ``X`` and returns a criterion value.
        criterion_name : str, optional
            Name for the custom criterion. Defaults to ``"Custom"``.
        """
        super().__init__(factors, n_runs, criterion="D")  # Dummy criterion
        self.name = f"{criterion_name}-Optimal Design"
        self.criterion_function = criterion_function
        self.criterion_name = criterion_name

    def _calculate_criterion(self, design: pd.DataFrame) -> float:
        """Calculate custom criterion value."""
        X = self._build_model_matrix(design)
        return self.criterion_function(X)
