# Round 15 trace package

Audit date: 28 September 2026, Pacific/Auckland. Read `../traceability.md` first.

## Offline reproduction

Python 3.10+ and `requests` for `stats19_trace.py`; the other two offline scripts use the standard library. Run from the repository root:

```bash
python3 research/trace/stats19_trace.py
python3 research/trace/worksafe_trace.py
python3 research/trace/calculations.py
```

These rewrite only derived outputs within this directory. They do not touch the model, manuscript or Git. Run without Python's `-O`: the assertions validate collision joins, row counts, severities and source-table sums.

From `research/trace/`, run `sha256sum -c SHA256SUMS` to check the public package.

## Fresh source download, preserving this audit

Copy the package before refreshing: live official files and WorkSafe notifications may be revised. Compare the original CSV hashes in `stats19-downloads.json` before expecting identical results.

```bash
cp -a research/trace /tmp/round15-recheck
python3 /tmp/round15-recheck/stats19_trace.py --download --start 2010 --end 2025 --cache /tmp/round15-fresh-stats19 --max-bytes 300000000
python3 /tmp/round15-recheck/worksafe_trace.py --refresh
python3 /tmp/round15-recheck/calculations.py
```

`stats19_trace.py --download` probes annual URLs, downloads available CSVs, hashes their original bytes, gzip-compresses the raw cache and saves only roadworks rows beside the script. Original collision/vehicle/casualty fields are retained; `accident_` column prefixes are normalised to `collision_`. It does not download the multi-gigabyte full-history files. At this audit's source version, 2010 to 2020 annual URLs returned 404 and 2021 to 2025 succeeded. Missing years are not zero counts. Delete any incomplete raw cache file before retrying a failed download; a refreshed manifest describes that invocation, so preserve the original manifest.

WorkSafe refresh also requires `beautifulsoup4`. It reads the public page's `#app[data-props]` JSON, not an authenticated API. Candidate screening is deliberately broad; names/duties in `nz-case-ledger.csv` are separately reviewed against source documents. A keyword match never establishes a controller fatality.

`verify_sources.py` requires `requests`, `beautifulsoup4` and `PyMuPDF`. It checks source URLs/content, using an existing locally downloaded PDF/XLSX when present; otherwise it streams a bounded GET (20 MB/file, 80 MB/run). Some sites reject raw HTTP with 403 although the linked text was readable through the browser. Those two outcomes are recorded separately; the saved browser observation is dated evidence, not a fresh automated check. The script does not refetch the 15 STATS19 files. Review its JSON if rechecking on another date.

## Files

| File(s) | Purpose |
|---|---|
| `roadworks-{collision,vehicle,casualty}-2021.csv` … `-2025.csv` | Frozen official-source subsets; all retained roadworks collisions and their joined vehicles/casualties |
| `stats19-downloads.json` | Each annual source URL, access timestamp, HTTP result, full-source SHA256, byte and row counts; failed-year probes |
| `stats19-membership.csv` | Collision-level membership for all ten head-on proxies and literal/harmonised roadworks |
| `stats19-annual.csv`, `stats19-period-comparison.csv` | Counts by year/severity/definition; all available contiguous windows of at least three years |
| `stats19-definitions.json`, `stats19-qa.json` | Filter definitions and join/severity validation |
| `dft-data-guide-2025.xlsx`, `*-selected.csv` | Official codebook and relevant code/conversion rows with workbook row numbers |
| `worksafe-snapshot.json` | Small public table snapshot with provenance and scope notes, including all rows so the screen can be rerun |
| `worksafe-candidates.csv`, `worksafe-selection.json` | Exact screening output, regexes, coverage and excluded invalid-date row |
| `nz-case-ledger.csv`, `nz-search-log.md` | Case evidence, exclusions, uncertain links and search limits |
| `table-inputs.json`, `calculations.json`, `published-extracts.md` | Published count transcriptions, calculations and short source excerpts |
| `sources.json`, `url-verification.json` | Source URLs, locators, access date, and verification method/results |
| `SHA256SUMS` | Public trace package integrity |

## Download budget and scope

The 15 complete annual STATS19 CSVs transferred **255,105,210 bytes** (255.1 MB, decimal); compressed temporary storage is about 54 MiB. The four main PDFs total **17,003,265 bytes**; the source verifier transferred a further **5,581,521 bytes** including the employer alert and HTML. The data guide is about 85 KB. Smaller discovery pages/probes were additional; the audit stayed below 500 MB. Full-history downloads were not attempted after size checks/range refusal. Only small extracts and the data guide are retained here; no large raw download is placed in the repository. The fresh-download recipe is for a later rerun, not an additional download made during this audit.

Statistics support the populations and units actually selected. GB recorded serious injury is not a direct MAIS3+ measure; any-vehicle-pair front/opposed geometry is a proxy, not a coded head-on collision type. The exposure numbers and NZ national rate remain unverified. The already documented NZ CAS head-on query was outside the four requested checks and was not rerun.
