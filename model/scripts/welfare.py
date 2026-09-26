"""Welfare reading of the delay trade, docs/prespec.md Addendum A7.

From the saved baseline traces: deterministic uniform delay per arriving vehicle under each
strategy's own cycle plan (D/D queue, symmetric demand), summed over the operation day; the
safety difference at the record calibration priced per serious-harm event; the delay
difference priced at the value of travel time. Values from model/config/welfare-values.toml.
The PRIMARY reading prices the record-calibrated safety change the decision outputs use, without
the queue-tail term (prespec A7.1, after review round 1: as sampled that term carries the panel's
queue-tail level, 15x the all-cause record). Sensitivities restore it scaled to the all-cause record
ceiling and at the elicited level. Writes welfare_summary.json into the newest dist. This is a
reading of the model's own outputs, not a delay model.
"""
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import numpy as np

MODEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEL / "src"))
from mtcpts.model import OPERATION_HOURS  # noqa: E402

BASELINE_Q = 300.0
HEADON_C, STRIKE_C = 1.2e-5, 1.0e-5


def newest_dist() -> Path:
    return max((MODEL / "outputs" / "dist").glob("*_2026*"), key=lambda d: d.stat().st_mtime)


def uniform_delay_per_vehicle_s(cycle_s, green_s, q_vps, sat_vps):
    """Webster's uniform term for D/D arrivals: d1 = r^2 / (2 T (1 - q/s)), r = T - g."""
    r = cycle_s - green_s
    return r * r / (2.0 * cycle_s * (1.0 - q_vps / sat_vps))


def main() -> None:
    vals = tomllib.load(open(MODEL / "config" / "welfare-values.toml", "rb"))
    vot = float(vals["value_of_travel_time_nzd_per_hour"]["value"])
    vosl = float(vals["value_of_statistical_life_nzd"]["value"])
    v_event = {"vosl": vosl}
    if "value_per_serious_injury_nzd" in vals:
        v_event["serious_injury"] = float(vals["value_per_serious_injury_nzd"]["value"])

    dist = newest_dist()
    t = np.load(dist / "baseline_traces.npz")
    q_vps = BASELINE_Q / 3600.0
    sat_vps = 1.0 / t["draw_sat_headway_s"]
    veh_day = 2.0 * BASELINE_Q * OPERATION_HOURS
    parts = {s: {k: t[f"part_{s}_{k}"] for k in ("W1", "W3", "W5", "W4d")} for s in ("S0", "S1a", "S1b", "S2")}
    l3 = STRIKE_C / float(np.nanmedian(parts["S0"]["W3"]))
    l5 = HEADON_C / float(np.nanmedian(parts["S1a"]["W5"]))

    delay_h = {}
    for s in ("S0", "S1a", "S1b", "S2"):
        d1 = uniform_delay_per_vehicle_s(t[f"diag_{s}_cycle_s"], t[f"diag_{s}_green_s"], q_vps, sat_vps)
        delay_h[s] = veh_day * d1 / 3600.0                       # vehicle-hours per op-day
    out = {"dist": dist.name, "value_of_travel_time_nzd_per_hour": vot,
           "value_per_event_nzd": v_event,
           "delay_veh_hours_per_op_day_median": {s: float(np.nanmedian(v)) for s, v in delay_h.items()},
           "mean_wait_s_per_vehicle_median": {s: float(np.nanmedian(v * 3600.0 / veh_day)) for s, v in delay_h.items()}}
    ALL_TTM_DSI_PER_OP_DAY = 146.0 / 4.0e5          # research/crash-record-bounds.md, all pathways
    w1_scale = ALL_TTM_DSI_PER_OP_DAY / float(np.nanmedian(parts["S0"]["W1"]))
    out["queue_tail_record_scale"] = w1_scale
    for s in ("S1a", "S1b", "S2"):
        base = (parts[s]["W4d"] + parts[s]["W3"] - l3 * parts["S0"]["W3"]
                + l5 * (parts[s]["W5"] - parts["S0"]["W5"]))          # the decision outputs' dH
        qt = parts[s]["W1"] - parts["S0"]["W1"]                       # queue-tail difference, elicited level
        ddelay = delay_h[s] - delay_h["S0"]
        fin = np.isfinite(base) & np.isfinite(ddelay) & np.isfinite(qt)
        base, qt, ddelay = base[fin], qt[fin], ddelay[fin]
        row = {
            "delta_delay_veh_hours_per_op_day_median": float(np.median(ddelay)),
            "delta_delay_cost_nzd_per_op_day_median": float(np.median(ddelay) * vot),
        }
        for label, dh in (("primary", base), ("queue_tail_at_record_ceiling", base + w1_scale * qt),
                          ("queue_tail_at_elicited_level", base + qt)):
            row[f"{label}_dh_median"] = float(np.median(dh))
            row[f"{label}_p_dh_neg"] = float((dh < 0).mean())
            for name, val in v_event.items():
                net = dh * val + ddelay * vot                     # NZD per op-day, positive = worse
                row[f"{label}_safety_cost_nzd_median_{name}"] = float(np.median(dh * val))
                row[f"{label}_net_social_cost_nzd_median_{name}"] = float(np.median(net))
                row[f"{label}_p_net_benefit_{name}"] = float((net < 0).mean())
                row[f"{label}_breakeven_delta_delay_veh_hours_{name}"] = float(-np.median(dh) * val / vot)
        out[s] = row
    (dist / "welfare_summary.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
