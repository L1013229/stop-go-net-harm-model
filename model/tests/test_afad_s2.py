"""Addendum A: the attended AFAD arm (S2) and the model-form hooks.

Pins (1) that unbound draws in the three frozen strategies reproduce production bit for bit
after the extension and entry-cap correction, (2) the S2 structural identities, (3) that the primary model form is
byte-identical to the pre-addendum tree and the alternatives move in the stated direction.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.conflict import ModelForm, TreeParams, q_fail, w5_tree  # noqa: E402
from mtcpts.distributions import Fixed, load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, p_dh_negative, run_cell  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
FROZEN = ROOT / "outputs" / "dist" / "2020f2c_20260709" / "baseline_traces.npz"


@pytest.fixture(scope="module")
def sej():
    return load_sej(CONFIG)   # per-expert fits when present, else the pooled release form


# ------------------------------------------------------------- frozen strategies unchanged
@pytest.mark.skipif(not FROZEN.exists(), reason="frozen production traces not on this machine")
def test_uncapped_draws_reproduce_frozen_production_bit_for_bit(sej):
    """The entry-cap addendum changes only binding draws and W5-derived quantities.
    Preserve the original bitwise regression everywhere else, including all inputs."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=20_000, n_grid=128)
    fr = np.load(FROZEN)
    for key, value in res.draws.items():
        if f"draw_{key}" in fr:
            np.testing.assert_array_equal(value, fr[f"draw_{key}"])
    for s in ("S0", "S1a", "S1b"):
        unchanged = ~res.diag[s]["onset_cap_binds"]
        assert np.array_equal(res.h(s)[unchanged], fr[f"h_{s.lower()}"][unchanged]), s
        for k in ("W1", "W3", "W5", "W4d", "W5b"):
            mask = unchanged if k in ("W5", "W5b") else np.ones(res.n_iter, dtype=bool)
            assert np.array_equal(res.parts[s][k][mask], fr[f"part_{s}_{k}"][mask]), (s, k)
        assert np.array_equal(res.diag[s]["collisions_per_day"][unchanged],
                              fr[f"diag_{s}_collisions_per_day"][unchanged])


def test_s2_draws_follow_every_existing_draw(sej):
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=200, n_grid=8)
    keys = list(res.draws)
    assert keys[-3:] == ["r_v2", "p_detect_s2", "offset_op_m"]


# ------------------------------------------------------------- S2 structural identities
def test_s2_queue_tail_equals_s0_exactly(sej):
    """Attended release: S2 runs the S0 plan, so W1 is identical and cancels."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=2_000, n_grid=16)
    assert np.array_equal(res.parts["S2"]["W1"], res.parts["S0"]["W1"])
    assert np.array_equal(res.diag["S2"]["clearance_s"], res.diag["S0"]["clearance_s"])


def test_s2_identity_reduces_to_minus_controller_pathway(sej):
    """Same violation rate and hold as S0, no encroachment (kills W3r and W4d) => the only
    difference left is the lane-standing controller pathway: dH(S2) = -W3 exactly."""
    pr = Priors(r_v2=Fixed(1.0e-3), r_v0=Fixed(1.0e-3),
                p_detect_s0=Fixed(0.6), p_detect_s2=Fixed(0.6),
                enc_rate_vkm=Fixed(0.0))
    res = run_cell(Cell(300, 250), sej, pr, n_iter=2_000, n_grid=16)
    assert np.allclose(res.parts["S2"]["W3"], 0.0) and np.allclose(res.parts["S2"]["W4d"], 0.0)
    assert np.array_equal(res.parts["S2"]["W5"], res.parts["S0"]["W5"])
    assert np.allclose(res.h_s2 - res.h_s0, -res.parts["S0"]["W3"], rtol=1e-10, atol=1e-18)


def test_s2_operator_exposure_falls_with_standing_offset(sej):
    near = run_cell(Cell(300, 250), sej, Priors(offset_op_m=Fixed(1.5)), n_iter=1_000, n_grid=8)
    far = run_cell(Cell(300, 250), sej, Priors(offset_op_m=Fixed(6.0)), n_iter=1_000, n_grid=8)
    assert np.all(far.parts["S2"]["W3"] < near.parts["S2"]["W3"])
    # the residual is a strike frequency times a severity: strikes/day is the frame's lambda
    assert np.all(near.diag["S2"]["controller_strikes_per_day"] > near.parts["S2"]["W3"])


def test_s2_violation_count_preserved_and_below_signal(sej):
    """The tree preserves the measured count for S2 too, and at the prior modes the attended
    device violates less often than the unattended signal (the ordering the record shows)."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=4_000, n_grid=16)
    d = res.diag["S2"]
    assert np.allclose(d["violations_per_day"], d["facing_per_day"] * res.draws["r_v2"])
    assert np.nanmedian(d["violations_per_day"]) < np.nanmedian(res.diag["S1a"]["violations_per_day"])


def test_s2_gate_1_at_baseline(sej):
    """Addendum A4: gate 1 applies to S2 exactly as to S1a."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=20_000, n_grid=64)
    d = res.diag["S2"]
    coll = float(np.nanmedian(d["collisions_per_day"]))
    pcv = float(np.nanmedian(d["collisions_per_day"] / np.maximum(d["violations_per_day"], 1e-300)))
    assert 1e-6 <= coll <= 1e-3, f"S2 implied {coll:.3e} head-on collisions/op-day"
    assert pcv < 8.5e-3


def test_s2_breakeven_is_consistent_with_dh_sign(sej):
    """dH(S2) < 0 iff r_v2 < r*, per iteration, by the closed form."""
    res = run_cell(Cell(300, 250), sej, Priors(), n_iter=2_000, n_grid=16)
    dh = res.h_s2 - res.h_s0
    ok = np.isfinite(dh)
    pred = res.draws["r_v2"][ok] < res.breakeven["S2"][ok]
    assert np.mean(pred == (dh[ok] < 0)) > 0.999


# ------------------------------------------------------------- model form (Addendum A6)
def _ci(n=64, L=250.0, C=30.0, g=24.0, sight=None):
    from mtcpts.conflict import ConflictInputs
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


def test_primary_form_is_the_default_and_byte_identical():
    a = w5_tree(_ci(), _tp())
    b = w5_tree(_ci(), _tp(), form=ModelForm(rho=0.0, curve="logistic"))
    for k in a:
        assert np.array_equal(a[k], b[k]), k


def test_common_cause_share_raises_collisions_monotonically():
    p0 = w5_tree(_ci(), _tp(), form=ModelForm(rho=0.0))["p_coll"]
    p5 = w5_tree(_ci(), _tp(), form=ModelForm(rho=0.5))["p_coll"]
    p1 = w5_tree(_ci(), _tp(), form=ModelForm(rho=1.0))["p_coll"]
    assert np.all(p0 <= p5 + 1e-15) and np.all(p5 <= p1 + 1e-15)
    assert np.all(p1 > p0)


def test_alternative_curves_share_the_median_and_bound_the_primary():
    tp = _tp(n=5)
    ttc = np.array([0.5, 1.0, 1.75, 3.0, 8.0])
    lg = q_fail(ttc, tp, ModelForm(curve="logistic"))
    ll = q_fail(ttc, tp, ModelForm(curve="loglogistic"))
    th = q_fail(ttc, tp, ModelForm(curve="threshold"))
    assert np.isclose(lg[2], 0.5) and np.isclose(ll[2], 0.5)
    assert np.array_equal(th, np.array([1.0, 1.0, 0.0, 0.0, 0.0]))
    assert np.all(np.diff(ll) < 0) and np.all((ll >= 0) & (ll <= 1))
    with pytest.raises(ValueError):
        q_fail(ttc, tp, ModelForm(curve="nonesuch"))


def test_model_form_reaches_run_cell(sej):
    a = run_cell(Cell(300, 250), sej, Priors(), n_iter=500, n_grid=8)
    b = run_cell(Cell(300, 250), sej, Priors(), n_iter=500, n_grid=8, form=ModelForm(rho=1.0))
    assert np.all(b.diag["S1a"]["collisions_per_day"] >= a.diag["S1a"]["collisions_per_day"])
    assert np.array_equal(a.draws["r_v1a"], b.draws["r_v1a"])   # same draws, different structure
    pa, _, _ = p_dh_negative(a.h_s1a, a.h_s0)
    assert 0.0 <= pa <= 1.0
