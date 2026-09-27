"""Prespecified 2026-09-27 entry cap: capacity, conservation and unchanged draws."""
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mtcpts.conflict import ModelForm, w5_tree
from mtcpts.distributions import load_sej
from mtcpts.model import Cell, Priors, run_cell
from test_model import _ci, _tp

FORMS = [ModelForm(), ModelForm(rho=.5), ModelForm(rho=1),
         ModelForm(curve='threshold'), ModelForm(curve='loglogistic')]

@pytest.mark.parametrize('form', FORMS)
def test_cap_after_sight_normalisation_preserves_entry_total_and_kernels(form):
    ci, tp = _ci(n=4), _tp(n=4)
    severity = lambda closing: np.minimum(closing / 100, .8)
    # Third draw binds ONLY after sight normalisation; fourth binds before it.
    raw = w5_tree(ci, tp, form=form, severity_fn=severity)
    rate = np.array([0, .001, (1 + raw['mean_w'][2]) / 2 * 5 / (84 * .8), .089])
    assert rate[2] * ci.red_s[2] * tp.w_onset[2] / 5 < 1
    cap = w5_tree(ci, tp, form=form, r_v_facing=rate, severity_fn=severity)
    on = w5_tree(ci, replace(tp, w_onset=np.ones(4)), form=form, severity_fn=severity)
    st = w5_tree(ci, replace(tp, w_onset=np.zeros(4)), form=form, severity_fn=severity)
    expected_fraction = np.minimum(tp.w_onset / raw['mean_w'],
                                   np.divide(5, rate * ci.red_s, out=np.full(4, np.inf), where=rate > 0))
    np.testing.assert_allclose(cap['onset_share'], expected_fraction, rtol=2e-15)
    assert cap['onset_cap_binds'].tolist() == [False, False, True, True]
    # Check the allocation itself, including the standing mass, rather than a clipped diagnostic.
    for key in ('p_conflict', 'p_coll', 'p_evade', 'p_harm'):
        np.testing.assert_allclose(cap[key], expected_fraction * on[key] +
                                   (1 - expected_fraction) * st[key], rtol=1e-12, atol=1e-16)
        np.testing.assert_array_equal(cap[key][:2], raw[key][:2])
    q = 300 / 3600
    total = q * ci.red_s * rate
    moving = total * cap['onset_share']
    standing = total * (1 - cap['onset_share'])
    assert np.all(moving / (q * 5) <= 1 + 2e-15)
    np.testing.assert_allclose(moving + standing, total, rtol=2e-15)

@pytest.mark.parametrize('cell', [Cell(300, 250), Cell(600, 2000), Cell(800, 1000)])
def test_all_controls_use_own_rate_and_grid_capacity(cell):
    sej = load_sej(Path(__file__).resolve().parents[1] / 'config')
    res = run_cell(cell, sej, Priors(), n_iter=256, n_grid=32)
    for control, key in [('S0', 'r_v0'), ('S1a', 'r_v1a'), ('S1b', 'r_v1a'), ('S2', 'r_v2')]:
        diag = res.diag[control]
        finite = np.isfinite(res.h(control))
        total = diag['facing_per_day'] * res.draws[key]
        np.testing.assert_array_equal(diag['violations_per_day'], total)
        red = 2 * diag['clearance_s'] + diag['green_s']
        expected_arrivals = diag['facing_per_day'] * np.minimum(res.draws['onset_window_s'], red) / red
        moving = total * diag['onset_share']
        assert np.all(moving[finite] <= expected_arrivals[finite] * (1 + 2e-15))
        np.testing.assert_allclose(moving + total * (1 - diag['onset_share']), total, rtol=2e-15)
