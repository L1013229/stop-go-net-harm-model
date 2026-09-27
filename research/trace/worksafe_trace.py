#!/usr/bin/env python3
"""Screen a frozen WorkSafe notification table; this is NOT a controller census.

Offline: python3 worksafe_trace.py
Refresh (changes snapshot): python3 worksafe_trace.py --refresh
Dependencies for refresh only: requests, beautifulsoup4.
"""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
URL = "https://data.worksafe.govt.nz/editorial/fatalities_summary_table"
# Deliberately broad screen. Keep original row numbers; identical rows may be
# different people (e.g. two 55-year-olds in the February 2019 incident).
DIRECT = r"road|traffic|flagger|stop[ /-]?go|culvert|expressway"
VEHICLE = r"truck|vehicle|car\b|roller|run over|ran over|struck|collision"
INDUSTRIES = {"Construction", "Administrative and Support Services"}


def main(refresh=False):
    snapshot = ROOT / "worksafe-snapshot.json"
    if refresh:
        import requests
        from bs4 import BeautifulSoup
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        assert len(response.content) < 5_000_000
        app = BeautifulSoup(response.text, "html.parser").select_one("#app[data-props]")
        props = json.loads(app["data-props"])
        snapshot.write_text(json.dumps({
            "url": URL, "accessed_utc": datetime.now(timezone.utc).isoformat(),
            "http_status": response.status_code,
            "http_body_sha256": hashlib.sha256(response.content).hexdigest(),
            "scope": props["description"], "coverage_note_html": props["contentBlockOne"],
            "rows": props["tableData"]["tableData"],
        }, ensure_ascii=False, indent=2) + "\n")
    data = json.loads(snapshot.read_text())
    selected, valid, invalid = [], [], []
    for n, row in enumerate(data["rows"], 1):
        try:
            day = datetime.strptime(row["formatted_date_of_incident"], "%d/%m/%Y").date()
        except (ValueError, TypeError):
            invalid.append(n)
            continue
        valid.append(day)
        text = row.get("summary_of_incident") or ""
        direct = bool(re.search(DIRECT, text, re.I))
        broad = row.get("industry") in INDUSTRIES and bool(re.search(VEHICLE, text, re.I))
        if direct or broad:
            selected.append({"snapshot_row": n, "date": day.isoformat(),
                "in_review_period_2010_2025": int(2010 <= day.year <= 2025),
                "selection": "direct_word" if direct else "industry_and_vehicle_word", **row})
    with (ROOT / "worksafe-candidates.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(selected[0]))
        w.writeheader()
        w.writerows(selected)
    result = {"source": URL, "snapshot_rows": len(data["rows"]),
        "valid_dated_rows": len(valid), "invalid_date_rows": invalid,
        "first_incident": min(valid).isoformat(), "last_incident": max(valid).isoformat(),
        "direct_regex": DIRECT, "vehicle_regex": VEHICLE, "industries": sorted(INDUSTRIES),
        "candidate_rows_all_years": len(selected),
        "candidate_rows_2010_2025": sum(r["in_review_period_2010_2025"] for r in selected),
        "warning": "Candidate screen only: no occupation/control-duty variable; notifications exclude other regulators. No national rate calculated."}
    (ROOT / "worksafe-selection.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    main(parser.parse_args().refresh)
