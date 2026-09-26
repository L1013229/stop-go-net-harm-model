# Injury-record bounds on the controller-struck pathway (model validity gate 2)

The symmetric companion to `crash-record-bounds.md`. Gate 1 held the pathway the
substitution *introduces* to the crash record. This holds the pathway it *removes* to the
occupational-injury record, on the same terms. Applying one gate and not the other would
rig the comparison toward the device.

## 1. What was elicited

`C.RE3_MTC` was elicited as a return period per vehicle pass: how many vehicle passes are
needed for one controller strike. Twelve experts, two rounds with anonymous feedback,
log10-normal fits per expert, equal-weight mixture. Pooled median return period 791,797
passes per strike (5th percentile 100,386; 95th 4,731,478). At the scenario's 4,800 passes
per operation-day this is a strike rate of 6.4e-3 per operation-day, one strike per 156
operating days at a single site. `C.SEV3`, the conditional probability of at least one death
or serious injury given a strike, has median 0.625, giving **4.0e-3 serious-harm events per
operation-day**, about one per operating year at one site.

## 2. What the record says

No jurisdiction publishes a direct per-operation-day controller-strike rate. Every figure
below is constructed from a sourced count and a named exposure denominator. Three
structurally independent constructions converge.

| Method | Numerator | Denominator | Fatal / op-day | DSI / op-day |
|---|---|---|---|---|
| **A. US occupational** (BLS CFOI + OEWS) | 10-12 flagging-activity struck-by deaths/yr [@pegula_2013] | 54,000-91,400 flaggers x 230 d | 1.8e-6 | ~9e-6 |
| **B. NZ actuarial** (WorkSafe, MoT, CAS) | controller deaths ~1 per 2-4 yr; worker DSI at roadworks 3-4/yr | ~175,000 stop/go op-days/yr (65k-630k) | 1.3-3.3e-6 | 6.5e-6 to 1.6e-5 |
| **C. Intrusion model** (Ullman/Finley/Theiss; Bryden & Andrew) | 7.5% intrusion share x 17% worker-collision; 24.4 fatal per 100,000 worker-years | 4,800 passes; ~3 workers | 1.0-1.5e-6 | ~7.5e-6 |
| **Consolidated** | | | **~2e-6** (1e-6 to 3.5e-6) | **~1e-5** (5e-6 to 2e-5) |

An occupational cross-check needs no exposure denominator at all: the measured flagger
struck-by fatality rate is 10 to 41 per 100,000 worker-years, central 14 to 20. That is
already among the most dangerous rates of any occupation, and it is where the record sits.

## 3. The comparison

| Quantity | Elicited (per op-day) | Record (per op-day) | Factor |
|---|---|---|---|
| Strike, any severity | 6.4e-3 | 2e-5 to 3.5e-4 | 18 to 320 |
| **Serious harm (>=1 DSI)** | **4.0e-3** | **~1e-5** (5e-6 to 2e-5) | **200 to 800, central 400** |
| Fatal | ~4e-4 to 8e-4 | ~2e-6 | 130 to 600 |

The serious-harm and fatal comparisons are the defensible ones, because fatalities are
near-completely recorded and serious injuries reliably captured. The all-severity comparison
is loose in exactly the way one expects, because minor strikes are recorded nowhere.

**The panel's entire 90 percent interval is excluded.** Its 5th-percentile serious-harm rate,
about 2.2e-4 per operation-day, still sits ten to forty times above the record's central-to-
upper range. Not one expert's optimistic tail reaches it.

### The reductio, which needs no exposure denominator
The elicited fatal rate is 4e-4 to 8e-4 per operation-day. Per controller, over a 230-day
year, that is an annual on-the-job fatality probability of **4.6 to 9 percent**, which is
4,600 to 9,000 per 100,000 worker-years against a measured 10 to 41, and implies roughly
sixty percent of controllers killed over a twenty-year career. No such workforce exists.

### The national reductio
4.0e-3 serious-harm events per operation-day across roughly 175,000 New Zealand stop/go
operation-days a year is about **700 controller deaths or serious injuries annually**, against
a national road toll of about 2,700 DSI and about 146 DSI a year at all temporary traffic
management sites. Stop/go controllers alone would account for five times the harm recorded at
every work zone in the country.

## 4. Corroboration from inside the elicitation

The panel does not behave as though it believes its own component frequency. Removing the
controller pathway from the panel's own per-day arithmetic implies a net risk multiplier near
0.59 for the substitution. The multiplier the same panel elicited directly for that
substitution was 0.91, a nine percent reduction. If they truly held that 4.0e-3 serious-harm
events per operation-day flowed through the controller, removing it should have cut site risk
by about forty percent, not nine. Their holistic judgement contradicts their component
frequency, which is internal evidence that the return period is inflated relative to what the
experts actually believe about the controller's share of harm.

## 5. Does the elicitation literature predict this

Yes, in direction. Over-estimation of a vivid, dreaded, highly available hazard is the
canonical finding [@lichtenstein_1978]; a controller struck and killed is the event the whole
temporary traffic management system exists to prevent. Expert intervals are routinely too
narrow [@lin_bier_2008; @colson_cooke_2018], and equal-weight aggregation is the configuration
Cooke's database usually shows to be outperformed [@cooke_experts_1991].

The even-handed counters are recorded and then answered. The description-experience gap can
make people *under*-weight unseen rare events; and struck-by events are genuinely
under-recorded. But the gap here is 130 to 600 times **on fatalities**, which are near-completely
recorded, and a generous three-to-fivefold under-recording correction for serious injuries
still leaves the serious-harm rate eighty to one hundred and thirty times too high. The
over-estimation is real, not a recording artefact, and it survived a two-round protocol with
calibration seeds, which is itself consistent with the finding that even good elicitations
struggle with rare dreaded events.

## 6. The gate

Median implied controller serious-harm events per operation-day must lie within
**[1e-6, 1e-4]**, one order either side of the consolidated record. The elicited value of
4.0e-3 **fails**, by a factor of forty against the gate's upper bound and four hundred against
the record's central estimate.

Gate 2 was added after gate 1 had been applied and the introduced pathway repaired, at the
point where the elicited controller-strike rate had become the sole determinant of the answer
and the answer agreed with the direction predicted in advance. It is recorded as added then,
not presented as though it had always been there.

## 7. Consequence

The elicited quantity is consumed whole by design and is not re-centred. What changes is what
the model is allowed to conclude. With gate 2 failed, no point probability computed at the
elicited value can be the paper's answer. The decision output is the surface over the two
observable serious-harm frequencies, in which a reader supplies the pair their jurisdiction
records. Read at the record, the pathway the substitution removes and the pathway it
introduces are the same order of magnitude, and the comparison is not resolvable by either
register.

## 8. What the record cannot establish

1. **A direct observed per-operation-day controller-strike rate does not exist** in any
   jurisdiction. Every figure here is constructed.
2. **The all-severity strike rate cannot be resolved** below about 2e-5 to 3.5e-4 per
   operation-day. Minor contacts appear only in severity-undefined self-report. No point
   value is offered.
3. **Controllers cannot be isolated in the registers.** The US occupational classification
   bundles flaggers with school crossing guards; neither the New Zealand nor the British crash
   register carries a control-mode field.
4. **Motorist-struck and plant-struck cannot be separated** for workers on foot. The elicited
   quantity is a public-vehicle strike; the recorded fatalities include some plant strikes, so
   the public-strike-specific record is lower still and the true gap wider.
5. Exposure denominators are known to about one order of magnitude. The per-worker-year routes
   sidestep this for fatalities.
6. Below about 1e-6 per operation-day the fatal record is silent.

None of these limits rescues the elicited value. The most generous defensible reading of the
record, corrected for both denominator and under-reporting, remains more than a hundred times
below it, and the fatal comparison is immune to every one of them.

## Sources
Pegula (2013), BLS *Monthly Labor Review*; CPWR Construction Chart Book 6th ed. (2018) and
Quarterly Data Report (2018); BLS OEWS May 2024 (SOC 33-9091); BLS CFOI via the National Work
Zone Safety Information Clearinghouse; NIOSH FACE case series; Demeke et al. (2025) *TRR*;
Ullman, Finley & Theiss (2010) FHWA/CA10-1102; Ullman et al. (2011) *TRR* 2258; Bryden &
Andrew (1999) *TRR* 1657; Bryden et al. (2000) *TRR* 1715; Ullman & Levine (1987) *TRR* 1148;
WorkSafe NZ *Working near live traffic*; NZ Ministry of Transport roadworks DSI series; NZTA
(2023) worksite casualty release; Highways England (2017) strategic road network figures;
CEDR IRIS D3.2 (Varhelyi et al. 2019); Cooke (1991); Colson & Cooke (2018); Lin & Bier (2008);
Lichtenstein et al. (1978); Morgan (2014); Hertwig et al. (2004).
