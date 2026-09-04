from __future__ import annotations

"""Fractional factorial design implementation."""

from dataclasses import dataclass
from itertools import combinations, product
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .base import ExperimentalDesign, Factor


def _bit_count(mask: int) -> int:
    """Return the number of set bits in ``mask``."""

    return int(mask.bit_count())


def _split_generator_terms(generator: str, base_names: Sequence[str]) -> List[str]:
    """Split a generator string into base factor names.

    The helper accepts generator expressions in one of the following formats:

    - ``"A*B*C"`` or ``"A:B:C"``
    - ``"A B C"`` or ``"A,B,C"``
    - Concatenated one-character factor names (e.g. ``"ABC"``)

    Parameters
    ----------
    generator:
        Generator expression.
    base_names:
        Candidate factor names (ordered) used when disambiguating concatenated
        representations.

    Returns
    -------
    list[str]
        List of factor names referenced by the generator.
    """

    if not generator:
        raise ValueError("Generator expression must be non-empty")

    delimiters = ["*", ":", ","]
    for delim in delimiters:
        if delim in generator:
            return [token.strip() for token in generator.split(delim) if token.strip()]
    if " " in generator:
        return [token.strip() for token in generator.split() if token.strip()]

    # Fall back to greedy matching of known base names (longest first).
    remaining = generator
    tokens: List[str] = []
    sorted_names = sorted(base_names, key=len, reverse=True)
    while remaining:
        matched = False
        for name in sorted_names:
            if remaining.startswith(name):
                tokens.append(name)
                remaining = remaining[len(name) :]
                matched = True
                break
        if not matched:
            raise ValueError(
                f"Cannot parse generator '{generator}'. Provide '*' or ':' separated names."
            )
    return tokens


def _mask_from_terms(terms: Sequence[str], name_to_index: Dict[str, int]) -> int:
    """Convert a sequence of factor names to a bit mask."""

    mask = 0
    for name in terms:
        try:
            idx = name_to_index[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Unknown factor '{name}' in generator definition"
            ) from exc
        mask |= 1 << idx
    return mask


def _word_length_pattern(words: Iterable[int]) -> Dict[int, int]:
    """Compute the word-length pattern for a collection of defining words."""

    pattern: Dict[int, int] = {}
    for word in words:
        if word == 0:
            continue
        length = _bit_count(word)
        pattern[length] = pattern.get(length, 0) + 1
    return pattern


def _extend_basis(basis: List[int], mask: int) -> Optional[List[int]]:
    """Extend a row-reduced basis in :math:`\\mathrm{GF}(2)` with ``mask``."""

    new_basis = basis.copy()
    vector = mask
    while vector:
        lsb = vector & -vector
        idx = lsb.bit_length() - 1
        if new_basis[idx]:
            vector ^= new_basis[idx]
        else:
            new_basis[idx] = vector
            return new_basis
    return None


def _combine_words(existing: Iterable[int], new_word: int) -> List[int]:
    """Combine an existing defining relation with ``new_word``."""

    updated = set(existing)
    updated.add(new_word)
    for word in existing:
        updated.add(word ^ new_word)
    return sorted(updated)


@dataclass
class _SearchResult:
    resolution: int
    pattern: Dict[int, int]
    generators: Tuple[int, ...]


class _MinimumAberrationSearch:
    """Search for minimum aberration generator sets."""

    def __init__(
        self, base_count: int, generator_count: int, candidates: Sequence[int]
    ):
        self.base_count = base_count
        self.generator_count = generator_count
        self.candidates = list(candidates)
        self.best: Optional[_SearchResult] = None

    def run(self) -> Tuple[int, ...]:
        """Execute the search and return generator masks."""

        basis = [0] * self.base_count
        self._dfs(0, [], basis, [])
        if not self.best:
            raise RuntimeError(
                "Unable to identify a minimum aberration generator set for the provided"
                " configuration."
            )
        return self.best.generators

    def _dfs(
        self,
        start: int,
        chosen: List[int],
        basis: List[int],
        defining_words: List[int],
    ) -> None:
        if len(chosen) == self.generator_count:
            pattern = _word_length_pattern(defining_words)
            resolution = min(pattern) if pattern else float("inf")
            result = _SearchResult(
                resolution=int(resolution), pattern=pattern, generators=tuple(chosen)
            )
            if self._is_better(result):
                self.best = result
            return

        for idx in range(start, len(self.candidates)):
            mask = self.candidates[idx]
            new_basis = _extend_basis(basis, mask)
            if new_basis is None:
                continue
            alias_index = self.base_count + len(chosen)
            new_word = mask | (1 << alias_index)
            new_defining = _combine_words(defining_words, new_word)
            pattern = _word_length_pattern(new_defining)
            if self.best:
                best_res = self.best.resolution
                candidate_res = min(pattern) if pattern else float("inf")
                if candidate_res < best_res:
                    continue
                if candidate_res == best_res:
                    # Compare counts for the minimal resolution length.
                    current_count = pattern.get(candidate_res, 0)
                    best_count = self.best.pattern.get(best_res, 0)
                    if current_count > best_count:
                        continue
            chosen.append(mask)
            self._dfs(idx + 1, chosen, new_basis, new_defining)
            chosen.pop()

    def _is_better(self, result: _SearchResult) -> bool:
        if not self.best:
            return True
        if result.resolution > self.best.resolution:
            return True
        if result.resolution < self.best.resolution:
            return False
        # Lexicographic comparison of the word-length pattern counts.
        max_length = max(
            max(result.pattern, default=0), max(self.best.pattern, default=0)
        )
        for length in range(result.resolution, max_length + 1):
            cand = result.pattern.get(length, 0)
            current = self.best.pattern.get(length, 0)
            if cand < current:
                return True
            if cand > current:
                return False
        # Tie-breaker: prefer lexicographically smaller generator masks.
        return result.generators < self.best.generators


class FractionalFactorialDesign(ExperimentalDesign):
    """Two-level fractional factorial design.

    This class generates regular two-level fractional factorial designs for
    three to fifteen factors and automatically selects minimum aberration
    generator strings for the most common fractions (:math:`1/2`, :math:`1/4`,
    :math:`1/8`, and :math:`1/16`).  The implementation mirrors the confounding
    analysis strategy described in :mod:`industrialstats.designs.README` by
    constructing the defining relation of the design and deriving alias chains
    through linear algebra over :math:`\\mathrm{GF}(2)`.

    Notes
    -----
    * All factors must be two-level factors with exactly two entries in
      ``Factor.levels``.
    * Fraction denominators must be powers of two; the numerator is assumed to
      be one.
    * When ``generators`` are not supplied, the class performs a constrained
      search for generator sets that maximise the design resolution and, as a
      tie-breaker, minimise the word-length pattern (the minimum aberration
      criterion of Montgomery and Wu & Hamada).
    * Alias structures reported by :meth:`alias_structure` include **all**
      factorial effects, not only main effects and two-factor interactions.

    References
    ----------
    Montgomery, D. C. (2017). *Design and Analysis of Experiments* (9th ed.).
        Wiley.
    Wu, C. F. J., & Hamada, M. S. (2009). *Experiments: Planning, Analysis, and
        Optimization* (2nd ed.). Wiley.
    Groemping, U. (2014). "R package FrF2 for creating and analysing 2-level
        factorial designs". *Journal of Statistical Software*, 56(1).
    Xu, H. (2005). "A catalogue of three-level and four-level fractional
        factorial designs with minimum aberration". *Technometrics*, 47(3).
    NIST/SEMATECH (2012). *e-Handbook of Statistical Methods*, Chapter 5.3.
    "FrF2" R package documentation for ``catlg52`` (minimum aberration tables).
    "Montgomery" Chapter 8 examples on foldover strategies.
    "NIST foldover guidance" on mitigating aliasing.
    "Xu & Wu (2001)" alias chain construction using defining relations.

    Examples
    --------
    >>> from industrialstats.designs.base import Factor
    >>> factors = [Factor(name, [-1, 1]) for name in "ABCDEFG"]
    >>> design = FractionalFactorialDesign(factors, fraction="1/8")
    >>> design.generators
    ['A*B*C', 'A*B*D', 'A*C*D']
    >>> metrics = design.resolution_analysis()
    >>> metrics["resolution"]
    4
    >>> alias = design.alias_structure()
    >>> alias['A'][:3]
    ['A', 'A:B:C:F:G', 'A:B:D:E:G']
    >>> design.foldover_options()[0]['type']
    'full'
    """

    def __init__(
        self,
        factors: List[Factor],
        fraction: str = "1/2",
        generators: Optional[List[str]] = None,
        resolution: Optional[int] = None,
        replicates: int = 1,
        randomize: bool = True,
    ) -> None:
        """Initialize fractional factorial design.

        Parameters
        ----------
        factors : list[Factor]
            Factors in the experiment. Must all have two levels.
        fraction : str, optional
            Fraction of the full design, e.g. ``"1/2"`` or ``"1/4"``.
        generators : list[str], optional
            Generator strings using factor names.
        resolution : int, optional
            Desired design resolution (for reference only).
        replicates : int, optional
            Number of replicates.
        randomize : bool, optional
            Whether to randomize run order.
        """
        super().__init__("Fractional Factorial Design")
        self.factors = factors
        self.fraction = fraction
        self.generators = generators or []
        self.requested_resolution = resolution
        self.replicates = replicates
        self.randomize_flag = randomize
        self._coded_matrix: Optional[pd.DataFrame] = None

        factor_count = len(factors)
        if factor_count < 3 or factor_count > 15:
            raise ValueError(
                "Fractional factorial designs support between 3 and 15 factors"
            )
        if not all(len(f.levels) == 2 for f in factors):
            raise ValueError("All factors must have exactly two levels")

        try:
            numerator, denominator = fraction.split("/")
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(
                "Fraction must be provided as 'numerator/denominator'"
            ) from exc
        if numerator.strip() != "1":
            raise ValueError("Only regular fractions with numerator 1 are supported")
        denom = int(denominator)
        p = int(np.log2(denom))
        if 2**p != denom:
            raise ValueError("Fraction denominator must be a power of 2")
        self.p = p

        self._base_count = factor_count - p
        if self._base_count <= 0:
            raise ValueError(
                "Number of generators exceeds number of available base factors"
            )

        if not self.generators:
            self.generators = self._auto_generators()

    def _auto_generators(self) -> List[str]:
        """Automatically identify minimum aberration generators.

        Returns
        -------
        list[str]
            Generator expressions using base factor names.
        """

        base_names = [factor.name for factor in self.factors[: self._base_count]]
        name_to_index = {name: idx for idx, name in enumerate(base_names)}
        # Generate candidate masks grouped by size. Larger interactions are
        # preferred to achieve higher resolution while keeping the search space
        # tractable for up to fifteen factors.
        candidates_by_length: Dict[int, List[int]] = {}
        for mask in range(1, 1 << self._base_count):
            length = _bit_count(mask)
            candidates_by_length.setdefault(length, []).append(mask)

        candidates: List[int] = []
        max_per_length = 12 if self._base_count > 6 else None
        for length in sorted(candidates_by_length, reverse=True):
            masks = sorted(candidates_by_length[length])
            if max_per_length is not None:
                masks = masks[:max_per_length]
            candidates.extend(masks)

        search = _MinimumAberrationSearch(self._base_count, self.p, candidates)
        best_masks = search.run()

        generator_strings: List[str] = []
        for mask in best_masks:
            terms = [name for name, idx in name_to_index.items() if mask & (1 << idx)]
            terms.sort(key=lambda item: name_to_index[item])
            generator_strings.append("*".join(terms))
        return generator_strings

    def _coded_levels(self) -> Dict[str, List[int]]:
        return {factor.name: [-1, 1] for factor in self.factors}

    def _parsed_generators(self) -> List[List[str]]:
        base_names = [factor.name for factor in self.factors[: self._base_count]]
        return [_split_generator_terms(gen, base_names) for gen in self.generators]

    @staticmethod
    def _evaluate_generator(terms: Sequence[str], row: Dict[str, int]) -> int:
        value = 1
        for name in terms:
            value *= row[name]
        return value

    def _generator_masks(self) -> List[int]:
        base_names = [factor.name for factor in self.factors[: self._base_count]]
        name_to_index = {name: idx for idx, name in enumerate(base_names)}
        masks: List[int] = []
        for offset, terms in enumerate(self._parsed_generators()):
            base_mask = _mask_from_terms(terms, name_to_index)
            alias_index = self._base_count + offset
            masks.append(base_mask | (1 << alias_index))
        return masks

    def _defining_words(self) -> List[int]:
        generator_masks = self._generator_masks()
        words: List[int] = []
        for r in range(1, len(generator_masks) + 1):
            for combo in combinations(generator_masks, r):
                word = 0
                for mask in combo:
                    word ^= mask
                words.append(word)
        return sorted(set(words))

    def _mask_to_effect(self, mask: int) -> str:
        names = [
            self.factors[idx].name
            for idx in range(len(self.factors))
            if mask & (1 << idx)
        ]
        return ":".join(names)

    def calculate_resolution(self) -> Tuple[Optional[int], Dict[int, int]]:
        """Return the design resolution and its word-length pattern."""

        pattern = _word_length_pattern(self._defining_words())
        if not pattern:
            return None, {}
        return min(pattern), pattern

    def verify_resolution(self, minimum: int) -> bool:
        """Check that the design resolution meets ``minimum``.

        Raises
        ------
        ValueError
            If the design resolution is undefined or below ``minimum``.
        """

        resolution, _ = self.calculate_resolution()
        if resolution is None:
            raise ValueError("Resolution is undefined for a design without generators")
        if resolution < minimum:
            raise ValueError(
                f"Design resolution {resolution} is below the required minimum of {minimum}."
            )
        return True

    def generate_design(self) -> pd.DataFrame:
        """Generate fractional factorial design matrix."""
        base_factors = self.factors[: self._base_count]
        alias_factors = self.factors[self._base_count :]

        base_names = [factor.name for factor in base_factors]
        parsed_generators = self._parsed_generators()
        runs = list(product([-1, 1], repeat=len(base_names)))
        data = []
        run_id = 1
        for rep in range(1, self.replicates + 1):
            for run in runs:
                row = dict(zip(base_names, run))
                for factor, terms in zip(alias_factors, parsed_generators):
                    row[factor.name] = self._evaluate_generator(terms, row)
                data.append({"RunID": run_id, "Replicate": rep, **row})
                run_id += 1

        coded_df = pd.DataFrame(data)
        df = coded_df.copy()
        for factor in self.factors:
            mapping = {-1: factor.levels[0], 1: factor.levels[1]}
            df[factor.name] = df[factor.name].map(mapping)

        if self.randomize_flag:
            df = df.sample(frac=1, random_state=None).reset_index(drop=True)
            df.insert(0, "RunOrder", range(1, len(df) + 1))
            self.randomized = True
        self.design_matrix = df
        self._coded_matrix = coded_df
        return df

    def validate_design(self) -> bool:
        """Validate fractional factorial parameters."""
        return (
            3 <= len(self.factors) <= 15
            and all(len(f.levels) == 2 for f in self.factors)
            and self.replicates > 0
        )

    def alias_structure(self) -> Dict[str, List[str]]:
        """Return alias chains for all factorial effects.

        The alias chains are computed by applying the defining relation of the
        design to every factorial effect.  Each entry contains the canonical
        effect (lexicographically smallest mask) followed by the remaining
        members of its alias class.
        """

        words = self._defining_words()
        total_factors = len(self.factors)
        alias_map: Dict[str, List[str]] = {}
        processed: set[int] = set()
        for mask in range(1, 1 << total_factors):
            if mask in processed:
                continue
            alias_class = {mask}
            for word in words:
                alias_class.add(mask ^ word)
            canonical = min(alias_class)
            if canonical != mask:
                continue
            canonical_name = self._mask_to_effect(canonical)
            effect_names = sorted(
                self._mask_to_effect(alias_mask) for alias_mask in alias_class
            )
            ordered = [canonical_name] + [
                name for name in effect_names if name != canonical_name
            ]
            alias_map[canonical_name] = ordered
            processed.update(alias_class)
        return alias_map

    def resolution_analysis(self) -> Dict[str, Any]:
        """Analyze design resolution and clarity."""
        resolution, pattern = self.calculate_resolution()
        if resolution is None:
            return {
                "resolution": None,
                "word_length_pattern": {},
                "minimum_aberration": [],
                "meets_requested_resolution": None,
            }
        max_length = max(pattern)
        aberration = [
            (length, pattern.get(length, 0))
            for length in range(resolution, max_length + 1)
        ]
        meets = None
        if self.requested_resolution is not None:
            meets = resolution >= self.requested_resolution
        return {
            "resolution": resolution,
            "word_length_pattern": pattern,
            "minimum_aberration": aberration,
            "meets_requested_resolution": meets,
        }

    def foldover_options(self) -> List[Dict[str, Any]]:
        """Suggest foldover strategies with supporting metadata.

        Foldover proposals follow Montgomery's guidance: a *full* foldover adds
        a replicate with all signs reversed, while *partial* foldovers target
        problematic columns.  The suggestions focus on breaking aliases for main
        effects with the longest alias chains.
        """

        resolution_info = self.resolution_analysis()
        resolution = resolution_info["resolution"]
        alias_map = self.alias_structure()
        base_names = [factor.name for factor in self.factors[: self._base_count]]
        alias_names = [factor.name for factor in self.factors[self._base_count :]]
        parsed = self._parsed_generators()

        severity: List[Tuple[str, int, List[str]]] = []
        for factor in self.factors:
            chain = alias_map.get(factor.name, [factor.name])
            severity.append((factor.name, len(chain) - 1, chain))
        severity.sort(key=lambda item: (-item[1], item[0]))

        # Full foldover suggestion.
        expected_resolution = (
            None if resolution is None else min(resolution + 1, len(self.factors))
        )
        options: List[Dict[str, Any]] = [
            {
                "type": "full",
                "description": (
                    "Add a full foldover by reversing the signs of all generators. "
                    "This mitigates main-effect aliasing and typically improves the resolution by one."
                ),
                "generators_to_reverse": self.generators,
                "expected_resolution": expected_resolution,
            }
        ]

        # Partial foldovers for the most aliased main effects.
        for factor_name, _, chain in severity[: min(3, len(severity))]:
            impacted_generators = []
            for gen, terms, alias_name in zip(self.generators, parsed, alias_names):
                if factor_name == alias_name or factor_name in terms:
                    impacted_generators.append(gen)
            options.append(
                {
                    "type": "partial",
                    "factor": factor_name,
                    "description": (
                        f"Fold over factor {factor_name} (reverse signs of runs where it is high) "
                        "to separate it from its aliases."
                    ),
                    "generators_to_reverse": impacted_generators,
                    "confounded_with": [
                        effect for effect in chain if effect != factor_name
                    ],
                }
            )

        return options
