"""Delay trade across cells (review round 2, practitioner finding P8). Uniform delay per arriving
vehicle under each strategy's own cycle plan (Webster's D/D term, as welfare.py), summed over the
operation day, at three demands and two section lengths. Fresh draws per cell (4,000), same
priors and seeds discipline as the suite; medians and means of the fixed-time signals' extra
delay over manual control, priced at the value of travel time. Writes delay_by_cell.json into
the newest dist. A reading of the model's cycle layer, not a delay model."""
from __future__ import annotations
import json, sys, tomllib
from pathlib import Path
import numpy as np
MODEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEL / "src")); sys.path.insert(0, str(MODEL / "scripts"))
from mtcpts.distributions import load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, run_cell, OPERATION_HOURS  # noqa: E402
import decision_outputs_s2 as D  # noqa: E402

def main() -> None:
    vals = tomllib.load(open(MODEL / "config" / "welfare-values.toml", "rb"))
    vot = float(vals["value_of_travel_time_nzd_per_hour"]["value"])
    sej = load_sej(MODEL / "config"); dist = D.newest_dist()
    rows = []
    for q in (300.0, 600.0, 800.0):
        for L in (250.0, 1000.0):
            res = run_cell(Cell(q, L), sej, Priors(), n_iter=4_000, n_grid=64)
            q_vps = q / 3600.0; sat = 1.0 / np.asarray(res.draws["sat_headway_s"]); veh = 2.0 * q * OPERATION_HOURS
            def veh_h(s):
                T = np.asarray(res.diag[s]["cycle_s"]); g = np.asarray(res.diag[s]["green_s"]); r = T - g
                return veh * (r * r / (2.0 * T * (1.0 - q_vps / sat))) / 3600.0
            d0, d1 = veh_h("S0"), veh_h("S1a"); dd = d1 - d0; ok = np.isfinite(dd)
            rows.append({"q_vph_dir": q, "section_m": L, "stable_share": float(np.nanmean(res.draws["_stable"])),
                         "s0_delay_veh_h_median": float(np.nanmedian(d0)), "s1a_delay_veh_h_median": float(np.nanmedian(d1)),
                         "extra_delay_veh_h_median": float(np.median(dd[ok])), "extra_delay_veh_h_mean": float(np.mean(dd[ok])),
                         "extra_delay_nzd_median": float(np.median(dd[ok]) * vot), "extra_delay_nzd_mean": float(np.mean(dd[ok]) * vot),
                         "p_s1a_adds_delay": float((dd[ok] > 0).mean()),
                         "mean_wait_s_s0_median": float(np.nanmedian(d0 * 3600.0 / veh)), "mean_wait_s_s1a_median": float(np.nanmedian(d1 * 3600.0 / veh))})
            print(rows[-1])
    (dist / "delay_by_cell.json").write_text(json.dumps({"dist": dist.name, "vot_nzd_per_hour": vot, "rows": rows}, indent=2))

if __name__ == "__main__":
    main()
