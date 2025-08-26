from __future__ import annotations

"""Design efficiency metrics and visualization utilities."""

from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


def _information_matrix(design_matrix: pd.DataFrame) -> np.ndarray:
    """Return the information matrix ``X^T X`` of a design matrix.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Encoded design matrix including intercept column.

    Returns
    -------
    numpy.ndarray
        Information matrix ``X^T X``.
    """

    X = np.asarray(design_matrix)
    return X.T @ X


def d_efficiency(design_matrix: pd.DataFrame) -> float:
    r"""Compute D-efficiency of a design.

    D-efficiency is defined as ``(\det(X^T X)^{1/p}) / n`` where ``p`` is the
    number of parameters and ``n`` is the run count.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Encoded design matrix including intercept.

    Returns
    -------
    float
        D-efficiency value.

    References
    ----------
    .. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*,
           9th ed. Wiley.
    """

    info = _information_matrix(design_matrix)
    n, p = design_matrix.shape
    det = np.linalg.det(info)
    return float(det ** (1 / p) / n)


def a_efficiency(design_matrix: pd.DataFrame) -> float:
    r"""Compute A-efficiency of a design.

    A-efficiency is ``p / (\operatorname{trace}((X^T X)^{-1}) \cdot n)``.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Encoded design matrix including intercept.

    Returns
    -------
    float
        A-efficiency value.
    """

    info = _information_matrix(design_matrix)
    n, p = design_matrix.shape
    inv_trace = np.trace(np.linalg.inv(info))
    return float(p / (inv_trace * n))


def g_efficiency(
    design_matrix: pd.DataFrame,
    candidate_points: pd.DataFrame,
) -> float:
    """Compute G-efficiency for a design.

    G-efficiency is the reciprocal of the maximum scaled prediction variance
    over the candidate set.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Design matrix used to fit the model.
    candidate_points : pandas.DataFrame
        Candidate matrix covering the region of interest.

    Returns
    -------
    float
        G-efficiency value.
    """

    info_inv = np.linalg.inv(_information_matrix(design_matrix))
    Xc = np.asarray(candidate_points)
    pv = np.einsum("ij,jk,ik->i", Xc, info_inv, Xc)
    return float(1 / pv.max())


def i_efficiency(
    design_matrix: pd.DataFrame,
    candidate_points: pd.DataFrame,
) -> float:
    """Compute I-efficiency for a design.

    I-efficiency is the reciprocal of the average scaled prediction variance
    over the candidate set.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Design matrix used to fit the model.
    candidate_points : pandas.DataFrame
        Candidate matrix covering the region of interest.

    Returns
    -------
    float
        I-efficiency value.
    """

    info_inv = np.linalg.inv(_information_matrix(design_matrix))
    Xc = np.asarray(candidate_points)
    pv = np.einsum("ij,jk,ik->i", Xc, info_inv, Xc)
    return float(1 / pv.mean())


def relative_efficiency(
    design_a: pd.DataFrame,
    design_b: pd.DataFrame,
    metric: str = "D",
) -> float:
    """Compare efficiencies of two designs.

    Parameters
    ----------
    design_a, design_b : pandas.DataFrame
        Design matrices to compare.
    metric : {"D", "A"}, optional
        Efficiency measure for comparison, by default ``"D"``.

    Returns
    -------
    float
        Relative efficiency ``eff_a / eff_b``.
    """

    metrics = {"D": d_efficiency, "A": a_efficiency}
    if metric not in metrics:
        raise ValueError("metric must be 'D' or 'A'")
    eff_a = metrics[metric](design_a)
    eff_b = metrics[metric](design_b)
    return float(eff_a / eff_b)


def variance_inflation_factors(design_matrix: pd.DataFrame) -> pd.Series:
    """Compute variance inflation factors (VIF) for regressors.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Encoded design matrix including intercept.

    Returns
    -------
    pandas.Series
        VIF values indexed by column name.
    """

    X = np.asarray(design_matrix)
    info = X.T @ X
    info_inv = np.linalg.inv(info)
    vif_vals = np.diag(info_inv) * np.diag(info)
    return pd.Series(vif_vals, index=design_matrix.columns)


def estimate_power(
    design_matrix: pd.DataFrame,
    effect_contrast: np.ndarray,
    effect_size: float,
    sigma: float = 1.0,
    alpha: float = 0.05,
) -> float:
    """Estimate power for detecting a specified contrast.

    Parameters
    ----------
    design_matrix : pandas.DataFrame
        Encoded design matrix including intercept.
    effect_contrast : numpy.ndarray
        Contrast vector ``c`` specifying the linear combination of coefficients
        under test.
    effect_size : float
        Magnitude of the effect along ``c``.
    sigma : float, optional
        Residual standard deviation, by default ``1.0``.
    alpha : float, optional
        Significance level, by default ``0.05``.

    Returns
    -------
    float
        Approximate statistical power.
    """

    X = np.asarray(design_matrix)
    n, p = X.shape
    info_inv = np.linalg.inv(X.T @ X)
    se = sigma * np.sqrt(effect_contrast @ info_inv @ effect_contrast)
    df = n - p
    tcrit = stats.t.ppf(1 - alpha / 2, df)
    ncp = effect_size / se
    power = 1 - stats.nct.cdf(tcrit, df, ncp) + stats.nct.cdf(-tcrit, df, ncp)
    return float(power)


def plot_efficiencies(efficiencies: Dict[str, float]) -> plt.Axes:
    """Plot efficiency metrics for multiple designs.

    Parameters
    ----------
    efficiencies : dict
        Mapping of design labels to efficiency values.

    Returns
    -------
    matplotlib.axes.Axes
        Axes containing a bar chart of efficiencies.
    """

    labels = list(efficiencies)
    values = [efficiencies[k] for k in labels]
    fig, ax = plt.subplots()
    ax.bar(labels, values, color="steelblue")
    ax.set_ylabel("Efficiency")
    ax.set_ylim(0, max(values) * 1.1)
    ax.set_title("Design Efficiency Comparison")
    return ax


__all__ = [
    "d_efficiency",
    "a_efficiency",
    "g_efficiency",
    "i_efficiency",
    "relative_efficiency",
    "variance_inflation_factors",
    "estimate_power",
    "plot_efficiencies",
]
