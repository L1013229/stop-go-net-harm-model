"""W5 violation-conflict event tree.

The pathway is NOT a product of independent factors. Published red-light violation rates
at portable signals count observed ENTRIES past a red aspect, and entry is a decision taken
with as much of the single-lane section in view as the alignment allows. The measured rate
is therefore already conditioned on the section APPEARING clear. Multiplying it by the
marginal probability that the section is occupied multiplies a conditional probability by
the probability of its own conditioning event. See docs/model-design.md.

Two things the conditioning does NOT do, and the tree must therefore carry explicitly:

1. "Appears clear" is not "is clear". The driver can confirm the section only as far as the
   mutual sight distance `sight_m` (crest, curve, vegetation, glare). An opposing vehicle
   beyond that line is invisible at entry and is met mid-section, with the time available to
   avoid set by the sight distance rather than by the section length.

2. "Clear now" is not "clear for the transit". A violator entering during the opposing green
   in a gap between opposing vehicles has a genuinely clear section in front of him, and the
   NEXT opposing arrival enters against him while he is still inside. The same applies to a
   pre-release violator who is still inside when the opposing queue is released: the
   clearance interval is sized for the last legitimate vehicle, which crossed at red onset,
   not for a violator who crossed later. A violation is protected by the clearance interval
   only when the remaining clearance covers the violator's own transit.

Phase convention for a direction's red, R = 2C + G_opp:

    t = 0              red onset; this direction's platoon begins to vacate
    [0, C)             all-red (clearance interval actually run by the control form)
    [C, C + G_opp)     opposing green: queued vehicles discharge at saturation headway
                       after startup lost time, then free arrivals
    [C + G_opp, R)     all-red; opposing platoon vacates

Queued opposing vehicles cross their stop line from rest and accelerate at `a_veh` toward
platoon speed. Free arrivals cross at platoon speed. An ONSET violator crosses the stop line
at platoon speed (he never stopped); a STANDING violator departs from rest and takes the
from-rest traverse time, so he is slower and remains in the section longer.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# --------------------------------------------------------------------- kinematics
def accel_distance(t: np.ndarray, a: np.ndarray, v_max: np.ndarray) -> np.ndarray:
    """Distance covered from rest at acceleration `a`, capped at `v_max`."""
    t_acc = v_max / a
    d_acc = 0.5 * v_max * t_acc
    t = np.maximum(t, 0.0)
    return np.where(t <= t_acc, 0.5 * a * t * t, d_acc + v_max * (t - t_acc))


def accel_speed(t: np.ndarray, a: np.ndarray, v_max: np.ndarray) -> np.ndarray:
    return np.minimum(a * np.maximum(t, 0.0), v_max)


def traverse_time_from_rest(L: np.ndarray, a: np.ndarray, v_max: np.ndarray) -> np.ndarray:
    """Time to cover L from rest, accelerating at `a` then cruising at `v_max`."""
    t_acc = v_max / a
    d_acc = 0.5 * v_max * t_acc
    return np.where(L <= d_acc,
                    np.sqrt(2.0 * np.maximum(L, 0.0) / a),
                    t_acc + (L - d_acc) / v_max)


def time_to_close(sep: np.ndarray, v1: np.ndarray, v2_0: np.ndarray,
                  a: np.ndarray, v_max: np.ndarray) -> np.ndarray:
    """Time for a gap `sep` to close: one vehicle at constant v1, the other starting at
    v2_0 and accelerating at `a` toward v_max."""
    sep = np.maximum(sep, 0.0)
    b = v1 + v2_0
    disc = b * b + 2.0 * a * sep
    T_acc = (-b + np.sqrt(disc)) / a
    t_to_cap = np.maximum(v_max - v2_0, 0.0) / a
    d_at_cap = b * t_to_cap + 0.5 * a * t_to_cap * t_to_cap
    T_cruise = t_to_cap + (sep - d_at_cap) / (v1 + v_max)
    return np.where(T_acc <= t_to_cap, T_acc, T_cruise)


# --------------------------------------------------------------------- cycle inputs
@dataclass(frozen=True)
class ConflictInputs:
    """Per-iteration cycle quantities, arrays over Monte Carlo iterations."""

    section_m: np.ndarray        # L, controlled single-lane length
    v_platoon: np.ndarray        # m/s
    a_veh: np.ndarray            # m/s^2, acceleration from rest
    clearance_s: np.ndarray      # C, the all-red the control form actually runs
    green_opp_s: np.ndarray      # G_opp
    n_queue_opp: np.ndarray      # opposing vehicles queued at their green onset
    q_opp_vps: np.ndarray        # opposing arrival rate (veh/s)
    sat_headway_s: np.ndarray    # saturation discharge headway
    startup_lost_s: np.ndarray   # startup lost time before the first discharge
    sight_m: np.ndarray          # mutual sight distance along the section, capped at L

    @property
    def transit_s(self) -> np.ndarray:
        """tau: violator's traverse time, entering at platoon speed."""
        return self.section_m / self.v_platoon

    @property
    def red_s(self) -> np.ndarray:
        return 2.0 * self.clearance_s + self.green_opp_s

    @property
    def release_start_s(self) -> np.ndarray:
        """First opposing vehicle crosses its stop line."""
        return self.clearance_s + self.startup_lost_s

    @property
    def t_rest_s(self) -> np.ndarray:
        """Traverse time from rest, the physical minimum a clearance interval must cover."""
        return traverse_time_from_rest(self.section_m, self.a_veh, self.v_platoon)


def nearest_opposing(t: np.ndarray, ci: ConflictInputs) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """State of the section at time `t`, as seen from the violator's stop line (x = 0).

    Returns (occupied, d_near, v_near): whether any opposing vehicle is inside the section,
    the distance from x = 0 to the nearest one, and that vehicle's speed.

    Vehicles do not overtake, so the vehicle nearest x = 0 is the earliest-entering one that
    has not yet exited. Both the queued block (constant headway, from-rest kinematics) and
    the free-arrival block (uniform spacing, platoon speed) admit a closed form for that
    index, so the cost is independent of the number of vehicles.
    """
    L, v, a = ci.section_m, ci.v_platoon, ci.a_veh
    h, rel = ci.sat_headway_s, ci.release_start_s
    n_q = np.maximum(ci.n_queue_opp, 0.0)
    T_rest, tau = ci.t_rest_s, ci.transit_s
    green_end = ci.clearance_s + ci.green_opp_s

    # ---- queued block: vehicle j crosses its stop line at rel + j*h, exits at +T_rest
    j_lo = np.ceil((t - rel - T_rest) / h)                 # earliest not-yet-exited
    j_lo = np.clip(j_lo, 0.0, np.inf)
    j_hi = np.floor((t - rel) / h)                         # latest already-entered
    j_hi = np.minimum(j_hi, n_q - 1.0)
    q_has = (j_lo <= j_hi) & (n_q > 0)
    j_q = np.where(q_has, j_lo, 0.0)
    t_q = rel + j_q * h
    d_q = accel_distance(t - t_q, a, v)                    # distance from the far end
    v_q = accel_speed(t - t_q, a, v)
    x_q = np.where(q_has, L - d_q, np.inf)                 # distance from x = 0

    # ---- free-arrival block: enters after the queue clears, at platoon speed, spacing 1/q
    t_clear = rel + n_q * h
    with np.errstate(divide="ignore", invalid="ignore"):
        spacing = np.where(ci.q_opp_vps > 0, 1.0 / ci.q_opp_vps, np.inf)
    k_lo = np.clip(np.ceil((t - t_clear - tau) / spacing - 0.5), 0.0, np.inf)
    k_hi = np.floor((t - t_clear) / spacing - 0.5)
    t_k = t_clear + (k_lo + 0.5) * spacing
    f_has = (k_lo <= k_hi) & np.isfinite(spacing) & (t_k < green_end)
    d_f = v * np.maximum(t - t_k, 0.0)
    x_f = np.where(f_has, L - d_f, np.inf)

    occupied = q_has | f_has
    take_q = x_q <= x_f
    d_near = np.where(take_q, x_q, x_f)
    v_near = np.where(take_q, v_q, v)
    d_near = np.where(occupied, np.clip(d_near, 0.0, L), np.inf)
    v_near = np.where(occupied, v_near, 0.0)
    return occupied, d_near, v_near


def next_opposing_entry(t: np.ndarray, ci: ConflictInputs) -> tuple[np.ndarray, np.ndarray]:
    """First opposing stop-line crossing strictly after time `t` within this red.

    Returns (t_next, v0_next): the entry time (inf if nothing further enters this red) and
    the entrant's speed at its stop line (0 for a queued vehicle departing from rest,
    platoon speed for a free arrival).
    """
    rel, h = ci.release_start_s, ci.sat_headway_s
    n_q = np.maximum(ci.n_queue_opp, 0.0)
    green_end = ci.clearance_s + ci.green_opp_s
    v = ci.v_platoon

    # next queued entry: rel + j*h with j the smallest index whose time exceeds t
    j = np.where(t < rel, 0.0, np.floor((t - rel) / h) + 1.0)
    t_q = rel + j * h
    t_q = np.where(j <= n_q - 1.0, t_q, np.inf)

    # next free arrival: t_clear + (k + 0.5) * spacing, strictly after t, within the green
    t_clear = rel + n_q * h
    with np.errstate(divide="ignore", invalid="ignore"):
        spacing = np.where(ci.q_opp_vps > 0, 1.0 / ci.q_opp_vps, np.inf)
    k = np.clip(np.ceil((t - t_clear) / spacing - 0.5), 0.0, np.inf)
    t_f = t_clear + (k + 0.5) * spacing
    t_f = np.where(t_f <= t, t_f + spacing, t_f)
    t_f = np.where(np.isfinite(spacing) & (t_f < green_end), t_f, np.inf)

    take_q = t_q <= t_f
    t_next = np.where(take_q, t_q, t_f)
    v0 = np.where(take_q, 0.0, v)
    return t_next, v0


# --------------------------------------------------------------------- model form
@dataclass(frozen=True)
class ModelForm:
    """Structural alternatives fixed in docs/prespec.md Addendum A (A6). The defaults ARE
    the primary tree; every production artefact before the addendum was produced with them.

    rho    beta-factor common-cause share of the two drivers' avoidance failures:
           P(collision | conflict) = rho * q + (1 - rho) * q^2. rho = 0 is independence
           (primary); rho = 1 means one driver's failure is enough.
    curve  avoidance-failure curve in TTC: 'logistic' (primary), 'threshold' (fail below
           ttc50, avoid above), 'loglogistic' (logistic in ln TTC, same median, scale
           s_ttc / ttc50 so the slope at the median matches the primary).
    """

    rho: float = 0.0
    curve: str = "logistic"


PRIMARY_FORM = ModelForm()


# --------------------------------------------------------------------- the event tree
@dataclass(frozen=True)
class TreeParams:
    """Behavioural conditionals of the tree. None has been measured at a portable signal;
    all are rule-3 priors and all are PRCC-reported.

    `w_occ` is the violator's entry rate when an opposing vehicle is VISIBLY in the section,
    scaled by that vehicle's distance within the visible range: entering is a judgement about
    a vehicle the violator can see, and the judgement fails less often the closer it is. An
    opposing vehicle beyond the sight line does not deter him at all, because he cannot see
    it; those entries carry full weight and their conflicts are discovered mid-section.

    `q_lead` is the probability that an opposing driver who CAN see the violator enters the
    section against him anyway (glare, inattention, misreading distance), scaled by the
    violator's distance within the visible range. An opposing driver who cannot see the
    violator, because the violator is beyond the sight line at the moment of entry, enters
    unknowingly with probability one.
    """

    w_occ: np.ndarray            # violator enters against a VISIBLE opposing vehicle
    q_lead: np.ndarray           # sighted opposing driver enters against a visible violator
    p_detect: np.ndarray         # radio hold (S0) / violation-aware all-red extension (S1b)
    ttc50: np.ndarray            # TTC at which one driver has 50% chance of failing to avoid
    s_ttc: np.ndarray            # slope of that logistic, seconds
    w_onset: np.ndarray          # share of violations committed at speed, at red onset
    onset_window_s: np.ndarray   # how long an arriving vehicle is still moving


def q_fail(ttc: np.ndarray, tp: TreeParams, form: ModelForm = PRIMARY_FORM) -> np.ndarray:
    """P(one driver fails to avoid | time-to-collision available at mutual discovery)."""
    if form.curve == "logistic":
        return 1.0 / (1.0 + np.exp((ttc - tp.ttc50) / tp.s_ttc))
    if form.curve == "threshold":
        return (ttc < tp.ttc50).astype(float)
    if form.curve == "loglogistic":
        scale = tp.s_ttc / tp.ttc50
        z = (np.log(np.maximum(ttc, 1e-9)) - np.log(tp.ttc50)) / scale
        return 1.0 / (1.0 + np.exp(z))
    raise ValueError(f"unknown avoidance-curve form {form.curve!r}")


def p_collision_given_conflict(q: np.ndarray, form: ModelForm = PRIMARY_FORM) -> np.ndarray:
    """Either driver avoiding suffices; the common-cause share `rho` couples the failures."""
    return form.rho * q + (1.0 - form.rho) * q * q


def w5_tree(ci: ConflictInputs, tp: TreeParams, severity_fn=None,
            n_grid: int = 128, form: ModelForm = PRIMARY_FORM) -> dict[str, np.ndarray]:
    """Integrate the W5 event tree over the arrival time of a vehicle facing red.

    `severity_fn(closing_ms) -> P(>=1 DSI | collision)` is evaluated INSIDE the integral,
    so severity is conditioned on the encounter that produced it. Omit it for geometry only.

    Returns per-iteration conditional expectations, all PER VIOLATION:
      p_conflict  E[the pair actually close head-on]
      p_coll      E[collision]
      p_evade     E[conflict that ends in a successful evasion]
      p_harm      E[collision with at least one DSI]  (zero if severity_fn is None)
      closing_ms  E[closing speed | collision], m/s
      mean_w      red-averaged entry weight; the normaliser that preserves the
                  literature-measured violation rate
      p_blind     E[conflict in which at least one driver entered without sight of the other]

    Diagnostics: f_clear (fraction of the red with a VISIBLY clear section), p_safe_window
    (fraction of the red from which an entering violator meets nothing at all), mean_ttc
    (collision-weighted).
    """
    n = len(ci.section_m)
    R, tau, v = ci.red_s, ci.transit_s, ci.v_platoon
    L, a, rel = ci.section_m, ci.a_veh, ci.release_start_s
    t_rest = ci.t_rest_s
    s = np.minimum(ci.sight_m, L)
    ow = np.minimum(tp.onset_window_s, R)

    u = (np.arange(n_grid) + 0.5) / n_grid                 # stratified midpoints
    zeros = np.zeros(n)

    acc = {k: np.zeros(n) for k in
           ("w", "conf", "coll", "harm", "collv", "collt", "blind", "clear", "safe")}

    def branch(t_a: np.ndarray, standing: bool, weight: np.ndarray) -> None:
        """Accumulate one violator type entering at t_a, with density `weight`."""
        occupied, d_near, v_near = nearest_opposing(t_a, ci)
        visible_occ = occupied & (d_near <= s)
        hidden_occ = occupied & (d_near > s)

        transit_v = t_rest if standing else tau
        v_vio0 = zeros if standing else v

        # ---- entry decision: conditioned on what the violator can SEE -----------------
        # visible opposing vehicle: rare entry, rarer the closer it is
        # hidden opposing vehicle or clear: full weight — he believes the section clear
        w = np.where(visible_occ, tp.w_occ * np.clip(d_near / s, 0.0, 1.0), 1.0) * weight

        # ---- branch A: VISIBLE occupancy — conflict from current separation -----------
        ttc_A = time_to_close(d_near, np.maximum(v_vio0, 0.5), v_near, a, v)
        closing_A = np.minimum(v_vio0 + a * ttc_A, v) + np.minimum(v_near + a * ttc_A, v)

        # ---- branch H: HIDDEN occupancy — discovered at the sight line -----------------
        # both close from d_near; mutual discovery when the gap reaches s
        t1 = np.maximum(d_near - s, 0.0) / np.maximum(v_vio0 + v_near + 0.5, 0.5)
        v_vio_H = np.minimum(np.maximum(v_vio0, 0.5) + (a * t1 if standing else 0.0), v)
        v_opp_H = np.minimum(v_near + a * t1, v)
        ttc_H = time_to_close(np.minimum(d_near, s), v_vio_H, v_opp_H, a, v)
        closing_H = np.minimum(v_vio_H + a * ttc_H, v) + np.minimum(v_opp_H + a * ttc_H, v)

        # ---- branch B: clear at entry — the NEXT opposing arrival can still meet him ---
        t_next, v0_next = next_opposing_entry(t_a, ci)
        meets = np.isfinite(t_next) & (t_next < t_a + transit_v)
        dt = np.where(meets, t_next - t_a, 0.0)
        x_v = accel_distance(dt, a, v) if standing else v * dt
        sep_e = np.clip(L - x_v, 0.0, L)
        v_vio_B = accel_speed(dt, a, v) if standing else np.full(n, 1.0) * v

        # detection bites only before the opposing release
        hold = np.where(t_a < rel, tp.p_detect, 0.0)
        # the entrant's decision is conditioned on what HE can see
        entrant_sees = sep_e <= s
        p_enter = np.where(entrant_sees, tp.q_lead * np.clip(sep_e / s, 0.0, 1.0), 1.0)
        p_conf_B = np.where(meets, (1.0 - hold) * p_enter, 0.0)
        ttc_B = time_to_close(np.minimum(sep_e, s), np.maximum(v_vio_B, 0.5), v0_next, a, v)
        closing_B = (np.minimum(v_vio_B + a * ttc_B, v)
                     + np.minimum(v0_next + a * ttc_B, v))

        # ---- combine ---------------------------------------------------------------------
        p_conf = np.where(occupied, 1.0, p_conf_B)
        ttc = np.where(visible_occ, ttc_A, np.where(hidden_occ, ttc_H, ttc_B))
        closing = np.where(visible_occ, closing_A, np.where(hidden_occ, closing_H, closing_B))
        blind = np.where(hidden_occ, 1.0,
                         np.where(~occupied & meets & ~entrant_sees, 1.0, 0.0))

        q = q_fail(ttc, tp, form)
        if form.rho == 0.0:
            p_coll = p_conf * q * q                        # either driver avoiding suffices
        else:                                              # common-cause share (Addendum A, MF1)
            p_coll = p_conf * p_collision_given_conflict(q, form)
        p_dsi = severity_fn(closing) if severity_fn is not None else zeros

        acc["w"] += w
        acc["conf"] += w * p_conf
        acc["coll"] += w * p_coll
        acc["harm"] += w * p_coll * p_dsi
        acc["collv"] += w * p_coll * closing
        acc["collt"] += w * p_coll * ttc
        acc["blind"] += w * p_conf * blind
        acc["clear"] += (~visible_occ).astype(float) * weight
        acc["safe"] += ((~occupied) & (~meets)).astype(float) * weight

    # ONSET type: arrives still moving, within the onset window, and runs the red rather
    # than stopping. Density 1/ow over [0, ow), carrying share w_onset.
    for g in range(n_grid):
        branch(u[g] * ow, standing=False, weight=tp.w_onset / n_grid)

    # STANDING type: has stopped at the stop line and departs against the red. It is the
    # queue's LEAD vehicle; those behind it are physically blocked and cannot violate.
    # Density 1/(R-ow) over [ow, R).
    span = np.maximum(R - ow, 1e-9)
    for g in range(n_grid):
        branch(ow + u[g] * span, standing=True, weight=(1.0 - tp.w_onset) / n_grid)

    denom = np.maximum(acc["coll"], 1e-300)
    conf_denom = np.maximum(acc["conf"], 1e-300)
    return {
        "mean_w": acc["w"],
        "p_conflict": acc["conf"] / acc["w"],
        "p_coll": acc["coll"] / acc["w"],
        "p_evade": (acc["conf"] - acc["coll"]) / acc["w"],
        "p_harm": acc["harm"] / acc["w"],
        "closing_ms": np.where(acc["coll"] > 0, acc["collv"] / denom, 0.0),
        "mean_ttc": np.where(acc["coll"] > 0, acc["collt"] / denom, 0.0),
        "p_blind": np.where(acc["conf"] > 0, acc["blind"] / conf_denom, 0.0),
        "f_clear": acc["clear"],
        "p_safe_window": acc["safe"],
    }
