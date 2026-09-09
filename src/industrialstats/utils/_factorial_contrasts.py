"""Canonical contrast calculations for two-level factorial experiments."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd


def calculate_two_level_factorial_effects(
    design_matrix: pd.DataFrame,
    response_data: Sequence[float] | np.ndarray,
    factor_names: Sequence[str],
    *,
    max_order: int = 2,
    level_orders: Mapping[str, Sequence[Any]] | None = None,
) -> dict[str, float]:
    r"""Calculate canonical factorial effects from :math:`-1/+1` contrasts.

    For a balanced two-level factorial design, the model written in coded
    variables is

    .. math::

        y = \beta_0 + \sum_S \beta_S x_S + \varepsilon,

    where ``x_S`` is the product of the coded columns in term ``S``. The
    conventional factorial effect is ``2 * beta_S``. Orthogonality gives

    .. math::

        \widehat{\mathrm{effect}}_S
        = \frac{2 x_S^T y}{x_S^T x_S}.

    The same expression handles equal replication without changing the effect
    estimate.

    Parameters
    ----------
    design_matrix
        Rows of the experiment containing the factor columns.
    response_data
        Numeric response aligned row-for-row with ``design_matrix``.
    factor_names
        Ordered factor names. Interaction names preserve this order.
    max_order
        Highest interaction order to calculate. ``1`` returns main effects
        only. Values larger than the number of factors are clipped.
    level_orders
        Optional mapping from factor name to ``(low, high)`` levels. When it is
        omitted, levels are sorted to preserve the historical
        :class:`EffectsAnalysis` convention.

    Returns
    -------
    dict[str, float]
        Main and interaction effects keyed by names such as ``A`` and ``A*B``.

    Raises
    ------
    ValueError
        If responses are misaligned, a factor is not two-level, factor names
        are invalid, or ``max_order`` is less than one.
    """
    names = list(factor_names)
    if not names:
        raise ValueError("At least one factor is required")
    if len(set(names)) != len(names):
        raise ValueError("Factor names must be unique")
    if max_order < 1:
        raise ValueError("max_order must be at least 1")

    response = np.asarray(response_data, dtype=float)
    if response.ndim != 1:
        raise ValueError("response_data must be one-dimensional")
    if len(response) != len(design_matrix):
        raise ValueError("Response data length must match design matrix rows")
    if not np.isfinite(response).all():
        raise ValueError("response_data must contain only finite numeric values")

    missing = [name for name in names if name not in design_matrix.columns]
    if missing:
        raise ValueError("Missing factor column(s): " + ", ".join(missing))

    coded_columns: dict[str, np.ndarray] = {}
    for name in names:
        series = design_matrix[name]
        if level_orders is None:
            try:
                levels = sorted(series.dropna().unique().tolist())
            except TypeError as exc:
                raise ValueError(
                    f"Factor {name!r} levels must be orderable or level_orders must be supplied"
                ) from exc
        else:
            if name not in level_orders:
                raise ValueError(f"Missing level order for factor {name!r}")
            levels = list(level_orders[name])

        if len(levels) != 2 or levels[0] == levels[1]:
            raise ValueError(f"Factor {name!r} must have exactly two distinct levels")

        low, high = levels
        values = series.to_numpy()
        valid = (values == low) | (values == high)
        if not np.all(valid):
            raise ValueError(
                f"Factor {name!r} contains values outside its declared two levels"
            )
        coded_columns[name] = np.where(values == high, 1.0, -1.0)

    effects: dict[str, float] = {}
    effective_order = min(max_order, len(names))
    for order in range(1, effective_order + 1):
        for term in combinations(names, order):
            contrast = np.ones(len(design_matrix), dtype=float)
            for name in term:
                contrast *= coded_columns[name]

            denominator = float(np.dot(contrast, contrast))
            if denominator == 0.0:
                raise ValueError(f"Contrast {'*'.join(term)!r} is not estimable")
            effects["*".join(term)] = float(
                2.0 * np.dot(contrast, response) / denominator
            )

    return effects
