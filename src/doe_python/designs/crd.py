"""Completely Randomized Design (CRD) implementation."""

from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from .base import ExperimentalDesign, Factor


class CompletelyRandomizedDesign(ExperimentalDesign):
    """
    Completely Randomized Design (CRD).

    This is the simplest experimental design where treatments are randomly
    assigned to experimental units without any restrictions or blocking.
    """

    def __init__(self, treatments: List[str], replicates: int):
        """Initialize CRD.

        Args:
            treatments (List[str]): List of treatment names or levels.
            replicates (int): Number of replicates per treatment.
        """
        super().__init__("Completely Randomized Design")

        if len(treatments) < 2:
            raise ValueError("Must have at least 2 treatments")
        if replicates < 1:
            raise ValueError("Must have at least 1 replicate")

        self.treatments = treatments
        self.replicates = replicates

        # Create a single factor with treatment levels
        treatment_factor = Factor("Treatment", treatments, "categorical")
        self.factors = [treatment_factor]

    def generate_design(self) -> pd.DataFrame:
        """Generate CRD matrix."""
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
        self.randomize()

        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate CRD parameters."""
        if len(self.treatments) < 2:
            return False
        if self.replicates < 1:
            return False
        return True

    def n_runs(self) -> int:
        """Calculate total number of runs."""
        return len(self.treatments) * self.replicates

    def degrees_of_freedom(self) -> Dict[str, int]:
        """Calculate degrees of freedom for CRD analysis."""
        n_treatments = len(self.treatments)
        total_runs = self.n_runs()

        return {
            "Treatment": n_treatments - 1,
            "Error": total_runs - n_treatments,
            "Total": total_runs - 1,
        }

    def expected_mean_squares(self) -> Dict[str, str]:
        """Return expected mean squares for CRD."""
        return {"Treatment": "σ² + r·σ²ₜ", "Error": "σ²"}

    def efficiency_vs_rcbd(self, block_variance: float, error_variance: float) -> float:
        """Calculate relative efficiency compared to RCBD.

        Args:
            block_variance (float): Estimated variance between blocks.
            error_variance (float): Estimated experimental error variance.

        Returns:
            float: Relative efficiency (> 1 means CRD is more efficient).
        """
        # Relative efficiency = (RCBD error MS) / (CRD error MS)
        rcbd_error_ms = error_variance
        crd_error_ms = error_variance + block_variance

        return crd_error_ms / rcbd_error_ms

    def sample_size_calculation(
        self, effect_size: float, alpha: float = 0.05, power: float = 0.8
    ) -> int:
        """Calculate required sample size per treatment.

        Args:
            effect_size (float): Expected effect size (Cohen's f).
            alpha (float, optional): Type I error rate. Defaults to ``0.05``.
            power (float, optional): Desired statistical power. Defaults to ``0.8``.

        Returns:
            int: Required number of replicates per treatment.
        """
        from scipy.stats import f
        import math

        k = len(self.treatments)  # Number of treatments

        # Degrees of freedom
        df1 = k - 1

        # Critical F-value (approximate for sample size calculation)
        f_critical = f.ppf(1 - alpha, df1, 100)  # Using large df2 for approximation

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
        self, response_variables: List[str] | None = None
    ) -> pd.DataFrame:
        """Create a data collection sheet for the experiment.

        Args:
            response_variables (List[str] | None): Names of response variables to measure.

        Returns:
            pd.DataFrame: Data collection sheet with empty response columns.
        """
        if self.design_matrix is None:
            self.generate_design()

        data_sheet = self.design_matrix.copy()

        # Add response variable columns
        if response_variables is None:
            response_variables = ["Response"]

        for response in response_variables:
            data_sheet[response] = np.nan

        # Add columns for data collection
        data_sheet["Date"] = ""
        data_sheet["Time"] = ""
        data_sheet["Observer"] = ""
        data_sheet["Notes"] = ""

        return data_sheet

    def summary_statistics(
        self, data: pd.DataFrame, response_column: str
    ) -> pd.DataFrame:
        """Calculate summary statistics by treatment.

        Args:
            data (pd.DataFrame): Experimental data with results.
            response_column (str): Name of the response variable column.

        Returns:
            pd.DataFrame: Summary statistics by treatment.
        """
        if response_column not in data.columns:
            raise ValueError(f"Response column '{response_column}' not found in data")

        summary = (
            data.groupby("Treatment")[response_column]
            .agg(["count", "mean", "std", "min", "max", "median"])
            .round(3)
        )

        # Add confidence intervals for means
        from scipy.stats import t

        ci_lower = []
        ci_upper = []

        for treatment in summary.index:
            treatment_data = data[data["Treatment"] == treatment][response_column]
            n = len(treatment_data)
            mean = treatment_data.mean()
            std = treatment_data.std()

            # 95% confidence interval
            t_critical = t.ppf(0.975, n - 1)
            margin_error = t_critical * std / np.sqrt(n)

            ci_lower.append(mean - margin_error)
            ci_upper.append(mean + margin_error)

        summary["CI_Lower"] = np.round(ci_lower, 3)
        summary["CI_Upper"] = np.round(ci_upper, 3)

        return summary
