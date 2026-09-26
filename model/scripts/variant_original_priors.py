"""The plan's surface under the two priors as first written (round-5 hostile referee, Opus).

On 9 July 2026 two priors were re-valued after a first calibrated result had been read (supplement
S7 item 1a; registry R65): the assumed clearance speed from uniform 30 to 36 km/h to uniform 20 to
40, and the released-platoon operating speed from uniform 40 to 60 km/h to triangular 30, 40, 50.
This script re-runs the baseline cell with the ORIGINAL values and reads both decision surfaces,
so the paper can report the pre-registered surface under the priors the plan first carried.
Output: <dist>/original_priors_reads.json. Nothing here changes the production run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision_outputs_s2 import (HEADON_C, HEADON_REC, MARGIN, STRIKE_C, STRIKE_REC, BASELINE,  # noqa: E402
                                 MODEL, UNGATED_R_V2, load_sej_mixtures, newest_dist, record_reads)
from mtcpts.distributions import Uniform  # noqa: E402
from mtcpts.model import Cell, Priors, run_cell  # noqa: E402

COLL_REC = 3.3e-5


def P(d):
    d = d[np.isfinite(d)]
    return float((d < 0).mean())


def main() -> None:
    dist = newest_dist()
    sej = load_sej(MODEL / "config")
    res = run_cell(Cell(*BASELINE), sej, Priors(v_clear_kmh=Uniform(30.0, 36.0), platoon_speed_kmh=Uniform(40.0, 60.0)),
                   n_iter=20_000, n_grid=128)
    parts = res.parts
    w5a = float(np.nanmedian(parts["S1a"]["W5"])); w3a = float(np.nanmedian(parts["S0"]["W3"]))
    out = {"dist": dist.name, "priors": {"v_clear_kmh": "uniform 30 to 36", "platoon_speed_kmh": "uniform 40 to 60"}}
    # serious-harm axis, medians matched
    rec = record_reads(parts, HEADON_C, STRIKE_C, w5a, w3a)
    out["serious_harm_axis"] = {s: P(rec[s]) for s in ("S1a", "S1b", "S2")}
    out["serious_harm_axis"]["S2_below_S1a"] = P(rec["S2"] - rec["S1a"])
    corners = {s: [P(record_reads(parts, h, c, w5a, w3a)[s]) for h in HEADON_REC for c in STRIKE_REC] for s in ("S1a", "S2")}
    out["serious_harm_axis_corners"] = {s: [min(v), max(v)] for s, v in corners.items()}
    # collision axis: scale S1a median collisions to the record; the same factor applies to the serious harm the tree implies
    coll = res.diag["S1a"]["collisions_per_day"]
    l5c = COLL_REC / float(np.nanmedian(coll)); l3 = STRIKE_C / w3a
    out["implied_headon_collisions_s1a_median"] = float(np.nanmedian(coll))
    for lab, qt in (("qt_panel", 1.0), ("qt_excluded", 0.0)):
        d = {}
        for s in ("S1a", "S1b", "S2"):
            d[s] = (parts[s]["W4d"] + parts[s]["W3"] - l3 * parts["S0"]["W3"] + l5c * (parts[s]["W5"] - parts["S0"]["W5"])
                    + qt * (parts[s]["W1"] - parts["S0"]["W1"]))
        fin = np.isfinite(d["S1a"])
        cc = []
        for h in (1e-5, 1e-4):
            for c in STRIKE_REC:
                l5h = h / float(np.nanmedian(coll)); l3c = c / w3a
                dd = (parts["S1a"]["W4d"] + parts["S1a"]["W3"] - l3c * parts["S0"]["W3"] + l5h * (parts["S1a"]["W5"] - parts["S0"]["W5"])
                      + qt * (parts["S1a"]["W1"] - parts["S0"]["W1"]))
                cc.append(P(dd))
        out[f"collision_axis_{lab}"] = {"S1a": P(d["S1a"]), "S1b": P(d["S1b"]), "S2": P(d["S2"]), "S2_below_S1a": P(d["S2"] - d["S1a"]),
                                        "S1a_corners": [min(cc), max(cc)], "S1a_median_dh": float(np.median(d["S1a"][fin])),
                                        "S1a_within_margin": float((np.abs(d["S1a"][fin]) <= MARGIN).mean())}
    (dist / "original_priors_reads.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
