"""Decision outputs for the attended AFAD arm (S2), docs/prespec.md Addendum A5.

Reads the newest production dist (baseline traces) and writes decision_summary_s2.json.
Everything is computed from the saved per-iteration traces with the same record-calibration
arithmetic as decision_outputs.py: the controller axis scales S0's lane-standing pathway, the
head-on axis scales the violation-conflict pathway in every arm. The head-on record was
observed at unattended signals, so the head-on axis is anchored on S1a's W5 median and S2's
head-on rate follows from the same tree at its own violation rate and hold. W3r (the
operator's residual beside-the-road exposure) and W4d are constants of the mechanism.

The one configuration sensitivity fixed in Addendum A3 (no gate arm) is run here at the
baseline cell, from the single-source ungated rate, and reported as a band.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.distributions import Triangular, load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, p_dh_negative, run_cell  # noqa: E402

MODEL = Path(__file__).resolve().parents[1]
BASELINE = (300, 250)
HEADON_REC = (6e-6, 2e-5)          # head-on serious harm per op-day, from the crash record
STRIKE_REC = (5e-6, 2e-5)          # controller serious harm per op-day, from the injury record
HEADON_C, STRIKE_C = 1.2e-5, 1.0e-5
# All-cause serious-harm record at temporary traffic management sites of every kind (supplement S1.3):
# 680 death-or-serious-injury crashes at New Zealand sites carrying any of the seven work-zone signals over
# 2018 to 2024 (Crash Analysis System, as loaded 2026-09-14), 97.1 a year, over about 0.4 million operation
# days a year of roadworks under traffic control. Crash basis, the unit the model counts. Replaces the
# 146-a-year figure (a persons count from an earlier note) on 27 Sep 2026 after review round 5.
ALL_TTM_DSI_PER_OP_DAY = (680.0 / 7.0) / 4.0e5

MARGIN = 1.0 / (100.0 * 250.0)     # one serious-harm event per 100 site-years
UNGATED_R_V2 = Triangular(1.1e-2, 2.2e-2, 4.4e-2)   # Addendum A3: single source, half/double


DIST = MODEL / "outputs/dist/capfix_20260927"


def newest_dist() -> Path:
    """Selected production output; explicit to protect the version 1.2 record."""
    return DIST


def record_reads(parts: dict, headon: float, controller: float, w5_anchor: float,
                 w3_anchor: float) -> dict[str, np.ndarray]:
    """Record-calibrated dH per iteration for every device strategy, queue tail suppressed."""
    l3, l5 = controller / w3_anchor, headon / w5_anchor
    out = {}
    for s in ("S1a", "S1b", "S2"):
        dh = (parts[s]["W4d"] + parts[s]["W3"] - l3 * parts["S0"]["W3"]
              + l5 * (parts[s]["W5"] - parts["S0"]["W5"]))
        out[s] = dh
    return out


def summarise(parts: dict, h: dict) -> dict:
    w5_anchor = float(np.nanmedian(parts["S1a"]["W5"]))
    w3_anchor = float(np.nanmedian(parts["S0"]["W3"]))
    fin = np.isfinite(h["S0"])

    def P(dh):
        d = dh[np.isfinite(dh)]
        return float((d < 0).mean())

    rec = record_reads(parts, HEADON_C, STRIKE_C, w5_anchor, w3_anchor)
    corners = {f"h{h_}_c{c_}": record_reads(parts, h_, c_, w5_anchor, w3_anchor)
               for h_ in HEADON_REC for c_ in STRIKE_REC}
    out = {
        "w5_anchor_s1a_median": w5_anchor,
        "w3_anchor_s0_median": w3_anchor,
        "headon_record_band": list(HEADON_REC), "strike_record_band": list(STRIKE_REC),
        "equiv_margin_per_op_day": MARGIN,
    }
    for s in ("S1a", "S2"):
        tag = s.lower()
        dh_el = h[s] - h["S0"]
        p_el, lo, hi = p_dh_negative(h[s], h["S0"])
        d = rec[s][np.isfinite(rec[s])]
        corner_ps = {k: P(v[s]) for k, v in corners.items()}
        out |= {
            f"{tag}_p_elicited": p_el, f"{tag}_p_elicited_wilson": [lo, hi],
            f"{tag}_dh_median_elicited": float(np.nanmedian(dh_el)),
            f"{tag}_p_at_record_central": P(rec[s]),
            f"{tag}_p_at_record_corners": corner_ps,
            f"{tag}_p_at_record_worst_for_device": min(corner_ps.values()),
            f"{tag}_p_at_record_best_for_device": max(corner_ps.values()),
            f"{tag}_dh_median_at_record": float(np.median(d)),
            f"{tag}_abs_dh_median_at_record": float(np.median(np.abs(d))),
            f"{tag}_abs_dh_q90_at_record": float(np.percentile(np.abs(d), 90)),
            f"{tag}_p_equivalent_at_record_central": float((np.abs(d) <= MARGIN).mean()),
            f"{tag}_p_equivalent_worst_record_corner": min(
                float((np.abs(v[s][np.isfinite(v[s])]) <= MARGIN).mean()) for v in corners.values()),
            f"{tag}_voi_span_strike_axis": abs(
                P(record_reads(parts, HEADON_C, STRIKE_REC[1], w5_anchor, w3_anchor)[s])
                - P(record_reads(parts, HEADON_C, STRIKE_REC[0], w5_anchor, w3_anchor)[s])),
            f"{tag}_voi_span_headon_axis": abs(
                P(record_reads(parts, HEADON_REC[1], STRIKE_C, w5_anchor, w3_anchor)[s])
                - P(record_reads(parts, HEADON_REC[0], STRIKE_C, w5_anchor, w3_anchor)[s])),
        }
    # S2 against the unattended signal, at the record (same lam3 and lam5 in both)
    d21 = rec["S2"] - rec["S1a"]
    d21 = d21[np.isfinite(d21)]
    out |= {
        "s2_vs_s1a_p_s2_lower_at_record_central": float((d21 < 0).mean()),
        "s2_vs_s1a_dh_median_at_record": float(np.median(d21)),
        "s2_vs_s1a_p_s2_lower_elicited": float(((h["S2"] - h["S1a"])[fin] < 0).mean()),
        # the S2 ledger at the record calibration, median per pathway
        "s2_w3r_operator_median": float(np.nanmedian(parts["S2"]["W3"])),
        "s2_w3r_vs_controller_record_central": float(np.nanmedian(parts["S2"]["W3"]) / STRIKE_C),
        "s2_w5_at_record_median": float(np.nanmedian(parts["S2"]["W5"]) * HEADON_C / w5_anchor),
        "s2_w4d_median": float(np.nanmedian(parts["S2"]["W4d"])),
        "s2_w5_elicited_median": float(np.nanmedian(parts["S2"]["W5"])),
        "s0_w5_at_record_median": float(np.nanmedian(parts["S0"]["W5"]) * HEADON_C / w5_anchor),
    }
    return out


def main() -> None:
    dist = newest_dist()
    t = np.load(dist / "baseline_traces.npz")
    parts = {s: {k: t[f"part_{s}_{k}"] for k in ("W1", "W3", "W5", "W4d", "W5b")}
             for s in ("S0", "S1a", "S1b", "S2")}
    h = {"S0": t["h_s0"], "S1a": t["h_s1a"], "S1b": t["h_s1b"], "S2": t["h_s2"]}
    summary = {"dist": dist.name, **summarise(parts, h)}

    # regression against the frozen record: S1a reads must reproduce R13/R14
    summary["check_s1a_record_central_reproduces_R13_0.431"] = bool(
        abs(summary["s1a_p_at_record_central"] - 0.4311) < 5e-4)

    # Addendum A3 configuration sensitivity: no gate arm, baseline cell
    sej = load_sej(MODEL / "config")
    res = run_cell(Cell(*BASELINE), sej, Priors(r_v2=UNGATED_R_V2), n_iter=20_000, n_grid=128)
    ung = summarise(res.parts, {"S0": res.h_s0, "S1a": res.h_s1a, "S1b": res.h_s1b, "S2": res.h_s2})
    d2 = res.diag["S2"]
    summary["s2_ungated"] = {
        "r_v2_prior": "Triangular(1.1e-2, 2.2e-2, 4.4e-2)",
        "p_elicited": ung["s2_p_elicited"],
        "p_at_record_central": ung["s2_p_at_record_central"],
        "p_at_record_worst_for_device": ung["s2_p_at_record_worst_for_device"],
        "p_equivalent_at_record_central": ung["s2_p_equivalent_at_record_central"],
        "vs_s1a_p_s2_lower_at_record_central": ung["s2_vs_s1a_p_s2_lower_at_record_central"],
        "implied_headon_collisions_per_op_day": float(np.nanmedian(d2["collisions_per_day"])),
        "violations_per_op_day": float(np.nanmedian(d2["violations_per_day"])),
    }
    # S2 event-tree ladder at the baseline (elicited levels) for the results text
    tt = {k: t[f"diag_S2_{k}"] for k in ("facing_per_day", "violations_per_day",
                                          "conflicts_per_day", "collisions_per_day",
                                          "p_safe_window", "clearance_s")}
    summary["s2_ladder"] = {k: float(np.nanmedian(v)) for k, v in tt.items()}
    summary["s2_ladder"]["violations_per_serious_harm_event"] = float(
        np.nanmedian(tt["violations_per_day"]) / np.nanmedian(parts["S2"]["W5"]))

    # the S2 surface on the same axis ranges as decision_outputs.py's S1a surface, so the
    # two panels of Figure 8 share their frame; built from the saved traces (parts and diag)
    from types import SimpleNamespace
    from mtcpts.model import decision_surface
    diag_s2 = {k[len("diag_S2_"):]: t[k] for k in t.files if k.startswith("diag_S2_")}
    diag_s1a = {k[len("diag_S1a_"):]: t[k] for k in t.files if k.startswith("diag_S1a_")}
    fake = SimpleNamespace(parts=parts, diag={"S2": diag_s2, "S1a": diag_s1a})
    surf = decision_surface(fake, "S2", lam_w3=np.geomspace(2.4e-4, 2.5, 61),
                            lam_w5=np.geomspace(0.05, 60.0, 61))
    np.savez_compressed(dist / "decision_surface_s2.npz",
                        **{k: np.asarray(v) for k, v in surf.items()})

    # ---- reads requested by review round 1 (all from the same traces) ------------------
    w5_anchor = float(np.nanmedian(parts["S1a"]["W5"])); w3_anchor = float(np.nanmedian(parts["S0"]["W3"]))
    rec = record_reads(parts, HEADON_C, STRIKE_C, w5_anchor, w3_anchor)
    fin = np.isfinite(rec["S1a"]) & np.isfinite(rec["S2"])
    # (a) Monte Carlo interval of the record-central reads (Wilson, 20,000 draws)
    for s in ("S1a", "S1b", "S2"):
        _, lo, hi = p_dh_negative(rec[s], np.zeros_like(rec[s]))
        summary[f"{s.lower()}_p_at_record_central_wilson"] = [float(lo), float(hi)]
    summary["s1b_p_at_record_central"] = float((rec["S1b"][np.isfinite(rec["S1b"])] < 0).mean())
    # (b) the attended device against the signal WITH the queue-tail difference, at the record
    #     ceiling for the queue-tail level (all-cause record / elicited) and at the elicited level
    w1_scale = ALL_TTM_DSI_PER_OP_DAY / float(np.nanmedian(parts["S0"]["W1"]))
    qt21 = parts["S2"]["W1"] - parts["S1a"]["W1"]
    for label, k in (("record_ceiling", w1_scale), ("elicited_level", 1.0)):
        d = (rec["S2"] - rec["S1a"] + k * qt21)[fin]
        summary[f"s2_vs_s1a_p_s2_lower_with_queue_tail_{label}"] = float((d < 0).mean())
        summary[f"s2_vs_s1a_dh_median_with_queue_tail_{label}"] = float(np.median(d))
    summary["queue_tail_record_scale"] = w1_scale
    # (c) the device's head-on axis anchored on its OWN median instead of the signal's
    own = record_reads(parts, HEADON_C, STRIKE_C, float(np.nanmedian(parts["S2"]["W5"])), w3_anchor)["S2"]
    own_c = {f"h{h_}_c{c_}": record_reads(parts, h_, c_, float(np.nanmedian(parts["S2"]["W5"])), w3_anchor)["S2"]
             for h_ in HEADON_REC for c_ in STRIKE_REC}
    summary["s2_own_anchor_p_at_record_central"] = float((own[np.isfinite(own)] < 0).mean())
    summary["s2_own_anchor_p_worst_best"] = [min(float((v[np.isfinite(v)] < 0).mean()) for v in own_c.values()),
                                             max(float((v[np.isfinite(v)] < 0).mean()) for v in own_c.values())]
    d = (own - rec["S1a"])[fin]
    summary["s2_own_anchor_vs_s1a_p_s2_lower"] = float((d < 0).mean())
    # (d) record boxes widened to a factor of 10 about the central values
    for s in ("S1a", "S2"):
        ps = [float((record_reads(parts, HEADON_C * fh, STRIKE_C * fc, w5_anchor, w3_anchor)[s] < 0).mean())
              for fh in (1 / np.sqrt(10), np.sqrt(10)) for fc in (1 / np.sqrt(10), np.sqrt(10))]
        summary[f"{s.lower()}_p_at_record_factor10_box"] = [min(ps), max(ps)]
    # (e) PRCC at the record calibration (the tree's inputs re-enter through the spread of W5)
    from mtcpts.sensitivity import prcc
    draws = {k[5:]: t[k] for k in t.files if k.startswith("draw_") and not k[5:].startswith("_") and np.std(t[k]) > 0}
    S2_ONLY = {"r_v2", "p_detect_s2", "offset_op_m"}
    for s in ("S1a", "S2"):
        names = [k for k in draws if not (s == "S1a" and k in S2_ONLY)]
        ok = np.isfinite(rec[s])
        pr = prcc({k: draws[k][ok] for k in names}, rec[s][ok], names)
        top = sorted(pr.items(), key=lambda kv: -abs(kv[1]))[:8]
        summary[f"{s.lower()}_prcc_at_record_top8"] = [[k, round(v, 3)] for k, v in top]
    # (f) sanity on the operator-offset input: its rank correlation with the term it enters
    from scipy.stats import spearmanr
    summary["offset_op_spearman_with_w3r"] = float(spearmanr(t["draw_offset_op_m"], parts["S2"]["W3"]).statistic)
    summary["offset_op_spearman_with_dh_s2_elicited"] = float(spearmanr(t["draw_offset_op_m"], (h["S2"] - h["S0"])[np.isfinite(h["S2"])]).statistic)

    # (g) anchoring on MEANS instead of medians (the records estimate mean rates per op-day)
    w5_mean = float(np.nanmean(parts["S1a"]["W5"])); w3_mean = float(np.nanmean(parts["S0"]["W3"]))
    recm = record_reads(parts, HEADON_C, STRIKE_C, w5_mean, w3_mean)
    for s in ("S1a", "S2"):
        d = recm[s][np.isfinite(recm[s])]
        summary[f"{s.lower()}_p_at_record_central_mean_anchored"] = float((d < 0).mean())
        summary[f"{s.lower()}_dh_mean_at_record_central"] = float(np.mean(rec[s][np.isfinite(rec[s])]))
    # (h) the avoidance-harm band (W5b) added to the head-on pathway in every arm, same scaling
    w5b = {s: t[f"part_{s}_W5b"] for s in ("S0", "S1a", "S2")}
    for s in ("S1a", "S2"):
        l3 = STRIKE_C / w3_anchor; l5 = HEADON_C / w5_anchor
        d = (parts[s]["W4d"] + parts[s]["W3"] - l3 * parts["S0"]["W3"]
             + l5 * ((parts[s]["W5"] + w5b[s]) - (parts["S0"]["W5"] + w5b["S0"])))
        d = d[np.isfinite(d)]
        summary[f"{s.lower()}_p_at_record_central_with_avoidance_harm"] = float((d < 0).mean())
    # (i) share of record-calibrated draws inside the record bands (the spread the reading keeps)
    l3 = STRIKE_C / w3_anchor; l5 = HEADON_C / w5_anchor
    w3s = (l3 * parts["S0"]["W3"]); w5s = (l5 * parts["S1a"]["W5"])
    summary["share_of_scaled_strike_draws_inside_band"] = float(((w3s >= STRIKE_REC[0]) & (w3s <= STRIKE_REC[1])).mean())
    summary["share_of_scaled_headon_draws_inside_band"] = float(((w5s >= HEADON_REC[0]) & (w5s <= HEADON_REC[1])).mean())
    summary["scaled_strike_q05_q95"] = [float(np.nanpercentile(w3s, 5)), float(np.nanpercentile(w3s, 95))]
    summary["scaled_headon_q05_q95"] = [float(np.nanpercentile(w5s, 5)), float(np.nanpercentile(w5s, 95))]

    # (j) the operator term CALIBRATED so that the encroachment frame reproduces the controller
    #     record for a person at the edge line (offset 0), then reduced by the sampled offset
    edge = parts["S2"]["W3"] / np.exp(-t["draw_reach_alpha"] * t["draw_offset_op_m"])   # offset removed
    k_op = STRIKE_C / float(np.nanmedian(edge))
    summary["operator_term_edge_line_median"] = float(np.nanmedian(edge))
    summary["operator_term_calibration_factor"] = k_op
    summary["operator_term_calibrated_median"] = float(np.nanmedian(k_op * parts["S2"]["W3"]))
    l3 = STRIKE_C / w3_anchor; l5 = HEADON_C / w5_anchor
    d = (parts["S2"]["W4d"] + k_op * parts["S2"]["W3"] - l3 * parts["S0"]["W3"]
         + l5 * (parts["S2"]["W5"] - parts["S0"]["W5"]))
    summary["s2_p_at_record_central_operator_calibrated"] = float((d[np.isfinite(d)] < 0).mean())
    cs = []
    for h_ in HEADON_REC:
        for c_ in STRIKE_REC:
            dd = (parts["S2"]["W4d"] + (c_ / STRIKE_C) * k_op * parts["S2"]["W3"] - (c_ / w3_anchor) * parts["S0"]["W3"]
                  + (h_ / w5_anchor) * (parts["S2"]["W5"] - parts["S0"]["W5"]))
            cs.append(float((dd[np.isfinite(dd)] < 0).mean()))
    summary["s2_p_operator_calibrated_worst_best"] = [min(cs), max(cs)]
    d21 = (d - rec["S1a"])[fin]
    summary["s2_operator_calibrated_vs_s1a_p_s2_lower"] = float((d21 < 0).mean())
    summary["s2_operator_calibrated_dh_median"] = float(np.median(d[np.isfinite(d)]))
    summary["s2_operator_calibrated_p_equivalent"] = float((np.abs(d[np.isfinite(d)]) <= MARGIN).mean())

    (dist / "decision_summary_s2.json").write_text(json.dumps(summary, indent=2))
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k:46s} {v:.6g}")
        else:
            print(f"  {k:46s} {v}")
    print(f"\n-> {dist / 'decision_summary_s2.json'}")


if __name__ == "__main__":
    main()
