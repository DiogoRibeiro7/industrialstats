"""Base class for all experimental designs."""

import json
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd


@dataclass
class Factor:
    """Represents an experimental factor.

    Attributes
    ----------
    name : str
        Factor name.
    levels : list of str or float or int
        Discrete factor levels.
    factor_type : str
        ``"categorical"`` or ``"continuous"``.
    """

    name: str
    levels: List[Union[str, float, int]]
    factor_type: str = "categorical"  # "categorical" or "continuous"

    def __post_init__(self) -> None:
        """Validate factor parameters.

        Raises
        ------
        ValueError
            If ``factor_type`` is not valid.
        """
        if self.factor_type not in ["categorical", "continuous"]:
            raise ValueError("factor_type must be 'categorical' or 'continuous'")


class ExperimentalDesign(ABC):
    """Abstract base class for all experimental designs."""

    def __init__(self, name: str) -> None:
        """Initialize the design container.

        Parameters
        ----------
        name : str
            Name of the design.
        """
        self.name = name
        self.factors: List[Factor] = []
        self.design_matrix: Optional[pd.DataFrame] = None
        self.randomized: bool = False
        self.seed: Optional[int] = None

    @abstractmethod
    def generate_design(self) -> pd.DataFrame:
        """Generate the experimental design matrix."""
        pass

    @abstractmethod
    def validate_design(self) -> bool:
        """Validate the experimental design."""
        pass

    def add_factor(self, factor: Factor) -> None:
        """Add a factor to the design."""
        if not isinstance(factor, Factor):
            raise TypeError("factor must be a Factor instance")
        self.factors.append(factor)

    def randomize(self, seed: Optional[int] = None) -> None:
        """Randomize the run order of the experiment.

        The design matrix is shuffled using :func:`pandas.DataFrame.sample` with a
        fixed ``random_state`` so that repeated calls with the same ``seed`` yield
        identical run orders. The resulting run order is stored in a new
        ``RunOrder`` column as ``1, 2, ... , n``.

        Parameters
        ----------
        seed : int, optional
            Random seed for reproducibility. If ``None`` (default), the shuffle
            is non-deterministic.

        Raises
        ------
        ValueError
            If the design matrix has not been generated.

        See Also
        --------
        industrialstats.designs.rcbd.RandomizedCompleteBlockDesign.generate_design
            RCBD implementation using block-wise randomization.
        to_excel, to_json
            Utilities for exporting randomized designs.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign({'A': [1, -1], 'B': [1, -1]})
        >>> design.generate_design()
        >>> design.randomize(seed=42)
        >>> design.design_matrix[['RunOrder', 'A', 'B']].head()
           RunOrder  A  B
        0         1  1 -1
        1         2 -1  1

        References
        ----------
        .. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*.
               9th ed. Wiley.
        """
        if self.design_matrix is None:
            raise ValueError(
                "Design matrix not generated yet. Call generate_design() first."
            )

        self.seed = seed

        # Shuffle the design matrix using an integer seed for broad pandas compatibility
        self.design_matrix = self.design_matrix.sample(
            frac=1, random_state=seed
        ).reset_index(drop=True)

        # Add run order column
        self.design_matrix.insert(0, "RunOrder", range(1, len(self.design_matrix) + 1))
        self.randomized = True

    def to_csv(self, filename: str) -> None:
        """Export design to a CSV file.

        Parameters
        ----------
        filename : str
            Destination file path.

        Raises
        ------
        ValueError
            If no design matrix is available.
        """
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")
        self.design_matrix.to_csv(filename, index=False)

    def to_excel(self, filename: str, include_metadata: bool = True) -> None:
        """Export design to an Excel workbook.

        Parameters
        ----------
        filename : str
            Destination file path.
        include_metadata : bool, optional
            Whether to add a summary sheet. Defaults to ``True``.

        Raises
        ------
        ValueError
            If no design matrix is available.
        """
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")

        try:
            with pd.ExcelWriter(filename) as writer:
                self.design_matrix.to_excel(writer, index=False, sheet_name="Design")
                if include_metadata:
                    summary_df = pd.DataFrame.from_dict(
                        self.summary(), orient="index", columns=["Value"]
                    )
                    summary_df.to_excel(writer, sheet_name="Summary")
        except ModuleNotFoundError:
            # Fallback when Excel backends are unavailable
            self.design_matrix.to_csv(filename, index=False)

    def to_json(self, filename: str) -> None:
        """Export design to a JSON file.

        Parameters
        ----------
        filename : str
            Destination file path.

        Raises
        ------
        ValueError
            If no design matrix is available.
        """
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")

        data = {
            "design": self.design_matrix.to_dict(orient="records"),
            "summary": self.summary(),
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def clone(self) -> "ExperimentalDesign":
        """Create a deep copy of the design.

        Returns
        -------
        ExperimentalDesign
            Cloned design instance.
        """
        return deepcopy(self)

    def merge_with(self, other_design: "ExperimentalDesign") -> "ExperimentalDesign":
        """Merge with another design for augmentation.

        Parameters
        ----------
        other_design : ExperimentalDesign
            Design to merge with.

        Returns
        -------
        ExperimentalDesign
            New design containing runs from both designs.

        Raises
        ------
        ValueError
            If either design lacks a generated matrix.
        """
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Both designs must have generated matrices to merge")

        merged = self.clone()
        merged.design_matrix = pd.concat(
            [self.design_matrix, other_design.design_matrix], ignore_index=True
        )
        return merged

    def compare_to(self, other_design: "ExperimentalDesign") -> Dict[str, Any]:
        """Compare this design with another design.

        Parameters
        ----------
        other_design : ExperimentalDesign
            Design to compare against.

        Returns
        -------
        Dict[str, Any]
            Summary of differences such as run count and factor sets.

        Raises
        ------
        ValueError
            If either design lacks a generated matrix.
        """
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Both designs must have generated matrices to compare")

        factor_diff = list(
            set(self.factor_names).symmetric_difference(other_design.factor_names)
        )
        run_diff = other_design.run_count - self.run_count
        return {"factor_diff": factor_diff, "run_diff": run_diff}

    @property
    def run_count(self) -> int:
        """Number of experimental runs currently in the design."""
        return len(self.design_matrix) if self.design_matrix is not None else 0

    @property
    def factor_names(self) -> List[str]:
        """List of factor names present in the design."""
        return [f.name for f in self.factors]

    @property
    def is_balanced(self) -> bool:
        """Check if the design is balanced across factor levels.

        Returns
        -------
        bool
            ``True`` if each factor level appears equally often.
        """
        if self.design_matrix is None:
            return False

        for factor in self.factors:
            counts = self.design_matrix[factor.name].value_counts()
            if counts.nunique() > 1:
                return False
        return True

    @property
    def design_efficiency(self) -> Dict[str, float]:
        """Calculate basic design efficiency metrics.

        Returns
        -------
        Dict[str, float]
            Dictionary with run fraction relative to full factorial.
        """
        if self.design_matrix is None or not self.factors:
            return {}

        possible_runs = np.prod([len(f.levels) for f in self.factors])
        actual_runs = len(self.design_matrix)
        return {"run_fraction": actual_runs / possible_runs}

    def summary(self) -> Dict[str, Any]:
        """Return summary information about the design.

        Returns
        -------
        Dict[str, Any]
            Key characteristics of the design.
        """
        if self.design_matrix is None:
            return {"status": "Design not generated"}

        return {
            "design_name": self.name,
            "n_factors": len(self.factors),
            "n_runs": len(self.design_matrix),
            "randomized": self.randomized,
            "factors": [f.name for f in self.factors],
            "factor_levels": {f.name: f.levels for f in self.factors},
            "design_matrix_shape": self.design_matrix.shape,
        }

    def __str__(self) -> str:
        """Return a human-readable representation of the design."""
        summary = self.summary()
        if summary.get("status") == "Design not generated":
            return f"{self.name} (not generated)"

        return (
            f"{self.name}\n"
            f"Factors: {summary['n_factors']}\n"
            f"Runs: {summary['n_runs']}\n"
            f"Randomized: {summary['randomized']}"
        )

    def __repr__(self) -> str:
        """Return a detailed representation for debugging."""
        return f"ExperimentalDesign(name='{self.name}', factors={len(self.factors)})"
