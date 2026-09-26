# Clearance-interval design basis (evidence for `v_clear_kmh`, `clear_buffer_s`, `t_confirm_s`)

**Correction record (2026-07-09).** An earlier version of this file claimed New Zealand and
Australia specify no all-red clearance for portable traffic signals. That was wrong, and the
error was ours: the sweep read CoPTTM Section C (static operations) when portable-signal
timing lives in Section B (equipment). The owner challenged the claim and named the correct
document. Both jurisdictions specify the all-red, and the corrected sources make the model's
clearance-margin mechanism BETTER evidenced, not worse. Primary-source captures:
`/tmp/.../scratchpad/ttm_specs/` (session artefacts); quotes below are from the documents.

Every jurisdiction that specifies the all-red sizes it from the distance between the stop
lines at a conservative assumed clearance speed, in stepped bands that round upward. That
margin over the operating transit is the protection an onset violator inherits, and it is why
the model separates the clearance interval from the transit time.

## New Zealand — M23 Appendix F (formerly CoPTTM Section B5.3.5)

**NZTA M23:2022 Appendix F, §6.3 "Portable traffic signals — timing of signal displays"**
(content carried verbatim from CoPTTM Part 8 Section B, clause B5.3.5, 4th ed. Nov 2018):

> "The length of the all-red period is a function of the length of the worksite, site
> conditions and the average speed of vehicles through the worksite... The all-red time must
> be at least five seconds. The all-red times recommended for straight level worksites are
> given in Table 2."

Table 2 (worksite length = distance between the signal limit lines): <50 m -> 5 s; 50-99 ->
10 s; 100-149 -> 15 s; 150-199 -> 20 s; 200-249 -> 25 s; 250-300 -> 30 s. The table states
no assumed speed; the stepped structure (5 s per 50 m) implies about 10 m/s (~36 km/h) at
each band's upper edge — an arithmetic inference from the table, not a stated figure. Fixed
yellow 4 s; minimum green 6 s; the controller must provide a variable all-red (§6.1(a)(v)).

## New South Wales — TCAWS Appendix B (mandatory appendix)

**TfNSW, Technical Manual: Traffic Control at Work Sites (TCAWS), 20.346, Issue 6.1,
28 Feb 2022 (as amended by TD 00003:2022), Appendix B §B.2.8:**

> "All red time — Measure the distance between the stop lines at each traffic signal. Select
> an appropriate all-red time from Table B-5 or Table B-6 depending on the minimum clearance
> speed is 20 km/h or 40 km/h respectively."

Tables B-5/B-6 run from 2 s (shortest band) to 100 s (525-575 m at 20 km/h; 1050-1150 m at
40 km/h). The assumed clearance speeds are STATED: about 20 km/h (B-5) and about 40 km/h
(B-6). A worked example (§B.2.9) selects 25 s for a 160 m site at 20 km/h clearance speed.

## Equipment standard — AS 4191

AS 4191 is an equipment-capability standard, not a clearance-computation method: the
controller must provide a pre-selectable variable all-red in the range 2 to 100 s (per
TfNSW TSI-SP-049 Issue 2.0, 2021, quoting the controller requirements). The SELECTION method
is jurisdiction-supplied: M23 Appendix F in NZ, TCAWS Appendix B in NSW.

## United Kingdom and United States (unchanged from the earlier round, re-verified)

**DfT Pink Book (3rd ed., 2016), p.9**: stepped all-red table, 5 s per 50 m band to 300 m,
implied 10 m/s (36 km/h) at band edges; operators instructed to lengthen for gradients and
slow vehicles, never shorten. **TTI/TxDOT 3926-2 (2000), pp.10-17**: clearance = travel time
at "a conservative work zone travel speed of 20 mph" plus a 3-5 s judgement buffer. The
federal MUTCD delegates the duration to the responsible engineer (Fig. 6H-12, Note 2).

## Derived priors

`v_clear_kmh ~ Uniform(20, 40)`. The stated or implied assumed clearance speeds across the
jurisdictions that specify the all-red: NSW 20 km/h (Table B-5, stated) and 40 km/h (Table
B-6, stated); NZ ~36 km/h (implied at Table 2 band edges, unstated); UK 36 km/h (implied);
US/TTI 32.2 km/h (stated). Rule 2, code-specified quantity; range = [min, max] of the
jurisdictional values.

`clear_buffer_s ~ Uniform(0, 5)`. TTI adds 3-5 s explicitly; the NZ, NSW and UK band tables
carry no separate buffer term (their margin lives in the assumed speed and the upward
rounding of the bands), so the lower bound is zero.

`t_confirm_s ~ Uniform(2, 8)`. Unchanged: no published time-and-motion data for the
controller radio exchange; operational estimate.

The minimum all-red (5 s in NZ; 2 s band floor in NSW) never binds at the modelled section
lengths and is not carried as a parameter.

## What the codes specify, and what they do not

The codes size the all-red for the LAST LEGITIMATE vehicle: a slow compliant vehicle that
entered at the end of the green. None of the instruments read for this study ties the
all-red, or the siting of the signal heads, to the INTERVISIBILITY of the two stop lines,
and none sizes any element for the violator case: a vehicle entering during the red meets
whatever the remaining clearance and the sight distance leave it. That gap, not the absence
of an all-red specification, is where the model locates the residual violation risk.

## Regulatory posture (for the manuscript's framing; verbatim-verified)

- **NSW**: hard mandate. TCAWS §5.4.2: "a PTCD must be used when the existing permanent
  speed limit is above 45 km/h", with a narrow, documented, one-up-approved exception path.
- **WA**: hard mandate. MRWA Code of Practice (March 2026) §6.8.3: PTCDs "must be used" on
  any Main Roads-controlled road, or 90 km/h+ with >2,000 vpd, or 70 km/h+ with >10,000 vpd.
- **Austroads (national)**: insufficiency framing, not a mandate. AGTTM Part 7 (2021) §2.1:
  controllers "are used when signs and devices for roadworks are considered insufficient".
  The "preferred method" phrase is attributed to AGTTM by MRWA's code; Parts 2/3 could not
  be accessed to verify it directly (403 at source) and the manuscript does not rely on it.
- **Queensland**: adopts the national framing by reference (QLD MUTCD Part 3, Nov 2025,
  cl. 1.3.19; QGTTM), not a QLD-authored numeric mandate.
- **Tasmania**: the national training matrix carries a literal N/A for traffic controllers
  under TTM Category 3, with the footnote that Tasmania has defined no Category 3 roads.
- **New Zealand**: no device mandate. The NZGTTM leaves the control-mode choice to
  site-by-site risk judgement under the general duty. New Zealand specifies the DEVICE'S
  TIMING (M23 Appendix F) but does not direct that the device be used.

## Access gaps (explicit)

AGTTM Parts 1-3, 6, 9, 10 (403 at source; Part 7 obtained via a mirror); AS 4191 and
AS 1742.3 full texts (paywalled, quoted via documents that cite them); VicRoads and SA
specifications; CoPTTM sections other than B and C; local-authority addenda.
