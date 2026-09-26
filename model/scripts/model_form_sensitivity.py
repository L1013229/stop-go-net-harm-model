"""Model-form sensitivity, docs/prespec.md Addendum A6.

Runs the baseline cell under the primary tree and each named structural alternative, for the
unattended signal (S1a) and the attended device (S2), and writes model_form_sensitivity.csv
into the newest production dist. Every headline is computed under every form; the paper
states each headline with its value under the most adverse form for the strategy concerned
(lowest P(dH < 0) at the record central).

Record calibration is re-anchored per form (the head-on axis on that form's S1a W5 median),
so what survives the calibration is the structural difference between arms, not the level
shift the form produces.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.conflict import ModelForm  # noqa: E402
from mtcpts.distributions import load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, p_dh_negative, run_cell  # noqa: E402

MODEL = Path(__file__).resolve().parents[1]
BASELINE = (300, 250)
HEADON_C, STRIKE_C = 1.2e-5, 1.0e-5
HEADON_REC, STRIKE_REC = (6e-6, 2e-5), (5e-6, 2e-5)
MARGIN = 1.0 / (100.0 * 250.0)
FORMS = {
    "primary (independent failures, logistic in TTC)": ModelForm(),
    "MF1 common cause rho=0.5": ModelForm(rho=0.5),
    "MF1 common cause rho=1.0": ModelForm(rho=1.0),
    "MF2a threshold at ttc50": ModelForm(curve="threshold"),
    "MF2b logistic in ln TTC": ModelForm(curve="loglogistic"),
}


def newest_dist() -> Path:
    return max((MODEL / "outputs" / "dist").glob("*_2026*"), key=lambda d: d.stat().st_mtime)


def reads(res, s: str, headon: float, controller: float) -> np.ndarray:
    P = res.parts
    l3 = controller / float(np.nanmedian(P["S0"]["W3"]))
    l5 = headon / float(np.nanmedian(P["S1a"]["W5"]))
    dh = P[s]["W4d"] + P[s]["W3"] - l3 * P["S0"]["W3"] + l5 * (P[s]["W5"] - P["S0"]["W5"])
    return dh[np.isfinite(dh)]


def main() -> None:
    dist = newest_dist()
    sej = load_sej(MODEL / "config")
    rows = []
    for label, form in FORMS.items():
        res = run_cell(Cell(*BASELINE), sej, Priors(), n_iter=20_000, n_grid=128, form=form)
        for s in ("S1a", "S2"):
            d = reads(res, s, HEADON_C, STRIKE_C)
            worst = min(float((reads(res, s, h_, c_) < 0).mean())
                        for h_ in HEADON_REC for c_ in STRIKE_REC)
            p_el, _, _ = p_dh_negative(res.h(s), res.h_s0)
            d21 = reads(res, "S2", HEADON_C, STRIKE_C) - reads(res, "S1a", HEADON_C, STRIKE_C)
            diag = res.diag[s]
            rows.append({
                "form": label, "strategy": s,
                "p_dh_neg_elicited": f"{p_el:.4f}",
                "p_dh_neg_record_central": f"{float((d < 0).mean()):.4f}",
                "p_dh_neg_record_worst_corner": f"{worst:.4f}",
                "p_equivalent_record_central": f"{float((np.abs(d) <= MARGIN).mean()):.4f}",
                "dh_median_record": f"{float(np.median(d)):.4e}",
                "abs_dh_median_record": f"{float(np.median(np.abs(d))):.4e}",
                "implied_collisions_per_op_day": f"{float(np.nanmedian(diag['collisions_per_day'])):.4e}",
                "w5_median_elicited": f"{float(np.nanmedian(res.parts[s]['W5'])):.4e}",
                "p_s2_lower_than_s1a_record_central": f"{float((d21 < 0).mean()):.4f}",
            })
            print(f"  {label:48s} {s:4s} P_rec={rows[-1]['p_dh_neg_record_central']} "
                  f"P_el={rows[-1]['p_dh_neg_elicited']} coll={rows[-1]['implied_collisions_per_op_day']}")
    with open(dist / "model_form_sensitivity.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    # most adverse form per strategy, by the pre-stated rule
    adverse = {}
    for s in ("S1a", "S2"):
        rs = [r for r in rows if r["strategy"] == s]
        worst = min(rs, key=lambda r: float(r["p_dh_neg_record_central"]))
        adverse[s] = {"form": worst["form"], **{k: worst[k] for k in worst if k not in ("form", "strategy")}}
    (dist / "model_form_most_adverse.json").write_text(json.dumps(adverse, indent=2))
    print(json.dumps(adverse, indent=2))
    print(f"\n-> {dist / 'model_form_sensitivity.csv'}")


if __name__ == "__main__":
    main()
