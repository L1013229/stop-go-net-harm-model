"""Partial rank correlation coefficients (PRCC).

Rank-transform every input and the target, then read the partial correlations off the inverse
of the rank-correlation matrix: for the correlation matrix C of [ranked inputs, ranked target],
the partial correlation between input i and the target, controlling for every other input, is
-P[i, y] / sqrt(P[i, i] * P[y, y]) with P = C^-1.

This is algebraically the residual-regression construction, which the test suite pins to 1e-10,
and it costs one matrix inversion rather than one least-squares solve per input, which is what
makes the bootstrap tractable at production sample sizes.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import rankdata


def _default_names(draws: dict[str, np.ndarray], target: np.ndarray) -> list[str]:
    return [k for k, v in draws.items()
            if np.ndim(v) == 1 and len(v) == len(target) and np.std(v) > 0]


def prcc(draws: dict[str, np.ndarray], target: np.ndarray,
         names: list[str] | None = None) -> dict[str, float]:
    names = names or _default_names(draws, target)
    M = np.column_stack([rankdata(draws[k]) for k in names] + [rankdata(target)])
    P = np.linalg.pinv(np.corrcoef(M, rowvar=False))
    d = np.sqrt(np.diag(P))
    return {k: float(-P[i, -1] / (d[i] * d[-1])) for i, k in enumerate(names)}


def prcc_bootstrap(draws: dict[str, np.ndarray], target: np.ndarray,
                   n_boot: int = 200, seed: int = 20260709,
                   names: list[str] | None = None) -> dict[str, tuple[float, float, float]]:
    """Point estimate plus a 2.5/97.5 percentile bootstrap interval per input."""
    rng = np.random.default_rng(seed)
    point = prcc(draws, target, names)
    names = list(point)
    n = len(target)
    samples: dict[str, list[float]] = {k: [] for k in names}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        sub = {k: draws[k][idx] for k in names}
        for k, v in prcc(sub, target[idx], names).items():
            samples[k].append(v)
    return {k: (point[k], float(np.percentile(samples[k], 2.5)),
                float(np.percentile(samples[k], 97.5))) for k in names}
