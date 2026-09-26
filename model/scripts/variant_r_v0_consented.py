"""Review-driven, ungated sensitivity (round 2, practitioner finding P3): count the entries a
manual controller consents to (a late arrival waved through unescorted to follow the departed
platoon) as entries into the section under the radio hold, instead of only driver-initiated
defiance. Kansas flagger-only: 9 of 814 vehicles (all flagger-consented), 1.1 per cent of all
vehicles, 1.3 per cent of facing vehicles at a 0.85 red-arrival share; Jeffreys 95 per cent
interval 0.6 to 2.4 per cent (research/violation-priors-harmonisation.md, definitional variant).
The primary prior r_v0 (driver-initiated only) is unchanged; this run replaces it with
Triangular(0.006, 0.0131, 0.024) at the baseline cell and reads the decision at the record
calibration with the same anchoring as the primary. Nothing here is a prior moved after a run
to improve an answer: it is an alternative definition of what counts as an entry, reported
beside the primary. Writes variant_r_v0_consented.json into the newest dist."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
MODEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEL / "src")); sys.path.insert(0, str(MODEL / "scripts"))
from mtcpts.distributions import Triangular, load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, run_cell  # noqa: E402
import decision_outputs_s2 as D  # noqa: E402

def main() -> None:
    dist = D.newest_dist()
    sej = load_sej(MODEL / "config")
    res = run_cell(Cell(*D.BASELINE), sej, Priors(r_v0=Triangular(0.006, 0.0131, 0.024)), n_iter=20_000, n_grid=128)
    parts = {s: {k: np.asarray(res.parts[s][k]) for k in ("W1", "W3", "W5", "W4d")} for s in ("S0", "S1a", "S1b", "S2")}
    w5a = float(np.nanmedian(parts["S1a"]["W5"])); w3a = float(np.nanmedian(parts["S0"]["W3"]))
    def P(d): d = d[np.isfinite(d)]; return float((d < 0).mean())
    rec = D.record_reads(parts, D.HEADON_C, D.STRIKE_C, w5a, w3a)
    out = {"dist": dist.name, "r_v0_variant": "Triangular(0.006, 0.0131, 0.024) per facing vehicle (Kansas incl. flagger-consented entries)",
           "s0_w5_elicited_median": float(np.nanmedian(parts["S0"]["W5"])),
           "s0_w5_at_record_median": float(np.nanmedian(parts["S0"]["W5"]) * D.HEADON_C / w5a),
           "s0_headon_share_of_s1a_at_record": float(np.nanmedian(parts["S0"]["W5"]) / w5a),
           "s1a_w5_median": w5a}
    for s in ("S1a", "S1b", "S2"):
        out[f"{s.lower()}_p_at_record_central"] = P(rec[s])
        out[f"{s.lower()}_dh_median_at_record"] = float(np.nanmedian(rec[s]))
        out[f"{s.lower()}_p_at_record_corners"] = {f"h{h}_c{c}": P(D.record_reads(parts, h, c, w5a, w3a)[s]) for h in D.HEADON_REC for c in D.STRIKE_REC}
        out[f"{s.lower()}_p_equivalent_at_record_central"] = float((np.abs(rec[s][np.isfinite(rec[s])]) <= D.MARGIN).mean())
    d21 = rec["S2"] - rec["S1a"]; out["s2_vs_s1a_p_s2_lower_at_record_central"] = P(d21)
    out["s1a_p_elicited"] = P(np.asarray(res.parts["S1a"]["W4d"]) + np.asarray(res.parts["S1a"]["W3"]) - np.asarray(res.parts["S0"]["W3"]) + np.asarray(res.parts["S1a"]["W5"]) - np.asarray(res.parts["S0"]["W5"]))
    (dist / "variant_r_v0_consented.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
