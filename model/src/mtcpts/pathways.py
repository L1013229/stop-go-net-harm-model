"""Harm-ledger pathway assembly.

Unit everywhere: expected serious-harm EVENTS per operation-day, a serious-harm event
being a collision with at least one DSI outcome.

Strategy dependence:
  W1  queue-tail rear-end     S0 and S1 — same per-stopped-vehicle event risk (SEJ-
                              anchored under the S0 cycle); each strategy's own cycle
                              profile supplies the stopped-vehicle count.
  W3  controller struck       S0 only — SEJ C.RE3 x C.SEV3 per-expert mixture, with the
                              elicited severity transported to the sampled operating
                              speed along the worker curve.
  W5  violation conflict      S0 and S1 — the event tree of conflict.py, whose branch
                              probabilities are conditioned on what each driver can see
                              and on the time available to avoid.
  W4d PTS placement delta     S1 and S2 — incremental on-foot device time, encroachment frame.
  W3r operator beside road    S2 only — the attended device's operator standing off the
                              carriageway for the operating day, encroachment frame
                              (docs/prespec.md Addendum A).
  W5b evasion secondary harm  bounded sensitivity, reported separately.
  W6  device dangerous fault  S1 sensitivity case only, reported separately.

The SEJ anchor convention: C.RE1 is elicited PER VEHICLE APPROACHING THE QUEUE under the
Scenario C stop/go operation, i.e. per stopped arrival under the S0 cycle. The model
applies that per-stopped-vehicle risk to each strategy's own stopped-vehicle count, so
cycle differences enter ONCE, through the cycle layer.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .conflict import PRIMARY_FORM, ConflictInputs, ModelForm, TreeParams, w5_tree
from .severity import (headon_delta_vs_from_closing, p_event_dsi_headon, p_worker,
                       sev_worker_at_speed)


@dataclass(frozen=True)
class DayContext:
    """Per-iteration operation-day quantities shared across pathways."""

    veh_per_day_dir: np.ndarray      # one direction's daily volume over the operation
    stopped_per_day: np.ndarray      # stopped arrivals per day, BOTH directions
    facing_stop_per_day: np.ndarray  # vehicles arriving on red/STOP per day, both directions
    cycles_per_day: np.ndarray


def w1_events(day: DayContext, re1_per_stop: np.ndarray, sev1: np.ndarray) -> np.ndarray:
    """Queue-tail rear-end events/day = stopped x per-stop rate x P(DSI | event).

    Severity is NOT speed-anchored: the queue tail lies upstream of both control forms,
    its approach speed is identical across strategies, and the pathway's difference between
    strategies is a small fraction of its level, so any speed response cancels from dH.
    """
    return day.stopped_per_day * re1_per_stop * sev1


def w3_events(day: DayContext, re3_per_pass: np.ndarray, sev3_elicited: np.ndarray,
              v_platoon_kmh: np.ndarray, active: bool) -> np.ndarray:
    """Controller-struck events/day (S0 only): passes x per-pass rate x P(DSI | struck, v).

    C.RE3 is per vehicle PASS at the site (both directions pass the two controllers);
    exposure = total daily passes. The elicited severity is transported from the scenario's
    stipulated 50 km/h operating speed to the sampled speed along the worker curve.
    """
    if not active:
        return np.zeros_like(re3_per_pass)
    passes = 2.0 * day.veh_per_day_dir
    sev3 = sev_worker_at_speed(sev3_elicited, v_platoon_kmh)
    return passes * re3_per_pass * sev3


def w5_terms(day: DayContext, ci: ConflictInputs, tp: TreeParams, r_v_facing: np.ndarray,
             impact_speed_frac: np.ndarray, m1: np.ndarray, m2: np.ndarray,
             occ1: np.ndarray, occ2: np.ndarray, n_grid: int = 128,
             form: ModelForm = PRIMARY_FORM) -> dict[str, np.ndarray]:
    """Violation-conflict pathway, evaluated as an event tree.

    The literature-measured violation rate `r_v_facing` is a rate of observed ENTRIES past
    a red aspect, already conditioned on the section appearing clear to the entering driver.
    `w5_tree` preserves that measured rate exactly while making its TIMING endogenous to the
    visible state of the section, so the pathway is never assembled as a product of the
    measured rate and an independent opposing-presence probability.

    Returns events/day plus the intermediate quantities the model is validated against:
    violations, conflicts and COLLISIONS per operation-day.
    """
    def severity_fn(closing_ms: np.ndarray) -> np.ndarray:
        closing_kmh = closing_ms * 3.6 * impact_speed_frac
        dv1, dv2 = headon_delta_vs_from_closing(closing_kmh, m1, m2)
        return p_event_dsi_headon(dv1, dv2, occ1, occ2)

    tree = w5_tree(ci, tp, severity_fn=severity_fn, n_grid=n_grid, form=form,
                   r_v_facing=r_v_facing)
    violations_per_day = day.facing_stop_per_day * r_v_facing
    return {
        "events": violations_per_day * tree["p_harm"],
        "violations_per_day": violations_per_day,
        "conflicts_per_day": violations_per_day * tree["p_conflict"],
        "collisions_per_day": violations_per_day * tree["p_coll"],
        "evasions_per_day": violations_per_day * tree["p_evade"],
        "p_harm_per_violation": tree["p_harm"],
        "closing_ms": tree["closing_ms"],
        "mean_ttc": tree["mean_ttc"],
        "p_blind": tree["p_blind"],
        "f_clear": tree["f_clear"],
        "p_safe_window": tree["p_safe_window"],
        "onset_cap_binds": tree["onset_cap_binds"],
        "onset_share": tree["onset_share"],
        "onset_entry_probability": tree["onset_entry_probability"],
    }


def w5b_band(evasions_per_day: np.ndarray, p_evade_harm: np.ndarray,
             v_platoon_kmh: np.ndarray) -> np.ndarray:
    """Bounded sensitivity: harm arising from a SUCCESSFUL evasion.

    An evading vehicle can reach the work crew, leave the carriageway, or be struck from
    behind. No study links an originating conflict to a downstream run-off-road outcome, so
    this is a bounded band, not a primary-ledger term. Worker-curve severity at the
    operating speed stands in for the crew-strike component, which dominates the DSI count.
    """
    return evasions_per_day * p_evade_harm * p_worker(v_platoon_kmh)


def w4d_events(q_vph: np.ndarray, t_deploy_s: np.ndarray, enc_rate_vkm: np.ndarray,
               reach_alpha: np.ndarray, offset_m: np.ndarray, l_exposed_km: np.ndarray,
               v_kmh: np.ndarray, p_worker_curve) -> np.ndarray:
    """Incremental PTS head placement/retrieval exposure (both ends, install + remove).

    Companion-model encroachment frame: strikes = N x (r_E x L) x P(reach >= c);
    serious-harm events = strikes x P(DSI | strike at operating speed).
    """
    n_veh = q_vph * (t_deploy_s / 3600.0)
    lam = n_veh * enc_rate_vkm * l_exposed_km * np.exp(-reach_alpha * offset_m)
    return lam * p_worker_curve(v_kmh)


def w3r_operator_events(veh_per_day_dir: np.ndarray, enc_rate_vkm: np.ndarray,
                        reach_alpha: np.ndarray, offset_op_m: np.ndarray,
                        l_exposed_km: np.ndarray, v_kmh: np.ndarray,
                        p_worker_curve) -> tuple[np.ndarray, np.ndarray]:
    """Residual exposure of the attended device's operator (S2), standing beside the road.

    The lane-standing controller pathway is removed under S2; what remains is an operator on
    the verge at each end for the operating day. That is an encroachment exposure, so it uses
    the W4d frame: every vehicle passes both operator positions (4 x the one-direction daily
    volume), and a passing vehicle reaches the operator with the reach-decay probability at
    the operator's standing offset. Returns (strikes per day, serious-harm events per day).
    """
    passes = 4.0 * veh_per_day_dir
    lam = passes * enc_rate_vkm * l_exposed_km * np.exp(-reach_alpha * offset_op_m)
    return lam, lam * p_worker_curve(v_kmh)


def w6_band(fault_rate_per_day: np.ndarray, p_conflict_fault: np.ndarray,
            p_dsi_event: np.ndarray) -> np.ndarray:
    """Bounded sensitivity band for dangerous device faults (NOT in the primary ledger)."""
    return fault_rate_per_day * p_conflict_fault * p_dsi_event
