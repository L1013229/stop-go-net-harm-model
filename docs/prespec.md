# Study design, decision rules and falsifiers

Fixed before the numeric priors are valued and before any production run. `run_suite.py`
refuses to execute unless the last commit touching this file predates the last commit
touching `model/config/priors.toml`, and both are clean. Prior VALUES are set after this
file, from the assembled evidence, by the construction rules below, blind to model output.

This is engineering discipline, not a claim: several of the model's behavioural conditionals
have never been measured, the direction they push the comparison is known in advance from
mechanism, and fixing the structure and the rules before valuing them is how the analyst is
prevented from tuning the answer.

## Fixed structure
Pathways W1, W3, W5, W4d in the primary ledger. W5b (harm from a successful evasion) and W6
(dangerous device fault) as bounded sensitivity cases, reported separately. W2 excluded by
scope statement (STMS retained under both strategies). Strategies S0, S1a, S1b per
`docs/model-design.md`. Expected-serious-harm-event units. Per-expert equal-weight SEJ
mixtures for C.RE1, C.SEV1, C.RE3, C.SEV3, C.D15. A single cycle/queue layer feeds every
exposure quantity, with the section transit time and the control form's clearance interval
held as distinct quantities. W5 is assembled as the event tree of `model-design.md`, not as
a product of independent factors.

## Fixed grid and baseline
Q in {100, 200, 300, 450, 600, 800, 1000} veh/h/dir; controlled section {150, 250, 500,
1000, 2000} m; baseline cell (300 veh/h, 250 m); 8-h operation; 20,000+ iterations per cell;
fixed seeds; Wilson 95% CIs on P(dH<0). Operating speed is additionally swept at the baseline
cell as a decision axis.

## Prior construction rules (mechanical, evidence-bracketing)
1. Behavioural rates measured in >= 2 independent field settings: range = [min, max] of
   reported central estimates, widened one step of the same order each side; log-uniform if
   the span exceeds one order of magnitude, else triangular(min, mode = pooled central, max).
   Per-cycle vs per-vehicle metrics converted to per-facing-vehicle via the cycle layer
   BEFORE pooling; every conversion documented per source.
2. Rates with a single credible source: triangular centred on it with bounds at half/double,
   disclosed as single-source. Quantities specified in a governing code of practice are taken
   from the code, with the spread across jurisdictions forming the range.
3. Quantities with no direct measurement: wide log-uniform or uniform spanning the
   plausible-mechanism bounds argued in Methods. PRCC must report them. If any of them tops
   the ranking, the conditional break-even frontier and the observational calibration curve,
   which condition on them, become the primary decision outputs rather than a point P(dH<0).
4. SEJ quantities: per-expert fits, equal-weight mixture, no reweighting, no truncation
   beyond domain bounds ([0,1] for severities). C.RE3 anchors W3 as a TOTAL and is consumed
   whole; W5 violation rates are independent literature priors for both modes.
5. Named variant sets fixed in advance: PRIMARY; OPTIMISTIC-DEVICE (each contested parameter
   at its PTS-favourable bound); PESSIMISTIC-DEVICE (converse). No other variant may be added
   after the first run.

## Contested-parameter list (frozen; rule-3 priors, PRCC-reported)
`w_occ` (violator enters against a VISIBLE opposing vehicle, scaled by its distance within
the sight range);
`q_lead` (an opposing entrant who CAN see the violator enters against him anyway, scaled by
distance within the sight range; an entrant who cannot see him enters with probability one);
`d_sight_m` (mutual sight distance along the section — the intervisibility of the site,
capped at the section length; the axis on which the violation pathway turns);
`w_onset` (share of violations committed at speed at red onset, rather than as a standing
departure by the queue's lead vehicle);
`ttc50`, `s_ttc` (probability one driver fails to avoid, as a function of available TTC);
`impact_speed_frac` (collision-conditional impact retention);
`p_detect_s0`, `p_detect_s1b` (detection-window effectiveness);
`p_evade_harm` (W5b); W6 dangerous-fault rate.

`onset_window_s`, `t_confirm_s` and `a_veh_ms2` are operational quantities under rule 2, not
rule 3. `v_clear_kmh` and `clear_buffer_s` are code-specified under rule 2.
`platoon_speed_kmh` is an operational quantity under rule 1: measured operating behaviour
through rural work zones under a 30 km/h temporary speed limit, not the limit itself. The
elicited severities remain anchored at the scenario's stipulated 50 km/h and are transported
to the sampled speed.

No other parameter may be added to rule 3 after the first run. Eligible-source rule:
peer-reviewed or state-DOT/national-agency field studies measuring the parameter in a
work-zone, signalised or driver-behaviour setting; simulator and survey data admissible as
variant bounds, never as central estimates. Conversion equations (per-cycle to
per-facing-vehicle) are frozen in `model/config/priors.toml` comments before the first run.

## Model validity gates (blocking, checked before any decision output is read)

The model implies an observable frequency for each of the two pathways that carry the
comparison. Both are confronted with the record. A model that fails either gate is repaired
at its structure, never by re-centring a prior to move the output. These are constraints the
model must satisfy, not quantities it is fitted to. No parameter is tuned to the record.

**Gate 1 — introduced pathway.** The model implies a head-on collision frequency per
operation-day at a single site. Portable signals have been the shuttle-lane default across
the United Kingdom for decades and are in wide use in New Zealand and Australia; two
independent national crash registers bound that frequency (`research/crash-record-bounds.md`).
The primary set is disqualified if its median implied head-on collision frequency at the
baseline cell falls outside [1e-6, 1e-3] per operation-day. The interval admits a
high-exposure 300 veh/h rural site sitting up to an order of magnitude above the
all-roadworks national average, and refuses a model that produces an implausibly safe world.

**Gate 2 — removed pathway.** The model implies a controller-strike frequency per
operation-day, and a death-or-serious-injury subset of it. That quantity is elicited from an
expert panel and has never been confronted with the occupational-injury record. It is subject
to gate 1's logic in exactly the same terms, against the bounds in
`research/controller-strike-bounds.md`.

**Disclosure on gate 2.** Gate 2 was added after gate 1 had been applied and the introduced
pathway repaired. At that point the elicited controller-strike rate carried the entire
comparison, and the result agreed with the direction this document recorded in advance. A
check introduced at that moment, on the pathway whose deflation would REMOVE the predicted
result, is the falsification the situation demands, and its omission from the first draft of
this specification was an error. It is recorded here rather than presented as though it had
always been present.

**Consequence for the decision output.** Because both pathways are, on their face, elicited
or modelled at rates the record does not support, the primary decision output is neither a
point P(dH<0) nor a frontier conditional on an unmeasured behavioural parameter. It is the
DECISION SURFACE over the two observable frequencies: controller-strike serious-harm events
per operation-day, and head-on collisions per operation-day. A reader supplies the pair their
jurisdiction observes and reads the answer off the surface. Nothing in it requires any
contested prior to be believed.

## Decision rules
p* = 0.5 (more likely to help than harm) and p* = 0.8 (high confidence), applied to
P(dH < 0) per cell. The frontier is reported as the violation rate at which each threshold is
crossed. Because dH is linear in the device violation rate within each iteration, the
break-even rate has a closed form per iteration and the frontier is computed exactly.

**The observational calibration curve is a primary output.** P(dH < 0) is reported as a
function of the model-implied head-on collision frequency per operation-day, an observable
quantity, so that the decision can be read without requiring any contested behavioural
parameter to be believed.

**Equivalence bound (reported alongside every threshold verdict).** Where neither threshold
is crossed at the record calibration, the result is stated as a bounded practical-equivalence
finding, not as ignorance: P(|dH| <= m) at the record-calibrated pair, for a pre-stated
margin m equal to one serious-harm event per 100 site-years of operation (m = 4.0e-5 per
operation-day at 250 operating days per year), together with the margin at which
equivalence would fail. A comparison bounded within m is decision-equivalent for site-level
safety and the choice passes to the quantities the model does not price: delay, cost,
the in-principle elimination of a worker exposure, and the site's intervisibility.

**Value of information.** For each of the two observable frequencies, the span of P(dH < 0)
across that record band with the other held central is reported. The larger span names the
measurement that most reduces decision uncertainty, which converts the residual uncertainty
into a ranked evidence agenda rather than a statement of ignorance.

**Elicited-level disclosure.** The elicited ABSOLUTE frequencies are confronted with the
record for every pathway, W1 included, not only for the two the decision turns on. Where the
levels are systematically high but the comparison survives, the mechanism (common terms
cancel in the difference; the decision outputs strip levels entirely) is stated as a finding
about the use of structured expert judgement in net-harm accounting.

## Falsifiers
- H is REJECTED at the baseline cell if P(dH < 0) <= 0.5 under the PRIMARY set (S1a is the
  primary comparison; S1b secondary).
- **Empirical frontier test**: H's practical claim fails if the literature-observed device
  violation band lies mostly ABOVE the p* = 0.5 break-even frontier at the baseline cell.
- **Attenuation clause**: rejected if P(dH < 0) does not decrease with the device violation
  rate at baseline. The section-length direction is NOT pre-specified; its sign is reported
  as an outcome.
- **W5-driven clause**: rejected if no W5 parameter appears in the top three PRCC ranks for
  dH at baseline, OR if removing W5 entirely changes P(dH < 0) by less than the Monte Carlo
  CI width (W3 removal alone would then carry the result).
- **Speed clause**: the sign of the operating-speed PRCC on dH is reported as an outcome, not
  pre-specified.
- **Tree closure**: the event tree's branch probabilities must sum to one at every node, and
  the terminal states must partition the initiating events. Tested, not asserted.
- Coherence outcomes reported regardless of direction: frame-matched ratio and full-mechanism
  ratio against the panel's D15 mixture. Pre-registered as a check, not a validation;
  discordance is a finding, not a failure.

## Directional expectation, recorded in advance
Mechanism says the event-tree treatment of W5 will move the comparison toward the device
relative to any accounting that multiplies the measured violation rate by an independent
opposing-presence probability. That expectation is recorded here, before the priors are
valued and before any run, so that it cannot afterwards be presented as a discovery, and so
that a device-favourable result is read with the reservations that attach to a predicted one.
No contested prior may be narrowed, widened or re-centred after any run.

## Reporting commitments
All grid cells reported; no cell suppression. Every headline number with a band.
Numeric-manifest and claim-ledger gates. Per-iteration traces retained. Negative and null
results published as-is. The implied collision frequency is reported alongside every headline
probability.

---

# Addendum A (2026-09-26): attended device arm, model-form sensitivity, welfare reading

Written for the journal version after the primary results (dist `2020f2c_20260709`) were
frozen and the conference manuscript submitted. Everything in this addendum is therefore a
POST-PRIMARY EXTENSION and is disclosed as such wherever its results appear. The discipline
is the same as above: structure and prior rules committed here, prior values committed in
`model/config/priors.toml` in the same commit, no run of the new arm before that commit, and
no prior moved after any run. The primary structure, grid, priors and variant sets above are
untouched; the frozen results stand as the record.

## A1. Strategy S2: attended automated flagger assistance device (AFAD)

An AFAD is a remotely operated STOP/SLOW sign or red/yellow lens unit with a gate arm at each
end of the section, each operated by a controller who stands off the carriageway (MUTCD Part
6 requires an AFAD to be attended; the operating controller holds the remote). New Zealand
and Queensland boom units operated from a safe zone are the same construct. S2 is defined as
the GATED, attended configuration.

Structure, per pathway, relative to S0 and S1:

- **Cycle plan.** Attended release: the operator releases a direction only after observing
  the section clear, so S2 runs the S0 adaptive plan and the S0 clearance interval
  (`C_0 = t_rest + t_confirm`). Consequence: W1 under S2 equals W1 under S0 by construction
  and cancels from the S2 comparison.
- **W3, controller struck.** The lane-standing controller pathway (C.RE3 x C.SEV3) is
  removed. What remains is the operator standing beside the road for the operating day,
  which is an ENCROACHMENT exposure, not a stop-line strike, so it is built with the W4d
  encroachment frame already in the model: vehicle passes at the two operator positions
  (each vehicle passes both, so 4 x the one-direction daily volume) x encroachment rate x
  exposed length x P(reach >= offset) x P(DSI | struck at the operating speed), with the
  operator's standing offset from the edgeline a new prior (`offset_op_m`). Named W3r.
  It is mechanism-built and carries no elicited level, so it does not scale with the
  controller-strike axis of the decision surface.
- **W5, violation conflict.** Violation rate `r_v2` from the attended gated AFAD field
  record (rule 1). A human hold applies as under S0: the operator sees a pre-release
  violation and holds the opposing unit on red, with its own effectiveness prior
  `p_detect_s2` (rule 3). The tree, its conditionals and the clearance are otherwise S0's.
- **W4d, placement.** The two AFAD units are placed and retrieved on foot like the two
  signal units: the same draws (`t_deploy_s`, `enc_rate_vkm`, `reach_alpha`, `offset_m`,
  `deploy_speed_kmh`) apply.
- **W5b, W6.** As for S1: bounded bands, not in the primary ledger.

Draw order. The three new draws (`r_v2`, `p_detect_s2`, `offset_op_m`) are taken AFTER every
existing draw in `run_cell`, so S0, S1a and S1b reproduce the frozen artefacts bit for bit
under the same seeds. A test pins this against the frozen traces.

## A2. Prior rules for the new quantities

- `r_v2` under rule 1: two independent settings with attended gated devices, Texas (TTI
  0-6407-1, four gated treatments) and Minnesota (MnDOT 1999 AutoFlagger); per-cycle counts
  converted to per-facing-vehicle with the same facing denominators as
  `research/violation-priors-harmonisation.md`; range = [min, max] of the setting centrals,
  widened one step of each endpoint's own order (the harmonisation's JC-1 reading), span
  under one order so triangular, mode at the pooled central. The widening carries the upper
  bound up to the ungated Texas observation, so the prior already admits a gate arm that is
  not respected.
- `p_detect_s2` under rule 3: the same bounds as `p_detect_s0`. The only field evidence on
  human interception of a violator (TTI 0-6407-1 p.127) was collected under attended
  AFADs, so it belongs to this configuration at least as much as to S0.
- `offset_op_m` under rule 3: no measurement of where AFAD operators stand; bounds argued
  from the shoulder just off the edgeline to a position behind the work area.
- `l_exposed_km` for the operator: the W4d point-target convention (1 m), shared.

## A3. Variant sets and the configuration sensitivity

The OPTIMISTIC-DEVICE and PESSIMISTIC-DEVICE sets gain `p_detect_s2` (0.9 / 0.3) and
`offset_op_m` (6.0 / 1.5); no other change. One configuration sensitivity is fixed now and
run at the baseline cell only: S2 with NO gate arm, `r_v2` replaced by the single-source
ungated Texas rate under rule 2 (triangular at half/double of 0.022 per facing vehicle).

## A4. Record checks for S2

Gate 1 applies to S2 exactly as to S1a: median implied head-on collisions per operation-day
at the baseline cell inside [1e-6, 1e-3], and P(collision | violation) under the
rule-of-three ceiling. Gate 2 has no elicited level to check under S2; the residual W3r is
reported against the controller record band (`research/controller-strike-bounds.md`) as a
coherence observation, with the expectation, recorded here, that an off-carriageway operator
sits BELOW the record for a lane-standing controller.

## A5. Decision outputs for S2

- P(H(S2) - H(S0) < 0) at the elicited values (grid and baseline), with the same reservation
  as for S1: not reportable as the answer while gate 2 fails.
- The decision surface over the same two observable rates, read at the record: the
  controller axis scales S0's W3 (the removed pathway), the head-on axis scales W5 in both
  arms; W3r and W4d are constants of the mechanism. Reported at record central, at the
  four record corners, with the queue-tail term suppressed (it is zero for S2 by
  construction).
- The equivalence probability P(|dH| <= m) at the record, m as above.
- The direct comparison against the unattended signal, P(H(S2) < H(S1a)), at the record.

## A6. Model-form sensitivity (structural alternatives, fixed before their runs)

PRCC measures influence within the tree and cannot test the tree. Two of its assumptions are
therefore varied as named alternatives, at the baseline cell, for S1a and S2:

- **MF1, dependent avoidance failures.** The primary tree takes the two drivers' failures
  as independent given TTC, `P(collision) = q^2`. Common causes (glare, dust, low sun) act
  on both drivers at once, so the alternative is the beta-factor common-cause form
  `P(collision) = rho * q + (1 - rho) * q^2` with rho in {0.5, 1.0}; rho = 1 means one
  driver's failure is enough.
- **MF2, avoidance-curve form.** The primary curve is logistic in TTC. Alternatives: (a)
  a hard threshold at `ttc50` (fail below, avoid above); (b) logistic in ln(TTC) with the
  same median and the scale `s_ttc / ttc50` (the same slope at the median).

Every headline number (P at the record central, the equivalence probability, the median
|dH|, the implied collision frequency) is reported under the primary form and under each
alternative, and the paper states each headline with its value under the MOST ADVERSE
alternative for the strategy concerned, defined as the setting giving the lowest P(dH < 0)
for that strategy at the record central. No alternative is adopted as primary after the fact.

## A7. Welfare reading of the delay trade

The delay each strategy imposes is computed from the same cycle layer, per iteration:
deterministic uniform delay per arriving vehicle under each plan, summed over the operation
day. The safety difference is priced with the national value of statistical life for a
serious-harm event, and the delay difference with the national value of travel time (both
from the MBCM edition the manuscript already cites), giving an expected net social cost per
operation-day for each substitution at the record calibration, and the delay difference at
which the two terms balance. The queue-tail term, suppressed from the safety decision
outputs because it buys safety with delay, is restored in this reading, since delay is now
priced. This is a reading of the model's own outputs, not a delay model; that limit stands.

## A8. Directional expectation for the extension, recorded in advance

Mechanism says S2 removes most of the controller exposure S0 carries and adds a fraction of
the head-on exposure S1a carries, so at the record calibration it is expected to sit closer
to a favourable verdict than S1a does. That expectation is recorded here before the first S2
run so a favourable S2 result is read as a predicted one, with the reservations that attach.

## A7.1 Amendment to the welfare reading (recorded 2026-09-26, after review round 1, with results known)

A7 said the queue-tail term is restored in the welfare reading. As sampled, that term carries
the panel's queue-tail level, which the record check found to be 15 times the all-cause record
(REGISTRY R30, R38). Restoring it at the panel's level prices a safety gain the record does not
support, so the welfare reading is reported three ways and all three are shown: the queue-tail
difference excluded (the same change in harm the decision outputs use); restored scaled to the
all-cause record ceiling (factor 0.0665, the reading consistent with the calibration the rest of
the paper applies); and restored at the panel's level, which is the A7 reading as first
written. A7 also said the reading gives an EXPECTED net social cost. The first implementation
reported medians and a sum of medians; the expected values (means over draws) are now computed
and reported beside them (welfare.py, fields *_mean). Both changes were made after the first
welfare run and after the first review round, are labelled as such in the manuscript, and move
no prior. Pricing by pathway (a strike priced at its recorded fatal share, a head-on at its) is
reported as a further sensitivity for the same reason.
