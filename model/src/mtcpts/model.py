"""mtcpts core: per-cell Monte Carlo assembly of the S0/S1a/S1b/S2 harm ledgers.

One cycle/queue layer feeds every exposure quantity, with the section transit time and
each control form's clearance interval held as distinct quantities. SEJ anchors are
consumed whole at the per-expert-mixture level. W5 is evaluated as the event tree of
conflict.py. Unit: expected serious-harm events per operation-day.

Strategy cycle plans:
  S0  adaptive (MTC): the controller releases after confirming the section observed clear,
      so the clearance interval is the from-rest traverse time plus a confirmation lag.
      Greens clear the standing queue plus an operating margin.
  S1a fixed-time PTS: the clearance interval is the programmed all-red, sized by the
      governing code of practice from the section length at a conservative assumed speed
      plus a buffer. Greens are the adaptive plan at that clearance, scaled by f_cycle_a
      (Kansas 2016 measured green-interval and wait-time equivalence).
  S1b actuated PTS: as S1a, scaled by f_cycle_b (gap-out tracks demand), plus a
      violation-aware all-red extension.
  S2  attended AFAD (docs/prespec.md Addendum A, post-primary extension): the S0 adaptive
      plan and clearance (attended release), the gated attended-device violation rate, an
      operator hold with its own effectiveness, the operator's residual beside-the-road
      exposure (W3r, encroachment frame) in place of the lane-standing controller, and the
      same placement exposure as the signal units. Its three draws are taken AFTER every
      existing draw so S0/S1a/S1b reproduce the frozen artefacts bit for bit.

SEJ W1 anchor conversion: C.RE1 is elicited per vehicle approaching the queue with the
companion study's stipulated 4,800 approaches/day under the S0 operation. The
mechanism-true exposure is the STOPPED arrival, so the per-stopped-vehicle rate is
RE1_rate / f_stop_S0(baseline), one documented conversion, then each strategy's own
stopped count applies.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .conflict import (PRIMARY_FORM, ConflictInputs, ModelForm, TreeParams,
                       traverse_time_from_rest)
from .distributions import (ExpertMixture, Fixed, LogUniform, PooledSEJ, Triangular,
                            Uniform)
from .pathways import (DayContext, w1_events, w3_events, w3r_operator_events, w4d_events,
                       w5_terms, w5b_band)

STRATEGIES = ("S0", "S1a", "S1b", "S2")
DEVICE_STRATEGIES = ("S1a", "S1b", "S2")
from .severity import p_worker

OPERATION_HOURS = 8.0


@dataclass(frozen=True)
class Cell:
    q_vph_dir: float          # per-direction hourly volume
    section_m: float          # controlled single-lane section length (incl. tapers)


@dataclass
class Priors:
    """All non-SEJ priors. Families set per the construction rules in docs/prespec.md;
    values finalised in config/priors.toml (frozen before the first production run)."""

    # ---- behavioural violation rates, per FACING vehicle, driver-initiated
    r_v0: object = field(default_factory=lambda: Triangular(0.0, 1.8e-4, 2.0e-3))
    r_v1a: object = field(default_factory=lambda: Triangular(1.0e-2, 3.7e-2, 8.9e-2))

    # ---- event-tree conditionals (contested, rule 3)
    w_occ: object = field(default_factory=lambda: LogUniform(1.0e-4, 1.0e-2))
    q_lead: object = field(default_factory=lambda: LogUniform(1.0e-3, 1.0e-1))
    ttc50: object = field(default_factory=lambda: Uniform(1.0, 2.5))
    s_ttc: object = field(default_factory=lambda: Uniform(0.3, 1.0))
    w_onset: object = field(default_factory=lambda: Uniform(0.50, 0.95))
    onset_window_s: object = field(default_factory=lambda: Uniform(2.0, 8.0))
    p_detect_s0: object = field(default_factory=lambda: Uniform(0.3, 0.9))
    p_detect_s1b: object = field(default_factory=lambda: Uniform(0.1, 0.7))
    impact_speed_frac: object = field(default_factory=lambda: Uniform(0.3, 1.0))
    p_evade_harm: object = field(default_factory=lambda: LogUniform(1.0e-5, 1.0e-3))
    d_sight_m: object = field(default_factory=lambda: LogUniform(150.0, 3000.0))

    # ---- clearance-interval design (codes of practice)
    v_clear_kmh: object = field(default_factory=lambda: Uniform(20.0, 40.0))
    clear_buffer_s: object = field(default_factory=lambda: Uniform(0.0, 5.0))
    t_confirm_s: object = field(default_factory=lambda: Uniform(2.0, 8.0))

    # ---- traffic / operations
    platoon_speed_kmh: object = field(default_factory=lambda: Triangular(30.0, 40.0, 50.0))
    a_veh_ms2: object = field(default_factory=lambda: Uniform(1.0, 2.0))
    sat_headway_s: object = field(default_factory=lambda: Uniform(1.9, 2.6))
    startup_lost_s: object = field(default_factory=lambda: Uniform(1.0, 3.0))
    s0_green_margin: object = field(default_factory=lambda: Uniform(1.05, 1.5))
    f_cycle_a: object = field(default_factory=lambda: Triangular(0.9, 1.0, 1.3))
    f_cycle_b: object = field(default_factory=lambda: Triangular(0.85, 1.0, 1.15))

    # ---- vehicle mix
    mass_kg: object = field(default_factory=lambda: Uniform(1200.0, 2200.0))
    occupancy: object = field(default_factory=lambda: Triangular(1.0, 1.3, 2.5))

    # ---- W4d incremental PTS placement
    t_deploy_s: object = field(default_factory=lambda: Triangular(240.0, 480.0, 960.0))
    enc_rate_vkm: object = field(default_factory=lambda: LogUniform(1e-7, 1e-5))
    reach_alpha: object = field(default_factory=lambda: Uniform(0.02, 0.15))
    offset_m: object = field(default_factory=lambda: Uniform(0.5, 2.0))
    l_exposed_km: object = field(default_factory=lambda: Fixed(0.001))
    deploy_speed_kmh: object = field(default_factory=lambda: Uniform(60.0, 100.0))

    # ---- S2 attended AFAD (Addendum A; drawn after every prior above)
    r_v2: object = field(default_factory=lambda: Triangular(3.5e-3, 6.8e-3, 2.1e-2))
    p_detect_s2: object = field(default_factory=lambda: Uniform(0.3, 0.9))
    offset_op_m: object = field(default_factory=lambda: Uniform(1.5, 6.0))


@dataclass(frozen=True)
class CellResult:
    cell: Cell
    n_iter: int
    h_s0: np.ndarray
    h_s1a: np.ndarray
    h_s1b: np.ndarray
    h_s2: np.ndarray
    parts: dict            # pathway breakdowns, per strategy
    diag: dict             # per-strategy intermediate quantities (violations, conflicts,
                           # collisions per operation-day; clearance; safe window)
    draws: dict            # sampled inputs (for PRCC)
    breakeven: dict        # per-iteration break-even r_v1 (dH<0 iff r_v1 < r*), per device

    def h(self, strategy: str) -> np.ndarray:
        return {"S0": self.h_s0, "S1a": self.h_s1a, "S1b": self.h_s1b, "S2": self.h_s2}[strategy]


def _cycle_quantities(q_vps: float, green: np.ndarray, clearance: np.ndarray,
                      sat_vps: np.ndarray):
    """Deterministic D/D cycle statistics for one symmetric alternating plan."""
    T = 2.0 * green + 2.0 * clearance
    red = green + 2.0 * clearance
    arr_cycle = q_vps * T
    stopped_red = q_vps * red
    t_clear_q = np.minimum(stopped_red / np.maximum(sat_vps - q_vps, 1e-9), green)
    stopped = stopped_red + q_vps * t_clear_q
    f_stop = np.clip(np.where(arr_cycle > 0, stopped / arr_cycle, 0.0), 0.0, 1.0)
    cycles_day = OPERATION_HOURS * 3600.0 / T
    facing_day = q_vps * red * 2.0 * cycles_day
    stopped_day = stopped * 2.0 * cycles_day
    return T, f_stop, cycles_day, stopped_red, facing_day, stopped_day


def run_cell(cell: Cell, sej: "dict[str, ExpertMixture] | PooledSEJ", priors: Priors,
             n_iter: int = 20_000, seed: int = 20260709, n_grid: int = 128,
             form: ModelForm = PRIMARY_FORM) -> CellResult:
    rng = np.random.default_rng([seed, int(cell.q_vph_dir), int(cell.section_m)])
    q_vps = cell.q_vph_dir / 3600.0
    draws: dict[str, np.ndarray] = {}

    def draw(name: str, dist) -> np.ndarray:
        v = dist.sample(rng.random(n_iter))
        draws[name] = v
        return v

    # ---- operations layer ---------------------------------------------------------
    v_p_kmh = draw("platoon_speed_kmh", priors.platoon_speed_kmh)
    v_p = v_p_kmh / 3.6                                   # m/s
    a_veh = draw("a_veh_ms2", priors.a_veh_ms2)
    h_sat = draw("sat_headway_s", priors.sat_headway_s)
    lost = draw("startup_lost_s", priors.startup_lost_s)
    margin = draw("s0_green_margin", priors.s0_green_margin)
    v_clear = draw("v_clear_kmh", priors.v_clear_kmh)
    buffer_s = draw("clear_buffer_s", priors.clear_buffer_s)
    t_confirm = draw("t_confirm_s", priors.t_confirm_s)

    L = np.full(n_iter, cell.section_m)
    transit = cell.section_m / v_p                        # violator, entering at speed
    t_rest = traverse_time_from_rest(L, a_veh, v_p)       # from a standing start
    sat_vps = 1.0 / h_sat

    # clearance intervals actually run by each control form
    C0 = t_rest + t_confirm                               # MTC confirms observed clear
    C1 = np.maximum(cell.section_m / (v_clear / 3.6) + buffer_s, t_rest)   # programmed all-red
    draws["_clearance_s0"], draws["_clearance_s1"] = C0, C1

    rho_q = q_vps / sat_vps
    stable = (2.0 * rho_q) < 1.0
    draws["_stable"] = stable.astype(float)

    def g_min(C: np.ndarray) -> np.ndarray:
        return np.where(stable, rho_q * 2.0 * C / np.maximum(1.0 - 2.0 * rho_q, 1e-9), np.nan)

    f_a = draw("f_cycle_a", priors.f_cycle_a)
    f_b = draw("f_cycle_b", priors.f_cycle_b)
    greens = {"S0": margin * g_min(C0),
              "S1a": f_a * margin * g_min(C1),
              "S1b": f_b * margin * g_min(C1)}
    clears = {"S0": C0, "S1a": C1, "S1b": C1}
    greens["S2"], clears["S2"] = greens["S0"], clears["S0"]      # attended release

    # ---- SEJ anchors (coupled expert draws) ---------------------------------------
    if isinstance(sej, PooledSEJ):                       # public-release form (pooled rows)
        re1_rate, sev1_p = sej.sample_pairs(rng, n_iter, "1")
        re3_rate, sev3_p = sej.sample_pairs(rng, n_iter, "3")
    else:
        re1, sev1 = sej["C.RE1_Queue"], sej["C.SEV1"]
        re3, sev3 = sej["C.RE3_MTC"], sej["C.SEV3"]
        idx1 = rng.integers(0, re1.n_experts, n_iter)
        idx3 = rng.integers(0, re3.n_experts, n_iter)
        re1_rate = 1.0 / re1.sample_with_index(idx1, rng.random(n_iter))
        sev1_p = sev1.sample_with_index(idx1, rng.random(n_iter))
        re3_rate = 1.0 / re3.sample_with_index(idx3, rng.random(n_iter))
        sev3_p = sev3.sample_with_index(idx3, rng.random(n_iter))
    draws["re1_rate"], draws["sev1_p"] = re1_rate, sev1_p
    draws["re3_rate"], draws["sev3_p"] = re3_rate, sev3_p

    # ---- behavioural priors --------------------------------------------------------
    r_v0 = draw("r_v0", priors.r_v0)
    r_v1a = draw("r_v1a", priors.r_v1a)
    w_occ = draw("w_occ", priors.w_occ)
    q_lead = draw("q_lead", priors.q_lead)
    ttc50 = draw("ttc50", priors.ttc50)
    s_ttc = draw("s_ttc", priors.s_ttc)
    w_onset = draw("w_onset", priors.w_onset)
    onset_win = draw("onset_window_s", priors.onset_window_s)
    p_det_s0 = draw("p_detect_s0", priors.p_detect_s0)
    p_det_s1b = draw("p_detect_s1b", priors.p_detect_s1b)
    f_imp = draw("impact_speed_frac", priors.impact_speed_frac)
    p_ev_harm = draw("p_evade_harm", priors.p_evade_harm)
    d_sight = draw("d_sight_m", priors.d_sight_m)
    sight = np.minimum(d_sight, L)
    m1 = draw("mass1_kg", priors.mass_kg)
    m2 = draw("mass2_kg", priors.mass_kg)
    occ1 = np.round(draw("occ1", priors.occupancy)).astype(int)
    occ2 = np.round(draw("occ2", priors.occupancy)).astype(int)

    # ---- W4d inputs (shared by S1a/S1b: same physical placement task) ---------------
    t_dep = draw("t_deploy_s", priors.t_deploy_s)
    enc = draw("enc_rate_vkm", priors.enc_rate_vkm)
    alpha = draw("reach_alpha", priors.reach_alpha)
    offset = draw("offset_m", priors.offset_m)
    l_exp = priors.l_exposed_km.sample(rng.random(n_iter))
    v_dep = draw("deploy_speed_kmh", priors.deploy_speed_kmh)

    # ---- S2 draws: AFTER every existing draw, so the frozen strategies are unchanged ----
    r_v2 = draw("r_v2", priors.r_v2)
    p_det_s2 = draw("p_detect_s2", priors.p_detect_s2)
    offset_op = draw("offset_op_m", priors.offset_op_m)

    veh_day_dir = np.full(n_iter, cell.q_vph_dir * OPERATION_HOURS)

    # W1 anchor conversion at the BASELINE S0 profile of this cell
    _, f_stop0, _, _, _, _ = _cycle_quantities(q_vps, greens["S0"], clears["S0"], sat_vps)
    re1_per_stop = re1_rate / np.maximum(f_stop0, 1e-6)

    results_h: dict[str, np.ndarray] = {}
    parts: dict[str, dict[str, np.ndarray]] = {}
    diag: dict[str, dict[str, np.ndarray]] = {}

    for name in STRATEGIES:
        green, clearance = greens[name], clears[name]
        T, f_stop, cycles_day, n_queue, facing_day, stopped_day = _cycle_quantities(
            q_vps, green, clearance, sat_vps)
        day = DayContext(veh_per_day_dir=veh_day_dir, stopped_per_day=stopped_day,
                         facing_stop_per_day=facing_day, cycles_per_day=cycles_day)
        ci = ConflictInputs(section_m=L, v_platoon=v_p, a_veh=a_veh,
                            clearance_s=clearance, green_opp_s=green,
                            n_queue_opp=np.maximum(np.round(n_queue), 0),
                            q_opp_vps=np.full(n_iter, q_vps),
                            sat_headway_s=h_sat, startup_lost_s=lost,
                            sight_m=sight)

        if name == "S0":
            r_v, p_det = r_v0, p_det_s0
            w3 = w3_events(day, re3_rate, sev3_p, v_p_kmh, active=True)
            strikes_day = 2.0 * veh_day_dir * re3_rate     # controller struck, any severity
            w4 = np.zeros(n_iter)
        elif name == "S2":
            r_v, p_det = r_v2, p_det_s2                   # attended gated device, operator hold
            strikes_day, w3 = w3r_operator_events(veh_day_dir, enc, alpha, offset_op, l_exp,
                                                  v_p_kmh, p_worker)
            w4 = w4d_events(np.full(n_iter, 2.0 * cell.q_vph_dir), t_dep, enc,
                            alpha, offset, l_exp, v_dep, p_worker)
        else:
            r_v = r_v1a                                   # same physical head, S1a and S1b
            p_det = np.zeros(n_iter) if name == "S1a" else p_det_s1b
            w3 = np.zeros(n_iter)
            strikes_day = np.zeros(n_iter)
            w4 = w4d_events(np.full(n_iter, 2.0 * cell.q_vph_dir), t_dep, enc,
                            alpha, offset, l_exp, v_dep, p_worker)

        tp = TreeParams(w_occ=w_occ, q_lead=q_lead, p_detect=p_det,
                        ttc50=ttc50, s_ttc=s_ttc,
                        w_onset=w_onset, onset_window_s=onset_win)
        w5 = w5_terms(day, ci, tp, r_v, f_imp, m1, m2, occ1, occ2, n_grid=n_grid, form=form)
        w1 = w1_events(day, re1_per_stop, sev1_p)
        w5b = w5b_band(w5["evasions_per_day"], p_ev_harm, v_p_kmh)

        results_h[name] = w1 + w3 + w5["events"] + w4
        parts[name] = {"W1": w1, "W3": w3, "W5": w5["events"], "W4d": w4, "W5b": w5b}
        diag[name] = {
            "clearance_s": clearance, "green_s": green, "cycle_s": T,
            "facing_per_day": facing_day, "stopped_per_day": stopped_day,
            "controller_strikes_per_day": strikes_day,
            "violations_per_day": w5["violations_per_day"],
            "conflicts_per_day": w5["conflicts_per_day"],
            "collisions_per_day": w5["collisions_per_day"],
            "evasions_per_day": w5["evasions_per_day"],
            "closing_kmh": w5["closing_ms"] * 3.6,
            "mean_ttc_s": w5["mean_ttc"], "p_blind": w5["p_blind"],
            "f_clear": w5["f_clear"], "p_safe_window": w5["p_safe_window"],
        }

    # ---- closed-form break-even in the device violation rate (dH linear in it) ---------
    # For S2 the residual operator term W3r sits in parts["S2"]["W3"]; it is a constant of
    # the mechanism and enters the base gap.
    breakeven: dict[str, np.ndarray] = {}
    for name in DEVICE_STRATEGIES:
        r_dev = r_v2 if name == "S2" else r_v1a
        k = parts[name]["W5"] / np.maximum(r_dev, 1e-300)
        base_gap = (parts[name]["W1"] - parts["S0"]["W1"] - parts["S0"]["W3"]
                    - parts["S0"]["W5"] + parts[name]["W4d"] + parts[name]["W3"])
        with np.errstate(divide="ignore", invalid="ignore"):
            r_star = np.where(k > 0, np.maximum(-base_gap, 0.0) / k, np.inf)
        breakeven[name] = r_star

    return CellResult(cell=cell, n_iter=n_iter, h_s0=results_h["S0"],
                      h_s1a=results_h["S1a"], h_s1b=results_h["S1b"], h_s2=results_h["S2"],
                      parts=parts, diag=diag, draws=draws, breakeven=breakeven)


def p_dh_negative(h_s1: np.ndarray, h_s0: np.ndarray) -> tuple[float, float, float]:
    """P(dH<0) with a 95% Wilson interval, over cycle-stable iterations only."""
    dh = h_s1 - h_s0
    dh = dh[np.isfinite(dh)]
    n = len(dh)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = float((dh < 0).mean())
    z = 1.959963984540054
    den = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, centre - half, centre + half


def _queue_gap(res: CellResult, strategy: str, include: bool) -> np.ndarray:
    """The queue-tail difference between the strategies.

    It is small, it favours the device, and it is a consequence of the fixed-time
    green-scaling prior: a longer green lets more vehicles through without stopping, so a
    less efficient plan stops fewer of them. That buys safety with delay, and delay is
    outside this paper's scope. The decision outputs therefore SUPPRESS it by default, which
    is conservative against the device, and its magnitude is reported separately.
    """
    gap = res.parts[strategy]["W1"] - res.parts["S0"]["W1"]
    return gap if include else np.zeros_like(gap)


def calibration_curve(res: CellResult, strategy: str = "S1a",
                      lams: np.ndarray | None = None,
                      include_queue_gap: bool = False) -> list[tuple[float, float, float]]:
    """P(dH<0) as a function of the model-implied head-on collision frequency.

    A common scaling `lam` of the collision chain applies to BOTH arms (the tree's
    conditionals are shared), so this traces the decision against an OBSERVABLE quantity
    without requiring any contested parameter to be believed.

    Returns [(lam, implied collisions per operation-day, P(dH<0)), ...].
    """
    if lams is None:
        lams = np.geomspace(1e-4, 10.0, 60)
    P, D = res.parts, res.diag
    base = (_queue_gap(res, strategy, include_queue_gap) - P["S0"]["W3"]
            + P[strategy]["W4d"] + P[strategy]["W3"])
    w5_gap = P[strategy]["W5"] - P["S0"]["W5"]
    coll = D[strategy]["collisions_per_day"]
    out = []
    for lam in lams:
        dh = base + lam * w5_gap
        dh = dh[np.isfinite(dh)]
        out.append((float(lam), float(np.nanmedian(coll) * lam), float((dh < 0).mean())))
    return out


def decision_surface(res: CellResult, strategy: str = "S1a",
                     lam_w3: np.ndarray | None = None,
                     lam_w5: np.ndarray | None = None) -> dict:
    """P(dH<0) over the plane of the two quantities the record can actually measure.

    `lam_w3` scales the controller-struck pathway, `lam_w5` scales the violation-conflict
    pathway in BOTH arms. Neither prior has to be believed: the surface is read at whatever
    controller-strike and head-on-collision frequencies a jurisdiction observes.

    For S2 the operator's residual beside-the-road term (W3r, in parts["S2"]["W3"]) is a
    constant of the mechanism, like W4d: it carries no elicited level and is not scaled.

    The queue-tail difference is SUPPRESSED here (see `_queue_gap`): it favours the device,
    it is a consequence of the cycle-plan prior rather than of the control form, and it buys
    its safety with delay, which this paper does not model. Suppressing it is conservative
    against the device. Its median is returned so a reader can restore it.
    """
    if lam_w3 is None:
        lam_w3 = np.geomspace(1e-4, 10.0, 41)
    if lam_w5 is None:
        lam_w5 = np.geomspace(1e-4, 10.0, 41)
    P, D = res.parts, res.diag
    w1_gap = P[strategy]["W1"] - P["S0"]["W1"]
    w5_gap = P[strategy]["W5"] - P["S0"]["W5"]
    w3 = P["S0"]["W3"]
    const = _queue_gap(res, strategy, include=False) + P[strategy]["W4d"] + P[strategy]["W3"]

    grid = np.empty((len(lam_w3), len(lam_w5)))
    for i, a3 in enumerate(lam_w3):
        for j, a5 in enumerate(lam_w5):
            dh = const - a3 * w3 + a5 * w5_gap
            dh = dh[np.isfinite(dh)]
            grid[i, j] = (dh < 0).mean()
    return {
        "lam_w3": lam_w3, "lam_w5": lam_w5, "p_grid": grid,
        # BOTH axes in the ledger's own unit, so each is directly comparable to a record and
        # the surface reduces to the trade it represents: the substitution helps exactly when
        # the controller pathway it removes exceeds the head-on pathway it introduces.
        "controller_dsi_per_day": np.nanmedian(w3) * lam_w3,
        "headon_dsi_per_day": np.nanmedian(P[strategy]["W5"]) * lam_w5,
        # collision count is retained as the gate-1 diagnostic, checkable against crash counts
        "headon_collisions_per_day": np.nanmedian(D[strategy]["collisions_per_day"]) * lam_w5,
        "w1_gap_median": float(np.nanmedian(w1_gap)),
        "w5_gap_median": float(np.nanmedian(w5_gap)),
        "w3_median": float(np.nanmedian(w3)),
        "w5_median": float(np.nanmedian(P[strategy]["W5"])),
    }
