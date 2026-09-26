"""Severity engines for mtcpts.

Curve registry ported from the companion advance-warning model (aw_model
risk_functions.py), whose provenance was verified against primary sources on
2026-07-04 (rosen_pedestrian_2010 GIDAS regressions; Wang 2022 NHTSA DOT HS 813 219
delta-V curves). This module adds the W5 head-on machinery: braking-adjusted closing
speed, momentum delta-V split between vehicles, per-occupant curve evaluation, and
the event-level P(>=1 DSI) = 1 - prod(1 - p_i) conversion (M1 finding 8: the model's
unit is expected serious-harm EVENTS, a collision with at least one DSI outcome).
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np

MPH_PER_KMH = 1.0 / 1.609344

WORKER_CURVES: Dict[str, Dict[str, Any]] = {
    "rosen_mais3plus": {"a": -4.6, "b": 0.078, "speed_unit": "kmh"},
    "rosen_fatality": {"a": -7.5, "b": 0.096, "speed_unit": "kmh"},
}
OCCUPANT_CURVES: Dict[str, Dict[str, Any]] = {
    "wang_mais3plus_all": {"a": -6.9540, "b": 0.1637, "speed_unit": "mph"},
    "wang_mais3plus_frontal": {"a": -6.9774, "b": 0.1620, "speed_unit": "mph"},
    "wang_fatality_all": {"a": -8.9819, "b": 0.1603, "speed_unit": "mph"},
}


def _logistic(v: np.ndarray, a: float, b: float) -> np.ndarray:
    return np.clip(1.0 / (1.0 + np.exp(-(a + b * v))), 0.0, 1.0)


def _resolve(spec: Any, registry: Dict[str, Dict[str, Any]], kind: str) -> Dict[str, Any]:
    if isinstance(spec, str):
        if spec not in registry:
            raise ValueError(f"Unknown {kind} curve '{spec}'. Known: {sorted(registry)}")
        return registry[spec]
    raise ValueError(f"Invalid {kind} curve spec: {spec!r}")


def p_worker(v_kmh: np.ndarray, curve: Any = "rosen_mais3plus") -> np.ndarray:
    c = _resolve(curve, WORKER_CURVES, "worker")
    v = np.asarray(v_kmh, dtype=float)
    if c["speed_unit"] == "mph":
        v = v * MPH_PER_KMH
    return _logistic(v, c["a"], c["b"])


def p_occupant(delta_v_kmh: np.ndarray, curve: Any = "wang_mais3plus_all") -> np.ndarray:
    c = _resolve(spec=curve, registry=OCCUPANT_CURVES, kind="occupant")
    dv = np.asarray(delta_v_kmh, dtype=float)
    if c["speed_unit"] == "mph":
        dv = dv * MPH_PER_KMH
    return _logistic(dv, c["a"], c["b"])


# --------------------------------------------------------------- W5 head-on chain
def braked_speed(v0_kmh: np.ndarray, decel_ms2: np.ndarray, dist_m: np.ndarray) -> np.ndarray:
    """Speed after braking at `decel` over `dist` from initial v0 (floors at 0)."""
    v0 = np.asarray(v0_kmh, dtype=float) / 3.6
    v1sq = np.maximum(v0 * v0 - 2.0 * decel_ms2 * dist_m, 0.0)
    return np.sqrt(v1sq) * 3.6


def headon_delta_vs(v1_kmh: np.ndarray, v2_kmh: np.ndarray,
                    m1_kg: np.ndarray, m2_kg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Perfectly inelastic 1-D head-on: closing speed splits by mass ratio.

    delta_V1 = closing * m2/(m1+m2); delta_V2 = closing * m1/(m1+m2). The same
    simplified mapping the companion model uses for delta-V-based curves applied to
    conflict configurations.
    """
    closing = np.asarray(v1_kmh, dtype=float) + np.asarray(v2_kmh, dtype=float)
    tot = m1_kg + m2_kg
    return closing * (m2_kg / tot), closing * (m1_kg / tot)


def p_event_dsi_headon(dv1_kmh: np.ndarray, dv2_kmh: np.ndarray,
                       occ1: np.ndarray, occ2: np.ndarray,
                       curve: str = "wang_mais3plus_all") -> np.ndarray:
    """P(>=1 DSI | head-on collision), occupants per vehicle as integer arrays.

    Occupants within a vehicle share that vehicle's delta-V; independence across
    persons given delta-V (disclosed simplification).
    """
    p1 = p_occupant(dv1_kmh, curve)
    p2 = p_occupant(dv2_kmh, curve)
    return 1.0 - (1.0 - p1) ** occ1 * (1.0 - p2) ** occ2


def headon_delta_vs_from_closing(closing_kmh: np.ndarray, m1_kg: np.ndarray,
                                 m2_kg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Momentum split of a given closing speed into each vehicle's delta-V."""
    tot = m1_kg + m2_kg
    return closing_kmh * (m2_kg / tot), closing_kmh * (m1_kg / tot)


# ------------------------------------------------- worker severity, speed-anchored
SEV_ANCHOR_SPEED_KMH = 50.0     # SEJ Scenario C stipulated platoon operating speed
_B_ROSEN = WORKER_CURVES["rosen_mais3plus"]["b"]     # 0.078 per km/h


def sev_worker_at_speed(sev_elicited: np.ndarray, v_kmh: np.ndarray,
                        v_anchor_kmh: float = SEV_ANCHOR_SPEED_KMH) -> np.ndarray:
    """Give an elicited P(>=1 DSI | worker struck) the worker curve's speed elasticity.

    The expert panel judged the conditional severity of a controller strike under a
    scenario whose stipulated platoon operating speed is `v_anchor_kmh`. Their judgement
    is preserved exactly at that speed and transported to other speeds by a logit shift
    along the Rosen pedestrian MAIS3+ curve, which is logistic in impact speed:

        logit sev(v) = logit sev_elicited + b_rosen * (v - v_anchor)

    Without this, the head-on pathway would be the only speed-responsive severity in the
    ledger, and faster traffic would make the device look better on the pathway it
    introduces while leaving the pathway it removes untouched. The elicited quantity is
    an anchor, not a constant.
    """
    p = np.clip(np.asarray(sev_elicited, dtype=float), 1e-9, 1.0 - 1e-9)
    logit = np.log(p / (1.0 - p)) + _B_ROSEN * (np.asarray(v_kmh, dtype=float) - v_anchor_kmh)
    return np.clip(1.0 / (1.0 + np.exp(-logit)), 0.0, 1.0)


def implied_strike_speed_kmh(sev: np.ndarray) -> np.ndarray:
    """Invert the Rosen curve on an elicited severity: the strike speed it corresponds to.
    Reported as a coherence observation on the panel's judgement, not used as an anchor."""
    p = np.clip(np.asarray(sev, dtype=float), 1e-9, 1.0 - 1e-9)
    a = WORKER_CURVES["rosen_mais3plus"]["a"]
    return (np.log(p / (1.0 - p)) - a) / _B_ROSEN
