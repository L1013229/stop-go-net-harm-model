"""Sampling primitives for mtcpts.

Everything samples by inverse-CDF from portable uniform streams (PCG64), mirroring the
Paper-4/Paper-5 reproducibility standard: `rng.random()` + `ppf`, never distribution-
specific generator methods (whose algorithms are not guaranteed stable across numpy
versions).

SEJ quantities are equal-weight per-expert mixtures over fits exported by
scripts/export_sej_priors.py (drift-guarded against the companion study's canonical
Monte Carlo artefacts).
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.stats import beta as _beta
from scipy.stats import norm as _norm


# ---------------------------------------------------------------- prior families
@dataclass(frozen=True)
class Triangular:
    lo: float
    mode: float
    hi: float

    def sample(self, u: np.ndarray) -> np.ndarray:
        lo, m, hi = self.lo, self.mode, self.hi
        span, fc = hi - lo, (m - lo) / (hi - lo)
        left = lo + np.sqrt(u * span * (m - lo))
        right = hi - np.sqrt((1.0 - u) * span * (hi - m))
        return np.where(u < fc, left, right)


@dataclass(frozen=True)
class LogUniform:
    lo: float
    hi: float

    def sample(self, u: np.ndarray) -> np.ndarray:
        return np.exp(np.log(self.lo) + u * (np.log(self.hi) - np.log(self.lo)))


@dataclass(frozen=True)
class Uniform:
    lo: float
    hi: float

    def sample(self, u: np.ndarray) -> np.ndarray:
        return self.lo + u * (self.hi - self.lo)


@dataclass(frozen=True)
class Fixed:
    value: float

    def sample(self, u: np.ndarray) -> np.ndarray:
        return np.full_like(u, self.value, dtype=float)


# ------------------------------------------------------------- SEJ expert mixtures
@dataclass(frozen=True)
class ExpertFit:
    family: str  # log10normal | beta | lognormal
    p1: float
    p2: float

    def ppf(self, u: np.ndarray) -> np.ndarray:
        if self.family == "log10normal":
            return 10.0 ** (self.p1 + self.p2 * _norm.ppf(u))
        if self.family == "beta":
            return _beta.ppf(u, self.p1, self.p2)  # fraction on [0, 1]
        if self.family == "lognormal":
            return np.exp(self.p1 + self.p2 * _norm.ppf(u))
        raise ValueError(self.family)


@dataclass(frozen=True)
class ExpertMixture:
    """Equal-weight mixture over per-expert fits; expert index supplied externally so
    RE and SEV can be coupled through the SAME expert draw (Paper-4 pattern)."""

    quantity_id: str
    fits: tuple[ExpertFit, ...]
    expert_uids: tuple[str, ...]

    @property
    def n_experts(self) -> int:
        return len(self.fits)

    def sample_with_index(self, idx: np.ndarray, u: np.ndarray) -> np.ndarray:
        out = np.empty_like(u, dtype=float)
        for i, f in enumerate(self.fits):
            m = idx == i
            if m.any():
                out[m] = f.ppf(u[m])
        return out

    def sample(self, rng: np.random.Generator, n: int) -> np.ndarray:
        idx = rng.integers(0, self.n_experts, size=n)
        return self.sample_with_index(idx, rng.random(n))


def load_sej_mixtures(path: str | Path) -> dict[str, ExpertMixture]:
    """Load the exported fitted-parameter table into ExpertMixture objects.

    Experts are ordered by uid within each quantity (deterministic); quantities that
    must couple through a shared expert draw (RE_k with SEV_k) have IDENTICAL uid
    orderings by construction, which `coupled_index_ok` verifies.
    """
    rows: dict[str, list[tuple[str, ExpertFit]]] = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["quantity_id"], []).append(
                (r["expert_uid"], ExpertFit(r["family"], float(r["p1"]), float(r["p2"])))
            )
    out = {}
    for qid, pairs in rows.items():
        pairs.sort(key=lambda t: t[0])
        out[qid] = ExpertMixture(
            quantity_id=qid,
            fits=tuple(f for _, f in pairs),
            expert_uids=tuple(uid for uid, _ in pairs),
        )
    return out


def coupled_index_ok(a: ExpertMixture, b: ExpertMixture) -> bool:
    """True when two mixtures can share one expert-index stream (same uid ordering)."""
    return a.expert_uids == b.expert_uids


# ------------------------------------------------------------- pooled release form
@dataclass(frozen=True)
class PooledSEJ:
    """The public-release form of the Scenario C priors: a large coupled sample drawn from
    the equal-weight per-expert mixtures by scripts/export_pooled_priors.py, holding no expert
    identifier and no per-expert parameter. `sample_pairs` returns coupled (rate, severity)
    rows for one pathway, so the coupling the model relies on is preserved."""

    re1_rate: np.ndarray
    sev1_p: np.ndarray
    re3_rate: np.ndarray
    sev3_p: np.ndarray
    d15_multiplier: np.ndarray

    @property
    def n_rows(self) -> int:
        return len(self.re1_rate)

    def sample_pairs(self, rng: np.random.Generator, n: int, pathway: str) -> tuple[np.ndarray, np.ndarray]:
        idx = rng.integers(0, self.n_rows, n)
        if pathway == "1":
            return self.re1_rate[idx], self.sev1_p[idx]
        if pathway == "3":
            return self.re3_rate[idx], self.sev3_p[idx]
        raise ValueError(pathway)


def load_sej_pooled(path: str | Path) -> PooledSEJ:
    z = np.load(path)
    return PooledSEJ(re1_rate=z["re1_rate"], sev1_p=z["sev1_p"], re3_rate=z["re3_rate"],
                     sev3_p=z["sev3_p"], d15_multiplier=z["d15_multiplier"])


def load_sej(config_dir: str | Path):
    """Prefer the per-expert fits (restricted store, bit-for-bit reproduction); fall back to
    the pooled release form when the fits are absent, as they are in the public release."""
    config_dir = Path(config_dir)
    fits = config_dir / "sej_scenario_c_fits.csv"
    if fits.exists():
        return load_sej_mixtures(fits)
    pooled = config_dir / "sej_scenario_c_pooled.npz"
    if pooled.exists():
        return load_sej_pooled(pooled)
    raise FileNotFoundError(f"no Scenario C priors in {config_dir} (fits csv or pooled npz)")
