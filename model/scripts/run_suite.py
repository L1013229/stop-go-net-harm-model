"""Production run suite (guarded).

Guard: refuses to run unless the last commit touching docs/prespec.md is no later than the
last commit touching model/config/priors.toml (the freeze), and both are clean. Outputs go
to model/outputs/dist/<sha>_<date>/ and are the ONLY artefacts the manuscript may cite.

Before any decision output is written, the model-validity gates of docs/prespec.md are
evaluated at the baseline cell and printed. A gate failure is reported, never silently
absorbed, and is repaired at the model's structure rather than by moving a prior.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.distributions import Fixed, load_sej  # noqa: E402
from mtcpts.model import (DEVICE_STRATEGIES, STRATEGIES, Cell, Priors,  # noqa: E402
                          calibration_curve, decision_surface, p_dh_negative, run_cell)
from mtcpts.sensitivity import prcc, prcc_bootstrap  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
MODEL = REPO / "model"
GRID_Q = [100, 200, 300, 450, 600, 800, 1000]
GRID_L = [150, 250, 500, 1000, 2000]
BASELINE = (300, 250)
SPEED_SWEEP = [30, 40, 50, 60, 70, 80]
SIGHT_SWEEP = [150, 250, 500, 1000, 2000, 3000]
SIGHT_CELLS = [(300, 250), (300, 1000)]
N_ITER = 20_000
N_GRID = 128
P_STARS = (0.5, 0.8)

# research/crash-record-bounds.md and research/controller-strike-bounds.md
GATE_HEADON = (1e-6, 1e-3)          # head-on collisions per operation-day, baseline cell
GATE_PCV = 8.5e-3                   # P(collision | violation), rule-of-three 95% ceiling
GATE_STRIKE_DSI = (1e-6, 1e-4)      # controller serious-harm events per operation-day
STRIKE_RECORD_CENTRAL = 1.0e-5      # controller record central (coherence read for S2's W3r)


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def prespec_guard() -> str:
    t_prespec = int(_git("log", "-1", "--format=%ct", "--", "docs/prespec.md"))
    t_priors = int(_git("log", "-1", "--format=%ct", "--", "model/config/priors.toml"))
    dirty = _git("status", "--porcelain", "--", "docs/prespec.md", "model/config/priors.toml")
    if dirty:
        raise SystemExit("GUARD: prespec/priors have uncommitted changes")
    if t_prespec > t_priors:
        raise SystemExit("GUARD: prespec postdates the priors freeze — recommit priors")
    return _git("rev-parse", "--short", "HEAD")


def variant_priors(which: str) -> Priors:
    """Rule-5 variant sets: contested parameters with a monotone device-favourability
    direction, at their PTS-favourable or PTS-unfavourable bounds. `s_ttc` has no monotone
    direction and is excluded. W5b and W6 are not in the primary ledger."""
    if which == "primary":
        return Priors()
    if which == "optdev":
        return Priors(w_occ=Fixed(1.0e-4), q_lead=Fixed(1.0e-3), w_onset=Fixed(0.95),
                      ttc50=Fixed(1.0), impact_speed_frac=Fixed(0.3),
                      p_detect_s0=Fixed(0.3), p_detect_s1b=Fixed(0.7),
                      d_sight_m=Fixed(3000.0),
                      p_detect_s2=Fixed(0.9), offset_op_m=Fixed(6.0))     # Addendum A3
    if which == "pessdev":
        return Priors(w_occ=Fixed(1.0e-2), q_lead=Fixed(1.0e-1), w_onset=Fixed(0.50),
                      ttc50=Fixed(2.5), impact_speed_frac=Fixed(1.0),
                      p_detect_s0=Fixed(0.9), p_detect_s1b=Fixed(0.1),
                      d_sight_m=Fixed(150.0),
                      p_detect_s2=Fixed(0.3), offset_op_m=Fixed(1.5))     # Addendum A3
    raise ValueError(which)


def _q(x, p):
    x = np.asarray(x)[np.isfinite(np.asarray(x))]
    return float(np.percentile(x, p)) if len(x) else float("nan")


def validity_gates(sej, out: Path) -> dict:
    """Evaluate the blocking gates at the baseline cell BEFORE any decision output."""
    res = run_cell(Cell(*BASELINE), sej, Priors(), n_iter=N_ITER, n_grid=N_GRID)
    d = res.diag["S1a"]
    coll = float(np.nanmedian(d["collisions_per_day"]))
    pcv = float(np.nanmedian(d["collisions_per_day"] / np.maximum(d["violations_per_day"], 1e-300)))
    strikes = float(np.nanmedian(res.diag["S0"]["controller_strikes_per_day"]))
    w3_dsi = float(np.nanmedian(res.parts["S0"]["W3"]))
    g = {
        "headon_collisions_per_op_day": coll,
        "gate1_band": list(GATE_HEADON),
        "gate1_pass": bool(GATE_HEADON[0] <= coll <= GATE_HEADON[1]),
        "p_collision_given_violation": pcv,
        "rule_of_three_ceiling": GATE_PCV,
        "rule_of_three_pass": bool(pcv < GATE_PCV),
        "controller_strikes_per_op_day": strikes,
        "controller_dsi_per_op_day": w3_dsi,
        "gate2_band": list(GATE_STRIKE_DSI),
        "gate2_pass": bool(GATE_STRIKE_DSI[0] <= w3_dsi <= GATE_STRIKE_DSI[1]),
        "headon_dsi_per_op_day": float(np.nanmedian(res.parts["S1a"]["W5"])),
    }
    # ---- Addendum A4: gate 1 for S2, and the operator residual read against the record
    d2 = res.diag["S2"]
    coll2 = float(np.nanmedian(d2["collisions_per_day"]))
    pcv2 = float(np.nanmedian(d2["collisions_per_day"] / np.maximum(d2["violations_per_day"], 1e-300)))
    w3r = float(np.nanmedian(res.parts["S2"]["W3"]))
    g |= {
        "s2_headon_collisions_per_op_day": coll2,
        "s2_gate1_pass": bool(GATE_HEADON[0] <= coll2 <= GATE_HEADON[1]),
        "s2_p_collision_given_violation": pcv2,
        "s2_rule_of_three_pass": bool(pcv2 < GATE_PCV),
        "s2_operator_strikes_per_op_day": float(np.nanmedian(d2["controller_strikes_per_day"])),
        "s2_operator_dsi_per_op_day": w3r,
        "s2_operator_below_controller_record_central": bool(w3r < STRIKE_RECORD_CENTRAL),
        "s2_headon_dsi_per_op_day": float(np.nanmedian(res.parts["S2"]["W5"])),
    }
    (out / "validity_gates.json").write_text(json.dumps(g, indent=2))
    print("\n=== MODEL VALIDITY GATES (baseline cell) ===")
    print(f"  gate 1  implied head-on collisions/op-day : {coll:.3e}  "
          f"band {GATE_HEADON[0]:.0e}-{GATE_HEADON[1]:.0e}  {'PASS' if g['gate1_pass'] else 'FAIL'}")
    print(f"          P(collision|violation)            : {pcv:.3e}  "
          f"< {GATE_PCV:.1e}  {'PASS' if g['rule_of_three_pass'] else 'FAIL'}")
    print(f"  gate 2  implied controller serious harm/op-day : {w3_dsi:.3e}  "
          f"band {GATE_STRIKE_DSI[0]:.0e}-{GATE_STRIKE_DSI[1]:.0e}  "
          f"{'PASS' if g['gate2_pass'] else 'FAIL'}   (strikes {strikes:.3e})")
    print(f"  S2      implied head-on collisions/op-day : {coll2:.3e}  "
          f"{'PASS' if g['s2_gate1_pass'] else 'FAIL'};  P(coll|viol) {pcv2:.3e}  "
          f"{'PASS' if g['s2_rule_of_three_pass'] else 'FAIL'}")
    print(f"  S2      operator residual serious harm/op-day : {w3r:.3e}  "
          f"(controller record central {STRIKE_RECORD_CENTRAL:.0e}; "
          f"{'below' if g['s2_operator_below_controller_record_central'] else 'NOT below'})")
    if not (g["gate1_pass"] and g["rule_of_three_pass"]):
        raise SystemExit("GATE 1 FAILURE: repair the model's structure, not its priors.")
    if not (g["s2_gate1_pass"] and g["s2_rule_of_three_pass"]):
        raise SystemExit("GATE 1 FAILURE (S2): repair the model's structure, not its priors.")
    if not g["gate2_pass"]:
        print("\n  GATE 2 FAILED. The elicited controller-strike rate is excluded by the")
        print("  occupational-injury record (research/controller-strike-bounds.md). The prior is")
        print("  consumed whole by design and is NOT re-centred. What changes is what the model")
        print("  may conclude: no point probability computed at the elicited value is reportable")
        print("  as the answer. The decision surface over the two observable serious-harm")
        print("  frequencies is the decision output.\n")
    return g


def run_grid(sej, priors: Priors, out: Path, suffix: str) -> None:
    rows = []
    for q in GRID_Q:
        for L in GRID_L:
            res = run_cell(Cell(q, L), sej, priors, n_iter=N_ITER, n_grid=N_GRID)
            row = {"q_vph_dir": q, "section_m": L,
                   "stable_frac": float(np.mean(res.draws["_stable"]))}
            for key in DEVICE_STRATEGIES:
                h, s = res.h(key), key.lower()
                p, lo, hi = p_dh_negative(h, res.h_s0)
                dh = h - res.h_s0
                row |= {f"p_dh_neg_{s}": p, f"p_lo_{s}": lo, f"p_hi_{s}": hi,
                        f"dh_q05_{s}": _q(dh, 5), f"dh_q50_{s}": _q(dh, 50),
                        f"dh_q95_{s}": _q(dh, 95),
                        f"breakeven_q50_{s}": _q(res.breakeven[key], 50)}
            for s in STRATEGIES:
                row |= {f"w1_{s}": _q(res.parts[s]["W1"], 50),
                        f"w3_{s}": _q(res.parts[s]["W3"], 50),
                        f"w5_{s}": _q(res.parts[s]["W5"], 50),
                        f"w4d_{s}": _q(res.parts[s]["W4d"], 50),
                        f"w5b_{s}": _q(res.parts[s]["W5b"], 50),
                        f"violations_day_{s}": _q(res.diag[s]["violations_per_day"], 50),
                        f"conflicts_day_{s}": _q(res.diag[s]["conflicts_per_day"], 50),
                        f"collisions_day_{s}": _q(res.diag[s]["collisions_per_day"], 50),
                        f"clearance_s_{s}": _q(res.diag[s]["clearance_s"], 50),
                        f"safe_window_{s}": _q(res.diag[s]["p_safe_window"], 50)}
            row["strikes_day_S0"] = _q(res.diag["S0"]["controller_strikes_per_day"], 50)
            row["strikes_day_S2"] = _q(res.diag["S2"]["controller_strikes_per_day"], 50)
            rows.append(row)
            print(f"  [{suffix}] {q:>4} vph {L:>4} m  P(dH<0) S1a={row['p_dh_neg_s1a']:.3f} "
                  f"S1b={row['p_dh_neg_s1b']:.3f} S2={row['p_dh_neg_s2']:.3f}  "
                  f"coll/day={row['collisions_day_S1a']:.2e}")
    with open(out / f"grid_results_{suffix}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def run_baseline_extras(sej, out: Path) -> None:
    res = run_cell(Cell(*BASELINE), sej, Priors(), n_iter=N_ITER, n_grid=N_GRID)
    dh = res.h_s1a - res.h_s0

    # PRCC on dH, sampled inputs only (drop private diagnostics); S1a (primary) and S2
    names = [k for k, v in res.draws.items() if not k.startswith("_") and np.std(v) > 0]
    for strat, dh_s in (("S1a", dh), ("S2", res.h_s2 - res.h_s0)):
        tag = strat.lower()
        ok = np.isfinite(dh_s)
        pt = prcc({k: res.draws[k][ok] for k in names}, dh_s[ok], names)
        with open(out / f"prcc_baseline_{tag}.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["input", "prcc"])
            for k, v in sorted(pt.items(), key=lambda t: -abs(t[1])):
                w.writerow([k, f"{v:.6f}"])
        bs = prcc_bootstrap({k: res.draws[k][ok] for k in names}, dh_s[ok], n_boot=200, names=names)
        fname = "prcc_bootstrap_full.csv" if strat == "S1a" else f"prcc_bootstrap_{tag}.csv"
        with open(out / fname, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["input", "prcc", "lo95", "hi95"])
            for k, (p, lo, hi) in sorted(bs.items(), key=lambda t: -abs(t[1][0])):
                w.writerow([k, f"{p:.6f}", f"{lo:.6f}", f"{hi:.6f}"])

    # observational calibration curve, per device strategy
    for strat, fname in (("S1a", "calibration_curve.csv"), ("S2", "calibration_curve_s2.csv")):
        with open(out / fname, "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["lambda", "headon_collisions_per_op_day", "p_dh_neg"])
            for lam, coll, p in calibration_curve(res, strat):
                w.writerow([f"{lam:.6g}", f"{coll:.6g}", f"{p:.6f}"])

    # joint decision surface over the two observable frequencies, per device strategy
    for strat, fname in (("S1a", "decision_surface.npz"), ("S2", "decision_surface_s2.npz")):
        surf = decision_surface(res, strat)
        np.savez_compressed(out / fname, **{k: np.asarray(v) for k, v in surf.items()})

    # operating-speed sweep (a decision axis, not a nuisance parameter)
    with open(out / "speed_sweep.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["platoon_speed_kmh", "p_dh_neg_s1a", "p_dh_neg_s1b", "p_dh_neg_s2",
                    "w3_median", "w5_s1a_median", "collisions_day_s1a",
                    "w5_s2_median", "w3r_s2_median", "collisions_day_s2"])
        for v in SPEED_SWEEP:
            r = run_cell(Cell(*BASELINE), sej, Priors(platoon_speed_kmh=Fixed(float(v))),
                         n_iter=N_ITER // 2, n_grid=N_GRID)
            pa, _, _ = p_dh_negative(r.h_s1a, r.h_s0)
            pb, _, _ = p_dh_negative(r.h_s1b, r.h_s0)
            p2, _, _ = p_dh_negative(r.h_s2, r.h_s0)
            w.writerow([v, f"{pa:.4f}", f"{pb:.4f}", f"{p2:.4f}",
                        f"{_q(r.parts['S0']['W3'],50):.6g}",
                        f"{_q(r.parts['S1a']['W5'],50):.6g}",
                        f"{_q(r.diag['S1a']['collisions_per_day'],50):.6g}",
                        f"{_q(r.parts['S2']['W5'],50):.6g}",
                        f"{_q(r.parts['S2']['W3'],50):.6g}",
                        f"{_q(r.diag['S2']['collisions_per_day'],50):.6g}"])
            print(f"  [speed] {v:>3} km/h  P(dH<0) S1a={pa:.3f} S1b={pb:.3f} S2={p2:.3f}")

    # intervisibility sweep: the design-controllable site axis, at two section lengths
    with open(out / "sight_sweep.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["section_m", "sight_m", "p_dh_neg_s1a", "w5_s1a_median",
                    "collisions_day_s1a", "p_blind_median",
                    "p_dh_neg_s2", "w5_s2_median", "collisions_day_s2"])
        for (q_cell, L_cell) in SIGHT_CELLS:
            # sight caps at the section length, so sweep up to L only; sig = L is full
            # end-to-end intervisibility
            for sig in [x for x in SIGHT_SWEEP if x <= L_cell]:
                r = run_cell(Cell(q_cell, L_cell), sej,
                             Priors(d_sight_m=Fixed(float(sig))),
                             n_iter=N_ITER // 2, n_grid=N_GRID)
                pa, _, _ = p_dh_negative(r.h_s1a, r.h_s0)
                p2, _, _ = p_dh_negative(r.h_s2, r.h_s0)
                w.writerow([L_cell, sig, f"{pa:.4f}",
                            f"{_q(r.parts['S1a']['W5'], 50):.6g}",
                            f"{_q(r.diag['S1a']['collisions_per_day'], 50):.6g}",
                            f"{_q(r.diag['S1a']['p_blind'], 50):.4f}",
                            f"{p2:.4f}", f"{_q(r.parts['S2']['W5'], 50):.6g}",
                            f"{_q(r.diag['S2']['collisions_per_day'], 50):.6g}"])
                print(f"  [sight] L={L_cell} s={sig}  P={pa:.3f} "
                      f"W5={_q(r.parts['S1a']['W5'],50):.2e}")

    # per-iteration traces for the figures
    np.savez_compressed(
        out / "baseline_traces.npz",
        h_s0=res.h_s0, h_s1a=res.h_s1a, h_s1b=res.h_s1b, h_s2=res.h_s2, dh=dh,
        dh_s2=res.h_s2 - res.h_s0,
        breakeven_s1a=res.breakeven["S1a"], breakeven_s2=res.breakeven["S2"],
        **{f"part_{s}_{k}": v for s in res.parts for k, v in res.parts[s].items()},
        **{f"diag_{s}_{k}": v for s in res.diag for k, v in res.diag[s].items()},
        **{f"draw_{k}": v for k, v in res.draws.items()})


def main() -> None:
    sha = prespec_guard()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    out = MODEL / "outputs" / "dist" / f"{sha}_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    sej = load_sej(MODEL / "config")

    validity_gates(sej, out)                      # blocking, before any decision output

    print("\n=== GRID ===")
    for suffix in ("primary", "optdev", "pessdev"):
        run_grid(sej, variant_priors(suffix), out, suffix)
    print("\n=== BASELINE EXTRAS ===")
    run_baseline_extras(sej, out)
    print(f"\nartefacts -> {out}")


if __name__ == "__main__":
    main()
