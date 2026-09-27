"""Readings added during review, reproduced from the saved production draws.

Every figure in the results registry (results/REGISTRY.md) that was first computed as a
scratch calculation over baseline_traces.npz is produced here by one script, so the release
regenerates each of them: rows R55 (tighter margins), R56 (draws inside both record bands;
mean matching), R61 (overall multiplier at the record), R66 and R72 (strike band at the police
fatal-to-serious ratio, medians and means matched), R67 (break-even violation rate at the
record; red-running removal at the panel's values), R69 (release-error bound), R71 and R75
(tied construction of the operator's exposure), R73 (what decides the sign of the delay
difference), R74 (the plan's surface with and without the queue-tail difference), and two
rows added in review round 5: red-running removal at the record (R78) and the speed sweep's
head-on term on each axis (R79). No prior is changed; every read uses the production draws.
Output: <dist>/review_reads.json.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision_outputs_s2 import (ALL_TTM_DSI_PER_OP_DAY, HEADON_C, HEADON_REC, MARGIN,  # noqa: E402
                                 STRIKE_C, STRIKE_REC, newest_dist)
from welfare import BASELINE_Q, OPERATION_HOURS, uniform_delay_per_vehicle_s  # noqa: E402

COLLISION_REC = 3.3e-5            # head-on collisions per operation day, both registers (S1.1)
POLICE_RATIO_CENTRALS = {8.5: 1.7e-5, 10.0: 2.0e-5, 12.0: 2.4e-5, 12.5: 2.5e-5}


def P(d):
    d = d[np.isfinite(d)]
    return float((d < 0).mean())


def q(d, p):
    return float(np.nanpercentile(d[np.isfinite(d)], p))


def spearman(a, b):
    m = np.isfinite(a) & np.isfinite(b)
    ra = np.argsort(np.argsort(a[m])).astype(float)
    rb = np.argsort(np.argsort(b[m])).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def main() -> None:
    dist = newest_dist()
    t = np.load(dist / "baseline_traces.npz")
    S = ("S0", "S1a", "S1b", "S2")
    parts = {s: {k: t[f"part_{s}_{k}"] for k in ("W1", "W3", "W5", "W4d")} for s in S}
    w3_med, w5_med = float(np.nanmedian(parts["S0"]["W3"])), float(np.nanmedian(parts["S1a"]["W5"]))
    w3_mean, w5_mean = float(np.nanmean(parts["S0"]["W3"])), float(np.nanmean(parts["S1a"]["W5"]))
    qt_scale = ALL_TTM_DSI_PER_OP_DAY / float(np.nanmedian(parts["S0"]["W1"]))

    def dh(s, l3, l5, queue=0.0, op=None):
        """Calibrated change in harm of strategy s against manual control; queue is the factor on the
        queue-tail difference (0 excluded, 1 the panel's level, qt_scale the record ceiling); op
        replaces the device's operator term when given."""
        w3 = parts[s]["W3"] if op is None else op
        return (queue * (parts[s]["W1"] - parts["S0"]["W1"]) + parts[s]["W4d"] + w3
                - l3 * parts["S0"]["W3"] + l5 * (parts[s]["W5"] - parts["S0"]["W5"]))

    l3, l5 = STRIKE_C / w3_med, HEADON_C / w5_med
    l3m, l5m = STRIKE_C / w3_mean, HEADON_C / w5_mean
    out = {"dist": dist.name, "constants": {"l3_median_matched": l3, "l5_median_matched": l5,
                                            "l3_mean_matched": l3m, "l5_mean_matched": l5m,
                                            "queue_tail_record_scale": qt_scale}}

    # R55: tighter margins at the record central, medians matched, queue-tail difference excluded
    out["R55_within_margin"] = {f"{m:g}": {s: float((np.abs(dh(s, l3, l5)[np.isfinite(dh(s, l3, l5))]) <= m).mean())
                                           for s in ("S1a", "S2")} for m in (MARGIN, MARGIN / 2, MARGIN / 4)}

    # R56: draws inside both record bands, and mean matching
    inside = ((l3 * parts["S0"]["W3"] >= STRIKE_REC[0]) & (l3 * parts["S0"]["W3"] <= STRIKE_REC[1])
              & (l5 * parts["S1a"]["W5"] >= HEADON_REC[0]) & (l5 * parts["S1a"]["W5"] <= HEADON_REC[1]))
    out["R56_inside_both_bands"] = {"share": float(inside.mean()), "n": int(inside.sum()),
                                    "p": {s: P(dh(s, l3, l5)[inside]) for s in ("S1a", "S1b", "S2")}}
    n_in = int(inside.sum()); p_in = out["R56_inside_both_bands"]["p"]["S1a"]
    z = 1.96; centre = (p_in + z * z / (2 * n_in)) / (1 + z * z / n_in)
    half = z * np.sqrt(p_in * (1 - p_in) / n_in + z * z / (4 * n_in * n_in)) / (1 + z * z / n_in)
    out["R56_inside_both_bands"]["wilson_s1a"] = [float(centre - half), float(centre + half)]
    out["R56_mean_matched"] = {s: P(dh(s, l3m, l5m)) for s in ("S1a", "S1b", "S2")}

    # R61: overall risk multiplier H(S1a)/H(S0) at the record calibration
    def H(s, l3_, l5_, queue):
        return (queue * parts[s]["W1"] + parts[s]["W4d"] + (l3_ * parts[s]["W3"] if s == "S0" else parts[s]["W3"])
                + l5_ * parts[s]["W5"])
    out["R61_multiplier"] = {}
    for label, queue in (("queue_tail_at_record_ceiling", qt_scale), ("queue_tail_at_panel_level", 1.0),
                         ("queue_tail_excluded", 0.0)):
        ratio = H("S1a", l3, l5, queue) / H("S0", l3, l5, queue)
        out["R61_multiplier"][label] = {"median": q(ratio, 50), "p5": q(ratio, 5), "p95": q(ratio, 95)}
    h0 = H("S0", l3, l5, qt_scale)
    out["R61_multiplier"]["queue_tail_share_of_S0_at_ceiling"] = float(np.nanmedian(qt_scale * parts["S0"]["W1"] / h0))

    # R82: the queue tail's share of manual control's harm at three levels of the term (round-6 practitioner,
    # Codex: the record-scaled level is a calibration level, not a demonstrated bound), and the retained
    # fraction of the controller's exposure under the tied operator construction (round-6 finding 3)
    rear_end_record = (54.0 / 7.0) / 4.0e5
    out["R82_queue_tail_share_and_retained_exposure"] = {}
    for label, level in (("rear_end_record_only", rear_end_record), ("all_cause_record_uncorrected", ALL_TTM_DSI_PER_OP_DAY),
                         ("all_cause_record_corrected_3x", 3 * ALL_TTM_DSI_PER_OP_DAY), ("all_cause_record_corrected_5x", 5 * ALL_TTM_DSI_PER_OP_DAY),
                         ("panel_level", float(np.nanmedian(parts["S0"]["W1"])))):
        k = level / float(np.nanmedian(parts["S0"]["W1"]))
        h0 = H("S0", l3, l5, k)
        out["R82_queue_tail_share_and_retained_exposure"][label] = {
            "queue_tail_level_per_op_day": level, "scale_on_panel_level": k,
            "queue_tail_share_of_S0_harm_median": float(np.nanmedian(k * parts["S0"]["W1"] / h0)),
            "p_S1a_with_difference_at_this_level": P(dh("S1a", l3, l5, k))}
    for d_ref in (0.0, 1.0):
        frac = np.exp(-t["draw_reach_alpha"] * (t["draw_offset_op_m"] - d_ref))
        out["R82_queue_tail_share_and_retained_exposure"][f"tied_retained_fraction_ref_{d_ref:.0f}m"] = {
            "mean": float(np.nanmean(frac)), "median": float(np.nanmedian(frac)), "p10": q(frac, 10), "p90": q(frac, 90)}
    # R66 and R72: strike central at the police fatal-to-serious ratio
    out["R66_police_ratio_medians_matched"] = {
        str(r): {s: P(dh(s, c / w3_med, l5)) for s in ("S1a", "S1b", "S2")} for r, c in POLICE_RATIO_CENTRALS.items()}
    out["R72_police_ratio_means_matched"] = {
        str(r): {s: P(dh(s, c / w3_mean, l5m)) for s in ("S1a", "S1b", "S2")} for r, c in POLICE_RATIO_CENTRALS.items()}
    out["R72_police_ratio_means_matched"]["record_central"] = {s: P(dh(s, l3m, l5m)) for s in ("S1a", "S1b", "S2")}

    # R67: break-even violation rate at the record calibration (the head-on term is linear in the
    # violation rate, so r* = r x (calibrated harm the signals remove) / (calibrated head-on harm they add))
    r = t["draw_r_v1a"]
    removed = l3 * parts["S0"]["W3"] + l5 * parts["S0"]["W5"] - parts["S1a"]["W3"] - parts["S1a"]["W4d"]
    r_star = r * removed / (l5 * parts["S1a"]["W5"])
    fin = np.isfinite(r_star)
    pos = r_star[fin & (r_star > 0)]
    check = t["draw_r_v1a"] * (parts["S0"]["W3"] + parts["S0"]["W5"] - parts["S1a"]["W3"] - parts["S1a"]["W4d"]) / parts["S1a"]["W5"]
    allf = r_star[fin]
    out["R67_breakeven_at_record"] = {
        "median_all_draws": float(np.median(allf)), "p20_all_draws": float(np.percentile(allf, 20)),
        "median_positive_draws_only": float(np.median(pos)), "p20_positive_draws_only": float(np.percentile(pos, 20)),
        "share_above_observed_band_top_0.079": float((r_star[fin] > 0.079).mean()),
        "share_above_sampled_rate": float((r_star[fin] > r[fin]).mean()),
        "share_no_positive_breakeven": float((r_star[fin] <= 0).mean()),
        "linearity_check_vs_saved_breakeven_at_elicited_level_median_abs_rel_diff":
            float(np.nanmedian(np.abs(check - t["breakeven_s1a"]) / np.abs(t["breakeven_s1a"])))}
    # the same frontier test on the plan's own surface (collision axis, queue-tail term at the panel's level)
    l5c_ = COLLISION_REC / float(np.nanmedian(t["diag_S1a_collisions_per_day"]))
    removed_c = (l3 * parts["S0"]["W3"] + l5c_ * parts["S0"]["W5"] - parts["S1a"]["W3"] - parts["S1a"]["W4d"]
                 - (parts["S1a"]["W1"] - parts["S0"]["W1"]))
    r_star_c = r * removed_c / (l5c_ * parts["S1a"]["W5"])
    finc = np.isfinite(r_star_c); posc = r_star_c[finc & (r_star_c > 0)]
    allc = r_star_c[finc]
    out["R67_breakeven_on_plan_surface"] = {
        "median_all_draws": float(np.median(allc)), "p20_all_draws": float(np.percentile(allc, 20)),
        "median_positive_draws_only": float(np.median(posc)), "p20_positive_draws_only": float(np.percentile(posc, 20)),
        "share_above_observed_band_top_0.079": float((r_star_c[finc] > 0.079).mean()),
        "share_above_sampled_rate": float((r_star_c[finc] > r[finc]).mean()),
        "share_no_positive_breakeven": float((r_star_c[finc] <= 0).mean())}
    # red-running removal at the panel's values (the second limb of the plan's clause)
    d_el = parts["S1a"]["W4d"] + parts["S1a"]["W3"] - parts["S0"]["W3"] + (parts["S1a"]["W5"] - parts["S0"]["W5"])
    d_el_no_w5 = parts["S1a"]["W4d"] + parts["S1a"]["W3"] - parts["S0"]["W3"]
    n = int(np.isfinite(d_el).sum()); p_el = P(d_el)
    out["R67_red_running_removal_panel_values"] = {"p_with": p_el, "p_without": P(d_el_no_w5),
                                                   "monte_carlo_interval_width": float(2 * 1.96 * np.sqrt(p_el * (1 - p_el) / n))}
    # R78: the same removal at the record calibration
    out["R78_red_running_removal_at_record"] = {"p_with": P(dh("S1a", l3, l5)),
                                                "p_without": P(parts["S1a"]["W4d"] + parts["S1a"]["W3"] - l3 * parts["S0"]["W3"])}

    # R69: release-error bound
    p_coll = t["diag_S1a_collisions_per_day"] / t["diag_S1a_conflicts_per_day"]
    p_harm = parts["S1a"]["W5"] / t["diag_S1a_collisions_per_day"]
    harm_per_error = p_coll * p_harm
    cycles_per_day = OPERATION_HOURS * 3600.0 / t["diag_S0_cycle_s"]
    eq_rate = HEADON_C / (harm_per_error * cycles_per_day)
    med_rate = HEADON_C / (float(np.nanmedian(p_coll)) * float(np.nanmedian(p_harm)) * float(np.nanmedian(cycles_per_day)))
    out["R69_release_error"] = {
        "p_collision_given_conflict_median": float(np.nanmedian(p_coll)),
        "p_serious_harm_given_collision_median": float(np.nanmedian(p_harm)),
        "serious_harm_per_error_at_medians": float(np.nanmedian(p_coll)) * float(np.nanmedian(p_harm)),
        "S0_cycles_per_day_median": float(np.nanmedian(cycles_per_day)),
        "equalising_error_rate_per_cycle_at_medians": med_rate, "one_in_cycles": 1.0 / med_rate,
        "operating_days_between_errors": 1.0 / (med_rate * float(np.nanmedian(cycles_per_day))),
        "per_draw_equalising_rate": {"median": q(eq_rate, 50), "p10": q(eq_rate, 10), "p90": q(eq_rate, 90)}}

    # R71 and R75: tied construction of the operator's exposure
    out["R71_R75_tied_operator"] = {}
    for d_ref in (0.0, 1.0):
        def tied(l3_, l5_):
            op = l3_ * parts["S0"]["W3"] * np.exp(-t["draw_reach_alpha"] * (t["draw_offset_op_m"] - d_ref))
            d2 = dh("S2", l3_, l5_, op=op)
            return d2, d2 - dh("S1a", l3_, l5_)
        d2, d21 = tied(l3, l5)
        corners = [P(tied(c / w3_med, h / w5_med)[0]) for h in HEADON_REC for c in STRIKE_REC]
        out["R71_R75_tied_operator"][f"reference_{d_ref:.0f}m"] = {
            "p": P(d2), "p_corners_min_max": [min(corners), max(corners)], "p_s2_below_s1a": P(d21)}

    # R89: the plan's coherence outcomes and the W5-driven clause on the plan's surface (round-6 hostile referee and
    # forensic writing reader, Opus: the frame-matched ratio was pre-specified and never reported; the W5 clause was
    # not read on the plan's own surface)
    def H_full(s, l3_, l5_, queue, strike=True):
        w3 = (l3_ * parts["S0"]["W3"] if strike else 0.0) if s == "S0" else parts[s]["W3"]
        return queue * parts[s]["W1"] + parts[s]["W4d"] + w3 + l5_ * parts[s]["W5"]
    out["R89_coherence_and_plan_surface_clause"] = {}
    l5c = COLLISION_REC / float(np.nanmedian(t["diag_S1a_collisions_per_day"]))
    for label, (l3_, l5_, queue) in (("panel_values", (1.0, 1.0, 1.0)), ("record_serious_harm_axis_queue_ceiling", (l3, l5, qt_scale)),
                                       ("record_serious_harm_axis_queue_excluded", (l3, l5, 0.0)), ("plan_surface_collision_axis", (l3, l5c, 1.0))):
        full = H_full("S1a", l3_, l5_, queue) / H_full("S0", l3_, l5_, queue)
        frame = H_full("S1a", l3_, l5_, queue) / H_full("S0", l3_, l5_, queue, strike=False)
        out["R89_coherence_and_plan_surface_clause"][label] = {
            "full_mechanism_ratio_median": q(full, 50), "full_p5": q(full, 5), "full_p95": q(full, 95),
            "frame_matched_ratio_median": q(frame, 50), "frame_p5": q(frame, 5), "frame_p95": q(frame, 95)}
    d_plan = dh("S1a", l3, l5c, 1.0); d_plan_no_w5 = 1.0 * (parts["S1a"]["W1"] - parts["S0"]["W1"]) + parts["S1a"]["W4d"] + parts["S1a"]["W3"] - l3 * parts["S0"]["W3"]
    n_p = int(np.isfinite(d_plan).sum()); p_p = P(d_plan)
    out["R89_coherence_and_plan_surface_clause"]["w5_removal_on_plan_surface"] = {
        "p_with": p_p, "p_without": P(d_plan_no_w5), "monte_carlo_interval_width": float(2 * 1.96 * np.sqrt(p_p * (1 - p_p) / n_p))}
    # R83: the adopted tied device reading priced as the welfare reading prices the others (round-6 desk reader, Codex:
    # Table 4 carried the pre-specified and independent-draw device rows but not the adopted comparison)
    import tomllib
    vals = tomllib.load(open(Path(__file__).resolve().parents[1] / "config" / "welfare-values.toml", "rb"))
    vosl = float(vals["value_of_statistical_life_nzd"]["value"]); v_si = float(vals["value_per_serious_injury_nzd"]["value"])
    out["R83_tied_device_priced"] = {}
    for d_ref in (0.0, 1.0):
        op = l3 * parts["S0"]["W3"] * np.exp(-t["draw_reach_alpha"] * (t["draw_offset_op_m"] - d_ref))
        d2 = dh("S2", l3, l5, op=op); f2 = d2[np.isfinite(d2)]
        out["R83_tied_device_priced"][f"reference_{d_ref:.0f}m"] = {
            "dh_median": float(np.median(f2)), "dh_mean": float(np.mean(f2)),
            "safety_cost_nzd_mean_vosl": float(np.mean(f2) * vosl), "safety_cost_nzd_mean_serious_injury": float(np.mean(f2) * v_si),
            "p_net_benefit": float((f2 < 0).mean())}
    # R91: cycles whose sampled green is shorter than the queue needs (round-8 risk analyst, Codex): share of draws,
    # decision probability without them, and the delay if their residual queue is priced as a deterministic
    # queue growing over the operation day (both directions), at the composite value of travel time
    VOT = 48.23; D = OPERATION_HOURS * 3600.0
    q_vps, sat_vps = BASELINE_Q / 3600.0, 1.0 / t["draw_sat_headway_s"]
    veh_day = 2.0 * BASELINE_Q * OPERATION_HOURS
    over = {k: (q_vps * t[f"diag_{k}_cycle_s"] > sat_vps * t[f"diag_{k}_green_s"]) for k in ("S0", "S1a", "S1b", "S2")}
    base_delay = {k: veh_day * uniform_delay_per_vehicle_s(t[f"diag_{k}_cycle_s"], t[f"diag_{k}_green_s"], q_vps, sat_vps) / 3600.0
                  for k in ("S0", "S1a", "S1b")}
    out["R91_non_clearing_cycles"] = {"share_oversaturated": {k: float(v.mean()) for k, v in over.items()}}
    for k in ("S1a", "S1b"):
        T, G = t[f"diag_{k}_cycle_s"], t[f"diag_{k}_green_s"]
        excess = np.clip(q_vps * T - sat_vps * G, 0.0, None)
        residual_vh = 2.0 * excess * D * D / (2.0 * T) / 3600.0
        dd = base_delay[k] - base_delay["S0"]; adj = dd + residual_vh
        m = np.isfinite(dd); keep = m & ~over[k] & ~over["S0"]
        d = dh(k, l3, l5); fd = np.isfinite(d)
        out["R91_non_clearing_cycles"][k] = {
            "p_dh_neg_all": P(d), "p_dh_neg_clearing_only": P(d[fd & ~over[k] & ~over["S0"]]),
            "extra_delay_mean_vh": float(np.mean(dd[m])), "extra_delay_mean_clearing_only_vh": float(np.mean(dd[keep])),
            "extra_delay_mean_with_residual_vh": float(np.mean(adj[m])), "extra_delay_median_with_residual_vh": float(np.median(adj[m])),
            "cost_mean_nzd": float(np.mean(dd[m]) * VOT), "cost_mean_with_residual_nzd": float(np.mean(adj[m]) * VOT),
            "cost_median_with_residual_nzd": float(np.median(adj[m]) * VOT)}
    # R85: within-margin probability and median change at New Zealand's own serious-harm levels (round-6 risk analyst)
    out["R85_within_margin_at_nz_levels"] = {}
    for label, h_ in (("record_central_1.2e-5", HEADON_C), ("nz_uncorrected_2.1e-5", 2.1e-5), ("nz_corrected_3x_6.4e-5", 6.4e-5), ("nz_corrected_6x_1.3e-4", 1.3e-4)):
        d1 = dh("S1a", l3, h_ / w5_med); f1 = d1[np.isfinite(d1)]
        out["R85_within_margin_at_nz_levels"][label] = {"p_dh_neg": P(d1), "p_within_margin": float((np.abs(f1) <= MARGIN).mean()),
                                                          "dh_median": float(np.median(f1)), "abs_dh_p90": q(np.abs(f1), 90)}
    # R86: value-of-information spans under the adopted tied construction (round-6 risk analyst)
    def tied_p(l3_, l5_, d_ref):
        op = l3_ * parts["S0"]["W3"] * np.exp(-t["draw_reach_alpha"] * (t["draw_offset_op_m"] - d_ref))
        return P(dh("S2", l3_, l5_, op=op))
    out["R86_tied_value_of_information_spans"] = {}
    for d_ref in (0.0, 1.0):
        span_strike = abs(tied_p(STRIKE_REC[1] / w3_med, l5, d_ref) - tied_p(STRIKE_REC[0] / w3_med, l5, d_ref))
        span_headon = abs(tied_p(l3, HEADON_REC[1] / w5_med, d_ref) - tied_p(l3, HEADON_REC[0] / w5_med, d_ref))
        out["R86_tied_value_of_information_spans"][f"reference_{d_ref:.0f}m"] = {"strike_span": span_strike, "headon_span": span_headon}
    # R73: what decides the sign of the signals' extra delay
    q_vps, sat_vps = BASELINE_Q / 3600.0, 1.0 / t["draw_sat_headway_s"]
    veh_day = 2.0 * BASELINE_Q * OPERATION_HOURS
    delay = {s: veh_day * uniform_delay_per_vehicle_s(t[f"diag_{s}_cycle_s"], t[f"diag_{s}_green_s"], q_vps, sat_vps) / 3600.0
             for s in ("S0", "S1a")}
    dd = delay["S1a"] - delay["S0"]
    dclear = t["diag_S1a_clearance_s"] - t["diag_S0_clearance_s"]
    m = np.isfinite(dd) & np.isfinite(dclear)
    out["R73_delay_sign"] = {
        "spearman_delay_diff_vs_clearance_diff": spearman(dd, dclear),
        "spearman_delay_diff_vs_clearance_speed": spearman(dd, t["draw_v_clear_kmh"]),
        "spearman_delay_diff_vs_fixed_plan_green_ratio": spearman(dd, t["draw_f_cycle_a"]),
        "share_signs_agree": float((np.sign(dd[m]) == np.sign(dclear[m])).mean()),
        "share_S1a_adds_delay": float((dd[m] > 0).mean()), "share_S1a_clearance_longer": float((dclear[m] > 0).mean())}

    # R74: the plan's surface (collision axis), with and without the queue-tail difference
    l5c = COLLISION_REC / float(np.nanmedian(t["diag_S1a_collisions_per_day"]))
    out["R74_plan_surface"] = {"l5_collision_axis": l5c}
    for label, queue in (("queue_tail_at_panel_level", 1.0), ("queue_tail_difference_excluded", 0.0)):
        d1, d2 = dh("S1a", l3, l5c, queue), dh("S2", l3, l5c, queue)
        out["R74_plan_surface"][label] = {"p_S1a": P(d1), "p_S2": P(d2), "p_S2_below_S1a": P(d2 - d1)}
    out["R74_plan_surface"]["implied_head_on_serious_harm_s1a"] = float(np.nanmedian(l5c * parts["S1a"]["W5"]))

    # R79: the speed sweep's head-on term on each axis (constants from the 40 km/h baseline row)
    rows = list(csv.DictReader(open(dist / "speed_sweep.csv")))
    base = next(r_ for r_ in rows if float(r_["platoon_speed_kmh"]) == 40)
    f_serious = HEADON_C / float(base["w5_s1a_median"])
    f_coll = COLLISION_REC / float(base["collisions_day_s1a"])
    out["R79_speed_sweep_axes"] = {"factor_serious_harm_axis": f_serious, "factor_collision_axis": f_coll, "rows": [
        {"speed_kmh": float(r_["platoon_speed_kmh"]), "head_on_model_level": float(r_["w5_s1a_median"]),
         "head_on_serious_harm_axis": f_serious * float(r_["w5_s1a_median"]),
         "head_on_collision_axis": f_coll * float(r_["w5_s1a_median"]),
         "device_head_on_serious_harm_axis": f_serious * float(r_["w5_s2_median"])} for r_ in rows]}

    (dist / "review_reads.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
