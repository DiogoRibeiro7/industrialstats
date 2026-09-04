"""Completely Randomized Design (CRD) implementation."""

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


class CompletelyRandomizedDesign(ExperimentalDesign):
    """
    Completely Randomized Design (CRD).

    This is the simplest experimental design where treatments are randomly
    assigned to experimental units without any restrictions or blocking.
    """

    def __init__(
        self,
        treatments: list[str],
        replicates: int,
        seed: int | None = None,
        response_variables: list[str] | None = None,
    ) -> None:
        """Initialize CRD.

        Parameters
        ----------
        treatments : list of str
            Names of treatment levels.
        replicates : int
            Number of replicates per treatment.
        seed : int, optional
            Random seed for reproducible run ordering.
        response_variables : list of str, optional
            Names of response variables measured in the experiment.
        """
        super().__init__("Completely Randomized Design")

        if len(treatments) < 2:
            raise ValueError("Must have at least 2 treatments")
        if replicates < 1:
            raise ValueError("Must have at least 1 replicate")

        # Copy the caller's list so a later mutation cannot desynchronise
        # the design from the factor levels derived from it.
        self.treatments = list(treatments)
        self.replicates = replicates
        self.seed = seed
        self.response_variables = response_variables or []

        # Create a single factor with treatment levels
        treatment_levels: list[str | float | int] = list(self.treatments)
        treatment_factor = Factor("Treatment", treatment_levels, "categorical")
        self.factors = [treatment_factor]

    def generate_design(self) -> pd.DataFrame:
        """Generate the CRD design matrix.

        Returns
        -------
        pandas.DataFrame
            Design matrix with randomized run order.
        """
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        # Create all treatment-replicate combinations
        design_data = []
        run_id = 1

        for rep in range(1, self.replicates + 1):
            for treatment in self.treatments:
                design_data.append(
                    {"RunID": run_id, "Treatment": treatment, "Replicate": rep}
                )
                run_id += 1

        self.design_matrix = pd.DataFrame(design_data)

        # Always randomize CRD (that's the point!)
        self.randomize(seed=self.seed)

        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate CRD parameters."""
        if len(self.treatments) < 2:
            return False
        if self.replicates < 1:
            return False
        if not all(isinstance(r, str) for r in self.response_variables):
            return False
        return len(self.response_variables) == len(set(self.response_variables))

    def n_runs(self) -> int:
        """Calculate total number of runs."""
        return len(self.treatments) * self.replicates

    def degrees_of_freedom(self) -> dict[str, int]:
        """Calculate degrees of freedom for CRD analysis."""
        n_treatments = len(self.treatments)
        total_runs = self.n_runs()

        return {
            "Treatment": n_treatments - 1,
            "Error": total_runs - n_treatments,
            "Total": total_runs - 1,
        }

    def expected_mean_squares(self) -> dict[str, str]:
        """Return expected mean squares for CRD."""
        return {"Treatment": "σ² + r·σ²ₜ", "Error": "σ²"}

    def efficiency_vs_rcbd(self, block_variance: float, error_variance: float) -> float:
        """Calculate relative efficiency compared to RCBD.

        Parameters
        ----------
        block_variance : float
            Estimated variance between blocks.
        error_variance : float
            Estimated experimental error variance.

        Returns
        -------
        float
            Relative efficiency (> 1 means CRD is more efficient).
        """
        # Relative efficiency = (RCBD error MS) / (CRD error MS)
        rcbd_error_ms = error_variance
        crd_error_ms = error_variance + block_variance

        return crd_error_ms / rcbd_error_ms

    def sample_size_calculation(
        self, effect_size: float, alpha: float = 0.05, power: float = 0.8
    ) -> int:
        """Calculate required sample size per treatment.

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
        int
            Required number of replicates per treatment.
        """

        from scipy.stats import f

        k = len(self.treatments)  # Number of treatments

        # Degrees of freedom
        df1 = k - 1

        # Non-centrality parameter for desired power
        from scipy.stats import ncf

        # Iterative search for required sample size
        for n_per_group in range(2, 1000):
            df2 = k * (n_per_group - 1)
            lambda_nc = effect_size**2 * n_per_group * k

            f_crit = f.ppf(1 - alpha, df1, df2)
            calculated_power = 1 - ncf.cdf(f_crit, df1, df2, lambda_nc)

            if calculated_power >= power:
                return n_per_group

        return -1  # Could not find required sample size

    def create_data_collection_sheet(
        self, response_variables: list[str] | None = None
    ) -> pd.DataFrame:
        """Create a data collection sheet for the experiment.

        Parameters
        ----------
        response_variables : list of str, optional
            Names of response variables to include. Defaults to the design's
            stored ``response_variables`` or ``["Response"]`` if none were
            specified.

        Returns
        -------
        pandas.DataFrame
            Data collection sheet with empty response columns.
        """
        design_matrix = self.design_matrix
        if design_matrix is None:
            design_matrix = self.generate_design()

        data_sheet = design_matrix.copy()

        responses = response_variables or self.response_variables or ["Response"]

        for response in responses:
            data_sheet[response] = np.nan

        # Add columns for data collection
        data_sheet["Date"] = ""
        data_sheet["Time"] = ""
        data_sheet["Observer"] = ""
        data_sheet["Notes"] = ""

        return data_sheet

    def _validate_response_data(
        self, data: pd.DataFrame, response_columns: list[str]
    ) -> None:
        """Validate response data prior to analysis.

        Parameters
        ----------
        data : pandas.DataFrame
            Experimental data containing response measurements.
        response_columns : list of str
            Names of response columns to validate.

        Raises
        ------
        ValueError
            If a response column is missing or contains NaNs.
        TypeError
            If a response column is non-numeric.
        """
        for col in response_columns:
            if col not in data.columns:
                raise ValueError(f"Response column '{col}' not found in data")
            if data[col].isna().any():
                raise ValueError(f"Missing values detected in column '{col}'")
            if not pd.api.types.is_numeric_dtype(data[col]):
                raise TypeError(f"Response column '{col}' must be numeric")

    def summary_statistics(
        self, data: pd.DataFrame, response_columns: list[str]
    ) -> dict[str, pd.DataFrame]:
        """Calculate summary statistics for multiple responses.

        Parameters
        ----------
        data : pandas.DataFrame
            Experimental data with results.
        response_columns : list of str
            Names of response variable columns to analyze.

        Returns
        -------
        dict of pandas.DataFrame
            Mapping of response names to summary statistics by treatment.
        """
        self._validate_response_data(data, response_columns)

        summaries: dict[str, pd.DataFrame] = {}
        from scipy.stats import t

        for column in response_columns:
            summary = (
                data.groupby("Treatment")[column]
                .agg(["count", "mean", "std", "min", "max", "median"])
                .round(3)
            )

            ci_lower: list[float] = []
            ci_upper: list[float] = []

            for treatment in summary.index:
                treatment_data = data[data["Treatment"] == treatment][column]
                n = len(treatment_data)
                mean = treatment_data.mean()
                std = treatment_data.std()

                t_critical = t.ppf(0.975, n - 1)
                margin_error = t_critical * std / np.sqrt(n)

                ci_lower.append(mean - margin_error)
                ci_upper.append(mean + margin_error)

            summary["CI_Lower"] = np.round(ci_lower, 3)
            summary["CI_Upper"] = np.round(ci_upper, 3)

            summaries[column] = summary

        return summaries
