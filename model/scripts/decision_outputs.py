"""Regenerate the two decision outputs and the queue-tail sensitivity.

Both suppress the queue-tail difference between the strategies (see model._queue_gap):
it favours the device, it descends from the fixed-time green-scaling prior rather than from
the control form, and the safety it buys is paid for in delay, which this paper does not
model. Suppressing it is conservative against the device. Its magnitude is reported here so
the decision can be read with it restored.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.distributions import load_sej  # noqa: E402
from mtcpts.model import (Cell, Priors, calibration_curve, decision_surface,  # noqa: E402
                          p_dh_negative, run_cell)

MODEL = Path(__file__).resolve().parents[1]
DIST = MODEL / "outputs/dist/capfix_20260927"
BASELINE = (300, 250)


def main() -> None:
    sej = load_sej(MODEL / "config")
    res = run_cell(Cell(*BASELINE), sej, Priors(), n_iter=20_000, n_grid=128)
    P = res.parts

    with open(DIST / "calibration_curve.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["lambda", "headon_collisions_per_op_day", "p_dh_neg",
                    "p_dh_neg_with_queue_gap"])
        a = calibration_curve(res, "S1a", include_queue_gap=False)
        b = calibration_curve(res, "S1a", include_queue_gap=True)
        for (lam, coll, p), (_, _, pq) in zip(a, b):
            w.writerow([f"{lam:.6g}", f"{coll:.6g}", f"{p:.6f}", f"{pq:.6f}"])

    # axis ranges chosen so both records and the elicited point are on the page
    surf = decision_surface(res, "S1a",
                            lam_w3=np.geomspace(2.4e-4, 2.5, 61),
                            lam_w5=np.geomspace(0.05, 60.0, 61))
    np.savez_compressed(DIST / "decision_surface.npz",
                        **{k: np.asarray(v) for k, v in surf.items()})

    # read the surface at the record, on both axes (research/*-bounds.md)
    x, y, G = surf["headon_dsi_per_day"], surf["controller_dsi_per_day"], surf["p_grid"]
    w3_med, w5_med = surf["w3_median"], surf["w5_median"]

    def P_at(headon_dsi, controller_dsi, queue=False):
        l3, l5 = controller_dsi / w3_med, headon_dsi / w5_med
        dh = ((P["S1a"]["W1"] - P["S0"]["W1"]) if queue else 0.0) + P["S1a"]["W4d"] \
            - l3 * P["S0"]["W3"] + l5 * (P["S1a"]["W5"] - P["S0"]["W5"])
        dh = dh[np.isfinite(dh)]
        return float((dh < 0).mean())

    HEADON_REC = (6e-6, 2e-5)          # head-on serious harm per op-day, from the crash record
    STRIKE_REC = (5e-6, 2e-5)          # controller serious harm per op-day, from the injury record
    HEADON_C, STRIKE_C = 1.2e-5, 1.0e-5

    def dh_at(headon_dsi, controller_dsi, queue=False):
        l3, l5 = controller_dsi / w3_med, headon_dsi / w5_med
        dh = ((P["S1a"]["W1"] - P["S0"]["W1"]) if queue else 0.0) + P["S1a"]["W4d"] \
            - l3 * P["S0"]["W3"] + l5 * (P["S1a"]["W5"] - P["S0"]["W5"])
        return dh[np.isfinite(dh)]

    # equivalence bound: one serious-harm event per 100 site-years (250 op-days/yr)
    MARGIN = 1.0 / (100.0 * 250.0)
    dh_rec = dh_at(HEADON_C, STRIKE_C)
    p_equiv = float((np.abs(dh_rec) <= MARGIN).mean())
    # margin at which 90% of record-calibrated mass is inside
    m90 = float(np.percentile(np.abs(dh_rec), 90))
    # worst corners of the record box, for the equivalence claim's robustness
    p_equiv_worst = min(
        float((np.abs(dh_at(h, c)) <= MARGIN).mean())
        for h in HEADON_REC for c in STRIKE_REC)

    # value of information: which measurement moves the decision more
    span_strike = abs(P_at(HEADON_C, STRIKE_REC[1]) - P_at(HEADON_C, STRIKE_REC[0]))
    span_headon = abs(P_at(HEADON_REC[1], STRIKE_C) - P_at(HEADON_REC[0], STRIKE_C))

    cross = {
        "p_at_elicited_w3_modelled_w5": P_at(w5_med, w3_med),
        "p_at_record_central": P_at(HEADON_C, STRIKE_C),
        "p_at_record_worst_for_device": P_at(HEADON_REC[1], STRIKE_REC[0]),
        "p_at_record_best_for_device": P_at(HEADON_REC[0], STRIKE_REC[1]),
        "p_at_record_central_with_queue_gap": P_at(HEADON_C, STRIKE_C, queue=True),
        "headon_record_band": list(HEADON_REC),
        "strike_record_band": list(STRIKE_REC),
        "equiv_margin_per_op_day": MARGIN,
        "p_equivalent_at_record_central": p_equiv,
        "p_equivalent_worst_record_corner": p_equiv_worst,
        "abs_dh_q90_at_record_central": m90,
        "voi_span_strike_axis": span_strike,
        "voi_span_headon_axis": span_headon,
    }

    # dH decomposition and the queue-tail sensitivity
    dh = res.h_s1a - res.h_s0
    p_full, _, _ = p_dh_negative(res.h_s1a, res.h_s0)
    supp = res.h_s1a - res.h_s0 - (P["S1a"]["W1"] - P["S0"]["W1"])
    p_supp = float((supp[np.isfinite(supp)] < 0).mean())

    # elicited-level disclosure, W1: the queue-tail level implied by the elicitation,
    # against the whole-of-TTM serious-harm rate the NZ record supports (about 97 DSI crashes a year
    # over ~0.4M op-days/yr ~= 2.4e-4 per op-day across ALL pathways and site types). W1 alone
    # exceeding that all-cause rate means the elicited LEVEL is high; it cancels in dH.
    w1_med = float(np.nanmedian(P["S0"]["W1"]))
    ALL_TTM_DSI_PER_OP_DAY = (680.0 / 7.0) / 4.0e5   # supplement S1.3 (CAS 2018 to 2024, crash basis); was 146/4e5 until 27 Sep 2026

    summary = {
        "w1_median_s0": w1_med,
        "w1_vs_all_ttm_record_factor": w1_med / ALL_TTM_DSI_PER_OP_DAY,
        "w1_gap_median": float(np.nanmedian(P["S1a"]["W1"] - P["S0"]["W1"])),
        "w5_gap_median": float(np.nanmedian(P["S1a"]["W5"] - P["S0"]["W5"])),
        "w3_median": float(np.nanmedian(P["S0"]["W3"])),
        "w4d_median": float(np.nanmedian(P["S1a"]["W4d"])),
        "w5b_median_s1a": float(np.nanmedian(P["S1a"]["W5b"])),
        "dh_median": float(np.nanmedian(dh)),
        "p_dh_neg": p_full,
        "p_dh_neg_queue_gap_suppressed": p_supp,
        "headon_dsi_per_op_day_s1a": float(np.nanmedian(P["S1a"]["W5"])),
        "collisions_per_op_day_s1a": float(np.nanmedian(res.diag["S1a"]["collisions_per_day"])),
        "conflicts_per_op_day_s1a": float(np.nanmedian(res.diag["S1a"]["conflicts_per_day"])),
        "violations_per_op_day_s1a": float(np.nanmedian(res.diag["S1a"]["violations_per_day"])),
        "controller_strikes_per_op_day": float(np.nanmedian(res.diag["S0"]["controller_strikes_per_day"])),
        "safe_window_frac_s1a": float(np.nanmedian(res.diag["S1a"]["p_safe_window"])),
        "clearance_s0": float(np.nanmedian(res.diag["S0"]["clearance_s"])),
        "clearance_s1": float(np.nanmedian(res.diag["S1a"]["clearance_s"])),
        **cross,
    }
    (DIST / "decision_summary.json").write_text(json.dumps(summary, indent=2))
    for k, v in summary.items():
        print(f"  {k:38s} {v:.6g}" if isinstance(v, float) else f"  {k:38s} {v}")
    print(f"\n-> {DIST}")


if __name__ == "__main__":
    main()
