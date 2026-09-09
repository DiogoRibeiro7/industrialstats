"""Full factorial experimental designs with statistically defined blocking."""

from __future__ import annotations

from itertools import combinations, product
from math import prod
from typing import Any

import numpy as np
import pandas as pd

from ..utils._factorial_contrasts import calculate_two_level_factorial_effects
from ._factorial_core import FactorialDesign as _FactorialDesignCore
from .base import Factor


class FactorialDesign(_FactorialDesignCore):
    """Full factorial design with regular blocking for two-level experiments."""

    def __init__(
        self,
        factors: list[Factor],
        replicates: int = 1,
        center_points: int = 0,
        randomize: bool = True,
        blocks: int | None = None,
        seed: int | None = None,
        block_generators: list[str] | None = None,
        allow_main_effect_confounding: bool = False,
    ) -> None:
        """Create a full factorial design."""
        super().__init__(
            factors=factors,
            replicates=replicates,
            center_points=center_points,
            randomize=randomize,
            blocks=None,
            seed=seed,
        )
        self.blocks = blocks
        self.block_generators = (
            list(block_generators) if block_generators is not None else None
        )
        self.allow_main_effect_confounding = allow_main_effect_confounding

        if not isinstance(allow_main_effect_confounding, bool):
            raise ValueError("allow_main_effect_confounding must be a boolean")
        if self.block_generators is not None and self.blocks is None:
            self.blocks = 2 ** len(self.block_generators)
        self._validate_blocking_configuration()

    def generate_design(self) -> pd.DataFrame:
        """Generate the full factorial design and apply regular blocking."""
        if not self.validate_design():
            raise ValueError("Invalid design configuration")

        combinations_list = list(product(*(factor.levels for factor in self.factors)))
        design_data: list[dict[str, Any]] = []
        run_id = 1

        for replicate in range(1, self.replicates + 1):
            for combination in combinations_list:
                row: dict[str, Any] = {
                    "RunID": run_id,
                    "Replicate": replicate,
                    "DesignPoint": "Factorial",
                    "StdOrder": run_id,
                }
                for index, factor in enumerate(self.factors):
                    row[factor.name] = combination[index]
                design_data.append(row)
                run_id += 1

        if self.center_points > 0:
            centers = self._calculate_center_points()
            for _ in range(self.center_points):
                row = {
                    "RunID": run_id,
                    "Replicate": 1,
                    "DesignPoint": "Center",
                    "StdOrder": run_id,
                }
                for index, factor in enumerate(self.factors):
                    row[factor.name] = centers[index]
                design_data.append(row)
                run_id += 1

        self.design_matrix = pd.DataFrame(design_data)
        if self._blocking_requested():
            self._apply_regular_blocking()

        if self.randomize_flag:
            if self._blocking_requested():
                self._randomize_within_blocks()
            else:
                self.randomize(self.seed)

        self._store_factor_level_orders()
        return self.design_matrix

    def validate_design(self) -> bool:
        """Validate the factorial design and its optional block structure."""
        if not self.factors or self.replicates < 1:
            return False
        if any(len(factor.levels) < 2 for factor in self.factors):
            return False
        try:
            self._validate_blocking_configuration()
        except ValueError:
            return False
        return True

    def _resolve_model_order(self, max_order: int | None) -> int:
        """Resolve and validate a requested hierarchical interaction order."""
        if not self.factors:
            raise ValueError("At least one factor is required")
        if max_order is None:
            return len(self.factors)
        if isinstance(max_order, bool) or not isinstance(max_order, int):
            raise ValueError("max_order must be an integer or None")
        if max_order < 1:
            raise ValueError("max_order must be at least 1")
        if max_order > len(self.factors):
            raise ValueError(
                f"max_order cannot exceed the number of factors ({len(self.factors)})"
            )
        return max_order

    def model_terms(self, max_order: int | None = None) -> list[str]:
        """Return hierarchical factorial terms through ``max_order``.

        Parameters
        ----------
        max_order
            Highest interaction order to include. ``None`` returns the saturated
            factorial hierarchy through the interaction involving every factor.

        Returns
        -------
        list[str]
            Ordered effect names such as ``A``, ``A*B`` and ``A*B*C``.
        """
        order = self._resolve_model_order(max_order)
        names = [factor.name for factor in self.factors]
        return [
            "*".join(term)
            for interaction_order in range(1, order + 1)
            for term in combinations(names, interaction_order)
        ]

    def degrees_of_freedom(self, max_order: int | None = None) -> dict[str, int]:
        """Calculate factorial degrees of freedom for a hierarchical model.

        For a term involving factors in a set ``S``, the term degrees of freedom
        are the product ``prod(len(levels_j) - 1 for j in S)``. With
        ``max_order=None`` the model is saturated over the factorial treatment
        combinations. A finite ``max_order`` gives a truncated hierarchical model;
        omitted higher-order treatment variation remains in ``Error`` together
        with replication and center-point residual degrees of freedom.
        """
        order = self._resolve_model_order(max_order)
        factor_by_name = {factor.name: factor for factor in self.factors}
        dof: dict[str, int] = {}

        for term_name in self.model_terms(order):
            term_factors = term_name.split("*")
            dof[term_name] = prod(
                len(factor_by_name[name].levels) - 1 for name in term_factors
            )

        total_runs = int(self.n_runs())
        model_dof = sum(dof.values())
        dof["Error"] = total_runs - model_dof - 1
        dof["Total"] = total_runs - 1
        return dof

    def model_structure(self, max_order: int | None = None) -> dict[str, Any]:
        """Describe a saturated or truncated hierarchical factorial model."""
        order = self._resolve_model_order(max_order)
        dof = self.degrees_of_freedom(order)
        terms = self.model_terms(order)
        return {
            "max_order": order,
            "saturated": order == len(self.factors),
            "terms": terms,
            "model_degrees_of_freedom": sum(dof[term] for term in terms),
            "error_degrees_of_freedom": dof["Error"],
            "total_degrees_of_freedom": dof["Total"],
        }

    def calculate_effects(
        self,
        response_data: list[float],
        max_order: int = 2,
    ) -> dict[str, float]:
        """Calculate canonical two-level factorial effects.

        Factor levels are coded according to their declared order: the first
        level is ``-1`` and the second is ``+1``. The returned factorial effect
        is twice the corresponding coefficient in a regression using these
        coded columns and their products.
        """
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")
        if not self._is_two_level_design():
            raise ValueError("Effect calculation only supported for 2-level designs")
        if not (self.design_matrix["DesignPoint"] == "Factorial").all():
            raise ValueError(
                "Canonical factorial effects require factorial treatment points only"
            )

        return calculate_two_level_factorial_effects(
            self.design_matrix,
            response_data,
            [factor.name for factor in self.factors],
            max_order=max_order,
            level_orders={factor.name: factor.levels for factor in self.factors},
        )

    def _store_factor_level_orders(self) -> None:
        """Attach declared low/high level order for downstream analysis."""
        if self.design_matrix is None:
            return
        self.design_matrix.attrs["factor_level_orders"] = {
            factor.name: list(factor.levels) for factor in self.factors
        }

    def _blocking_requested(self) -> bool:
        """Return whether regular factorial blocking is requested."""
        return self.blocks is not None and self.blocks > 1

    def _validate_blocking_configuration(self) -> None:
        """Validate regular two-level factorial blocking semantics."""
        if self.blocks is None:
            if self.block_generators:
                raise ValueError("block_generators require a block count")
            return
        if isinstance(self.blocks, bool) or not isinstance(self.blocks, int):
            raise ValueError("blocks must be an integer or None")
        if self.blocks < 1:
            raise ValueError("blocks must be at least 1")
        if self.blocks == 1:
            if self.block_generators:
                raise ValueError("block_generators require more than one block")
            return
        if not self._is_two_level_design():
            raise ValueError(
                "Regular factorial blocking currently requires exactly two levels "
                "for every factor"
            )
        if self.center_points > 0:
            raise ValueError(
                "Center points are not yet supported inside regular factorial blocks"
            )

        names = [factor.name for factor in self.factors]
        if len(set(names)) != len(names):
            raise ValueError("Factor names must be unique when defining blocks")
        if self.blocks & (self.blocks - 1):
            raise ValueError(
                "blocks must be a power of two for regular factorial blocking"
            )

        max_blocks = 2 ** len(self.factors)
        if self.blocks > max_blocks:
            raise ValueError(
                f"At most {max_blocks} blocks are possible for "
                f"{len(self.factors)} two-level factors"
            )

        n_generators = self.blocks.bit_length() - 1
        if n_generators == len(self.factors) and not self.allow_main_effect_confounding:
            raise ValueError(
                "This block count necessarily confounds main effects; set "
                "allow_main_effect_confounding=True to request it explicitly"
            )

        if self.block_generators is not None:
            if len(self.block_generators) != n_generators:
                raise ValueError(
                    f"{self.blocks} blocks require exactly {n_generators} "
                    "independent block generators"
                )
            masks = [
                self._parse_block_generator(generator)
                for generator in self.block_generators
            ]
            self._validate_block_masks(masks, n_generators)

    def _parse_block_generator(self, expression: str) -> int:
        """Convert a generator expression into a GF(2) treatment word."""
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("Each block generator must be a non-empty string")
        parts = [part.strip() for part in expression.split("*")]
        if any(not part for part in parts):
            raise ValueError(f"Invalid block generator {expression!r}")
        if len(set(parts)) != len(parts):
            raise ValueError(f"Block generator {expression!r} repeats a factor name")

        factor_index = {factor.name: index for index, factor in enumerate(self.factors)}
        unknown = [name for name in parts if name not in factor_index]
        if unknown:
            raise ValueError(
                f"Unknown factor(s) in block generator {expression!r}: "
                + ", ".join(unknown)
            )

        mask = 0
        for name in parts:
            mask |= 1 << factor_index[name]
        return mask

    @staticmethod
    def _gf2_rank(masks: list[int]) -> int:
        """Return the row rank of treatment words over GF(2)."""
        basis: dict[int, int] = {}
        for mask in masks:
            value = mask
            while value:
                pivot = value.bit_length() - 1
                if pivot in basis:
                    value ^= basis[pivot]
                else:
                    basis[pivot] = value
                    break
        return len(basis)

    @staticmethod
    def _defining_masks(generators: list[int]) -> list[int]:
        """Return non-identity words in the block defining subgroup."""
        words = {0}
        for generator in generators:
            existing = tuple(words)
            words.update(word ^ generator for word in existing)
        return sorted(words - {0})

    def _validate_block_masks(self, masks: list[int], n_generators: int) -> None:
        """Validate generator independence and protected main effects."""
        if self._gf2_rank(masks) != n_generators:
            raise ValueError("Block generators must be linearly independent over GF(2)")

        main_effect_masks = [
            word for word in self._defining_masks(masks) if word.bit_count() == 1
        ]
        if main_effect_masks and not self.allow_main_effect_confounding:
            names = [self._mask_to_word(mask) for mask in main_effect_masks]
            raise ValueError(
                "Block defining contrasts confound main effect(s): "
                + ", ".join(names)
                + ". Set allow_main_effect_confounding=True only if intentional."
            )

    def _automatic_block_masks(self, n_generators: int) -> list[int]:
        """Construct deterministic independent block generators."""
        n_factors = len(self.factors)
        if n_generators == 0:
            return []
        if n_generators >= n_factors:
            return [1 << index for index in range(n_generators)]

        patterns = sorted(
            range(1, 2**n_generators),
            key=lambda value: (-value.bit_count(), value),
        )
        columns = [patterns[index % len(patterns)] for index in range(n_factors)]

        masks: list[int] = []
        for bit in range(n_generators):
            mask = 0
            for factor_index, pattern in enumerate(columns):
                if pattern & (1 << bit):
                    mask |= 1 << factor_index
            masks.append(mask)

        defining = self._defining_masks(masks)
        if self._gf2_rank(masks) == n_generators and all(
            word.bit_count() >= 2 for word in defining
        ):
            return masks

        anchor = 1 << (n_factors - 1)
        return [(1 << index) | anchor for index in range(n_generators)]

    def _resolve_block_masks(self) -> list[int]:
        """Resolve explicit or automatic generators to bit masks."""
        if not self._blocking_requested():
            return []
        assert self.blocks is not None
        n_generators = self.blocks.bit_length() - 1
        if self.block_generators is not None:
            masks = [
                self._parse_block_generator(generator)
                for generator in self.block_generators
            ]
        else:
            masks = self._automatic_block_masks(n_generators)
        self._validate_block_masks(masks, n_generators)
        return masks

    def _mask_to_word(self, mask: int) -> str:
        """Convert a treatment word to a readable interaction name."""
        return "*".join(
            factor.name
            for index, factor in enumerate(self.factors)
            if mask & (1 << index)
        )

    def block_structure(self) -> dict[str, Any]:
        """Return generators, defining contrasts, and block diagnostics."""
        if not self._blocking_requested():
            return {
                "n_blocks": 1,
                "generators": [],
                "defining_contrasts": [],
                "confounded_main_effects": [],
                "runs_per_block": int(self.n_factorial_runs()),
            }

        assert self.blocks is not None
        masks = self._resolve_block_masks()
        defining = self._defining_masks(masks)
        return {
            "n_blocks": self.blocks,
            "generators": [self._mask_to_word(mask) for mask in masks],
            "defining_contrasts": [self._mask_to_word(mask) for mask in defining],
            "confounded_main_effects": [
                self._mask_to_word(mask) for mask in defining if mask.bit_count() == 1
            ],
            "runs_per_block": int(self.n_factorial_runs() // self.blocks),
        }

    def _apply_regular_blocking(self) -> None:
        """Assign runs to blocks from treatment-interaction signs."""
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")
        if not (self.design_matrix["DesignPoint"] == "Factorial").all():
            raise ValueError(
                "Regular block assignment requires factorial treatment points only"
            )

        masks = self._resolve_block_masks()
        n_runs = len(self.design_matrix)
        coded_columns: list[np.ndarray] = []
        for factor in self.factors:
            values = self.design_matrix[factor.name].to_numpy()
            coded = np.where(
                values == factor.levels[0],
                -1,
                np.where(values == factor.levels[1], 1, 0),
            )
            if np.any(coded == 0):
                raise ValueError(
                    f"Unexpected level found while coding factor {factor.name!r}"
                )
            coded_columns.append(coded.astype(int))

        block_ids = np.ones(n_runs, dtype=int)
        for bit, mask in enumerate(masks):
            sign = np.ones(n_runs, dtype=int)
            for factor_index, coded in enumerate(coded_columns):
                if mask & (1 << factor_index):
                    sign *= coded
            block_ids += (sign > 0).astype(int) << bit

        self.design_matrix["Block"] = block_ids
        assert self.blocks is not None
        counts = self.design_matrix["Block"].value_counts()
        expected = n_runs // self.blocks
        if len(counts) != self.blocks or not (counts == expected).all():
            raise RuntimeError("Block generators did not produce balanced blocks")

        self.design_matrix = self.design_matrix.sort_values(
            ["Block", "StdOrder"], kind="stable"
        ).reset_index(drop=True)

    def _randomize_within_blocks(self) -> None:
        """Randomize run order independently inside each treatment block."""
        if self.design_matrix is None or "Block" not in self.design_matrix:
            raise ValueError("Blocked design matrix not generated")

        rng = np.random.default_rng(self.seed)
        randomized_blocks: list[pd.DataFrame] = []
        for block in sorted(self.design_matrix["Block"].unique()):
            frame = self.design_matrix[self.design_matrix["Block"] == block]
            randomized_blocks.append(
                frame.sample(
                    frac=1,
                    random_state=int(rng.integers(0, np.iinfo("int32").max)),
                )
            )

        self.design_matrix = pd.concat(randomized_blocks, ignore_index=True)
        if "RunOrder" in self.design_matrix.columns:
            self.design_matrix = self.design_matrix.drop(columns="RunOrder")
        self.design_matrix.insert(0, "RunOrder", range(1, len(self.design_matrix) + 1))
        self.randomized = True

    def blocking_scheme(self, block_size: int) -> pd.DataFrame:
        """Reassign an existing design using regular treatment contrasts."""
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated")
        if isinstance(block_size, bool) or not isinstance(block_size, int):
            raise ValueError("block_size must be a positive integer")
        if block_size <= 0:
            raise ValueError("block_size must be a positive integer")
        if not (self.design_matrix["DesignPoint"] == "Factorial").all():
            raise ValueError("blocking_scheme requires factorial treatment points only")

        n_runs = len(self.design_matrix)
        if n_runs % block_size != 0:
            raise ValueError("block_size must divide the number of factorial runs")
        n_blocks = n_runs // block_size
        if n_blocks < 2:
            raise ValueError("block_size must define at least two blocks")

        self.blocks = n_blocks
        self.block_generators = None
        self._validate_blocking_configuration()

        if "RunOrder" in self.design_matrix.columns:
            self.design_matrix = self.design_matrix.drop(columns="RunOrder")
        self.design_matrix = self.design_matrix.sort_values(
            "StdOrder", kind="stable"
        ).reset_index(drop=True)
        self._apply_regular_blocking()
        if self.randomize_flag:
            self._randomize_within_blocks()
        self._store_factor_level_orders()
        return self.design_matrix
