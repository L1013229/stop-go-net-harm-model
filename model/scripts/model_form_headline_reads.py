"""Reproduce the four headline shares under the pre-specified avoidance forms.

Run from the repository with:
    PYTHONDONTWRITEBYTECODE=1 python3 model/scripts/model_form_headline_reads.py

The production dist is explicit. Existing outputs are never replaced. First verify
the saved primary headlines against the selected review reads, then reproduce every primary trace array
before running alternatives with the production seed, draws, grid and priors.

review_reads.main contains nested calibration and tied-operator functions. Invoke
that imported function in an isolated temporary dist, redirecting only newest_dist,
and select its headline results. No calibration or operator arithmetic is copied.
Its unrelated speed-sweep readings are discarded; the production speed sweep is
linked only because main reads it. The primary trace remains baseline_traces.npz.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import platform
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parent))

import review_reads  # noqa: E402
from model_form_sensitivity import FORMS  # noqa: E402
from run_suite import BASELINE, N_GRID, N_ITER  # noqa: E402
from mtcpts.distributions import load_sej  # noqa: E402
from mtcpts.model import Cell, Priors, run_cell  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / "model/outputs/dist/capfix_20260927"
SEED = 20260709
FORM_IDS = ("primary", "common_cause_0p5", "common_cause_1p0", "threshold", "loglogistic")
METRICS = ("signal_medians_matched", "signal_means_matched", "tied_device_0m", "tied_device_1m")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(REPO))


def headline_reads(trace: Path) -> tuple[dict, dict]:
    """Use the unmodified review reader without writing into the production dist."""
    with tempfile.TemporaryDirectory(prefix="model-form-review-") as name:
        staging = Path(name)
        (staging / "baseline_traces.npz").symlink_to(trace.resolve())
        (staging / "speed_sweep.csv").symlink_to(DIST / "speed_sweep.csv")
        with patch.object(review_reads, "newest_dist", return_value=staging):
            with contextlib.redirect_stdout(io.StringIO()):
                review_reads.main()
        reads = json.loads((staging / "review_reads.json").read_text())
    values = dict(zip(METRICS, (
        reads["R78_red_running_removal_at_record"]["p_with"],
        reads["R56_mean_matched"]["S1a"],
        reads["R71_R75_tied_operator"]["reference_0m"]["p"],
        reads["R71_R75_tied_operator"]["reference_1m"]["p"],
    ), strict=True))
    factors = {k: v for k, v in reads["constants"].items() if k.startswith(("l3_", "l5_"))}
    return values, factors


def registered_primary() -> dict:
    """Cross-check against the selected run's independently regenerated review reads."""
    reads = json.loads((DIST / "review_reads.json").read_text())
    return dict(zip(METRICS, (
        reads["R78_red_running_removal_at_record"]["p_with"],
        reads["R56_mean_matched"]["S1a"],
        reads["R71_R75_tied_operator"]["reference_0m"]["p"],
        reads["R71_R75_tied_operator"]["reference_1m"]["p"],
    ), strict=True))


def trace_arrays(res) -> dict:
    """The exact key layout saved by run_suite.run_baseline_extras."""
    return dict(
        h_s0=res.h_s0, h_s1a=res.h_s1a, h_s1b=res.h_s1b, h_s2=res.h_s2,
        dh=res.h_s1a - res.h_s0, dh_s2=res.h_s2 - res.h_s0,
        breakeven_s1a=res.breakeven["S1a"], breakeven_s2=res.breakeven["S2"],
        **{f"part_{s}_{k}": v for s in res.parts for k, v in res.parts[s].items()},
        **{f"diag_{s}_{k}": v for s in res.diag for k, v in res.diag[s].items()},
        **{f"draw_{k}": v for k, v in res.draws.items()},
    )


def require_same_arrays(actual: dict, expected: dict, keys) -> None:
    different = [k for k in keys if actual[k].dtype != expected[k].dtype
                 or actual[k].shape != expected[k].shape
                 or actual[k].tobytes() != expected[k].tobytes()]
    if different:
        raise RuntimeError(f"STOP: trace arrays differ from production: {different}")


def require_schema_and_finite_inputs(arrays: dict, baseline: dict) -> None:
    if arrays.keys() != baseline.keys():
        raise RuntimeError("STOP: trace schema differs from baseline_traces.npz")
    for key, value in arrays.items():
        if value.shape != baseline[key].shape or value.dtype != baseline[key].dtype:
            raise RuntimeError(f"STOP: trace shape or dtype differs: {key}")
    # These are all inputs to the four headline deltas; none may lose draws.
    keys = [f"part_{s}_{k}" for s in ("S0", "S1a", "S2") for k in ("W3", "W4d", "W5")]
    keys += ["draw_reach_alpha", "draw_offset_op_m"]
    if any(arrays[k].shape != (N_ITER,) or not np.isfinite(arrays[k]).all() for k in keys):
        raise RuntimeError("STOP: headline inputs do not contain 20,000 finite paired draws")


def main() -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=REPO, text=True).strip()
    if branch != "trr-v1.2-cut":
        raise RuntimeError(f"STOP: expected branch trr-v1.2-cut, found {branch}")
    target = DIST / "model_form_headline_reads.json"
    paths = {form_id: DIST / f"model_form_traces_{form_id}.npz" for form_id in FORM_IDS[1:]}
    existing = [str(p) for p in (target, *paths.values()) if p.exists() or p.is_symlink()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite existing outputs: {existing}")

    sources = [REPO / "model/config/priors.toml", REPO / "model/config/sej_scenario_c_fits.csv",
               REPO / "model/scripts/run_suite.py", REPO / "model/scripts/review_reads.py",
               REPO / "model/scripts/model_form_sensitivity.py", Path(__file__).resolve(),
               REPO / "model/scripts/decision_outputs_s2.py", REPO / "model/scripts/welfare.py",
               REPO / "model/config/welfare-values.toml", REPO / "docs/prespec.md",
               REPO / "docs/model-design.md", DIST / "baseline_traces.npz",
               DIST / "review_reads.json", DIST / "model_form_sensitivity.csv", DIST / "speed_sweep.csv"]
    sources += sorted((REPO / "model/src/mtcpts").glob("*.py"))
    source_hashes = {relative(p): sha256(p) for p in sources}
    registry_hash = sha256(REPO / "results/REGISTRY.md")

    baseline_path = DIST / "baseline_traces.npz"
    expected = registered_primary()
    primary_values, primary_factors = headline_reads(baseline_path)
    if primary_values != expected:
        raise RuntimeError(f"STOP: primary mismatch: computed {primary_values}; review reads {expected}")
    print(f"Primary shares exactly reproduce review reads: {primary_values}", flush=True)

    with np.load(baseline_path, allow_pickle=False) as saved:
        baseline = {key: saved[key] for key in saved.files}
    sej = load_sej_mixtures(REPO / "model/config/sej_scenario_c_fits.csv")
    with (DIST / "model_form_sensitivity.csv").open(newline="") as fh:
        old_median_shares = {row["form"]: row["p_dh_neg_record_central"]
                            for row in csv.DictReader(fh) if row["strategy"] == "S1a"}
    draw_keys = [key for key in baseline if key.startswith("draw_")]
    rows = []
    for form_id, (label, form) in zip(FORM_IDS, FORMS.items(), strict=True):
        print(f"Running {form_id}: {label}", flush=True)
        res = run_cell(Cell(*BASELINE), sej, Priors(), n_iter=N_ITER, seed=SEED, n_grid=N_GRID, form=form)
        arrays = trace_arrays(res)
        require_schema_and_finite_inputs(arrays, baseline)
        require_same_arrays(arrays, baseline, draw_keys)
        if form_id == "primary":
            require_same_arrays(arrays, baseline, baseline.keys())
            trace = baseline_path
            values, factors = primary_values, primary_factors
            print(f"Primary rerun: all {len(arrays)} trace arrays bitwise identical", flush=True)
        else:
            # Verify and read the candidate before publishing it to the production dist.
            with tempfile.TemporaryDirectory(prefix="model-form-trace-") as name:
                candidate = Path(name) / "baseline_traces.npz"
                with candidate.open("xb") as fh:
                    np.savez_compressed(fh, **arrays)
                values, factors = headline_reads(candidate)
                if f"{values['signal_medians_matched']:.4f}" != old_median_shares[label]:
                    raise RuntimeError(f"STOP: {form_id} does not reproduce the earlier median-matched share")
                trace = paths[form_id]
                with trace.open("xb") as fh:
                    fh.write(candidate.read_bytes())
            with np.load(trace, allow_pickle=False) as saved:
                require_same_arrays(saved, arrays, arrays.keys())
        rows.append({
            "form": form_id, "label": label, "rho": form.rho, "curve": form.curve,
            "trace_file": relative(trace), "trace_sha256": sha256(trace),
            "n_draws": N_ITER, "finite_draws_per_headline": N_ITER,
            "sampled_input_arrays_bitwise_equal_to_primary": len(draw_keys),
            **values, "calibration_factors": factors,
            "signal_implied_collisions_per_op_day_median": float(np.nanmedian(res.diag["S1a"]["collisions_per_day"])),
            "device_implied_collisions_per_op_day_median": float(np.nanmedian(res.diag["S2"]["collisions_per_day"])),
        })
        print(json.dumps({"form": form_id, **values}), flush=True)

    adverse = {}
    for metric in METRICS:
        value = min(row[metric] for row in rows)
        winners = [row for row in rows if row[metric] == value]
        adverse[metric] = {"form": winners[0]["form"], "label": winners[0]["label"],
                           "value": value, "all_tied_forms": [row["form"] for row in winners],
                           "primary_value": rows[0][metric], "direction": "minimum"}
    for path, digest in source_hashes.items():
        if sha256(REPO / path) != digest:
            raise RuntimeError(f"STOP: an input/source changed during execution: {path}")
    output = {
        "dist": DIST.name, "script": relative(Path(__file__).resolve()),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "branch": branch, "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "production": {"seed": SEED, "rng": "PCG64", "rng_seed_sequence": [SEED, *BASELINE],
                       "n_draws": N_ITER, "n_grid": N_GRID, "q_vph_dir": BASELINE[0], "section_m": BASELINE[1],
                       "priors": "unmodified Priors(); production per-expert SEJ fits"},
        "reading": {"signal_strategy": "S1a", "device_strategy": "S2",
                    "device_matching": "medians", "queue_tail_difference": "excluded",
                    "avoidance_harm": "excluded", "headon_central": review_reads.HEADON_C,
                    "controller_central": review_reads.STRIKE_C,
                    "calibration": "Re-anchor each form on its own S0 W3 and S1a W5 means or medians.",
                    "implementation": "Imported review_reads.main, including its nested dh and tied functions.",
                    "extracted_keys": ["R78_red_running_removal_at_record.p_with", "R56_mean_matched.S1a",
                                       "R71_R75_tied_operator.reference_0m.p", "R71_R75_tied_operator.reference_1m.p"]},
        "primary_reproduction": {"source": relative(DIST / "review_reads.json"), "expected": expected,
                                 "actual": primary_values, "exact_headline_match": True,
                                 "rerun_trace_arrays_bitwise_identical": len(baseline),
                                 "registry_sha256_before_new_rows": registry_hash},
        "validation": {"all_sampled_inputs_identical_across_forms": True,
                       "existing_model_form_median_shares_reproduced_at_saved_precision": True,
                       "existing_outputs_overwritten": False,
                       "source_sha256_unchanged_during_run": source_hashes},
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "rows": rows,
        "most_adverse_rule": "Minimum favourable share for each headline separately across all five forms (docs/prespec.md A6); lower shares weaken favourability of substitution.",
        "most_adverse": adverse,
    }
    with target.open("x") as fh:
        json.dump(output, fh, indent=2, allow_nan=False)
        fh.write("\n")
    print(f"Saved {relative(target)}", flush=True)
    print(json.dumps(adverse, indent=2), flush=True)


if __name__ == "__main__":
    main()
