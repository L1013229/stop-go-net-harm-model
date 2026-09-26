"""Structural identities, tree closure, monotonicities, anchors, validity gate."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.conflict import (ConflictInputs, TreeParams, accel_distance,  # noqa: E402
                             q_fail, time_to_close, traverse_time_from_rest, w5_tree)
from mtcpts.distributions import Fixed, load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, run_cell, p_dh_negative  # noqa: E402
from mtcpts.severity import (implied_strike_speed_kmh, p_event_dsi_headon,  # noqa: E402
                             p_worker, sev_worker_at_speed)

CONFIG = Path(__file__).resolve().parents[1] / "config"


@pytest.fixture(scope="module")
def sej():
    return load_sej(CONFIG)   # per-expert fits when present, else the pooled release form


# --------------------------------------------------------------------- kinematics
def test_traverse_from_rest_exceeds_transit_at_speed():
    """A vehicle starting from rest always takes longer than one entering at speed.
    This difference IS the safe-entry window a clearance margin creates."""
    L, a, v = np.array([250.0]), np.array([1.5]), np.array([50 / 3.6])
    assert traverse_time_from_rest(L, a, v)[0] > (L / v)[0]


def test_accel_distance_matches_cruise_after_cap():
    a, v = np.array([1.5]), np.array([13.89])
    t_acc = v / a
    d = accel_distance(t_acc + np.array([10.0]), a, v)
    assert np.isclose(d[0], 0.5 * v[0] * t_acc[0] + v[0] * 10.0)


def test_time_to_close_monotone_in_separation():
    a, v = np.full(3, 1.5), np.full(3, 13.89)
    t = time_to_close(np.array([10.0, 100.0, 250.0]), v, np.zeros(3), a, v)
    assert t[0] < t[1] < t[2]


def test_q_fail_monotone_decreasing_in_ttc():
    tp = TreeParams(*[np.full(4, x) for x in (1e-3, 1e-2, 0.0, 1.75, 0.65, 0.8, 5.0)])
    q = q_fail(np.array([0.5, 1.75, 3.0, 8.0]), tp)
    assert q[0] > q[1] > q[2] > q[3]
    assert np.isclose(q[1], 0.5, atol=1e-9)      # by construction at ttc50


# --------------------------------------------------------------------- tree closure
def _ci(n=64, L=250.0, C=30.0, g=24.0, sight=None):
    return ConflictInputs(
        section_m=np.full(n, L), v_platoon=np.full(n, 50 / 3.6), a_veh=np.full(n, 1.5),
        clearance_s=np.full(n, C), green_opp_s=np.full(n, g),
        n_queue_opp=np.full(n, 7.0), q_opp_vps=np.full(n, 300 / 3600),
        sat_headway_s=np.full(n, 2.25), startup_lost_s=np.full(n, 2.0),
        sight_m=np.full(n, L if sight is None else sight))


def _tp(n=64, **kw):
    d = dict(w_occ=1e-3, q_lead=1e-2, p_detect=0.0, ttc50=1.75, s_ttc=0.65,
             w_onset=0.8, onset_window_s=5.0)
    d.update(kw)
    return TreeParams(**{k: np.full(n, v) for k, v in d.items()})


def test_tree_probabilities_are_ordered_and_bounded():
    t = w5_tree(_ci(), _tp(), severity_fn=lambda c: np.full(len(c), 0.1))
    for k in ("p_conflict", "p_coll", "p_harm", "p_evade"):
        assert np.all(t[k] >= -1e-12) and np.all(t[k] <= 1.0 + 1e-12), k
    assert np.all(t["p_coll"] <= t["p_conflict"] + 1e-12)
    assert np.all(t["p_harm"] <= t["p_coll"] + 1e-12)
    assert np.allclose(t["p_evade"], t["p_conflict"] - t["p_coll"], atol=1e-12)


def test_no_conflict_when_fully_intervisible_and_nobody_enters_wrongly():
    """With FULL intervisibility, w_occ = 0 and q_lead = 0 must terminate every violation
    harmlessly: every conflict route requires someone to enter against a vehicle they can
    see. The identity holds only at full sight; restricted sight opens blind routes."""
    t = w5_tree(_ci(sight=250.0), _tp(w_occ=0.0, q_lead=0.0))
    assert np.allclose(t["p_conflict"], 0.0)
    assert np.allclose(t["p_coll"], 0.0)


def test_restricted_sight_creates_blind_conflicts_no_behaviour_can_remove():
    """Dave's intervisibility point: an opposing vehicle beyond the sight line cannot deter
    entry, and a violator beyond the entrant's sight line cannot be yielded to. Even with
    w_occ = 0 and q_lead = 0, a sight-restricted section carries conflicts, and they are
    blind ones."""
    t = w5_tree(_ci(L=1000.0, C=80.0, g=40.0, sight=150.0), _tp(w_occ=0.0, q_lead=0.0))
    assert np.all(t["p_conflict"] > 0.0)
    assert np.all(t["p_blind"] > 0.99)


def test_collisions_decrease_with_sight_distance():
    lo = w5_tree(_ci(L=1000.0, C=80.0, g=40.0, sight=150.0), _tp())["p_coll"]
    hi = w5_tree(_ci(L=1000.0, C=80.0, g=40.0, sight=1000.0), _tp())["p_coll"]
    assert np.all(hi < lo)


def test_green_gap_entries_face_future_arrivals():
    """Dave's red-light logic point: a violator entering a genuinely clear gap during the
    opposing green is met by the NEXT arrival. With entry-against-visible-traffic switched
    off entirely (w_occ = 0) and full sight, conflicts must still exist, and they must come
    through the q_lead route (q_lead = 0 kills them; q_lead > 0 revives them)."""
    dead = w5_tree(_ci(sight=250.0), _tp(w_occ=0.0, q_lead=0.0))["p_conflict"]
    live = w5_tree(_ci(sight=250.0), _tp(w_occ=0.0, q_lead=0.5))["p_conflict"]
    assert np.allclose(dead, 0.0)
    assert np.all(live > 0.0)


def test_detection_hold_cannot_increase_conflict():
    lo = w5_tree(_ci(), _tp(p_detect=0.0))["p_conflict"]
    hi = w5_tree(_ci(), _tp(p_detect=0.9))["p_conflict"]
    assert np.all(hi <= lo + 1e-12)


def test_conflict_monotone_in_q_lead():
    a = w5_tree(_ci(), _tp(q_lead=1e-3))["p_conflict"]
    b = w5_tree(_ci(), _tp(q_lead=1e-1))["p_conflict"]
    assert np.all(b > a)


def test_longer_clearance_reduces_collisions():
    """The mechanism the codes of practice rely on: a clearance interval longer than the
    violator's transit lets an onset violator clear before the opposing release."""
    short = w5_tree(_ci(C=19.0), _tp())["p_coll"]     # ~= transit at platoon speed
    long_ = w5_tree(_ci(C=35.0), _tp())["p_coll"]
    assert np.all(long_ < short)


def test_onset_violations_are_safer_than_standing_departures():
    """The field record's onset clustering is benign, and the model must say so: shifting
    the mixture toward onset entries reduces collisions."""
    mostly_onset = w5_tree(_ci(), _tp(w_onset=0.95))["p_coll"]
    mostly_stand = w5_tree(_ci(), _tp(w_onset=0.05))["p_coll"]
    assert np.all(mostly_onset < mostly_stand)


# --------------------------------------------------------------------- severity
def test_speed_anchor_reproduces_elicited_value_at_the_anchor():
    sev = np.array([0.2, 0.625, 0.9])
    assert np.allclose(sev_worker_at_speed(sev, np.full(3, 50.0)), sev)


def test_speed_anchor_is_monotone_and_bounded():
    sev = np.full(5, 0.625)
    v = np.array([20.0, 40.0, 50.0, 60.0, 90.0])
    out = sev_worker_at_speed(sev, v)
    assert np.all(np.diff(out) > 0) and np.all((out >= 0) & (out <= 1))


def test_implied_strike_speed_inverts_the_worker_curve():
    v = np.array([30.0, 50.0, 65.5])
    assert np.allclose(implied_strike_speed_kmh(p_worker(v)), v, atol=1e-6)


def test_event_dsi_rises_with_occupancy():
    dv = np.full(3, 40.0)
    p = p_event_dsi_headon(dv, dv, np.array([1, 2, 3]), np.array([1, 1, 1]))
    assert p[0] < p[1] < p[2]


# --------------------------------------------------------------------- model identities
def test_identity_dh_reduces_to_minus_w3(sej):
    """Behaviourally identical strategies, identical clearance, no detection, no placement
    exposure => dH = -W3 exactly. W1 and W5 must cancel to machine precision."""
    pr = Priors(
        r_v0=Fixed(1.0e-3), r_v1a=Fixed(1.0e-3),
        p_detect_s0=Fixed(0.0), p_detect_s1b=Fixed(0.0),
        f_cycle_a=Fixed(1.0), f_cycle_b=Fixed(1.0),
        t_confirm_s=Fixed(0.0), v_clear_kmh=Fixed(500.0), clear_buffer_s=Fixed(0.0),
        enc_rate_vkm=Fixed(0.0),
    )
    res = run_cell(Cell(300, 250), sej, pr, n_iter=2_000, n_grid=32)
    assert np.allclose(res.diag["S0"]["clearance_s"], res.diag["S1a"]["clearance_s"])
    assert np.allclose(res.h_s1a - res.h_s0, -res.parts["S0"]["W3"], rtol=1e-10, atol=1e-18)


def test_violation_count_is_preserved_by_the_tree(sej):
    """The tree makes violation TIMING endogenous; it must not alter the literature-measured
    violation COUNT. violations/day == facing/day * r_v exactly."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=2_000, n_grid=32)
    d = res.diag["S1a"]
    assert np.allclose(d["violations_per_day"], d["facing_per_day"] * res.draws["r_v1a"])


def test_anchor_reproduction_w1_w3_at_stipulated_speed(sej):
    """The companion study's canonical per-day figures were elicited under Scenario C, whose
    stipulated operating speed is 50 km/h. The anchors must reproduce THERE; at the sampled
    realistic speeds (median 40) the speed-transported severity is correctly lower."""
    pr = Priors(platoon_speed_kmh=Fixed(50.0))
    res = run_cell(Cell(300, 250), sej, pr, n_iter=20_000, n_grid=32)
    w1 = float(np.median(res.parts["S0"]["W1"]))
    w3 = float(np.median(res.parts["S0"]["W3"]))
    assert 0.8 * 5.496e-3 < w1 < 1.25 * 5.496e-3
    assert 0.85 * 4.032e-3 < w3 < 1.15 * 4.032e-3


def test_w3_falls_below_anchor_at_realistic_speeds(sej):
    """At the realistic operating-speed prior (median 40 km/h) the transported controller
    severity must sit BELOW the 50 km/h anchor value, not above it."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=8_000, n_grid=32)
    assert float(np.median(res.parts["S0"]["W3"])) < 4.032e-3


def test_oversaturation_is_nan_not_a_number(sej):
    res = run_cell(Cell(1000, 250), sej, Priors(), n_iter=500, n_grid=16)
    assert np.all(~np.isfinite(res.h_s0))
    p, _, _ = p_dh_negative(res.h_s1a, res.h_s0)
    assert np.isnan(p)


def test_bit_level_reproducibility(sej):
    a = run_cell(Cell(300, 250), sej, Priors(), n_iter=1_000, n_grid=16)
    b = run_cell(Cell(300, 250), sej, Priors(), n_iter=1_000, n_grid=16)
    assert np.array_equal(a.h_s1a, b.h_s1a)


# --------------------------------------------------------------------- validity gate
def test_validity_gate_1_implied_headon_collision_frequency(sej):
    """Blocking gate: the model must imply a head-on collision frequency the crash record
    admits. See research/crash-record-bounds.md. Repaired at structure, never by prior."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=20_000, n_grid=64)
    coll = float(np.nanmedian(res.diag["S1a"]["collisions_per_day"]))
    assert 1e-6 <= coll <= 1e-3, f"implied {coll:.3e} head-on collisions/op-day"


def test_p_collision_given_violation_under_rule_of_three_ceiling(sej):
    """355 observed violations, zero collisions => P(coll|viol) < 8.5e-3 at 95%."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=20_000, n_grid=64)
    d = res.diag["S1a"]
    pcv = float(np.nanmedian(d["collisions_per_day"] / np.maximum(d["violations_per_day"], 1e-300)))
    assert pcv < 8.5e-3, f"P(collision|violation) = {pcv:.3e}"


# --------------------------------------------------------------------- sensitivity
def test_prcc_matches_the_residual_regression_construction():
    """The precision-matrix form must agree with an explicit residual regression, or the
    speed-up has changed the estimator rather than the implementation."""
    from scipy.stats import rankdata

    from mtcpts.sensitivity import prcc
    rng = np.random.default_rng(0)
    n = 3_000
    X = {f"x{i}": rng.random(n) for i in range(6)}
    y = 2 * X["x0"] - 1.5 * X["x1"] + 0.4 * X["x2"] ** 2 + 0.2 * rng.random(n)
    names = list(X)

    def residual(a, B):
        A = np.column_stack([np.ones(len(B)), B])
        coef, *_ = np.linalg.lstsq(A, a, rcond=None)
        return a - A @ coef

    R = {k: rankdata(X[k]) for k in names}
    t = rankdata(y)
    for k in names:
        others = np.column_stack([R[j] for j in names if j != k])
        rx, ry = residual(R[k], others), residual(t, others)
        ref = float((rx * ry).sum() / np.sqrt((rx * rx).sum() * (ry * ry).sum()))
        assert abs(prcc(X, y, names)[k] - ref) < 1e-10
