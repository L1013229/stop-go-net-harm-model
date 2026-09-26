"""The frozen configuration file and the code's Priors defaults must not drift apart.

config/priors.toml is the citable record of what was frozen, with its evidence trail;
model.Priors carries the values the model actually samples. A silent divergence between
them would make the evidence trail a fiction.
"""
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mtcpts.distributions import Fixed, LogUniform, Triangular, Uniform  # noqa: E402
from mtcpts.model import Priors  # noqa: E402

TOML = Path(__file__).resolve().parents[1] / "config" / "priors.toml"

# priors.toml key -> Priors field. Masses and occupancy are sampled twice from one prior.
ALIASES = {"mass_kg": "mass_kg", "occupancy": "occupancy"}


@pytest.fixture(scope="module")
def cfg():
    with open(TOML, "rb") as fh:
        return tomllib.load(fh)


def _from_cfg(spec):
    fam = spec["family"]
    if fam == "triangular":
        return Triangular(spec["lo"], spec["mode"], spec["hi"])
    if fam == "uniform":
        return Uniform(spec["lo"], spec["hi"])
    if fam == "loguniform":
        return LogUniform(spec["lo"], spec["hi"])
    if fam == "fixed":
        return Fixed(spec["value"])
    raise ValueError(fam)


def test_every_toml_entry_matches_the_sampled_prior(cfg):
    p = Priors()
    missing = []
    for key, spec in cfg.items():
        field = ALIASES.get(key, key)
        if not hasattr(p, field):
            missing.append(key)
            continue
        assert _from_cfg(spec) == getattr(p, field), f"{key} drifted from priors.toml"
    assert not missing, f"priors.toml declares unknown priors: {missing}"


def test_every_sampled_prior_is_declared_in_the_toml(cfg):
    declared = set(cfg) | {"mass_kg", "occupancy"}
    fields = {f for f in Priors().__dataclass_fields__}
    undeclared = fields - declared
    assert not undeclared, f"sampled without an evidence entry: {sorted(undeclared)}"


def test_every_prior_carries_an_evidence_string(cfg):
    for key, spec in cfg.items():
        assert spec.get("evidence", "").strip(), f"{key} has no evidence trail"


def test_contested_parameters_are_the_frozen_list(cfg):
    """docs/prespec.md freezes the rule-3 list. Adding to it after a run is forbidden."""
    frozen = {"w_occ", "q_lead", "d_sight_m", "w_onset", "ttc50", "s_ttc",
              "impact_speed_frac", "p_detect_s0", "p_detect_s1b", "p_evade_harm"}
    assert frozen <= set(cfg), sorted(frozen - set(cfg))
