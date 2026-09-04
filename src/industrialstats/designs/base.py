"""Base class for all experimental designs."""

import json
import math
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np
import pandas as pd


@dataclass
class Factor:
    """Represents an experimental factor.

    Attributes:
        name: Name of the factor as it appears in the design matrix.
        levels: Supported discrete levels for the factor.
        factor_type: Either ``"categorical"`` or ``"continuous"``.
    """

    name: str
    levels: List[Union[str, float, int]]
    factor_type: str = "categorical"  # "categorical" or "continuous"

    def __post_init__(self) -> None:
        """Validate factor parameters.

        Raises:
            ValueError: If ``factor_type`` is not recognised.
        """

        # Confirm that the factor type is within the accepted domain.
        if self.factor_type not in ["categorical", "continuous"]:
            raise ValueError("factor_type must be 'categorical' or 'continuous'")


class ExperimentalDesign(ABC):
    """Abstract base class for experimental designs.

    Subclasses must implement :meth:`generate_design` and :meth:`validate_design`
    to provide bespoke construction and integrity checks for the experiment.
    """

    def __init__(self, name: str) -> None:
        """Initialise the design container.

        Args:
            name: Human-readable label describing the design.
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
        """Randomise the run order of the experiment."""
        if self.design_matrix is None:
            raise ValueError(
                "Design matrix not generated yet. Call generate_design() first."
            )
        self.seed = seed
        self.design_matrix = self.design_matrix.sample(
            frac=1, random_state=seed
        ).reset_index(drop=True)
        self.design_matrix.insert(0, "RunOrder", range(1, len(self.design_matrix) + 1))
        self.randomized = True

    def to_csv(self, filename: str) -> None:
        """Export design to a CSV file."""
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")
        self.design_matrix.to_csv(filename, index=False)

    def to_excel(self, filename: str, include_metadata: bool = True) -> None:
        """Export the design to an Excel workbook with optional metadata."""
        if self.design_matrix is None:
            raise ValueError("No design matrix available for export.")
        path = Path(filename)
        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise ValueError("Excel export only supports .xlsx or .xlsm files.")
        design_df = self.design_matrix.copy()
        try:
            with pd.ExcelWriter(path) as writer:
                design_df.to_excel(writer, index=False, sheet_name="Design")
                self._format_excel_sheet(writer, "Design", design_df)
                if include_metadata:
                    metadata = self._build_metadata_frame()
                    metadata.to_excel(writer, sheet_name="Summary")
                    self._format_excel_sheet(writer, "Summary", metadata, autofit=False)
        except ModuleNotFoundError:  # pragma: no cover
            design_df.to_csv(path.with_suffix(".csv"), index=False)
        except OSError as exc:  # pragma: no cover
            raise OSError(f"Failed to write Excel file '{path}': {exc}") from exc

    def to_json(self, filename: str) -> None:
        """Serialise the design to a JSON document suitable for APIs."""
        if self.design_matrix is None:
            raise ValueError("No design matrix available for export.")
        path = Path(filename)
        if path.suffix.lower() != ".json":
            raise ValueError("JSON export requires a '.json' file extension.")
        payload = {
            "name": self.name,
            "exported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "metadata": self._metadata_payload(),
            "design_matrix": self.design_matrix.to_dict(orient="records"),
        }
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except OSError as exc:  # pragma: no cover
            raise OSError(f"Failed to write JSON file '{path}': {exc}") from exc

    def clone(self) -> "ExperimentalDesign":
        """Create and return a deep copy of the design instance."""
        return deepcopy(self)

    def merge_with(self, other_design: "ExperimentalDesign") -> "ExperimentalDesign":
        """Merge the design with another compatible design."""
        if not isinstance(other_design, ExperimentalDesign):
            raise TypeError("other_design must be an ExperimentalDesign instance")
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Both designs must have generated matrices to merge.")
        merged_design = self.clone()
        merged_design.factors = self._merge_factor_metadata(other_design)
        merged_design.design_matrix = self._aligned_concat(other_design)
        merged_design.design_matrix.reset_index(drop=True, inplace=True)
        merged_design.randomized = False
        merged_design.seed = None
        return merged_design

    def compare_to(self, other_design: "ExperimentalDesign") -> Dict[str, Any]:
        """Compare this design with another design."""
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
        """Indicate whether the design is balanced across categorical factors."""
        if self.design_matrix is None or self.design_matrix.empty:
            return False
        df = self.design_matrix
        categorical_factors = [
            f.name for f in self.factors if f.factor_type == "categorical"
        ]
        if not categorical_factors:
            return not df.isna().any().any()
        missing_columns = [col for col in categorical_factors if col not in df.columns]
        if missing_columns:
            raise ValueError(
                "Design matrix is missing columns required for balance check: "
                f"{', '.join(missing_columns)}"
            )
        if df[categorical_factors].isna().any().any():
            return False
        level_counts = (
            df[categorical_factors].groupby(categorical_factors, dropna=False).size()
        )
        if level_counts.empty:
            return False
        return level_counts.nunique() == 1

    @property
    def design_efficiency(self) -> Dict[str, float]:
        """Compute baseline efficiency metrics for the design."""
        if self.design_matrix is None or not self.factors:
            return {}
        actual_runs = float(len(self.design_matrix))
        possible_runs = float(np.prod([len(f.levels) for f in self.factors]))
        run_fraction = actual_runs / possible_runs if possible_runs else np.nan
        categorical_factors = [
            f.name for f in self.factors if f.factor_type == "categorical"
        ]
        replication_factor = np.nan
        balance_index = np.nan
        if categorical_factors:
            has_missing = self.design_matrix[categorical_factors].isna().any().any()
            if has_missing:
                balance_index = np.nan
            else:
                counts = (
                    self.design_matrix[categorical_factors]
                    .groupby(categorical_factors, dropna=False)
                    .size()
                )
                if not counts.empty:
                    replication_factor = actual_runs / float(len(counts))
                    balance_index = (
                        float(counts.min() / counts.max()) if counts.max() else np.nan
                    )
        missing_rate = float(
            self.design_matrix.isna().to_numpy().sum() / self.design_matrix.size
        )
        return {
            "run_fraction": float(run_fraction),
            "replication_factor": (
                float(replication_factor)
                if not np.isnan(replication_factor)
                else np.nan
            ),
            "balance_index": (
                float(balance_index) if not np.isnan(balance_index) else np.nan
            ),
            "missing_rate": missing_rate,
        }

    def _format_excel_sheet(
        self,
        writer: pd.ExcelWriter,
        sheet_name: str,
        data: Optional[pd.DataFrame] = None,
        autofit: bool = True,
    ) -> None:
        """Apply lightweight formatting to an Excel worksheet."""
        worksheet = writer.sheets.get(sheet_name)
        if worksheet is None:
            return
        engine = getattr(writer, "engine", "") or ""
        engine = engine.lower() if isinstance(engine, str) else ""
        if engine == "xlsxwriter":
            workbook = writer.book
            header_format = workbook.add_format({"bold": True})
            worksheet.freeze_panes(1, 0)
            worksheet.set_row(0, None, header_format)
            if data is not None and autofit:
                for col_idx, column in enumerate(data.columns):
                    series = data[column].astype(str)
                    max_length = max([len(str(column))] + [len(val) for val in series])
                    worksheet.set_column(col_idx, col_idx, min(max_length + 2, 60))
        else:
            try:
                worksheet.freeze_panes = worksheet["A2"]
            except (TypeError, KeyError, AttributeError):
                pass
            if data is not None and autofit:
                try:
                    from openpyxl.utils import get_column_letter
                except ModuleNotFoundError:  # pragma: no cover
                    return
                for idx, column in enumerate(data.columns, start=1):
                    series = data[column].astype(str)
                    max_length = max([len(str(column))] + [len(val) for val in series])
                    worksheet.column_dimensions[get_column_letter(idx)].width = min(
                        max_length + 2, 60
                    )

    def _build_metadata_frame(self) -> pd.DataFrame:
        """Create a tabular summary of metadata for Excel export."""
        payload = self._metadata_payload()
        rows: Dict[str, Any] = {
            "Design Name": payload.get("design_name", self.name),
            "Run Count": payload.get("run_count", self.run_count),
            "Randomized": payload.get("randomized", self.randomized),
            "Balanced": payload.get("is_balanced", False),
            "Design Matrix Shape": payload.get("design_matrix_shape", (0, 0)),
        }
        for key, value in payload.get("design_efficiency", {}).items():
            label = f"Efficiency - {key.replace('_', ' ').title()}"
            rows[label] = value
        factor_lines = []
        for factor in payload.get("factors", []):
            levels = ", ".join(map(str, factor.get("levels", [])))
            factor_lines.append(
                f"{factor.get('name')}: {levels} (type={factor.get('factor_type')})"
            )
        if factor_lines:
            rows["Factors"] = "\n".join(factor_lines)
        return pd.DataFrame.from_dict(rows, orient="index", columns=["Value"])

    def _metadata_payload(self) -> Dict[str, Any]:
        """Construct a metadata dictionary describing the design."""
        if self.design_matrix is None:
            summary: Dict[str, Any] = {"status": "Design not generated"}
        else:
            summary = self.summary()
        efficiency: Dict[str, Any] = {}
        for key, value in self.design_efficiency.items():
            if isinstance(value, (int, np.integer)):
                efficiency[key] = int(value)
            elif isinstance(value, (float, np.floating)):
                efficiency[key] = None if math.isnan(float(value)) else float(value)
            else:
                efficiency[key] = value
        factors = [
            {
                "name": factor.name,
                "levels": list(factor.levels),
                "factor_type": factor.factor_type,
            }
            for factor in self.factors
        ]
        payload: Dict[str, Any] = {
            "design_name": self.name,
            "run_count": summary.get("n_runs", self.run_count),
            "randomized": self.randomized,
            "is_balanced": (
                self.is_balanced if self.design_matrix is not None else False
            ),
            "design_efficiency": efficiency,
            "factors": factors,
        }
        if self.design_matrix is not None:
            payload["design_matrix_shape"] = self.design_matrix.shape
        if self.seed is not None:
            payload["seed"] = self.seed
        return payload

    def _merge_factor_metadata(
        self, other_design: "ExperimentalDesign"
    ) -> List[Factor]:
        """Merge factor definitions from two designs ensuring compatibility."""
        merged_factors: List[Factor] = []
        other_map = {factor.name: factor for factor in other_design.factors}
        seen: Set[str] = set()
        for factor in self.factors:
            other_factor = other_map.get(factor.name)
            if other_factor:
                if factor.factor_type != other_factor.factor_type:
                    raise ValueError(
                        f"Factor '{factor.name}' has incompatible types: "
                        f"{factor.factor_type} vs {other_factor.factor_type}."
                    )
                combined_levels = list(factor.levels)
                for level in other_factor.levels:
                    if level not in combined_levels:
                        combined_levels.append(level)
                merged_factors.append(
                    Factor(factor.name, combined_levels, factor.factor_type)
                )
            else:
                merged_factors.append(
                    Factor(factor.name, list(factor.levels), factor.factor_type)
                )
            seen.add(factor.name)
        for factor in other_design.factors:
            if factor.name in seen:
                continue
            merged_factors.append(
                Factor(factor.name, list(factor.levels), factor.factor_type)
            )
        return merged_factors

    def _aligned_concat(self, other_design: "ExperimentalDesign") -> pd.DataFrame:
        """Align design matrices and concatenate them row-wise."""
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Design matrices must exist before concatenation.")
        left = self.design_matrix.copy()
        right = other_design.design_matrix.copy()
        columns: List[str] = list(left.columns)
        for column in right.columns:
            if column not in columns:
                columns.append(column)
        left_aligned = left.reindex(columns=columns)
        right_aligned = right.reindex(columns=columns)
        return pd.concat([left_aligned, right_aligned], ignore_index=True)

    def summary(self) -> Dict[str, Any]:
        """Return summary information about the design."""
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
