"""The public-release priors (pooled rows, no expert identifiers) reproduce the paper's
baseline within Monte Carlo tolerance, and the release loader falls back to them only when
the restricted per-expert file is absent."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.distributions import PooledSEJ, load_sej, load_sej_mixtures, load_sej_pooled  # noqa: E402
from mtcpts.model import Cell, Priors, p_dh_negative, run_cell  # noqa: E402

CONFIG = Path(__file__).resolve().parents[1] / "config"


@pytest.mark.skipif(not (CONFIG / "sej_scenario_c_pooled.npz").exists(), reason="pooled file not exported")
def test_pooled_rows_carry_no_expert_identifier():
    z = np.load(CONFIG / "sej_scenario_c_pooled.npz")
    assert set(z.files) == {"re1_rate", "sev1_p", "re3_rate", "sev3_p", "d15_multiplier", "n_rows", "seed"}


@pytest.mark.skipif(not (CONFIG / "sej_scenario_c_pooled.npz").exists() or not (CONFIG / "sej_scenario_c_fits.csv").exists(),
                    reason="needs both the pooled file and the restricted per-expert table")
def test_pooled_release_reproduces_baseline_within_mc_tolerance():
    fits = load_sej_mixtures(CONFIG / "sej_scenario_c_fits.csv")
    pooled = load_sej_pooled(CONFIG / "sej_scenario_c_pooled.npz")
    a = run_cell(Cell(300, 250), fits, Priors(), n_iter=20_000, n_grid=32)
    b = run_cell(Cell(300, 250), pooled, Priors(), n_iter=20_000, n_grid=32)
    pa, _, _ = p_dh_negative(a.h_s1a, a.h_s0)
    pb, _, _ = p_dh_negative(b.h_s1a, b.h_s0)
    assert abs(pa - pb) < 0.005
    for s, k in (("S0", "W1"), ("S0", "W3")):
        ma, mb = np.nanmedian(a.parts[s][k]), np.nanmedian(b.parts[s][k])
        assert abs(np.log10(ma / mb)) < 0.05, (s, k, ma, mb)


def test_release_loader_prefers_fits_and_falls_back(tmp_path):
    if (CONFIG / "sej_scenario_c_fits.csv").exists():
        assert not isinstance(load_sej(CONFIG), PooledSEJ)      # restricted table present: exact route
    else:
        assert isinstance(load_sej(CONFIG), PooledSEJ)          # public release: pooled route
    if (CONFIG / "sej_scenario_c_pooled.npz").exists():
        (tmp_path / "sej_scenario_c_pooled.npz").write_bytes((CONFIG / "sej_scenario_c_pooled.npz").read_bytes())
        assert isinstance(load_sej(tmp_path), PooledSEJ)         # fits absent: pooled form
    with pytest.raises(FileNotFoundError):
        load_sej(tmp_path / "empty")
