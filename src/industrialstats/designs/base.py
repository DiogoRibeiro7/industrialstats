"""Base class for all experimental designs."""

import contextlib
import json
import math
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class Factor:
    """Represents an experimental factor.

    Attributes
    ----------
    name
        Name of the factor as it appears in the design matrix.
    levels
        Supported discrete levels for the factor.
    factor_type
        Either ``"categorical"`` or ``"continuous"``.
    """

    name: str
    levels: list[str | float | int]
    factor_type: str = "categorical"  # "categorical" or "continuous"

    def __post_init__(self) -> None:
        """Validate factor parameters.

        Raises
        ------
        ValueError
            If ``factor_type`` is not recognised.
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

        Parameters
        ----------
        name
            Human-readable label describing the design.
        """

        # Persist metadata and runtime state for the design definition.
        self.name = name
        self.factors: list[Factor] = []
        self.design_matrix: pd.DataFrame | None = None
        self.randomized: bool = False
        self.seed: int | None = None

    @abstractmethod
    def generate_design(self) -> pd.DataFrame:
        """Generate the experimental design matrix."""
        pass

    @abstractmethod
    def validate_design(self) -> bool:
        """Validate the experimental design."""
        pass

    def add_factor(self, factor: Factor) -> None:
        """Add a factor to the design.

        Parameters
        ----------
        factor
            Factor description to register.

        Raises
        ------
        TypeError
            If ``factor`` is not a :class:`Factor` instance.
        """

        # Enforce a consistent factor representation for downstream logic.
        if not isinstance(factor, Factor):
            raise TypeError("factor must be a Factor instance")

        # Append the validated factor to the ordered factor list.
        self.factors.append(factor)

    def randomize(self, seed: int | None = None) -> None:
        """Randomise the run order of the experiment.

        Parameters
        ----------
        seed
            Optional random seed used to create deterministic shuffles.

        Raises
        ------
        ValueError
            If the design matrix has not been generated.

        References
        ----------
        Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th
        ed., Wiley.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign({"A": [1, -1], "B": [1, -1]})
        >>> design.generate_design()
        >>> design.randomize(seed=42)
        >>> design.design_matrix[["RunOrder", "A", "B"]].head()
           RunOrder  A  B
        0         1  1 -1
        1         2 -1  1
        """

        # Guard against missing design matrices prior to shuffling runs.
        if self.design_matrix is None:
            raise ValueError(
                "Design matrix not generated yet. Call generate_design() first."
            )

        # Persist the seed so exported metadata reflects the randomisation state.
        self.seed = seed

        # Shuffle the design matrix using a reproducible random state when provided.
        self.design_matrix = self.design_matrix.sample(
            frac=1, random_state=seed
        ).reset_index(drop=True)

        # Insert the sequential run order column for traceability of randomisation.
        self.design_matrix.insert(0, "RunOrder", range(1, len(self.design_matrix) + 1))
        self.randomized = True

    def to_csv(self, filename: str) -> None:
        """Export design to a CSV file.

        Parameters
        ----------
        filename
            Destination file path.

        Raises
        ------
        ValueError
            If no design matrix is available.
        """

        # Ensure that the design matrix exists before writing to disk.
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")

        # Persist the design matrix in a simple comma-separated format.
        self.design_matrix.to_csv(filename, index=False)

    def to_excel(self, filename: str, include_metadata: bool = True) -> None:
        """Export the design to an Excel workbook with optional metadata.

        Parameters
        ----------
        filename
            Path to the output workbook (``.xlsx`` or ``.xlsm``).
        include_metadata
            Whether to include a summary worksheet.

        Raises
        ------
        ValueError
            If no design matrix exists or the extension is invalid.
        OSError
            If the workbook cannot be written to disk.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign([Factor("A", ["Low", "High"])], randomize=False)
        >>> design.generate_design()
        >>> design.to_excel("factorial_design.xlsx")
        """

        # Disallow export when the design has not yet been generated.
        if self.design_matrix is None:
            raise ValueError("No design matrix available for export.")

        # Resolve and validate the requested output path and extension.
        path = Path(filename)
        if path.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise ValueError("Excel export only supports .xlsx or .xlsm files.")

        # Make a defensive copy so that formatting mutations do not affect the source.
        design_df = self.design_matrix.copy()

        try:
            # Open an Excel writer context for structured output.
            with pd.ExcelWriter(path) as writer:
                # Persist the design matrix on the primary sheet.
                design_df.to_excel(writer, index=False, sheet_name="Design")
                self._format_excel_sheet(writer, "Design", design_df)

                # Append supplementary metadata when requested.
                if include_metadata:
                    metadata = self._build_metadata_frame()
                    metadata.to_excel(writer, sheet_name="Summary")
                    self._format_excel_sheet(writer, "Summary", metadata, autofit=False)
        except ModuleNotFoundError:  # pragma: no cover
            # Fallback gracefully by emitting CSV if Excel engines are missing.
            design_df.to_csv(path.with_suffix(".csv"), index=False)
        except OSError as exc:  # pragma: no cover
            raise OSError(f"Failed to write Excel file '{path}': {exc}") from exc

    def to_json(self, filename: str) -> None:
        """Serialise the design to a JSON document suitable for APIs.

        Parameters
        ----------
        filename
            Destination path ending with ``.json``.

        Raises
        ------
        ValueError
            If the design matrix is missing or the extension is invalid.
        OSError
            If writing the JSON file fails.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign([Factor("A", [1, -1])], randomize=False)
        >>> design.generate_design()
        >>> design.to_json("design.json")
        """

        # Confirm that a design matrix exists before constructing the payload.
        if self.design_matrix is None:
            raise ValueError("No design matrix available for export.")

        # Ensure the destination path targets a JSON extension for interoperability.
        path = Path(filename)
        if path.suffix.lower() != ".json":
            raise ValueError("JSON export requires a '.json' file extension.")

        # Build a serialisable payload containing metadata and the design matrix.
        payload = {
            "name": self.name,
            "exported_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "metadata": self._metadata_payload(),
            "design_matrix": self.design_matrix.to_dict(orient="records"),
        }

        try:
            # Persist the JSON payload with indentation for readability.
            with path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except OSError as exc:  # pragma: no cover
            raise OSError(f"Failed to write JSON file '{path}': {exc}") from exc

    def clone(self) -> "ExperimentalDesign":
        """Create and return a deep copy of the design instance.

        Returns
        -------
        ExperimentalDesign
            Deep copy of ``self`` with independent factor
            and matrix structures.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign([Factor("A", [0, 1])], randomize=False)
        >>> design.generate_design()
        >>> clone = design.clone()
        >>> clone is design
        False
        >>> clone.design_matrix.equals(design.design_matrix)
        True
        """

        # Delegate to :func:`copy.deepcopy` to replicate nested containers safely.
        return deepcopy(self)

    def merge_with(self, other_design: "ExperimentalDesign") -> "ExperimentalDesign":
        """Merge the design with another compatible design.

        Parameters
        ----------
        other_design
            Design whose runs will be appended to this design.

        Returns
        -------
        ExperimentalDesign
            Deep copy of the current design containing runs
            from both designs.

        Raises
        ------
        TypeError
            If ``other_design`` is not an :class:`ExperimentalDesign`.
        ValueError
            If either design lacks a generated design matrix or the
            factor metadata is incompatible.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> factors = [Factor("A", [0, 1])]
        >>> d1 = FactorialDesign(factors, randomize=False)
        >>> _ = d1.generate_design()
        >>> d2 = FactorialDesign(factors, randomize=False)
        >>> _ = d2.generate_design()
        >>> merged = d1.merge_with(d2)
        >>> merged.run_count
        4
        """

        # Validate type compatibility to avoid merging unrelated implementations.
        if not isinstance(other_design, ExperimentalDesign):
            raise TypeError("other_design must be an ExperimentalDesign instance")

        # Ensure both designs are generated prior to concatenation.
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Both designs must have generated matrices to merge.")

        # Clone so the current design remains immutable to callers.
        merged_design = self.clone()

        # Merge factor metadata to reconcile level information.
        merged_design.factors = self._merge_factor_metadata(other_design)

        # Concatenate design matrices while respecting differing column orders.
        merged_design.design_matrix = self._aligned_concat(other_design)
        merged_design.design_matrix = merged_design.design_matrix.reset_index(drop=True)

        # Reset randomisation metadata after the merge.
        merged_design.randomized = False
        merged_design.seed = None
        return merged_design

    def compare_to(self, other_design: "ExperimentalDesign") -> dict[str, Any]:
        """Compare this design with another design.

        Parameters
        ----------
        other_design
            Design to compare against.

        Returns
        -------
        Dict[str, Any]
            Summary of differences such as run count and factor
            sets.

        Raises
        ------
        ValueError
            If either design lacks a generated matrix.
        """

        # Ensure both designs have been generated before comparing characteristics.
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Both designs must have generated matrices to compare")

        # Identify differing factor names between both designs.
        factor_diff = list(
            set(self.factor_names).symmetric_difference(other_design.factor_names)
        )
        # Compute the run-count difference for quick diagnostics.
        run_diff = other_design.run_count - self.run_count
        return {"factor_diff": factor_diff, "run_diff": run_diff}

    @property
    def run_count(self) -> int:
        """Number of experimental runs currently in the design."""
        return len(self.design_matrix) if self.design_matrix is not None else 0

    @property
    def factor_names(self) -> list[str]:
        """List of factor names present in the design."""
        return [f.name for f in self.factors]

    @property
    def is_balanced(self) -> bool:
        """Indicate whether the design is balanced across categorical factors.

        Returns
        -------
        bool
            ``True`` when every combination of categorical factor levels
            is represented equally often without missing values. If the design
            has not been generated the property returns ``False``.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> factors = [Factor("A", [0, 1]), Factor("B", [0, 1])]
        >>> design = FactorialDesign(factors, randomize=False)
        >>> design.generate_design()
        >>> design.is_balanced
        True
        """

        # Immediately fail if no design matrix is present.
        if self.design_matrix is None or self.design_matrix.empty:
            return False

        # Work on the design matrix view used for balance checking.
        df = self.design_matrix

        # Identify categorical factors because balance is defined for discrete levels.
        categorical_factors = [
            f.name for f in self.factors if f.factor_type == "categorical"
        ]

        # A design with only continuous factors is deemed balanced when no missing data exist.
        if not categorical_factors:
            return not df.isna().any().any()

        # Validate that all categorical factor columns are present.
        missing_columns = [col for col in categorical_factors if col not in df.columns]
        if missing_columns:
            raise ValueError(
                "Design matrix is missing columns required for balance check: "
                f"{', '.join(missing_columns)}"
            )

        # Any missing values break balance assumptions.
        if df[categorical_factors].isna().any().any():
            return False

        # Count occurrences for each categorical combination.
        level_counts = (
            df[categorical_factors].groupby(categorical_factors, dropna=False).size()
        )

        # Reject degenerate cases without category combinations.
        if level_counts.empty:
            return False

        # Balanced if all counts match.
        return level_counts.nunique() == 1

    @property
    def design_efficiency(self) -> dict[str, float]:
        """Compute baseline efficiency metrics for the design.

        Returns
        -------
        dict[str, float]
            Dictionary containing efficiency statistics such
            as the run fraction, replication factor, balance index, and the
            proportion of missing data.

        Examples
        --------
        >>> from industrialstats.designs.factorial import FactorialDesign
        >>> design = FactorialDesign([Factor("A", [0, 1])], randomize=False)
        >>> design.generate_design()
        >>> metrics = design.design_efficiency
        >>> sorted(metrics.keys())
        ['balance_index', 'missing_rate', 'replication_factor', 'run_fraction']
        """

        # Return an empty result if the design has not been generated yet.
        if self.design_matrix is None or not self.factors:
            return {}

        # Compute run fraction relative to the full factorial size.
        actual_runs = float(len(self.design_matrix))
        possible_runs = float(np.prod([len(f.levels) for f in self.factors]))
        run_fraction = actual_runs / possible_runs if possible_runs else np.nan

        # Focus on categorical factors for replication and balance diagnostics.
        categorical_factors = [
            f.name for f in self.factors if f.factor_type == "categorical"
        ]
        replication_factor = np.nan
        balance_index = np.nan

        if categorical_factors:
            # Check for missing values that would invalidate replication counts.
            has_missing = self.design_matrix[categorical_factors].isna().any().any()
            if has_missing:
                balance_index = np.nan
            else:
                # Count occurrences per combination to derive replication metrics.
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

        # Measure the prevalence of missing entries in the design matrix.
        missing_rate = float(
            self.design_matrix.isna().to_numpy().sum() / self.design_matrix.size
        )

        # Assemble the metrics while converting NaNs to floats for JSON compatibility.
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
        data: pd.DataFrame | None = None,
        autofit: bool = True,
    ) -> None:
        """Apply lightweight formatting to an Excel worksheet.

        Parameters
        ----------
        writer
            Active Excel writer instance.
        sheet_name
            Name of the sheet to format.
        data
            Optional tabular content for computing column widths.
        autofit
            Whether to resize columns to their contents.
        """

        # Access the worksheet reference produced by pandas.
        worksheet = writer.sheets.get(sheet_name)
        if worksheet is None:
            return

        # Normalise the engine name for backend-specific formatting calls.
        engine = getattr(writer, "engine", "") or ""
        engine = engine.lower() if isinstance(engine, str) else ""

        if engine == "xlsxwriter":
            # Apply header styling and frozen panes using the XlsxWriter API.
            # The concrete workbook type follows from the engine selected at
            # runtime; in this branch it is an xlsxwriter Workbook, which the
            # writer's declared type cannot express.
            workbook: Any = writer.book
            header_format = workbook.add_format({"bold": True})
            worksheet.freeze_panes(1, 0)
            worksheet.set_row(0, None, header_format)
            if data is not None and autofit:
                # Derive column widths from the stringified contents.
                for col_idx, column in enumerate(data.columns):
                    series = data[column].astype(str)
                    max_length = max([len(str(column))] + [len(val) for val in series])
                    worksheet.set_column(col_idx, col_idx, min(max_length + 2, 60))
        else:
            # Some engines expose a cell-like interface for frozen panes.
            with contextlib.suppress(TypeError, KeyError, AttributeError):
                worksheet.freeze_panes = worksheet["A2"]
            if data is not None and autofit:
                try:
                    from openpyxl.utils import get_column_letter
                except ModuleNotFoundError:  # pragma: no cover
                    return
                # Adjust column widths when openpyxl-style attributes exist.
                for idx, column in enumerate(data.columns, start=1):
                    series = data[column].astype(str)
                    max_length = max([len(str(column))] + [len(val) for val in series])
                    worksheet.column_dimensions[get_column_letter(idx)].width = min(
                        max_length + 2, 60
                    )

    def _build_metadata_frame(self) -> pd.DataFrame:
        """Create a tabular summary of metadata for Excel export.

        Returns
        -------
        pandas.DataFrame
            Metadata table containing summary metrics.
        """

        # Gather metadata payload shared between JSON and Excel exports.
        payload = self._metadata_payload()
        rows: dict[str, Any] = {
            "Design Name": payload.get("design_name", self.name),
            "Run Count": payload.get("run_count", self.run_count),
            "Randomized": payload.get("randomized", self.randomized),
            "Balanced": payload.get("is_balanced", False),
            "Design Matrix Shape": payload.get("design_matrix_shape", (0, 0)),
        }

        # Append efficiency metrics as human-readable rows.
        for key, value in payload.get("design_efficiency", {}).items():
            label = f"Efficiency - {key.replace('_', ' ').title()}"
            rows[label] = value

        # Describe factor metadata with formatted level listings.
        factor_lines = []
        for factor in payload.get("factors", []):
            levels = ", ".join(map(str, factor.get("levels", [])))
            factor_lines.append(
                f"{factor.get('name')}: {levels} (type={factor.get('factor_type')})"
            )

        if factor_lines:
            rows["Factors"] = "\n".join(factor_lines)

        # Convert the metadata dictionary into a two-column DataFrame.
        return pd.DataFrame.from_dict(rows, orient="index", columns=["Value"])

    def _metadata_payload(self) -> dict[str, Any]:
        """Construct a metadata dictionary describing the design.

        Returns
        -------
        dict[str, Any]
            Metadata describing the design state.
        """

        # Use the summary when a design matrix exists, otherwise provide status info.
        if self.design_matrix is None:
            summary: dict[str, Any] = {"status": "Design not generated"}
        else:
            summary = self.summary()

        # Normalise efficiency metrics into JSON-friendly primitives.
        efficiency: dict[str, Any] = {}
        for key, value in self.design_efficiency.items():
            if isinstance(value, (int, np.integer)):
                efficiency[key] = int(value)
            elif isinstance(value, (float, np.floating)):
                efficiency[key] = None if math.isnan(float(value)) else float(value)
            else:
                efficiency[key] = value

        # Capture factor definitions with level details for downstream consumers.
        factors = [
            {
                "name": factor.name,
                "levels": list(factor.levels),
                "factor_type": factor.factor_type,
            }
            for factor in self.factors
        ]

        # Assemble the payload dictionary with core design metadata.
        payload: dict[str, Any] = {
            "design_name": self.name,
            "run_count": summary.get("n_runs", self.run_count),
            "randomized": self.randomized,
            "is_balanced": (
                self.is_balanced if self.design_matrix is not None else False
            ),
            "design_efficiency": efficiency,
            "factors": factors,
        }

        # Include optional details when available.
        if self.design_matrix is not None:
            payload["design_matrix_shape"] = self.design_matrix.shape
        if self.seed is not None:
            payload["seed"] = self.seed

        return payload

    def _merge_factor_metadata(
        self, other_design: "ExperimentalDesign"
    ) -> list[Factor]:
        """Merge factor definitions from two designs ensuring compatibility.

        Parameters
        ----------
        other_design
            Design providing additional factor definitions.

        Returns
        -------
        list[Factor]
            Combined factor list with reconciled level sets.

        Raises
        ------
        ValueError
            If a factor shares a name but mismatched type across designs.
        """

        # Index the other design's factors for quick lookups by name.
        merged_factors: list[Factor] = []
        other_map = {factor.name: factor for factor in other_design.factors}
        seen: set[str] = set()

        # Merge factors defined in the current design.
        for factor in self.factors:
            other_factor = other_map.get(factor.name)
            if other_factor:
                # Ensure factors with the same name share the same type.
                if factor.factor_type != other_factor.factor_type:
                    raise ValueError(
                        f"Factor '{factor.name}' has incompatible types: "
                        f"{factor.factor_type} vs {other_factor.factor_type}."
                    )
                # Combine unique levels across both definitions.
                combined_levels = list(factor.levels)
                for level in other_factor.levels:
                    if level not in combined_levels:
                        combined_levels.append(level)
                merged_factors.append(
                    Factor(factor.name, combined_levels, factor.factor_type)
                )
            else:
                # Retain the factor as-is when only present in the current design.
                merged_factors.append(
                    Factor(factor.name, list(factor.levels), factor.factor_type)
                )
            seen.add(factor.name)

        # Append factors unique to the other design.
        for factor in other_design.factors:
            if factor.name in seen:
                continue
            merged_factors.append(
                Factor(factor.name, list(factor.levels), factor.factor_type)
            )

        return merged_factors

    def _aligned_concat(self, other_design: "ExperimentalDesign") -> pd.DataFrame:
        """Align design matrices and concatenate them row-wise.

        Parameters
        ----------
        other_design
            Design providing the second matrix to concatenate.

        Returns
        -------
        pandas.DataFrame
            Combined design matrix with aligned columns.

        Raises
        ------
        ValueError
            If either design lacks a generated matrix.
        """

        # Validate the presence of design matrices before attempting concatenation.
        if self.design_matrix is None or other_design.design_matrix is None:
            raise ValueError("Design matrices must exist before concatenation.")

        # Copy matrices to avoid mutating caller state.
        left = self.design_matrix.copy()
        right = other_design.design_matrix.copy()

        # Build a superset of columns across both designs.
        columns: list[str] = list(left.columns)
        for column in right.columns:
            if column not in columns:
                columns.append(column)

        # Align both matrices to the shared column order.
        left_aligned = left.reindex(columns=columns)
        right_aligned = right.reindex(columns=columns)

        # Concatenate the aligned matrices row-wise.
        return pd.concat([left_aligned, right_aligned], ignore_index=True)

    def summary(self) -> dict[str, Any]:
        """Return summary information about the design.

        Returns
        -------
        dict[str, Any]
            Key characteristics of the design.
        """

        # Provide a status indicator when the design has not been generated yet.
        if self.design_matrix is None:
            return {"status": "Design not generated"}

        # Report headline metadata for quick inspection.
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
