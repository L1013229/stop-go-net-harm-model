#!/usr/bin/env python3
"""Download bounded DfT annual CSVs, retain roadworks rows, reproduce head-on proxies.

Python 3 + requests. No full-history download. Raw downloads are gzip-compressed in
--cache, with HTTP payload bytes capped at 450,000,000 per invocation. Offline rerun
uses the small selected CSVs. Counts are collisions, not vehicle-pairs or casualties.
"""
import argparse
import csv
import gzip
import hashlib
import io
import itertools
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
BASE = "https://data.dft.gov.uk/road-accidents-safety-data/"
DEFINITIONS = {
    "S0_two_front_opposite_straight_ahead": "Exactly 2 vehicles; both front; opposite from and to; each from opposite own to; both manoeuvre going ahead",
    "S1_two_front_opposite_straight": "Exactly 2 vehicles; both front; opposite from and to; each from opposite own to",
    "S2_two_front_opposite_from": "Exactly 2 vehicles; both front; from directions opposite",
    "M1_pair_front_opposite_from": "Any vehicle pair; both front; from directions opposite",
    "M2_pair_front_near_opposite_from": "Any vehicle pair; both front; from directions 135, 180 or 225 degrees apart",
    "M3_two_front": "Exactly 2 vehicles; both front; no direction condition",
    "M4_pair_front": "Any vehicle pair; both front; no direction condition",
    "L1_pair_one_front_opposite_from": "Any vehicle pair; at least one front; from directions opposite",
    "L2_pair_opposite_from": "Any vehicle pair; from directions opposite; no impact condition",
    "L3_multi_any_front": "At least 2 vehicles; at least one front impact; no direction condition (deliberately nonspecific)",
}


def integer(v):
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return -1


def opposite(a, b):
    return 1 <= a <= 8 and 1 <= b <= 8 and abs(a - b) == 4


def near_opposite(a, b):
    return 1 <= a <= 8 and 1 <= b <= 8 and abs(a - b) in (3, 4, 5)


def classify(c, vehicles):
    flags = dict.fromkeys(DEFINITIONS, False)
    two = integer(c["number_of_vehicles"]) == 2 and len(vehicles) == 2
    for a, b in itertools.combinations(vehicles, 2):
        af, bf = integer(a["first_point_of_impact"]) == 1, integer(b["first_point_of_impact"]) == 1
        a0, a1 = integer(a["vehicle_direction_from"]), integer(a["vehicle_direction_to"])
        b0, b1 = integer(b["vehicle_direction_from"]), integer(b["vehicle_direction_to"])
        opp = opposite(a0, b0)
        straight = opp and opposite(a1, b1) and opposite(a0, a1) and opposite(b0, b1)
        ahead = all(integer(v.get("vehicle_manoeuvre")) in (16, 17, 18, 19) for v in (a, b))
        values = [two and af and bf and straight and ahead, two and af and bf and straight,
                  two and af and bf and opp, af and bf and opp,
                  af and bf and near_opposite(a0, b0), two and af and bf, af and bf,
                  (af or bf) and opp, opp, af or bf]
        for k, v in zip(DEFINITIONS, values):
            flags[k] |= v
    return flags


def write_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rows_from(path):
    with gzip.open(path, "rt", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            yield {k.lower().replace("accident_", "collision_"): v for k, v in r.items()}


def download(args):
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    manifest = []
    payload_bytes = 0
    session = requests.Session()
    for year in range(args.start, args.end + 1):
        year_rows = {}
        keys = set()
        for kind in ("collision", "vehicle", "casualty"):
            name = f"dft-road-casualty-statistics-{kind}-{year}.csv"
            url = BASE + name
            target = cache / (name + ".gz")
            info = {"year": year, "kind": kind, "url": url,
                    "accessed_utc": datetime.now(timezone.utc).isoformat()}
            if target.exists():
                with gzip.open(target, "rb") as f:
                    h = hashlib.sha256()
                    n = 0
                    for chunk in iter(lambda: f.read(1048576), b""):
                        h.update(chunk)
                        n += len(chunk)
                info.update(status="cached", bytes=n, sha256=h.hexdigest())
            else:
                with session.get(url, stream=True, timeout=90) as r:
                    info.update(status=r.status_code, final_url=r.url,
                                content_length=r.headers.get("Content-Length"))
                    if r.status_code != 200:
                        manifest.append(info)
                        continue
                    declared = int(r.headers.get("Content-Length", 0))
                    if payload_bytes + declared > args.max_bytes:
                        raise RuntimeError("Download cap would be exceeded")
                    h = hashlib.sha256()
                    n = 0
                    with gzip.open(target, "wb") as f:
                        for chunk in r.iter_content(1048576):
                            n += len(chunk)
                            payload_bytes += len(chunk)
                            if payload_bytes > args.max_bytes:
                                raise RuntimeError("Download cap exceeded")
                            h.update(chunk)
                            f.write(chunk)
                    if declared and n != declared:
                        raise RuntimeError(f"Truncated download: {url}")
                    info.update(bytes=n, sha256=h.hexdigest())
            selected = []
            total = 0
            for row in rows_from(target):
                total += 1
                # Retain literal request and mapped 2024 roadworks for sensitivity.
                if kind == "collision":
                    if integer(row.get("special_conditions_at_site")) == 4 or integer(row.get("carriageway_hazards")) == 13:
                        selected.append(row)
                        keys.add(row["collision_index"])
                elif row["collision_index"] in keys:
                    selected.append(row)
            info.update(rows=total, selected_rows=len(selected))
            manifest.append(info)
            year_rows[kind] = selected
            print(year, kind, total, "selected", len(selected), flush=True)
        if len(year_rows) == 3:
            for kind, rows in year_rows.items():
                write_csv(ROOT / f"roadworks-{kind}-{year}.csv", rows)
        (ROOT / "stats19-downloads.json").write_text(json.dumps({"payload_bytes_this_run": payload_bytes,
            "max_bytes": args.max_bytes, "files": manifest}, indent=2) + "\n")


def analyse():
    annual, membership, qa = [], [], []
    for path in sorted(ROOT.glob("roadworks-collision-*.csv")):
        year = int(path.stem.rsplit("-", 1)[1])
        collisions = list(csv.DictReader(path.open()))
        vehicles, casualties = defaultdict(list), defaultdict(list)
        for kind, data in (("vehicle", vehicles), ("casualty", casualties)):
            for r in csv.DictReader((ROOT / f"roadworks-{kind}-{year}.csv").open()):
                data[r["collision_index"]].append(r)
        if len({c["collision_index"] for c in collisions}) != len(collisions):
            raise AssertionError("Duplicate collision IDs")
        counts = defaultdict(Counter)
        for c in collisions:
            key = c["collision_index"]
            vs, cs = vehicles[key], casualties[key]
            assert len(vs) == integer(c["number_of_vehicles"]), (year, key, "vehicle join")
            assert len(cs) == integer(c["number_of_casualties"]), (year, key, "casualty join")
            assert len({v["vehicle_reference"] for v in vs}) == len(vs)
            sev = integer(c["collision_severity"])
            assert sev == min(integer(x["casualty_severity"]) for x in cs), (year, key, "severity")
            flags = classify(c, vs)
            literal = integer(c.get("special_conditions_at_site")) == 4
            row = {"year": year, "collision_index": key, "collision_severity": sev,
                   "literal_roadworks": int(literal), **{k: int(v) for k, v in flags.items()}}
            membership.append(row)
            for scope in ("literal_special4", "harmonised_special4_or_hazard13"):
                if scope.startswith("literal") and not literal:
                    continue
                for definition, selected in {"ALL_ROADWORKS": True, **flags}.items():
                    if not selected:
                        continue
                    count = counts[scope, definition]
                    count["collisions"] += 1
                    count[{1: "fatal", 2: "serious", 3: "slight"}[sev]] += 1
                    count["fatal_or_serious"] += int(sev <= 2)
                    count["casualties"] += len(cs)
                    count["fatal_casualties"] += sum(integer(x["casualty_severity"]) == 1 for x in cs)
                    count["serious_casualties"] += sum(integer(x["casualty_severity"]) == 2 for x in cs)
        for scope in ("literal_special4", "harmonised_special4_or_hazard13"):
            for definition in ("ALL_ROADWORKS", *DEFINITIONS):
                count = counts[scope, definition]
                annual.append({"year": year, "scope": scope, "definition": definition,
                    **{k: count[k] for k in ("collisions", "fatal", "serious", "slight", "fatal_or_serious",
                                            "casualties", "fatal_casualties", "serious_casualties")}})
        qa.append({"year": year, "retained_collisions": len(collisions),
                   "literal_roadworks": sum(integer(c.get("special_conditions_at_site")) == 4 for c in collisions),
                   "vehicle_casualty_joins_and_severity": "all passed"})
    write_csv(ROOT / "stats19-annual.csv", annual)
    write_csv(ROOT / "stats19-membership.csv", membership)
    (ROOT / "stats19-qa.json").write_text(json.dumps(qa, indent=2) + "\n")
    (ROOT / "stats19-definitions.json").write_text(json.dumps(DEFINITIONS, indent=2) + "\n")
    # Exhaustive descriptive comparison, not estimation or recovery of lost provenance.
    windows = []
    years = sorted({r["year"] for r in annual})
    for scope in ("literal_special4", "harmonised_special4_or_hazard13"):
        for definition in DEFINITIONS:
            for start in years:
                for end in years:
                    n = end - start + 1
                    if n < 3 or not set(range(start, end + 1)).issubset(years):
                        continue
                    subset = [r for r in annual if r["scope"] == scope and r["definition"] == definition and start <= r["year"] <= end]
                    rates = {k: sum(r[k] for r in subset) / n for k in ("collisions", "fatal_or_serious", "fatal")}
                    diffs = {"delta_" + k: rates[k] - target for k, target in (("collisions", 50), ("fatal_or_serious", 19), ("fatal", 1.6))}
                    score = sum(((rates[k] - target) / target) ** 2 for k, target in (("collisions", 50), ("fatal_or_serious", 19), ("fatal", 1.6)))
                    windows.append({"scope": scope, "definition": definition, "start": start, "end": end, "years": n, **rates, **diffs, "relative_squared_error": score})
    write_csv(ROOT / "stats19-period-comparison.csv", sorted(windows, key=lambda r: r["relative_squared_error"]))
    print(json.dumps(qa), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--download", action="store_true")
    p.add_argument("--start", type=int, default=2010)
    p.add_argument("--end", type=int, default=2025)
    p.add_argument("--cache", default="/tmp/trbam-round15-stats19")
    p.add_argument("--max-bytes", type=int, default=450_000_000)
    args = p.parse_args()
    if args.download:
        download(args)
    analyse()
