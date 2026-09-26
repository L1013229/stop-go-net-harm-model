"""Export the POOLED Scenario C priors for public release (owner ruling 2026-09-26).

The public code must run without any participant-level row. The per-expert fitted table
(`sej_scenario_c_fits.csv`, one row per expert per quantity) stays in the restricted store.
This script draws a large coupled sample from the equal-weight per-expert mixtures, exactly
as the model consumes them (RE and SEV of one pathway drawn through the SAME expert index),
and writes only the pooled draws: no expert identifier, no per-expert parameter.

The released model samples rows of this table instead of the mixtures. Results reproduce the
paper's within Monte Carlo tolerance (pinned by tests/test_pooled_release.py); the exact
per-expert route reproduces them bit for bit and needs the restricted file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

MODEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODEL / "src"))
from mtcpts.distributions import load_sej  # noqa: E402

N_ROWS = 400_000
SEED = 20260926


def main() -> None:
    sej = load_sej(MODEL / "config")
    rng = np.random.default_rng(SEED)
    out = {}
    for re_id, sev_id, tag in (("C.RE1_Queue", "C.SEV1", "1"), ("C.RE3_MTC", "C.SEV3", "3")):
        re, sev = sej[re_id], sej[sev_id]
        assert re.expert_uids == sev.expert_uids
        idx = rng.integers(0, re.n_experts, N_ROWS)
        out[f"re{tag}_rate"] = (1.0 / re.sample_with_index(idx, rng.random(N_ROWS))).astype(np.float64)
        out[f"sev{tag}_p"] = sev.sample_with_index(idx, rng.random(N_ROWS)).astype(np.float64)
    d15 = sej["C.D15_PortSignals"]
    out["d15_multiplier"] = d15.sample(rng, N_ROWS).astype(np.float64)
    path = MODEL / "config" / "sej_scenario_c_pooled.npz"
    np.savez_compressed(path, **out, n_rows=np.array(N_ROWS), seed=np.array(SEED))
    for k, v in out.items():
        q = np.quantile(v, [0.05, 0.5, 0.95])
        print(f"  {k:16s} q05 {q[0]:.4g}  q50 {q[1]:.4g}  q95 {q[2]:.4g}")
    print(f"wrote {path} ({N_ROWS} coupled rows, no expert identifiers)")


if __name__ == "__main__":
    main()
