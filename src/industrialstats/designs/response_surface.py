"""Response surface methodology (RSM) designs.

This module implements the :class:`ResponseSurfaceDesign` class for constructing
central composite and Box–Behnken designs used in process optimization.
"""

from collections.abc import Callable, Iterable, Sequence
from itertools import product
from typing import Any

import numpy as np
import pandas as pd
from scipy import optimize, stats

from .base import ExperimentalDesign, Factor


class ResponseSurfaceDesign(ExperimentalDesign):
    """Response surface design for optimization studies.

    Parameters
    ----------
    factors : list[Factor]
        Continuous factors (must be 2-level for coding).
    design_type : str, optional
        ``"CCD"`` for Central Composite or ``"BBD"`` for Box-Behnken. Defaults
        to ``"CCD"``.
    alpha : float, optional
        Alpha value for axial points (CCD only). If ``None``, calculated for
        rotatability.
    center_points : int, optional
        Number of center point replicates. Defaults to ``5``.

    Examples
    --------
    Generate a Box-Behnken design with three factors and one center point::

        >>> factors = [
        ...     Factor("A", [-1, 1]),
        ...     Factor("B", [-1, 1]),
        ...     Factor("C", [-1, 1]),
        ... ]
        >>> design = ResponseSurfaceDesign(factors, design_type="BBD", center_points=1)
        >>> design.generate_design().shape[0]
        13
    """

    def __init__(
        self,
        factors: list[Factor],
        design_type: str = "CCD",
        alpha: float | None = None,
        center_points: int = 5,
    ) -> None:
        """Initialize response surface design.

        Parameters
        ----------
        factors : list[Factor]
            Continuous factors (must be 2-level for coding).
        design_type : str, optional
            ``"CCD"`` for Central Composite or ``"BBD"`` for Box-Behnken. Defaults to ``"CCD"``.
        alpha : float, optional
            Alpha value for axial points (CCD only). If ``None``, calculated for rotatability.
        center_points : int, optional
            Number of center point replicates. Defaults to ``5``.
        """
        super().__init__(f"{design_type} Response Surface Design")

        if design_type not in ["CCD", "BBD"]:
            raise ValueError("design_type must be 'CCD' or 'BBD'")

        # Validate factors for RSM
        for factor in factors:
            if factor.factor_type != "continuous":
                raise ValueError(
                    "Response surface designs require continuous factors only"
                )
            if len(factor.levels) != 2:
                raise ValueError("Factors must have exactly 2 levels for coding")

        self.factors = factors
        self.design_type = design_type
        self.center_points = center_points
        self.alpha = alpha

        if center_points < 1:
            raise ValueError("Must have at least 1 center point")

    def generate_design(self) -> pd.DataFrame:
        """Generate response surface design matrix."""
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        if self.design_type == "CCD":
            return self._generate_ccd()
        if self.design_type == "BBD":
            return self._generate_bbd()
        return None

    def _generate_ccd(self) -> pd.DataFrame:
        """Generate Central Composite Design."""
        k = len(self.factors)  # Number of factors

        # Calculate alpha for rotatability if not specified
        if self.alpha is None:
            self.alpha = (2**k) ** (1 / 4)  # Fourth root of 2^k

        design_points = []
        run_id = 1

        # 1. Factorial points (2^k)
        factorial_levels = [[-1, 1] for _ in range(k)]
        factorial_combinations = list(product(*factorial_levels))

        for combo in factorial_combinations:
            point = {
                "RunID": run_id,
                "DesignPoint": "Factorial",
                "PointType": "Factorial",
            }
            for i, factor in enumerate(self.factors):
                point[factor.name] = combo[i]
            design_points.append(point)
            run_id += 1

        # 2. Axial points (2k)
        for i in range(k):
            # Positive axial point
            point_pos = {"RunID": run_id, "DesignPoint": "Axial", "PointType": "Axial"}
            for j, factor in enumerate(self.factors):
                point_pos[factor.name] = self.alpha if i == j else 0
            design_points.append(point_pos)
            run_id += 1

            # Negative axial point
            point_neg = {"RunID": run_id, "DesignPoint": "Axial", "PointType": "Axial"}
            for j, factor in enumerate(self.factors):
                point_neg[factor.name] = -self.alpha if i == j else 0
            design_points.append(point_neg)
            run_id += 1

        # 3. Center points
        for _cp in range(self.center_points):
            point = {"RunID": run_id, "DesignPoint": "Center", "PointType": "Center"}
            for factor in self.factors:
                point[factor.name] = 0  # Coded center
            design_points.append(point)
            run_id += 1

        # Convert to DataFrame
        self.design_matrix = pd.DataFrame(design_points)

        # Convert from coded to actual levels
        self._convert_to_actual_levels()

        return self.design_matrix

    def _generate_bbd(self) -> pd.DataFrame:
        """Generate a Box-Behnken design.

        Returns
        -------
        pandas.DataFrame
            Design matrix with factors in actual levels.

        Raises
        ------
        ValueError
            If the design cannot be verified as orthogonal.
        """
        k = len(self.factors)

        if k < 3:
            raise ValueError("Box-Behnken design requires at least 3 factors")

        design_points = []
        run_id = 1

        # Box-Behnken points: each pair of factors at ±1, others at 0
        for i in range(k):
            for j in range(i + 1, k):
                for level_i in [-1, 1]:
                    for level_j in [-1, 1]:
                        point = {
                            "RunID": run_id,
                            "DesignPoint": "BoxBehnken",
                            "PointType": "BoxBehnken",
                        }
                        for idx, factor in enumerate(self.factors):
                            if idx == i:
                                point[factor.name] = level_i
                            elif idx == j:
                                point[factor.name] = level_j
                            else:
                                point[factor.name] = 0
                        design_points.append(point)
                        run_id += 1

        # Center points
        for _cp in range(self.center_points):
            point = {"RunID": run_id, "DesignPoint": "Center", "PointType": "Center"}
            for factor in self.factors:
                point[factor.name] = 0
            design_points.append(point)
            run_id += 1

        design_df = pd.DataFrame(design_points)

        # Verify orthogonality in coded units
        coded = design_df[[factor.name for factor in self.factors]].to_numpy()
        xtx = coded.T @ coded
        off_diag = xtx - np.diag(np.diag(xtx))
        if not np.allclose(off_diag, 0):
            raise ValueError("Generated Box-Behnken design is not orthogonal")

        self.design_matrix = design_df
        self._convert_to_actual_levels()
        return self.design_matrix

    def _convert_to_actual_levels(self):
        """Convert coded levels (-1, 0, +1, ±α) to actual factor levels."""
        for factor in self.factors:
            coded_values = self.design_matrix[factor.name].values

            # Calculate center and range
            low_level = factor.levels[0]
            high_level = factor.levels[1]
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2

            # Convert coded to actual
            actual_values = center + coded_values * half_range
            self.design_matrix[factor.name] = actual_values

    def validate_design(self) -> bool:
        """Validate response surface design parameters."""
        if len(self.factors) < 2:
            return False

        if self.design_type == "BBD" and len(self.factors) < 3:
            return False

        for factor in self.factors:
            if factor.factor_type != "continuous":
                return False
            if len(factor.levels) != 2:
                return False

        return not self.center_points < 1

    def n_runs(self) -> int:
        """Calculate total number of runs."""
        k = len(self.factors)

        if self.design_type == "CCD":
            factorial_runs = 2**k
            axial_runs = 2 * k
            return factorial_runs + axial_runs + self.center_points
        if self.design_type == "BBD":
            # Box-Behnken: 2 * k * (k-1) + center points
            bbd_runs = 2 * k * (k - 1)
            return bbd_runs + self.center_points
        return None

    def design_properties(self) -> dict[str, Any]:
        """Calculate design properties (rotatability, orthogonality, etc.)."""
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")

        k = len(self.factors)
        properties = {}

        # Basic properties
        properties["n_factors"] = k
        properties["n_runs"] = len(self.design_matrix)
        properties["design_type"] = self.design_type

        if self.design_type == "CCD":
            properties["alpha"] = self.alpha
            properties["rotatable"] = abs(self.alpha - (2**k) ** (1 / 4)) < 0.001

            # Efficiency calculations
            factorial_runs = 2**k
            axial_runs = 2 * k
            center_runs = self.center_points

            properties["factorial_fraction"] = factorial_runs / self.n_runs()
            properties["axial_fraction"] = axial_runs / self.n_runs()
            properties["center_fraction"] = center_runs / self.n_runs()

        elif self.design_type == "BBD":
            coded = self._get_design_matrix_coded()
            xtx = coded.T @ coded
            off_diag = xtx - np.diag(np.diag(xtx))
            properties["orthogonal"] = bool(np.allclose(off_diag, 0))
            properties["rotatable"] = False  # Box-Behnken is not rotatable

        return properties

    def prediction_variance(self, prediction_points: list[list[float]]) -> np.ndarray:
        """Calculate prediction variance at specified points.

        Parameters
        ----------
        prediction_points : list[list[float]]
            Points in coded units where prediction variance is calculated.

        Returns
        -------
        np.ndarray
            Prediction variances.
        """
        if self.design_matrix is None:
            raise ValueError("Design not generated yet")

        # Convert design matrix to coded units for calculation
        X_coded = self._get_design_matrix_coded()

        # Add intercept column
        X_coded = np.column_stack([np.ones(len(X_coded)), X_coded])

        # Add quadratic terms
        k = len(self.factors)
        for i in range(k):
            X_coded = np.column_stack([X_coded, X_coded[:, i + 1] ** 2])

        # Add interaction terms
        for i in range(k):
            for j in range(i + 1, k):
                X_coded = np.column_stack(
                    [X_coded, X_coded[:, i + 1] * X_coded[:, j + 1]]
                )

        # Calculate (X'X)^-1
        XtX_inv = np.linalg.inv(X_coded.T @ X_coded)

        # Calculate prediction variance for each point
        variances = []
        for point in prediction_points:
            # Create expanded point vector
            x_point = [1.0]  # intercept
            x_point.extend(point)  # linear terms
            x_point.extend([xi**2 for xi in point])  # quadratic terms

            # interaction terms
            for i in range(len(point)):
                for j in range(i + 1, len(point)):
                    x_point.append(point[i] * point[j])

            x_point = np.array(x_point)
            variance = x_point.T @ XtX_inv @ x_point
            variances.append(variance)

        return np.array(variances)

    def _get_design_matrix_coded(self) -> np.ndarray:
        """Get design matrix in coded units."""
        coded_matrix = np.zeros((len(self.design_matrix), len(self.factors)))

        for i, factor in enumerate(self.factors):
            actual_values = self.design_matrix[factor.name].values

            # Calculate coding parameters
            low_level = factor.levels[0]
            high_level = factor.levels[1]
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2

            # Convert to coded
            coded_matrix[:, i] = (actual_values - center) / half_range

        return coded_matrix

    def response_surface_analysis(self, response_data: list[float]) -> dict[str, Any]:
        """Fit response surface model and analyze results.

        Parameters
        ----------
        response_data : list[float]
            Response values for each design point.

        Returns
        -------
        dict[str, Any]
            Analysis results including coefficients, model fit, and optimum.
        """
        if len(response_data) != len(self.design_matrix):
            raise ValueError("Response data length must match design matrix")

        # Get coded design matrix
        X_coded = self._get_design_matrix_coded()
        k = len(self.factors)

        # Build full quadratic model matrix
        # Intercept
        X_model = np.ones((len(X_coded), 1))
        term_names = ["Intercept"]

        # Linear terms
        X_model = np.column_stack([X_model, X_coded])
        term_names.extend([f.name for f in self.factors])

        # Quadratic terms
        for i, factor in enumerate(self.factors):
            X_model = np.column_stack([X_model, X_coded[:, i] ** 2])
            term_names.append(f"{factor.name}²")

        # Interaction terms
        for i in range(k):
            for j in range(i + 1, k):
                X_model = np.column_stack([X_model, X_coded[:, i] * X_coded[:, j]])
                term_names.append(f"{self.factors[i].name}*{self.factors[j].name}")

        # Fit model using least squares
        y = np.array(response_data)

        try:
            # Calculate coefficients
            XtX_inv = np.linalg.inv(X_model.T @ X_model)
            coefficients = XtX_inv @ X_model.T @ y

            # Calculate fitted values and residuals
            y_fitted = X_model @ coefficients
            residuals = y - y_fitted

            # Calculate R-squared
            ss_total = np.sum((y - np.mean(y)) ** 2)
            ss_residual = np.sum(residuals**2)
            r_squared = 1 - (ss_residual / ss_total)

            # Adjusted R-squared
            n = len(y)
            p = len(coefficients) - 1  # excluding intercept
            adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p - 1)

            # Standard errors
            mse = ss_residual / (n - len(coefficients))
            std_errors = np.sqrt(np.diag(XtX_inv) * mse)

            # t-statistics and p-values
            t_stats = coefficients / std_errors
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - len(coefficients)))

            # Find optimum (coded units)
            optimum_coded = self._find_optimum_coded(coefficients, term_names)

            # Convert optimum to actual units
            optimum_actual = {}
            if optimum_coded is not None:
                for i, factor in enumerate(self.factors):
                    low_level = factor.levels[0]
                    high_level = factor.levels[1]
                    center = (low_level + high_level) / 2
                    half_range = (high_level - low_level) / 2

                    actual_value = center + optimum_coded[i] * half_range
                    optimum_actual[factor.name] = actual_value

            # Prepare results
            results = {
                "coefficients": dict(zip(term_names, coefficients, strict=True)),
                "std_errors": dict(zip(term_names, std_errors, strict=True)),
                "t_statistics": dict(zip(term_names, t_stats, strict=True)),
                "p_values": dict(zip(term_names, p_values, strict=True)),
                "r_squared": r_squared,
                "adj_r_squared": adj_r_squared,
                "rmse": np.sqrt(mse),
                "fitted_values": y_fitted,
                "residuals": residuals,
                "optimum_coded": optimum_coded,
                "optimum_actual": optimum_actual,
                "information_matrix_inv": XtX_inv,
                "degrees_of_freedom": n - len(coefficients),
                "mse": mse,
            }

            return results

        except np.linalg.LinAlgError as e:
            raise ValueError("Unable to fit model - design matrix is singular") from e

    def _find_optimum_coded(
        self, coefficients: np.ndarray, term_names: list[str]
    ) -> np.ndarray | None:
        """Find stationary point (optimum) in coded units."""
        k = len(self.factors)

        # Extract linear coefficients (b vector)
        b = coefficients[1 : k + 1]

        # Extract quadratic coefficients (B matrix)
        B = np.zeros((k, k))

        # Diagonal elements (pure quadratic terms)
        for i in range(k):
            quad_term = f"{self.factors[i].name}²"
            if quad_term in term_names:
                idx = term_names.index(quad_term)
                B[i, i] = coefficients[idx]

        # Off-diagonal elements (interaction terms)
        for i in range(k):
            for j in range(i + 1, k):
                interaction_term = f"{self.factors[i].name}*{self.factors[j].name}"
                if interaction_term in term_names:
                    idx = term_names.index(interaction_term)
                    B[i, j] = B[j, i] = (
                        coefficients[idx] / 2
                    )  # Divide by 2 for symmetric matrix

        # Find stationary point: x_s = -0.5 * B^(-1) * b
        try:
            x_stationary = -0.5 * np.linalg.inv(B) @ b

            # Check if stationary point is within reasonable bounds
            if np.all(np.abs(x_stationary) <= 3):  # Within ±3 coded units
                return x_stationary
            return None  # Optimum outside reasonable region

        except np.linalg.LinAlgError:
            return None  # Singular matrix

    def _actual_to_coded_vector(self, actual: Iterable[float]) -> np.ndarray:
        """Convert an iterable of actual factor levels to coded coordinates."""

        coded = np.zeros(len(self.factors), dtype=float)
        for i, (value, factor) in enumerate(zip(actual, self.factors, strict=True)):
            low_level, high_level = factor.levels
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2
            if half_range == 0:
                raise ValueError(
                    f"Factor '{factor.name}' has identical levels; cannot code values."
                )
            coded[i] = (value - center) / half_range
        return coded

    def _coded_to_actual_vector(self, coded: Iterable[float]) -> np.ndarray:
        """Convert an iterable of coded coordinates to actual factor levels."""

        actual = np.zeros(len(self.factors), dtype=float)
        for i, (value, factor) in enumerate(zip(coded, self.factors, strict=True)):
            low_level, high_level = factor.levels
            center = (low_level + high_level) / 2
            half_range = (high_level - low_level) / 2
            actual[i] = center + value * half_range
        return actual

    def _quadratic_components(
        self, coefficient_map: dict[str, float]
    ) -> tuple[float, np.ndarray, np.ndarray]:
        """Extract intercept, linear vector, and Hessian matrix for the surface."""

        k = len(self.factors)
        intercept = float(coefficient_map.get("Intercept", 0.0))
        b = np.zeros(k, dtype=float)
        B = np.zeros((k, k), dtype=float)

        for i, factor in enumerate(self.factors):
            b[i] = float(coefficient_map.get(factor.name, 0.0))
            B[i, i] = float(coefficient_map.get(f"{factor.name}²", 0.0))

        for i in range(k):
            for j in range(i + 1, k):
                interaction = float(
                    coefficient_map.get(
                        f"{self.factors[i].name}*{self.factors[j].name}", 0.0
                    )
                )
                if interaction:
                    B[i, j] = B[j, i] = interaction / 2

        return intercept, b, B

    def _evaluate_quadratic(
        self, coefficient_map: dict[str, float], coded_point: np.ndarray
    ) -> float:
        """Evaluate the quadratic response model at a coded point."""

        intercept, b, B = self._quadratic_components(coefficient_map)
        return float(intercept + coded_point @ b + coded_point.T @ B @ coded_point)

    def _quadratic_plotter(self, coefficient_map: dict[str, float]):
        """Create a ResponseSurfacePlotter backed by the quadratic coefficients."""

        class _QuadraticPredictor:
            def __init__(
                self, design: "ResponseSurfaceDesign", coefs: dict[str, float]
            ):
                self.design = design
                self.coefs = coefs

            def predict(self, frame: pd.DataFrame) -> pd.Series:
                coded = np.vstack(
                    [
                        self.design._actual_to_coded_vector(
                            frame.loc[idx, self.design.factor_names].to_numpy()
                        )
                        for idx in frame.index
                    ]
                )
                values = [
                    self.design._evaluate_quadratic(self.coefs, coded[i])
                    for i in range(coded.shape[0])
                ]
                return pd.Series(values, index=frame.index)

        from industrialstats.visualizations.response_surface_plots import (
            ResponseSurfacePlotter,
        )

        return ResponseSurfacePlotter(self, _QuadraticPredictor(self, coefficient_map))

    def steepest_ascent(
        self,
        model_results: dict[str, Any],
        start_point: dict[str, float] | None = None,
        step_length: float = 0.5,
        n_steps: int = 10,
        direction: str = "ascent",
        visualize: bool = False,
        plot_factors: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """Compute the steepest ascent/descent path for the fitted surface.

        This routine follows the gradient-based approach described by Box and
        Draper [1]_ to generate an ordered sequence of points in the direction of
        the largest increase (or decrease) in the response. Steps are taken in
        coded units and converted back to actual factor levels for reporting.

        Parameters
        ----------
        model_results
            Output from :meth:`response_surface_analysis`
            containing the fitted coefficients.
        start_point
            Starting location in actual units. If omitted, the
            design centre is used.
        step_length
            Length of each step in coded units once the gradient
            direction is normalised. Defaults to ``0.5``.
        n_steps
            Number of steps to compute along the path. Defaults to
            ``10``.
        direction
            Direction of movement relative to the gradient. Defaults
            to ``"ascent"``.
        visualize
            Whether to return a contour plot overlay. Defaults to
            ``False``.
        plot_factors
            Pair of factor names to use on the contour plot. When
            ``None`` the first two factors are used.

        Returns
        -------
        Dict[str, Any]
            Dictionary with keys ``"path"`` (DataFrame of coded
            and actual points) and ``"figure"`` (Plotly figure when
            ``visualize`` is ``True``).

        Raises
        ------
        ValueError
            If an invalid direction is provided or the gradient is
            zero.

        Examples
        --------
        >>> factors = [Factor("x1", [-1, 1]), Factor("x2", [-1, 1])]
        >>> design = ResponseSurfaceDesign(factors)
        >>> dm = design.generate_design()
        >>> y = dm["x1"] * -2 + dm["x2"]
        >>> results = design.response_surface_analysis(y.tolist())
        >>> path = design.steepest_ascent(results, n_steps=3)
        >>> list(path["path"]["Step"])
        [0, 1, 2, 3]

        References
        ----------
        Box, G. E. P., & Draper, N. R. (2007). *Response Surfaces, Mixtures,
        and Ridge Analyses* (2nd ed.). Wiley.
        """

        if direction not in {"ascent", "descent"}:
            raise ValueError("direction must be 'ascent' or 'descent'")

        coefficient_map = model_results.get("coefficients")
        if coefficient_map is None:
            raise ValueError("model_results must include 'coefficients'")

        _, b, _ = self._quadratic_components(coefficient_map)
        gradient = b if direction == "ascent" else -b

        norm = float(np.linalg.norm(gradient))
        if norm == 0:
            raise ValueError("Gradient is zero; steepest path is undefined")

        unit_direction = gradient / norm

        if start_point is None:
            coded_start = np.zeros(len(self.factors))
        else:
            missing = set(self.factor_names).difference(start_point)
            if missing:
                missing_str = ", ".join(sorted(missing))
                raise ValueError(
                    f"start_point is missing levels for factors: {missing_str}"
                )
            ordered_actual = [start_point[f.name] for f in self.factors]
            coded_start = self._actual_to_coded_vector(ordered_actual)

        coded_points = [coded_start.copy()]
        for step in range(1, n_steps + 1):
            coded_points.append(coded_start + step_length * step * unit_direction)

        actual_points = [self._coded_to_actual_vector(point) for point in coded_points]
        responses = [
            self._evaluate_quadratic(coefficient_map, point) for point in coded_points
        ]

        index_lookup = {name: idx for idx, name in enumerate(self.factor_names)}

        data = {
            "Step": list(range(len(coded_points))),
            **{
                f"coded_{factor.name}": [point[i] for point in coded_points]
                for i, factor in enumerate(self.factors)
            },
            **{
                factor.name: [point[i] for point in actual_points]
                for i, factor in enumerate(self.factors)
            },
            "predicted_response": responses,
        }
        path_df = pd.DataFrame(data)

        figure = None
        if visualize:
            chosen = (
                plot_factors
                if plot_factors is not None
                else (self.factors[0].name, self.factors[1].name)
            )
            plotter = self._quadratic_plotter(coefficient_map)
            path_points = [
                (point[index_lookup[chosen[0]]], point[index_lookup[chosen[1]]])
                for point in actual_points
            ]
            figure = plotter.contour_plot(chosen[0], chosen[1], path=path_points)

        return {"path": path_df, "figure": figure}

    def ridge_analysis(
        self,
        model_results: dict[str, Any],
        radii: Sequence[float],
        constraints: Sequence[Callable[[np.ndarray], float]] | None = None,
        penalty_weight: float = 100.0,
        visualize: bool = False,
        plot_factors: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """Perform ridge analysis for constrained optimisation.

        Ridge analysis seeks the best point on a hypersphere of radius ``r`` in
        coded units by solving the Lagrangian system ``(B + λI) x = -0.5 b`` for
        each candidate radius [1]_. Optional inequality constraints ``g_i(x) ≤ 0``
        are enforced through quadratic penalties to discourage infeasible
        solutions.

        Parameters
        ----------
        model_results : dict[str, Any]
            Output from :meth:`response_surface_analysis` containing the fitted
            coefficients.
        radii : sequence of float
            Radii in coded units at which to evaluate the ridge solution.
        constraints : sequence of callable, optional
            Functions mapping a coded point to a real value. Positive values are
            treated as violations and penalised. Defaults to ``None``.
        penalty_weight : float, optional
            Penalty scaling factor applied to squared constraint violations.
            Defaults to ``100.0``.
        visualize : bool, optional
            When ``True`` returns a contour plot of the first two factors with the
            ridge path overlay. Defaults to ``False``.
        plot_factors : tuple[str, str], optional
            Factor names to use for the visualisation. Defaults to the first two
            factors.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the ridge solutions (``"solutions"`` DataFrame)
            and ``"figure"`` with the optional Plotly contour.

        References
        ----------
        .. [1] Box, G. E. P., & Draper, N. R. (2007). *Response Surfaces,
           Mixtures, and Ridge Analyses* (2nd ed.). Wiley.
        """

        coefficient_map = model_results.get("coefficients")
        if coefficient_map is None:
            raise ValueError("model_results must include 'coefficients'")

        intercept, b, B = self._quadratic_components(coefficient_map)
        k = len(self.factors)
        identity = np.eye(k)
        penalties = constraints or []

        def _solve_radius(radius: float) -> tuple[np.ndarray, float, float]:
            def norm_difference(lmbda: float) -> float:
                matrix = B + lmbda * identity
                solution = np.linalg.solve(matrix, -0.5 * b)
                return float(solution @ solution - radius**2)

            # Identify a bracket for the root of norm_difference.
            bracket = None
            candidates = np.linspace(-50.0, 50.0, 400)
            previous_value = None
            previous_lambda = None
            for lmbda in candidates:
                try:
                    value = norm_difference(lmbda)
                except np.linalg.LinAlgError:
                    previous_value = None
                    previous_lambda = None
                    continue
                if previous_value is not None and value * previous_value <= 0:
                    bracket = (previous_lambda, lmbda)
                    break
                previous_value = value
                previous_lambda = lmbda

            if bracket is None:
                # Fall back to the best candidate if no sign change is found.
                feasible_values = []
                for lmbda in candidates:
                    try:
                        difference = abs(norm_difference(lmbda))
                        feasible_values.append((difference, lmbda))
                    except np.linalg.LinAlgError:
                        continue
                if not feasible_values:
                    raise ValueError(
                        "Unable to bracket Lagrange multiplier for ridge analysis"
                    )
                lmbda = min(feasible_values, key=lambda item: item[0])[1]
            else:
                lmbda = optimize.brentq(norm_difference, *bracket, maxiter=200)

            solution = np.linalg.solve(B + lmbda * identity, -0.5 * b)
            response = intercept + solution @ b + solution.T @ B @ solution
            penalty = 0.0
            if penalties:
                for constraint in penalties:
                    violation = float(constraint(solution))
                    penalty += penalty_weight * max(0.0, violation) ** 2
            return solution, response, penalty

        coded_solutions = []
        responses = []
        penalties_applied = []
        for radius in radii:
            if radius <= 0:
                raise ValueError("radii must contain positive values")
            point, response, penalty = _solve_radius(radius)
            coded_solutions.append(point)
            responses.append(response)
            penalties_applied.append(penalty)

        actual_points = [
            self._coded_to_actual_vector(point) for point in coded_solutions
        ]

        results_df = pd.DataFrame(
            {
                "radius": list(radii),
                "objective": responses,
                "penalty": penalties_applied,
                **{
                    f"coded_{factor.name}": [point[i] for point in coded_solutions]
                    for i, factor in enumerate(self.factors)
                },
                **{
                    factor.name: [point[i] for point in actual_points]
                    for i, factor in enumerate(self.factors)
                },
            }
        )

        figure = None
        if visualize:
            chosen = (
                plot_factors
                if plot_factors is not None
                else (self.factors[0].name, self.factors[1].name)
            )
            index_lookup = {name: idx for idx, name in enumerate(self.factor_names)}
            plotter = self._quadratic_plotter(coefficient_map)
            path_points = [
                (point[index_lookup[chosen[0]]], point[index_lookup[chosen[1]]])
                for point in actual_points
            ]
            figure = plotter.contour_plot(chosen[0], chosen[1], path=path_points)

        return {"solutions": results_df, "figure": figure}

    def canonical_analysis(self, model_results: dict[str, Any]) -> dict[str, Any]:
        """Carry out canonical analysis of the fitted response surface.

        Canonical analysis diagonalises the quadratic form to reveal the surface
        curvature and nature of the stationary point (minimum, maximum, saddle,
        or ridge) following Box and Draper [1]_. Eigenvectors define the
        canonical directions while eigenvalues quantify curvature along each
        axis.

        Parameters
        ----------
        model_results : dict[str, Any]
            Output from :meth:`response_surface_analysis` containing model
            coefficients and residual degrees of freedom.

        Returns
        -------
        dict[str, Any]
            Summary including the stationary point in coded and actual units,
            eigenvalues/eigenvectors, surface classification, and 95 % confidence
            ellipsoid axes for the optimum when degrees of freedom are available.

        References
        ----------
        .. [1] Box, G. E. P., & Draper, N. R. (2007). *Response Surfaces,
           Mixtures, and Ridge Analyses* (2nd ed.). Wiley.
        """

        coefficient_map = model_results.get("coefficients")
        if coefficient_map is None:
            raise ValueError("model_results must include 'coefficients'")

        intercept, b, B = self._quadratic_components(coefficient_map)
        try:
            stationary_coded = -0.5 * np.linalg.solve(B, b)
        except np.linalg.LinAlgError:
            stationary_coded = None

        stationary_actual = (
            self._coded_to_actual_vector(stationary_coded)
            if stationary_coded is not None
            else None
        )

        eigenvalues, eigenvectors = np.linalg.eigh(B)

        if np.all(eigenvalues > 0):
            surface_type = "minimum"
        elif np.all(eigenvalues < 0):
            surface_type = "maximum"
        elif np.any(np.isclose(eigenvalues, 0)):
            surface_type = "ridge"
        else:
            surface_type = "saddle"

        df_resid = model_results.get("degrees_of_freedom")
        confidence = None
        if df_resid is not None and df_resid > 0:
            k = len(self.factors)
            f_value = stats.f.ppf(0.95, k, df_resid)
            axes = []
            for value in eigenvalues:
                if np.isclose(value, 0):
                    axes.append(np.inf)
                else:
                    axes.append(float(np.sqrt(f_value / abs(value))))
            confidence = {
                "alpha": 0.95,
                "axes": axes,
                "eigenvectors": eigenvectors,
            }

        stationary_response = None
        if stationary_coded is not None:
            stationary_response = self._evaluate_quadratic(
                coefficient_map, stationary_coded
            )

        return {
            "intercept": intercept,
            "stationary_point_coded": stationary_coded,
            "stationary_point_actual": stationary_actual,
            "stationary_response": stationary_response,
            "eigenvalues": eigenvalues,
            "eigenvectors": eigenvectors,
            "surface_type": surface_type,
            "confidence_region": confidence,
        }

    def multiple_response_optimization(
        self,
        response_models: dict[str, dict[str, Any]],
        weights: dict[str, float] | None = None,
        desirability_functions: dict[str, Callable[[float], float]] | None = None,
        constraint_functions: Sequence[Callable[[np.ndarray], float]] | None = None,
        grid_resolution: int = 25,
        search_radius: float = 1.5,
        penalty_weight: float = 50.0,
        weight_perturbation: float = 0.15,
    ) -> dict[str, Any]:
        """Simultaneously optimise multiple responses.

        The optimisation proceeds by evaluating fitted response models on a
        lattice in the coded factor space, computing desirability functions for
        each response, and aggregating them using weighted geometric means. A
        Pareto frontier of feasible points is additionally identified, and
        weight sensitivity analysis perturbs the supplied weights to study
        robustness.

        Parameters
        ----------
        response_models : dict[str, dict[str, Any]]
            Mapping from response name to model results produced by
            :meth:`response_surface_analysis`. Each entry may include a
            ``"goal"`` field (``"max"`` or ``"min"``).
        weights : dict[str, float], optional
            Importance weights for each response. If omitted, equal weights are
            assigned.
        desirability_functions : dict[str, callable], optional
            Custom desirability functions mapping response values to ``[0, 1]``.
            Defaults to piecewise-linear ramps based on the response range.
        constraint_functions : sequence of callable, optional
            Inequality constraints ``g_i(x)`` evaluated in coded space. Positive
            values are penalised quadratically.
        grid_resolution : int, optional
            Number of grid points per factor in the coded space. Defaults to
            ``25``.
        search_radius : float, optional
            Extent of the coded search space (``[-radius, radius]`` per factor).
            Defaults to ``1.5``.
        penalty_weight : float, optional
            Penalty multiplier for constraint violations. Defaults to ``50.0``.
        weight_perturbation : float, optional
            Relative perturbation applied to weights during the sensitivity
            analysis. Defaults to ``0.15``.

        Returns
        -------
        dict[str, Any]
            Dictionary containing the best compromise solution, Pareto frontier,
            and weight sensitivity study.

        References
        ----------
        .. [1] Box, G. E. P., & Draper, N. R. (2007). *Response Surfaces,
           Mixtures, and Ridge Analyses* (2nd ed.). Wiley.
        """

        if not response_models:
            raise ValueError("response_models must not be empty")

        desirability_functions = desirability_functions or {}
        response_names = list(response_models)

        if weights is None:
            weights = dict.fromkeys(response_names, 1.0)
        missing_weights = set(response_names).difference(weights)
        if missing_weights:
            for name in missing_weights:
                weights[name] = 1.0

        weight_sum = float(sum(weights.values()))
        if weight_sum <= 0:
            raise ValueError("weights must sum to a positive value")
        normalised_weights = {k: v / weight_sum for k, v in weights.items()}

        axes = [
            np.linspace(-search_radius, search_radius, grid_resolution)
            for _ in self.factors
        ]
        grid_points = np.array(list(product(*axes)))

        predictions: dict[str, np.ndarray] = {}
        goals: dict[str, str] = {}
        for name, result in response_models.items():
            coeffs = result.get("coefficients")
            if coeffs is None:
                raise ValueError(
                    f"response model '{name}' must include 'coefficients' from response_surface_analysis"
                )
            goals[name] = result.get("goal", "max").lower()
            preds = np.array(
                [self._evaluate_quadratic(coeffs, point) for point in grid_points]
            )
            if goals[name] not in {"max", "min"}:
                raise ValueError("goal must be 'max' or 'min'")
            predictions[name] = preds

        desirabilities: dict[str, np.ndarray] = {}
        for name in response_names:
            if name in desirability_functions:
                func = desirability_functions[name]
                desirabilities[name] = np.array(
                    [func(value) for value in predictions[name]]
                )
            else:
                values = predictions[name]
                v_min = float(np.min(values))
                v_max = float(np.max(values))
                if np.isclose(v_max, v_min):
                    desirabilities[name] = np.ones_like(values)
                else:
                    if goals[name] == "max":
                        desirabilities[name] = np.clip(
                            (values - v_min) / (v_max - v_min), 0.0, 1.0
                        )
                    else:
                        desirabilities[name] = np.clip(
                            (v_max - values) / (v_max - v_min), 0.0, 1.0
                        )

        penalties = np.zeros(len(grid_points), dtype=float)
        if constraint_functions:
            for idx, point in enumerate(grid_points):
                violation = 0.0
                for constraint in constraint_functions:
                    violation_value = float(constraint(point))
                    violation += max(0.0, violation_value) ** 2
                penalties[idx] = penalty_weight * violation

        def combined_desirability(weight_map: dict[str, float]) -> np.ndarray:
            overall = np.ones(len(grid_points), dtype=float)
            for name in response_names:
                overall *= desirabilities[name] ** weight_map[name]
            return overall

        base_scores = combined_desirability(normalised_weights) - penalties
        best_index = int(np.argmax(base_scores))

        best_coded = grid_points[best_index]
        best_actual = self._coded_to_actual_vector(best_coded)
        best_predictions = {
            name: predictions[name][best_index] for name in response_names
        }
        best_desirabilities = {
            name: desirabilities[name][best_index] for name in response_names
        }

        feasible_indices = (
            np.where(penalties <= 1e-8)[0]
            if constraint_functions
            else np.arange(len(grid_points))
        )
        pareto_indices: list[int] = []
        if feasible_indices.size > 0:
            signed = []
            for name in response_names:
                if goals[name] == "max":
                    signed.append(predictions[name][feasible_indices])
                else:
                    signed.append(-predictions[name][feasible_indices])
            signed_matrix = np.column_stack(signed)
            for idx, candidate in enumerate(signed_matrix):
                dominated = False
                for other_idx, other in enumerate(signed_matrix):
                    if other_idx == idx:
                        continue
                    if np.all(other >= candidate) and np.any(other > candidate):
                        dominated = True
                        break
                if not dominated:
                    pareto_indices.append(int(feasible_indices[idx]))

        pareto_points = []
        for idx in pareto_indices:
            coded = grid_points[idx]
            actual = self._coded_to_actual_vector(coded)
            pareto_points.append(
                {
                    "coded": coded,
                    "actual": actual,
                    "responses": {
                        name: predictions[name][idx] for name in response_names
                    },
                }
            )

        def _weight_analysis(new_weights: dict[str, float]) -> dict[str, Any]:
            total = float(sum(new_weights.values()))
            if total <= 0:
                return {"weights": new_weights, "best_index": None}
            norm = {k: v / total for k, v in new_weights.items()}
            scores = combined_desirability(norm) - penalties
            idx = int(np.argmax(scores))
            return {
                "weights": norm,
                "coded_point": grid_points[idx],
                "actual_point": self._coded_to_actual_vector(grid_points[idx]),
                "responses": {name: predictions[name][idx] for name in response_names},
                "overall_desirability": float(scores[idx]),
            }

        sensitivity: list[dict[str, Any]] = []
        for name in response_names:
            base = dict(weights)
            base[name] *= 1 + weight_perturbation
            sensitivity.append(_weight_analysis(base))
            base = dict(weights)
            base[name] *= max(1 - weight_perturbation, 0)
            sensitivity.append(_weight_analysis(base))

        grid_df = pd.DataFrame(
            {
                **{
                    f"coded_{factor.name}": grid_points[:, idx]
                    for idx, factor in enumerate(self.factors)
                },
                **{f"pred_{name}": predictions[name] for name in response_names},
                "overall_desirability": combined_desirability(normalised_weights),
                "penalty": penalties,
            }
        )

        return {
            "optimum": {
                "coded": best_coded,
                "actual": best_actual,
                "responses": best_predictions,
                "desirabilities": best_desirabilities,
                "overall_desirability": float(base_scores[best_index]),
            },
            "pareto_frontier": pareto_points,
            "weight_sensitivity": sensitivity,
            "grid": grid_df,
        }

    def contour_data(
        self,
        coefficients: dict[str, float],
        factor1: str,
        factor2: str,
        grid_size: int = 20,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate contour plot data for two factors.

        Parameters
        ----------
        coefficients : dict[str, float]
            Model coefficients from :func:`response_surface_analysis`.
        factor1 : str
            Name of the first factor for the plot.
        factor2 : str
            Name of the second factor for the plot.
        grid_size : int, optional
            Grid resolution. Defaults to ``20``.

        Returns
        -------
        tuple[np.ndarray, np.ndarray, np.ndarray]
            ``X``, ``Y``, ``Z`` arrays for contour plotting.
        """
        # Find factor indices
        factor1_idx = next(i for i, f in enumerate(self.factors) if f.name == factor1)
        factor2_idx = next(i for i, f in enumerate(self.factors) if f.name == factor2)

        # Create grid in coded units
        x_coded = np.linspace(-2, 2, grid_size)
        y_coded = np.linspace(-2, 2, grid_size)
        X_coded, Y_coded = np.meshgrid(x_coded, y_coded)

        # Calculate response surface
        Z = np.zeros_like(X_coded)

        for i in range(grid_size):
            for j in range(grid_size):
                # Set other factors to center (0)
                point = np.zeros(len(self.factors))
                point[factor1_idx] = X_coded[i, j]
                point[factor2_idx] = Y_coded[i, j]

                # Calculate response using model
                response = coefficients["Intercept"]

                # Linear terms
                for k, factor in enumerate(self.factors):
                    response += coefficients.get(factor.name, 0) * point[k]

                # Quadratic terms
                for k, factor in enumerate(self.factors):
                    response += coefficients.get(f"{factor.name}²", 0) * point[k] ** 2

                # Interaction terms
                for k in range(len(self.factors)):
                    for m in range(k + 1, len(self.factors)):
                        interaction_coef = coefficients.get(
                            f"{self.factors[k].name}*{self.factors[m].name}", 0
                        )
                        response += interaction_coef * point[k] * point[m]

                Z[i, j] = response

        # Convert grid to actual units
        factor1_obj = next(f for f in self.factors if f.name == factor1)
        factor2_obj = next(f for f in self.factors if f.name == factor2)

        # Factor 1 conversion
        center1 = (factor1_obj.levels[0] + factor1_obj.levels[1]) / 2
        range1 = (factor1_obj.levels[1] - factor1_obj.levels[0]) / 2
        X_actual = center1 + X_coded * range1

        # Factor 2 conversion
        center2 = (factor2_obj.levels[0] + factor2_obj.levels[1]) / 2
        range2 = (factor2_obj.levels[1] - factor2_obj.levels[0]) / 2
        Y_actual = center2 + Y_coded * range2

        return X_actual, Y_actual, Z
