#!/usr/bin/env python3
"""Repeat arithmetic from frozen STATS19 rows and published-table transcriptions."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
t = json.loads((ROOT / "table-inputs.json").read_text())
annual = list(csv.DictReader((ROOT / "stats19-annual.csv").open()))
gb = []
for scope in sorted({r["scope"] for r in annual}):
    for definition in sorted({r["definition"] for r in annual}):
        rows = [r for r in annual if r["scope"] == scope and r["definition"] == definition]
        years = sorted(int(r["year"]) for r in rows)
        assert years == list(range(2021, 2026))
        sums = {k: sum(int(r[k]) for r in rows) for k in
                ("collisions", "fatal", "serious", "slight", "fatal_or_serious",
                 "casualties", "fatal_casualties", "serious_casualties")}
        gb.append({"scope": scope, "definition": definition, "years": years,
                   "totals": sums, "annual_mean": {k: v / len(rows) for k, v in sums.items()}})
p = t["dft_2016_table_3_8"]
a = t["dft_2016_table_8_1"]
assert p["works_noticing"] + p["works_permit"] == p["works_total"] == sum(a["works"])
assert p["duration_days_noticing"] + p["duration_days_permit"] == p["duration_days_total"] == sum(a["duration_days"])
sm2 = t["dft_street_manager_table_2"]["2023_24"]
sm3 = t["dft_street_manager_table_3"]
assert sum(v for k, v in sm2.items() if k != "total") == sm2["total"]
assert sum(sm3[k] for k in ("no_incursion", "some_incursion", "traffic_management_and_carriageway_restrictions")) == sm3["total"]
us = t["pegula_2003_2010"]
assert us["employed_as_flaggers"] + us["other_occupations"] == us["traffic_control_activity_fatalities"]
n = us["end"] - us["start"] + 1
assumptions = t["paper_values_not_verified_exposure_data"]
car = t["auckland_2018_19"]["corridor_access_requests_approximately"]
answer = {
    "gb_2021_2025": gb,
    "dft_2016": {
        "all_works_mean_duration_days": p["duration_days_total"] / p["works_total"],
        "traffic_control_mean_duration_days": a["duration_days"][2] / a["works"][2],
        "paper_1_5m_minus_source_works": assumptions["gb_annual_opdays"] - p["works_total"],
        "paper_1_5m_minus_source_traffic_control_duration": assumptions["gb_annual_opdays"] - a["duration_days"][2],
        "warning": "Works, elapsed duration days and 8-hour operation-days are different units; these differences do not reproduce the paper's denominator."
    },
    "dft_street_manager_2023_24": {
        "table_3_minus_table_2_works": sm3["total"] - sm2["total"],
        "implied_opdays_per_restricted_work_for_paper_gb_central": assumptions["gb_annual_opdays"] / sm3["traffic_management_and_carriageway_restrictions"],
        "implied_opdays_per_restricted_work_for_paper_gb_range": [v / sm3["traffic_management_and_carriageway_restrictions"] for v in assumptions["gb_range"]],
        "warning": "Reverse arithmetic only. No source supplies these operation-days per work. England is not GB."
    },
    "nz": {
        "implied_national_uplift_times_realised_sites_per_car_times_opdays_per_site": assumptions["nz_annual_opdays"] / car,
        "implied_product_for_range": [v / car for v in assumptions["nz_range"]],
        "stopgo_fraction_of_central_total_assumed": assumptions["nz_stopgo_annual_opdays"] / assumptions["nz_annual_opdays"],
        "fatalities_needed_over_2010_2025_to_support_claim": [v * 16 for v in assumptions["nz_controller_deaths_per_year"]],
        "warning": "No national fatality rate estimated from an incomplete incident search. Exposure factors and ranges are unsupported assumptions."
    },
    "us": {"years": n,
        "activity_deaths_per_year": us["traffic_control_activity_fatalities"] / n,
        "flagger_occupation_deaths_per_year": us["employed_as_flaggers"] / n,
        "other_occupation_deaths_per_year": us["other_occupations"] / n}
}
(ROOT / "calculations.json").write_text(json.dumps(answer, indent=2) + "\n")
print(json.dumps({k: v for k, v in answer.items() if k != "gb_2021_2025"}, indent=2))
