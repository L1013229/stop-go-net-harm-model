# Round 15 ;  count and exposure provenance

**Access date: 28 September 2026 (Pacific/Auckland).** Branch `trr-v1.2-cut`; no manuscript edits by this audit. This audit supplies a new, repeatable GB reconstruction and verifies the US published count. It does **not** recover the original GB query, establish a complete NZ controller-death series, or validate either national exposure denominator.

| Paper value | Finding | Source / repeatable result |
|---|---|---|
| GB head-on injury collisions ≈50/year | **Reproduced approximately:** 50.6; difference +0.6 (+1.2%) | STATS19 2021 to 2025, definition M1 and harmonised roadworks flag below: 253 / 5. |
| GB fatal-or-serious collisions ≈19/year | **Reproduced approximately:** 18.8; difference −0.2 (−1.1%) | Same selection: 94 / 5. These are collisions, not injured people. |
| GB fatal collisions 1.6/year | **Reproduced exactly, numerical value:** 1.6 | Same selection: 8 / 5. Original years/filter remain unknown. |
| GB strict ≈21/year | **Reproduced approximately:** 21.4; difference +0.4 (+1.9%) | Definition S1: 107 / 5. |
| GB loose ≈156/year | **Reproduced approximately:** 153.4; difference −2.6 (−1.7%) | Definition M4: 767 / 5. |
| NZ controller death every 2 to 4 years (0.25 to 0.5/year) | **Not reproducible** | No original observation period or complete eligible case list. Cases and exclusions below. |
| GB 1.5M operation-days/year; 0.9M to 2.5M | **Not reproducible** | DfT publishes works and duration days; no documented conversion to these GB eight-hour operation-days or range. |
| NZ 0.4M operation-days/year; 0.15M to 0.75M | **Not reproducible** | Local approvals are available; national coverage, realised sites and operating duration are missing. |
| US 92 traffic-control-duty deaths, 2003 to 2010; 32 employed as flaggers | **Reproduced exactly from published document** | Pegula (2013), “Working onsite”, paragraph after Table 4. 92 / 8 = 11.5/year; 32 / 8 = 4/year. |
| Associated NZ claims: 175k stop/go days (65k to 630k); roadworker DSI 3 to 4/year | **Not reproducible in this audit** | No source selection/period or exposure arithmetic recovered; they cannot inherit provenance from the cases below. |

## GB: database selection and counts

Sources: [DfT open data][DFT_OPEN], [2025 data dictionary][DFT_GUIDE]. The 15 annual collision, vehicle and casualty CSVs for **2021 to 2025** were downloaded in full; original URLs, timestamps, SHA256 hashes and row counts are in [stats19-downloads.json](trace/stats19-downloads.json). Small roadworks-only extracts retain all source columns and IDs.

**Coverage limit:** annual URLs for 2010 to 2020 returned 404. The current landing page provides annual files for 2021 to 2025 and full-history files; the latter exceed the 500 MB budget (collision file alone ≈1.53 GB). The full-history endpoint did not honour a byte-range request. Thus 2010 to 2020 were **not analysed**, not treated as zero. No claim is made that the closest matching available window identifies the author's original window.

| Selection step | Exact rule |
|---|---|
| Population | GB police-reported personal-injury collisions in each calendar year, 2021 to 2025 inclusive; all road types, urban/rural areas, vehicle types and control types. No damage-only collisions. |
| Roadworks, literal request | `special_conditions_at_site == 4`. |
| Roadworks, harmonised | `special_conditions_at_site == 4 OR carriageway_hazards == 13`. The dictionary maps legacy roadworks code 4 to the 2024 specification's hazard code 13. Using only the legacy field loses newer records. |
| Join | Join collision, vehicle and casualty files on `collision_index`; normalise historic `accident_` column prefixes if encountered. Check all vehicle/casualty row counts against each collision's reported totals. |
| Front impact | Vehicle `first_point_of_impact == 1`. |
| Opposite directions | Both direction values in `1..8` and absolute difference `4` (N/S, NE/SW, E/W, SE/NW). Exclude parked, unknown and missing directions from direction-dependent matches. |
| M1, principal reconstruction | At least one pair of distinct vehicles in the collision has **both front impacts and opposite `vehicle_direction_from` values**. Multi-vehicle collisions allowed; count each collision once. |
| Severity | `collision_severity`: 1 fatal, 2 serious, 3 slight. Fatal-or-serious = codes 1 or 2. Unadjusted recorded severity; casualty severity is a separate count/check. |

M1 with the harmonised roadworks flag:

| Year | All roadworks collisions: literal / harmonised | M1 injury collisions | Fatal | Serious | Slight | Fatal + serious | Fatal casualties |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1,410 / 1,410 | 56 | 2 | 19 | 35 | 21 | 2 |
| 2022 | 1,225 / 1,225 | 53 | 2 | 16 | 35 | 18 | 3 |
| 2023 | 1,225 / 1,225 | 60 | 3 | 17 | 40 | 20 | 3 |
| 2024 | 466 / 1,196 | 46 | 0 | 18 | 28 | 18 | 0 |
| 2025 | 140 / 1,042 | 38 | 1 | 16 | 21 | 17 | 1 |
| **Total** | **4,466 / 6,098** | **253** | **8** | **86** | **159** | **94** | **9** |
| **Annual mean** | | **50.6** | **1.6** | **17.2** | **31.8** | **18.8** | **1.8** |

The casualty join gives **413 injured people: 9 fatal, 112 serious and 292 slight**. Therefore 18.8 is not a DSI-person count, and 1.6 is not the annual number of deaths. Recorded STATS19 serious injury is not an exact MAIS3+ definition.

Definition sensitivity, all using 2021 to 2025 harmonised roadworks:

| Script ID | Head-on proxy | Collisions/year | Fatal + serious/year | Fatal/year |
|---|---|---:|---:|---:|
| S0 | S1 plus both manoeuvres going ahead (legacy 16/17/18 or converted 19) | 13.4 | 5.0 | 0.4 |
| **S1** | Exactly two vehicles; both front; opposite from and to directions; each vehicle's from/to directions also opposite | **21.4** | 7.8 | 0.6 |
| S2 | Exactly two vehicles; both front; opposite from directions | 36.0 | 12.4 | 0.6 |
| **M1** | Any pair; both front; opposite from directions | **50.6** | **18.8** | **1.6** |
| M2 | Any pair; both front; from directions 135°, 180° or 225° apart | 60.8 | 21.8 | 1.6 |
| M3 | Exactly two vehicles; both front; no direction condition | 104.0 | 30.8 | 1.0 |
| **M4** | Any pair; both front; no direction condition | **153.4** | 44.2 | 2.6 |
| L1 | Any pair; at least one front; opposite from directions | 110.2 | 32.8 | 1.6 |
| L2 | Any pair; opposite from directions; any impact points | 125.4 | 35.6 | 1.6 |
| L3 | At least two vehicles; any front impact; no direction condition (nonspecific) | 780.4 | 158.0 | 9.6 |

**Literal-filter sensitivity:** M1 annual collision counts are 56, 53, 60, 21, 3; means **38.6 injury / 13.4 fatal-or-serious / 1.4 fatal**. This literal selection does not reproduce the paper's triple over 2021 to 2025.

[stats19-period-comparison.csv](trace/stats19-period-comparison.csv) compares every contiguous available window of at least three years, all ten definitions and both roadworks flags. M1/harmonised/2021 to 2025 is closest to (50, 19, 1.6) by summed squared relative differences. This is a descriptive provenance search, **not** an independently validated head-on classifier. Opposite approaches and front impacts do not prove those two vehicles struck each other; bends, turns and multi-vehicle events remain possible. No selection identifies PTS or two-way stop/go operation.

Repeat: [stats19_trace.py](trace/stats19_trace.py). Exact collision membership: [stats19-membership.csv](trace/stats19-membership.csv). Every annual/definition/severity result: [stats19-annual.csv](trace/stats19-annual.csv). Join/severity checks: [stats19-qa.json](trace/stats19-qa.json).

## NZ: deaths found and limits of the selection

Main search period: **2010 to 2025**, chosen for this audit; the paper gives no period. The [WorkSafe notification table][WS_TABLE] snapshot contains 414 dated rows, **9 January 2019 to 24 July 2026**, and excludes notifications to other regulators. Its short descriptions have no occupation or flagging-duty field. The [combined fatality dashboard][WS_FATAL] covers January 2011 to August 2025 but also lacks a flagging-duty selector. Neither is a complete controller query.

| Date | Person; place | Duty / inclusion decision | Source |
|---|---|---|---|
| 24 Mar 2011 | Unnamed 55-year-old; Woodlands Rd, northeast of Hamilton | Tarseal-truck strike; roadworker, control duty unknown | [Police release republished][POL_WOODLANDS] |
| 19 Mar 2013 | George Taiaroa; Tram Rd, Ātiamuri | **Confirmed stop/go operator; homicide. Exclude from vehicle-strike deaths.** | [Police, 19 Apr 2013][POL_TAIAROA] |
| 4 Mar 2015 | Unnamed motorcyclist; Island Block Rd, Meremere | **Road user, not an established worker.** Prosecution of a traffic-control contractor is not evidence of controller death. | [WorkSafe court summary][WS_MOTORCYCLIST] |
| 26 Feb 2019 | Dudley Sole Raroa; David Reginald Te Wira Eparaima; Haki Graham Hiha; SH2 Matatā Straights | Three culvert-maintenance workers; no flagging-duty evidence | [Police names][POL_MATATA]; [incident report][NEWS_MATATA] |
| 11 Mar 2019 | Joji Bilo; Ngauranga Gorge, Wellington | Measuring resealing work; runaway works truck; no flagging-duty evidence | [Court reporting][NEWS_BILO]; WorkSafe date |
| 7 May 2019 | Unnamed; Northland | Truck struck a traffic-management vehicle; deceased person's role unknown | WorkSafe snapshot row 383 |
| 13 May 2021 | Christopher Tahitahi; Waikato Expressway | Roadworker struck; control duty unknown. Police says truck; notification says car. | [Police][POL_TAHITAHI]; WorkSafe row 260 |
| **12 Feb 2023** | **Brian Barnes; SH23 roadblock near Cogswell Rd, Raglan** | **Confirmed traffic controller removing cones for a works truck.** Broader traffic-control duty; no evidence of bat use at impact or a public-motorist strike. | [WorkSafe undertaking][WS_ITCL], [§§1.2 to 1.3 PDF][WS_ITCL_PDF]; [employer alert, p.1][FH_BARNES] |
| 15 Jan 2024 | Gabriel Fa’amausili; Abbey Caves Rd, Whangārei | Reseal worker; control duty unknown | [Named incident][NEWS_GABRIEL]; WorkSafe row 136 |
| 19 Mar 2024* | Unnamed; West Coast Rd, Te Kōpuru | Traffic-control foreman reported; specific duty unconfirmed | [Incident/date][NEWS_KOPURU]; WorkSafe row 121; [opinion][NEWS_FOREMAN] |
| May 2024† | Johnathon Walters; Remuera, Auckland | Roadworker; runaway works truck; control duty unknown | [RNZ report via ODT][NEWS_WALTERS]; WorkSafe row 112 |

\* Opinion gives 18 March; same-place incident reporting and WorkSafe give 19 March. Provisionally one event, not two. † 8 May is a tentative match to the WorkSafe Auckland notification; the named report gives only May. These links are not person-ID matches.

The [case ledger](trace/nz-case-ledger.csv) lists the three Matatā victims separately and retains two later, unresolved notification candidates (13 January and 12 May 2026). [worksafe_trace.py](trace/worksafe_trace.py) repeats the broad keyword/industry screen against the frozen [snapshot](trace/worksafe-snapshot.json); it yields 44 candidate rows within 2010 to 2025, **not 44 controller deaths**. [Search scope and decisions](trace/nz-search-log.md) records the criteria and gaps. No controller-specific coronial finding or NZTA/MoT national fatality table was located; [WorkSafe roadside guidance][WS_LIVE] is qualitative.

**No national death rate follows from this incomplete list.** Over a complete 16-year census, 0.25 to 0.5/year would require 4 to 8 eligible deaths. The evidence found does not establish that census, and a missing report cannot be counted as zero. The associated 3 to 4 worker-DSI/year claim is likewise not established by fatality cases.

## Exposure: published statistics and missing arithmetic

These are traceable **candidate source statistics**, not proof that they were the author's inputs. The paper defines an operation-day as eight operating hours.

| Published source and exact statistic | Repeatable arithmetic | What it establishes about the paper's denominator |
|---|---|---|
| [DfT permit evaluation][DFT_PERMIT], Table 3.8, printed p.41/PDF p.43; **England, 2016**. “Works total (no.)”: 694,880 noticing + 813,916 permitted = **1,508,796**. “Total duration (days)”: 3,623,105 + 3,747,029 = **7,370,134**. | 7,370,134 / 1,508,796 = **4.8848 duration days/work**. 1.5M differs from the works count by −8,796 (−0.58%). | Close numerical match to **works**, not operation-days. Possible unit confusion is an inference, not recovered provenance. England, all works and elapsed duration do not match GB traffic-control eight-hour days. |
| [Same evaluation, annexes][DFT_ANNEX], Table 8.1, printed p.58/PDF p.59; **England, 2016**, “Traffic Control” column | **410,395 works; 2,018,405 duration days**; 2,018,405 / 410,395 = **4.9182 days/work**. | This closer activity category still does not give 1.5M operation-days: difference −518,405 duration days. No published derivation of 0.9M to 2.5M was found. |
| [DfT Street Manager evidence MIS0064][DFT_SM], Tables 2 to 3; **England, Apr 2023 to Mar 2024** | Table 2: **2,209,516 actual works**. Table 3: **870,296** works with traffic management/carriageway restrictions. 1.5M / 870,296 = **1.7236 assumed operation-days/work**; range endpoints imply **1.0341 to 2.8726**. | This is reverse arithmetic, not a sourced duration. Table 3 includes HS2 and totals 2,210,304, **788** above Table 2. Permit applications must not be substituted for actual works. |
| [Auckland Transport annual report 2019][AT_2019], highlights, printed pp.3 to 4/PDF p.3; **2018/19** | “We approved around 29,000 corridor access requests, each of which had anywhere from one to 20 Traffic Management Plans (TMPs) attached.” 400,000 / 29,000 = **13.7931**. | To obtain the national denominator, the product **national coverage multiplier × realised sites per approval × eight-hour operating days per site** must equal 13.7931 (range **5.1724 to 25.8621**). None of those factors is supplied. Approvals/TMPs are not observed operation-days. |
| NZ stop/go subset used in controller note: 175k from 400k total | 175,000 / 400,000 = **43.75%** | An implied share only; no source was found for this share or 65k to 630k range. |

All transcribed cells: [table-inputs.json](trace/table-inputs.json). All arithmetic: [calculations.py](trace/calculations.py) → [calculations.json](trace/calculations.json). A defensible exposure query would require realised, deduplicated site operating intervals, geography/year/control-mode selection, and `sum(operating_hours) / 8`. Current published totals do not supply these inputs. Dividing a reproduced numerator by an unverified exposure assumption does not reproduce an observed per-operation-day rate.

## US: exact published count

[Stephen M. Pegula (2013), *Monthly Labor Review*, November, DOI 10.21916/mlr.2013.36][PEGULA]. Locator: **“Working onsite”, paragraph following Table 4 and the backup-alarm paragraph**; not a row of Table 4.

> Workers were flagging or performing other traffic control duties in 92 cases.

> Only 32 of the workers were employed as flaggers

| Selection / calculation | Result |
|---|---|
| US CFOI, 2003 to 2010 inclusive; workers at road-construction sites, struck by vehicles/mobile equipment; article's narrative identification of flagging/traffic-control activity | **92 deaths**, including **32 employed as flaggers** and 60 in other occupations |
| 92 / (2010 − 2003 + 1) | **11.5/year**, within the paper's 10 to 12/year wording |
| 32 / 8; 60 / 8 | **4/year** employed as flaggers; **7.5/year** other occupations |

Footnote 4 identifies the narrative classifications as specially compiled for this analysis, independently reviewed, and not standard official CFOI products. Public microdata do not reproduce this narrative coding here; the **published paragraph is the exact citation**. Do not relabel 92 as a flagger-occupation-only count or a public-motorist-only count. The article supplies no annual split for these 92.

## Reproduction and verification

From the repository root, using the frozen small extracts:

```bash
python3 research/trace/stats19_trace.py
python3 research/trace/worksafe_trace.py
python3 research/trace/calculations.py
```

Download recipe, dependencies, file map and preservation instructions: [trace/README.md](trace/README.md). [Source register](trace/sources.json) gives URLs, access date and document/table locators. [URL checks](trace/url-verification.json) distinguish successful HTTP/content checks from sources read through the browser when raw HTTP returned 403. All cited source contents were checked. The model/manuscript build was not run: this is a standalone provenance audit.

[DFT_OPEN]: https://www.gov.uk/government/statistical-data-sets/road-safety-open-data
[DFT_GUIDE]: https://assets.publishing.service.gov.uk/media/6ab2a71d997a4b2950cced58/dft-road-casualty-statistics-road-safety-open-dataset-data-guide-2025.xlsx
[DFT_PERMIT]: https://assets.publishing.service.gov.uk/media/5ad5f284ed915d32a3a70c07/permit-schemes-evaluation-report.pdf
[DFT_ANNEX]: https://assets.publishing.service.gov.uk/media/5ad5f29440f0b617dca7148e/permit-schemes-evaluation-annexes.pdf
[DFT_SM]: https://committees.parliament.uk/writtenevidence/135172/html/
[AT_2019]: https://at.govt.nz/media/1981078/item-101-attachment-1-open-22-october-2019-annual-report-performance-against-the-2018-19-soi.pdf
[WS_TABLE]: https://data.worksafe.govt.nz/editorial/fatalities_summary_table
[WS_FATAL]: https://data.worksafe.govt.nz/graph/detail/fatalities?accident_type=Vehicle+Incident
[WS_LIVE]: https://www.worksafe.govt.nz/topic-and-industry/road-and-roadside/keeping-healthy-safe-working-road-or-roadside/part-c/19-0-working-near-live-traffic/
[WS_ITCL]: https://www.worksafe.govt.nz/laws-and-regulations/enforceable-undertakings/accepted-enforceable-undertakings/independent-traffic-control-limited/
[WS_ITCL_PDF]: https://www.worksafe.govt.nz/dmsdocument/72900-enforceable-undertaking-independent-traffic-control-limited/latest/
[FH_BARNES]: https://www.wellingtonwater.co.nz/assets/WW-Knowledge-Base-/Health-and-Safety/Red-Safety-Alerts/Red-Alerts/2023/REDNZ23-006-Traffic-Management-at-Road-Closures.pdf
[POL_TAIAROA]: https://www.police.govt.nz/news/release/34843
[POL_TAHITAHI]: https://www.police.govt.nz/news/release/name-release-%E2%80%93-waikato-expressway-crash
[NEWS_KOPURU]: https://www.1news.co.nz/2024/03/19/pedestrian-dies-after-being-hit-by-car-in-northland/
[NEWS_FOREMAN]: https://www.nzherald.co.nz/northern-advocate/news/john-williamson-northland-road-fatalities-at-road-works-has-traffic-management-soul-searching/HQYSHAWNYNHGFEM5MPRDGDBCM4/
[NEWS_GABRIEL]: https://www.nzherald.co.nz/nz/police-name-roadworker-killed-in-workplace-incident-in-abbey-caves-whangarei/EPXFHYRFE5DL7NGOMFU5PYS7MM/
[NEWS_BILO]: https://www.1news.co.nz/2022/09/13/faulty-handbrake-on-truck-most-likely-killed-road-worker-court-told/
[NEWS_WALTERS]: https://www.odt.co.nz/news/national/police-wanted-driver-off-the-road-before-dodgy-truck-killed-roadworker-ufjn7nc5
[NEWS_MATATA]: https://www.odt.co.nz/news/national/three-killed-horror-crash-worked-same-firm
[POL_MATATA]: https://www.police.govt.nz/news/release/name-release-fatal-crash-near-whakatane
[POL_WOODLANDS]: https://www.infonews.co.nz/news.cfm?id=65251
[WS_MOTORCYCLIST]: https://www.worksafe.govt.nz/laws-and-regulations/prosecutions/court-summaries/broadspectrum-new-zealand-limited/
[PEGULA]: https://www.bls.gov/opub/mlr/2013/article/an-analysis-of-fatal-occupational-injuries-at-road-construction-sites-2003-2010.htm
