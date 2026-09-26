"""Device readings with the operator's exposure scaled to the controller record for a
reference controller standing at a stated offset from the edge line, and with one operator.

Review round 3 (practitioner and regulator, Opus, finding 4) noted that the like-for-like
scaling in decision_outputs_s2.py places the reference controller AT the edge line (offset 0),
while the standards keep the controller on the shoulder. A controller standing further from
the lane implies a larger calibration factor for the same record and a larger operator term.
Finding 13 noted that the United States manual permits one operator to run both units when
both are in view, which halves the operator exposure. Both readings come from the saved
baseline draws with no prior changed; the queue-tail term is suppressed as in every decision
output. Output: <dist>/operator_reference_variants.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decision_outputs_s2 import (HEADON_C, HEADON_REC, MARGIN, STRIKE_C, STRIKE_REC,  # noqa: E402
                                 newest_dist)


def main() -> None:
    dist = newest_dist()
    t = np.load(dist / "baseline_traces.npz")
    parts = {s: {k: t[f"part_{s}_{k}"] for k in ("W1", "W3", "W5", "W4d", "W5b")}
             for s in ("S0", "S1a", "S1b", "S2")}
    w5_anchor = float(np.nanmedian(parts["S1a"]["W5"]))
    w3_anchor = float(np.nanmedian(parts["S0"]["W3"]))
    edge = parts["S2"]["W3"] / np.exp(-t["draw_reach_alpha"] * t["draw_offset_op_m"])

    def P(d):
        d = d[np.isfinite(d)]
        return float((d < 0).mean())

    def reads(k_op: float, operators: float, headon: float = HEADON_C, controller: float = STRIKE_C):
        l3, l5 = controller / w3_anchor, headon / w5_anchor
        op = operators * (controller / STRIKE_C) * k_op * parts["S2"]["W3"]
        d = parts["S2"]["W4d"] + op - l3 * parts["S0"]["W3"] + l5 * (parts["S2"]["W5"] - parts["S0"]["W5"])
        d1a = (parts["S1a"]["W4d"] + parts["S1a"]["W3"] - l3 * parts["S0"]["W3"]
               + l5 * (parts["S1a"]["W5"] - parts["S0"]["W5"]))
        d21 = d - d1a
        fin = np.isfinite(d)
        return {"p": P(d), "dh_median": float(np.median(d[fin])),
                "p_equivalent": float((np.abs(d[fin]) <= MARGIN).mean()),
                "p_s2_below_s1a": P(d21), "operator_term_median": float(np.nanmedian(op))}

    out = {"dist": dist.name, "note": __doc__.strip().splitlines()[0], "variants": {}}
    for d_ref in (0.0, 1.0, 1.5, 2.0):
        term_ref = edge * np.exp(-t["draw_reach_alpha"] * d_ref)
        k_op = STRIKE_C / float(np.nanmedian(term_ref))
        for operators, tag in ((1.0, "two_operators"), (0.5, "one_operator")):
            r = reads(k_op, operators)
            corners = [reads(k_op, operators, h_, c_)["p"] for h_ in HEADON_REC for c_ in STRIKE_REC]
            r |= {"k_op": k_op, "reference_controller_offset_m": d_ref,
                  "p_corners_min_max": [min(corners), max(corners)]}
            out["variants"][f"like_for_like_ref_{d_ref:.1f}m_{tag}"] = r
    for operators, tag in ((1.0, "two_operators"), (0.5, "one_operator")):
        r = reads(1.0, operators)
        corners = [reads(1.0, operators, h_, c_)["p"] for h_ in HEADON_REC for c_ in STRIKE_REC]
        r |= {"k_op": 1.0, "p_corners_min_max": [min(corners), max(corners)]}
        out["variants"][f"pre_specified_{tag}"] = r
    (dist / "operator_reference_variants.json").write_text(json.dumps(out, indent=2))
    for k, v in out["variants"].items():
        print(f"{k:45s} P={v['p']:.3f} corners={v['p_corners_min_max'][0]:.3f}-{v['p_corners_min_max'][1]:.3f} "
              f"P(S2<S1a)={v['p_s2_below_s1a']:.3f} op_term={v['operator_term_median']:.2e} k={v['k_op']:.2f}")


if __name__ == "__main__":
    main()
