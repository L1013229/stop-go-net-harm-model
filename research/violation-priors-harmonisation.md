# Stop-Violation Rate Harmonisation for Two-Way Stop/Go (One-Lane) Work-Zone Model

**Purpose.** Extract exact violation definitions and counts from primary texts, harmonise to a common
**per-facing-vehicle** probability (facing = vehicle arrives while the stop indication / STOP paddle / red is
displayed to it), and construct priors for `r_v0` (human flagger control) and `r_v1a` (unattended portable
traffic signal, PTS). Prepared 2026-07-05. All intervals are Jeffreys 95% unless noted.

**Target metric.** r = P(a facing vehicle enters the one-lane section against the stop indication, driver-initiated).

**Definition classes** (per task brief):
- **A** — vehicle crosses stop line during red/stop indication and *proceeds through* the control point;
- **B** — crosses during red but stops downstream / enters on red-onset (end-of-amber, dilemma-zone);
- **C** — cycle-level metric (any violation in cycle / violations per cycle).

---

## 1. Source extractions

### 1.1 TTI 0-6407-1 — Finley, Ullman, Trout & Park (Oct 2011 / pub. Jan 2012), Texas AFAD field study
Source text: `tti-0-6407.txt` (saved full text). Field study = Part 1, pp. 57–70 (report pages).

**Violation definition (exact).** The report never gives a one-sentence definition in the results chapter; it is
assembled from three passages:
- Experimental design (p.59): *"The primary measure of effectiveness for the field studies was whether or not
  the first vehicle in the queue complied with the treatment's (flagger or AFAD) instructions."* and (p.60)
  *"researchers observed the compliance of the first vehicle in the queue under the stop condition. If the first
  vehicle did not comply with the treatment's instructions, researchers described the non-compliance and noted
  the actions of the other vehicles in the queue."*
- Recommendations (p.127): violations = motorists who *"misunderstand the directions provided by AFADs and
  enter the lane closure under the stop condition"*.
- Crucially (p.127): *"for all the documented violations the flagger was able to stop the motorist before they
  encountered oncoming traffic"* — i.e., events are **attempted proceed-throughs** (class A attempts), most
  intercepted downstream by the supervising flagger. Discussion (p.69) describes the dominant mechanism:
  motorist approaches stop face, hesitates, then **proceeds to catch up with the back of the departed queue**
  (no-gate-arm treatments only).
- **Class: A-attempt, counted per stop cycle (C-format reporting), scored on the first vehicle in queue.**

**Stop-cycle definition.** One stop condition event; researchers logged *"the arrival and departure times of the
first vehicle in the queue (i.e., length of the stop condition)"*. Stop cycle duration: <1 to 16 min, mean 1–2 min
(Table 21). "Stop period" and "stop cycle" used interchangeably (102 h / 1,708 stop periods overall incl. treatments
later dropped; Table 22 subtotals: 97.8 h / 1,673 cycles).

**Rate formula (Table 22 note a):** violations / stop cycles × 100.

**Table 22 — Field Study Violation Rate Statistics (verbatim numbers):**

| Treatment | Hours | Stop cycles | Violations | per 100 cycles |
|---|---|---|---|---|
| Flagger | 13.7 | 294 | 0 | 0.0 |
| Red/Yellow lens AFAD (gate arm) | 19.4 | 367 | 8 | 2.2 |
| Stop/Slow AFAD, WAIT ON STOP (WOS), no gate | 20.7 | 360 | 24 | 6.7 (sig. > R/Y) |
| Stop/Slow AFAD, WOS + gate arm | 13.0 | 198 | 8 | 4.0 |
| Stop/Slow AFAD, WOS/GOS + gate arm | 18.0 | 190 | 6 | 3.2 |
| Stop/Slow AFAD, Alt. signs + gate arm | 13.0 | 264 | 10 | 3.8 |
| **Total AFADs** | **84.1** | **1,379** | **56** | **4.1** |

**Vehicles per cycle (Table 21, avg (sd) [min–max]):** Flagger 2 (1.8) [1–12]; R/Y AFAD 2 (1.9) [1–20];
S/S WOS 3 (2.5) [1–16]; WOS+gate 6 (7.5) [1–46]; WOS/GOS+gate 7 (11.5) [1–60]; Alt+gate 6 (6.1) [1–33].

**Sites/conditions.** 17 observation sites, two-lane two-way farm-to-market & state highways (Bryan, Lufkin,
Paris, San Antonio districts, TX); mostly rural; 2009 AADT 220–5,100 vpd (55% < 2,000); lane closures ~300 ft–1 mi
(75% < 2,500 ft); speed limits 35–70 mph. AFADs were **attended**: the operating flagger stood near the work-area
midpoint (visible from both ends, not at the device); all treatments had centreline cones; gate-arm treatments
as marked. No-gate S/S evaluations were terminated early on safety grounds (non-compliance). Pilot cars: not part
of the studied treatments (only 4% of flagger-condition survey respondents mentioned proceeding on pilot-car
arrival — some sites may have operated one; not documented as a treatment variable). Volume/violation trend:
violation rate *fell* with AADT and *rose* with work-zone length (Figures 18–19; researchers attribute low-volume
effect to locals judging conflict risk low).

### 1.2 Minnesota DOT 1999 AFAD datapoint (from 0-6407-1 lit review, p.14, citing AUTOFLAGGER Final Report, MnDOT 2005)
*"Motorist behavior data were collected during that same year [1999] at four work zones where the stop/slow AFADs
were used. Over a 15-hour period, traffic was stopped 313 times during which five violations occurred. Thus, a
motorist entered the open travel lane under the stop condition approximately every 3 hours, or 63 stop periods."*
- Definition: **entered the open travel lane under the stop condition** (class A-attempt, per stop event = class C format).
- 5/313 = **1.6 per 100 stop cycles**. No queue-size, speed or volume data for these observations; MnDOT's
  subsequent usage limits (ADT < 1,500 vpd, closure ≤ 800 ft) indicate the operating envelope. No flagger
  comparison data collected. AFAD attended (flagger operating nearby, per MnDOT protocol of the era).

Also in the same lit review (context, Virginia DOT 2006 stop/slow AFAD): 59 h operation, ADT 100–1,600; 6
violations in first four deployments (*"motorists entered the open travel lane when the stop face was displayed"*,
most stopped then proceeded slowly — stale-stop proceed-throughs, class A), 1 violation at the next five sites,
0 in a later 32 h. No cycle counts → not convertible, qualitative support only.

### 1.3 Kansas PTS study — Schrock, Patil & Fitzsimmons, TRR 2555-09 (2016); K-TRAN full report (Patil/Schrock/Fitzsimmons/Sarikonda), fetched via Wayback copy of ROSA-P dot/30782 (`ktran-wb.pdf`, 209 pp.)
**Context.** Four long rural two-lane work zones in Kansas, **all operated with pilot car escort**; PTS = trailer
signal at each end. Data 7/30–8/28/2014, ~164 h of video (site totals 50.2/40.7/48.0/24.6 h). Sites: US-56 Osage Co.
(30–60 mph, AADT 1,010–3,320, zone 2–2.5 mi); K-31 Melvern (30–55 mph, AADT 490–585, 2–2.5 mi); US-24 Beloit
(45–65 mph, AADT 2,750–3,890, 2.2–2.8 mi); US-50 Newton (65 mph, AADT 4,700–5,130, 2.6 mi). AADT written
"total/heavy" (e.g., 1,660/110). PTS timing: min green 30 s, max green 60 s (US-50: 240 s), gap-to-red 5 s (US-50: 12 s).
Mean first-vehicle wait (≈ red experienced by queue head): 8.3–9.6 min by condition (Table 5.1). Cycles analysed:
flagger-only 108, PTS+flagger 271, PTS-only 398 → ≈7.4–7.5 vehicles/cycle.

**Violation definitions (exact, report §5.3):**
- Flagger-only: *"an event when a vehicle was waved through by a flagger to enter the work zone and/or traveled in
  the direction of the work zone with no consent from the flagger and without being escorted by a pilot car."*
- PTS (±flagger): *"an event when a vehicle entered the work zone and/or traveled in the direction of the work zone
  when the signal was displaying a red indication."* → **class A (proceeds toward/through the zone unescorted).**
- RLR% = RLR vehicles / **total vehicles observed** in the period × 100 (Eq. 5.1) → per-vehicle metric, denominator
  includes green-arrival (non-facing) vehicles.
- Typology: (a) follow already-departed queue on fresh red; (b) leave a stopped queue on red; (c) disregard signal
  at speed; (d) flagger-sanctioned: (d-1) waved through to follow departed queue, (d-2) entered with flagger's
  consent unescorted, (d-3) disregard flagger's STOP paddle.

**Counts (Tables 5.4–5.9):**

| Condition | Vehicles | Violations | % | Composition |
|---|---|---|---|---|
| Flagger only | 814 | 9 | 1.1 | **all 9 = type d-2 (flagger-consented unescorted entry); 0 driver-initiated** |
| PTS + flagger (excl. Beloit intersection confound) | 3,779 | 52 | 1.3 (report: 1.3) | 47 waved-through (d-1), 3 leave queue, 2 disregard flagger → **5 driver-initiated (0.13%)** |
| PTS + flagger (all data) | 4,349 | 93 | 2.1 | Beloit 4-leg intersection excluded from tests |
| PTS only | 2,944 | 92 | 3.1 | 36 follow departed queue (39%), 44 leave stopped queue (48%), 12 disregard (13%) — all driver-initiated |

Flagger-only site detail: 0/157, 2/363, 7/102 (K-31 — all consented), 0/192. Test of proportions (one-tail z,
α=0.05): flagger < PTS+flagger (p<0.001), flagger < PTS-only (p<0.001), PTS+flagger < PTS-only (overall sig.).
Weather cost the US-50 flagger-only day → Cases 1–2 use sites 1–3 (814 vs 805 / 2,150 vehicles).

**Lit-review bonus datapoints extracted from the same report (report-level, not primary here):**
- Carlson et al. (2015), TX, PTS ± flagger with pilot car, 8 sites, AADT 470–2,800, 55–75 mph, closures 0.41–1.42 mi:
  ~**3% of drivers** non-compliant in both conditions, no significant with/without-flagger difference.
- Finley et al. (2015), Ohio District 11, 15 lane-closure zones, AADT 520–9,230, closures 700–3,430 ft: PTS
  **47.1 violations/100 stop cycles**, 99% at end of green following the visible departed queue (mean green 39 s;
  36% of cycles queue did not clear). Flagger significantly lower (value not given in this summary).
- Ullman & Levine (1987), TX fixed-time portable signals, 3 sites 600–10,000 ADT: noncompliance flagged
  qualitatively; no rate given.

### 1.4 Yousif, Alterawi & Henson (2014), AAP 66:147–157, DOI 10.1016/j.aap.2014.01.021
Full text paywalled (ScienceDirect/Worktribe Cloudflare-blocked); **abstract extracted verbatim via Semantic
Scholar**; PubMed 24531116 concurs.
- Setting: **six urban shuttle-lane roadworks sites, Greater Manchester, UK**; >25 h video; ≈1,500 signal cycles;
  portable/temporary two-way signals (fixed-time and vehicle-actuated); single-carriageway urban network.
- Metric (verbatim): *"around 30% of cycles were violated where drivers cross the stop line on the onset of amber
  and red (18.9% pass through amber and 11.3% run through red lights)."*
- Reading: **11.3% = share of cycles with ≥1 red-light-running vehicle** (class C). 18.9% = cycles with amber
  crossing. (18.9 + 11.3 ≈ 30 supports the cycle-share reading; the full text was not accessible to verify whether
  multiple violators per cycle were counted once — flagged.)
- RLR categories: dilemma zone, dilemma-zone follower, single violation, group violations → composition includes
  **red-onset (class B) crossings**, not only stale-red defiance.
- Non-compliance stated to be higher than at permanent signalised junctions.

### 1.5 Bonneson & Zimmerman, TTI 0-4196-2 (Sept 2004) — permanent-signal benchmark
Full text fetched (`tti-0-4196-2.pdf/.txt`).
- Data: 13 signalised intersections (26 approaches), TX; 6 h per approach; **11,266 cycles; 170,905 vehicles;
  595 red-light violations**. Approach flow 59–1,872 veh/h (mean 637); cycle 47–161 s (mean 92); yellow 3.2–5.3 s;
  85th-pct speeds 32–60 mph.
- Definition (exact): vehicles that *"entered the intersection (as defined by the stop line) after the change in
  signal indication from yellow to red"* → **class A at red onset** (end-of-phase proceed-throughs; stale-red
  entries not the measured phenomenon).
- Rates as published: **3.5 violations/1,000 vehicles** (0.35%) and **0.9 per 10,000 veh-cycles**. Heavy vehicles
  0.83% vs cars 0.32%.
- **Reconciling the 0-6407-1 citation:** 0-6407-1 cites this source as "5.3 violations per 100 stop cycles". The
  report itself never prints that number; it is reproduced by 595/11,266 = **5.28 ≈ 5.3 violations/100 cycles**.
  (Beware a live trap: the same report quotes Baguley (1988, UK) at an unrelated but numerically identical
  **5.3 violations per 1,000 vehicles**.) The citation is therefore a derived, unit-converted figure — legitimate,
  but per-cycle comparisons between B&Z (≈16 arrivals/cycle) and TTI AFAD stop cycles (2–7 queued vehicles/cycle)
  are volume-inconsistent; per-vehicle comparison is the defensible one (0.35% vs AFAD ≈1%).

---

## 2. Harmonisation to per-facing-vehicle rates

**Facing-vehicle definitions used.** For stop/go one-lane control, every queued vehicle arrived while the stop
indication faced it → facing count/cycle = queue size. For per-total-vehicle metrics (Kansas), facing share =
fraction of observed vehicles arriving on red, `f_red`.

**Conversion assumptions (all flagged):**
1. **TTI/MN (cycle-based):** r = violations / (cycles × mean queue). Assumes (i) mean queue = mean facing
   vehicles per cycle; (ii) all violations captured (protocol scored the first vehicle; mid-queue pull-outs — Kansas
   type (b), 48% of PTS-only events — would have been logged only qualitatively). Direction of bias: **TTI/MN
   per-facing rates may understate by up to ~2×** in no-gate conditions; gate arm + cones physically suppress
   type-(b) at gated treatments.
2. **Kansas (per-total-vehicle):** r = RLR% / f_red. With 8.3–9.6 min mean first-vehicle waits, green 30–240 s,
   ≈7.4 vehicles/cycle and pilot-car cycles of ~10–20 min, most arrivals face red: **f_red = 0.85 [0.70–0.95]**.
3. **Yousif (cycle-share):** mean red-runners/cycle λ = −ln(1−0.113) = 0.12 (Poisson; ≈0.113 if strictly ≤1
   counted/cycle); facing vehicles/cycle **n̂ = 6 [4–8]** (urban single carriageway, ~60 cycles/h observed,
   both directions; no queue data published). r = λ/n̂.
4. **B&Z benchmark:** left per-vehicle (0.35%); "facing" conversion not meaningful because violators
   overwhelmingly arrive during yellow/red-onset, not while queued on stale red.

**Harmonised table (Jeffreys 95% CI on counts; conversion uncertainty separate):**

| Source / condition | Class | Raw | Facing denominator assumption | r per facing vehicle (central [CI]) | Conversion uncertainty |
|---|---|---|---|---|---|
| TTI flagger (attended, TX rural) | A-attempt/C | 0/294 cycles | 294×2 = 588 | **0.0004 [0–0.0043]** (0 observed; rule-of-3 up 0.0051) | queue sd large; ±2× |
| Kansas flagger-only, driver-initiated | A | 0/814 veh | 814×0.85 = 692 | **0.0003 [0–0.0036]** | f_red ±; all-events variant below |
| Kansas flagger-only, incl. flagger-consented | A+sanctioned | 9/814 | ÷0.85 | 0.0131 [0.006–0.024] | definitional variant |
| Kansas PTS+flagger (excl. Beloit) | A | 52/3,779 | ÷0.85 | 0.0162 [0.012–0.021] | 90% were flagger-waved (d-1) |
| Kansas PTS+flagger, driver-initiated | A | 5/3,779 | ÷0.85 | **0.0016 [0.0006–0.0034]** | — |
| **Kansas PTS-only (unattended, pilot-car zone)** | A | 92/2,944 | ÷0.85 | **0.037 [0.030–0.045]**; f_red span 0.033–0.045 | best primary anchor |
| Yousif UK urban temporary signals | C→A/B mix | ≥1 red-run in 11.3% of ~1,500 cycles | λ=0.12, n̂=6 [4–8] | **0.020 [0.015–0.030]** | n̂ assumed; incl. red-onset events |
| TTI R/Y lens AFAD (attended, gate) | A-attempt | 8/367 cycles | 367×2=734 | 0.011 [0.005–0.020] | AFAD family |
| TTI S/S AFAD WOS no gate | A-attempt | 24/360 | 360×3=1,080 | 0.022 [0.015–0.032] | AFAD family |
| TTI S/S gated (3 variants pooled) | A-attempt | 24/652 | ≈4,100 | 0.0045–0.0067 | AFAD family |
| TTI all AFADs | A-attempt | 56/1,379 | ≈5,916 | 0.0095 [0.007–0.012] | AFAD family |
| MN 1999 S/S AFAD | A-attempt | 5/313 cycles | q̂=2 [1.5–3] | 0.008 [0.005–0.011 central span] | queue unreported |
| Carlson 2015 TX PTS±flagger (lit) | A | ~3% of drivers | ÷0.85 | ≈0.035 | report-level only |
| Finley 2015 Ohio PTS (lit) | A/C | 47.1/100 cycles | q̂=6 [4–8] | ≈0.079 [0.059–0.118] | gross rate; 99% end-of-green queue-following |
| B&Z permanent signals (benchmark) | A at red onset | 595/170,905 veh; 5.28/100 cycles | n/a | 0.0035 per **all** vehicles | not facing-comparable |

Ordering (per facing vehicle): **flagger ≈ 0 (≤0.004) < gated S/S AFAD 0.005–0.007 < MN AFAD ≈0.008 < R/Y AFAD 0.011
< ungated S/S AFAD 0.022 ≈ UK temporary signals 0.020 < unattended PTS 0.033–0.045 < Ohio PTS 0.06–0.12.**
A clean monotone human-presence/physical-barrier gradient; AFADs sit between flagger and unattended PTS, as expected
for attended devices → good transferability support for treating `r_v1a` > AFAD rates > `r_v0`.

---

## 3. Prior construction

Rules applied (from task): ≥2 independent settings → range [min, max] of central estimates widened one step of the
same order each side; log-uniform if span > 1 order else triangular; single source → triangular at half/double.
"One step of the same order" operationalised as ± 1×10^floor(log10(endpoint)) — **judgement call JC-1**.

### r_v0 — human flagger control (driver-initiated violation per facing vehicle)
Evidence: two independent settings, **both zero-event**: TTI TX 0/588 facing (13.7 h, 294 cycles); Kansas 0/692
facing-adjusted (all nine recorded "violations" were flagger-consented entries, none defiance; two disregard-flagger
events existed only in the PTS+flagger condition, 2/3,779). Centrals (Jeffreys medians): 3.9×10⁻⁴, 3.3×10⁻⁴.

- **Rule-strict prior:** range [3.3, 3.9]×10⁻⁴ → widened [2.3, 4.9]×10⁻⁴; span ≪ 1 order → **Triangular(2.3×10⁻⁴,
  mode 3.6×10⁻⁴, 4.9×10⁻⁴)**. **Flagged as overconfident (JC-2):** with zero events the "central estimate" is a
  prior-artefact and the rule's widening (±1×10⁻⁴) is far narrower than sampling uncertainty (95% uppers
  3.6–4.3×10⁻³).
- **Recommended (adjusted) prior:** pool the zero-event settings (0/1,280 facing; exchangeability of TX/KS rural
  flagger operations — JC-3): Jeffreys median 1.8×10⁻⁴, 95% upper 2.0×10⁻³ →
  **r_v0 ~ Triangular(min 0, mode 1.8×10⁻⁴, max 2.0×10⁻³)**.
- **Definitional sensitivity (JC-4):** if the model's r_v0 must count flagger-sanctioned unescorted entries
  (consent/wave-through) as violations — arguably a *control* failure rather than a *compliance* failure —
  use Kansas all-events: r_v0′ ≈ 1.3×10⁻² [0.6–2.4×10⁻²]. This choice moves r_v0 by ~two orders of magnitude
  and dominates every downstream ratio.

### r_v1a — unattended PTS (per facing vehicle)
Evidence settings: (1) **Kansas PTS-only 3.7×10⁻²** (primary, n=2,944, facing-adjusted); (2) **Yousif UK urban
temporary signals 2.0×10⁻²** (assumption-heavy conversion); (3) Carlson 2015 TX ≈3.5×10⁻² (report-level);
(4) Finley 2015 Ohio ≈7.9×10⁻² (report-level, gross). Including (3)–(4) is **JC-5** (they were extracted from the
K-TRAN lit review, not primary texts; they add setting diversity: with/without pilot car, short/long zones).

- Centrals {2.0, 3.5, 3.7, 7.9}×10⁻² → range [2.0, 7.9]×10⁻²; widened one step of order 10⁻² each side →
  [1.0, 8.9]×10⁻²; span < 1 order → triangular. Mode set at the best primary estimate (Kansas 3.7×10⁻²) rather
  than mid-range (**JC-6**).
- **Proposed: r_v1a ~ Triangular(min 1.0×10⁻², mode 3.7×10⁻², max 8.9×10⁻²).**
- Two-source (task-named only) variant: [2.0, 3.7]×10⁻² → widened [1.0, 4.7]×10⁻² →
  Triangular(1.0×10⁻², 3.7×10⁻², 4.7×10⁻²) — use if report-level evidence is inadmissible.
- Composition note: at unattended PTS ~87% of violations are queue-related (follow departed queue 39% + leave
  stopped queue 48%); outright disregard-at-speed is only ~13% (0.4–0.5% of facing vehicles) — relevant if the
  model separates conflict-exposure by violation type (JC-7).

### AFAD family (transferability evidence, attended devices — not a prior input)
Per facing vehicle: gated S/S 0.0045–0.0067; R/Y lens 0.011; ungated S/S 0.022; pooled 0.0095 [0.007–0.012];
MN 1999 ≈0.008 [0.005–0.011]; VA 2006 qualitative (7 events/91 h, ADT 100–1,600). Attended-device rates fall
strictly between r_v0 and r_v1a in every setting → supports the interpolation logic and suggests human presence
(even remote) plus physical barrier each buy roughly a halving-to-quartering of the violation rate.

### Implied flagger:PTS ratio
- Driver-initiated basis (recommended definitions): central 3.7×10⁻² / 1.8×10⁻⁴ ≈ **200×**; at the extremes
  (r_v0 at its 95% upper 2.0×10⁻³ vs r_v1a lower 1.0×10⁻²) ≈ **5×**; unbounded above as r_v0 → 0.
  Report as **≥5×, central ~20–200×**.
- All-events basis (flagger-sanctioned entries counted): 3.7×10⁻² / 1.3×10⁻² ≈ **2.8×** [~1.5–7×] — matches the
  naive 3.1%/1.1% = 2.8 from the abstracts.

---

## 4. Judgement-call register

| # | Call | Basis / alternative |
|---|---|---|
| JC-1 | "One step of same order" = ±1×10^floor(log10(endpoint)) | Could read as ×/÷2 or half-order; stated rule ambiguous |
| JC-2 | Rule-strict r_v0 prior rejected as overconfident for zero-count data | Zero-event centrals are prior artefacts; widening ≪ sampling CI |
| JC-3 | Pooling TTI+Kansas flagger zero-events | Exchangeability: both US rural two-lane; Kansas has pilot car + long zones, TTI short zones |
| JC-4 | r_v0 defined as driver-initiated defiance; flagger-consented unescorted entries excluded | If model treats any unescorted entry as hazard exposure, use r_v0′ ≈ 1.3×10⁻²; two-order swing |
| JC-5 | Carlson/Ohio (lit-review, report-level) admitted into r_v1a range | Primary texts not fetched; numbers as summarised in K-TRAN report |
| JC-6 | r_v1a mode at Kansas (3.7×10⁻²), not mid-range | Largest primary n; alternative mid-range mode 4.5×10⁻² |
| JC-7 | Violation types pooled into single r_v1a | 87% queue-related vs 13% disregard have different conflict exposure |
| JC-8 | TTI facing denominator = cycles × mean queue | First-vehicle-scored protocol may miss mid-queue pull-outs → rates could understate ≤2× (no-gate treatments) |
| JC-9 | Kansas f_red = 0.85 [0.70–0.95] | Derived from wait/green/cycle structure, not measured |
| JC-10 | Yousif 11.3% read as % of cycles with ≥1 red-run; λ=0.12; n̂=6 [4–8] facing/cycle | Full text inaccessible (paywall/Cloudflare); abstract wording "30% of cycles were violated" supports cycle-share; includes red-onset (class B) events → overstates stale-red defiance |
| JC-11 | MN queue size q̂=2 [1.5–3] assumed | Unreported; MnDOT envelope ADT<1,500 |
| JC-12 | B&Z used as benchmark only; "5.3/100 cycles" confirmed derived (595/11,266=5.28), not the report's headline metric | Numerically identical Baguley 5.3/1,000-vehicles figure is an unrelated trap; B&Z RLR is red-onset, denominator all vehicles |
| JC-13 | Kansas Beloit intersection data excluded (following authors) | Their stated protocol non-compliance; raises PTS+flagger to 2.1% if included |

## 5. File/evidence trail
- TTI 0-6407-1 full text: `scratchpad/tti-0-6407.txt` (Table 22 ≈ report p.64; definitions pp.59–60, 127; MN p.14; VA pp.14–15).
- K-TRAN report (ROSA-P dot/30782 via Wayback): `scratchpad/ktran-wb.pdf` + `ktran.txt` (definitions §5.3 pp.45–47; Tables 5.4–5.9; sites Tables 4.2–4.8; wait Table 5.1).
- TRR 2555-09 abstract: workzonesafety.org publication page (verbatim); DOI 10.3141/2555-09 paywalled.
- Yousif 2014 abstract: Semantic Scholar API (DOI 10.1016/j.aap.2014.01.021); PubMed 24531116. Full text not accessible.
- Bonneson & Zimmerman 0-4196-2: `scratchpad/tti-0-4196-2.pdf` + `.txt` (Tables 4-3/4-4, pp.4-5–4-7).
