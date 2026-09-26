# Model design — net-harm comparison S0 (manual traffic control) vs S1 (portable signals)

Configuration = SEJ Scenario C baseline: rural two-lane road, 100 km/h posted, 30 km/h
temporary speed limit, ~50 km/h platoon operating speed, Q = 300 veh/h/direction, 5% HV,
closure 150 m (controlled single-lane section including tapers ~250 m), 8-h operation day,
STMS on site under BOTH strategies.

## Strategies
- **S0** two manual traffic controllers (MTC), one per end, radio-coordinated, adaptive release.
- **S1a** unattended portable traffic signal (PTS) pair, fixed-time plan.
- **S1b** actuated/monitored PTS (vehicle actuation, violation-aware all-red extension).

Primary technology construct = unattended two-head PTS (matches the SEJ D15 construct
"Portable Traffic Signals (Automated)"). AFAD evidence enters for transferability only.
All other traffic management identical; plant/crew coordination carried by the STMS under
every strategy (scope statement).

## Unit
EXPECTED SERIOUS-HARM EVENTS per operation-day, a serious-harm event being a collision
with at least one death-or-serious-injury (DSI / MAIS3+) outcome. SEJ severities are
natively P(>=1 DSI | event). Head-on severity converts per-occupant curve probabilities
to P(>=1 DSI | collision) = 1 - prod(1 - p_i) over both vehicles' occupants. Multi-event
chains excluded as second-order (RSAP-consistent, disclosed).

## Pathways

| ID | Pathway | S0 | S1 | Ledger |
|---|---|---|---|---|
| W1 | Queue-tail rear-end | yes | yes | primary |
| W3 | Controller struck (violation-strike + platoon-strike, elicited TOTAL) | yes | no | primary |
| W5 | Stop-line violation -> opposing conflict -> head-on collision | yes | yes | primary |
| W4d | Incremental PTS head placement/retrieval exposure | -- | yes | primary |
| W5b | Harm arising from a SUCCESSFUL evasion (crew strike, run-off-road, struck from behind) | yes | yes | bounded sensitivity |
| W6 | Dangerous device fault | -- | bounded | bounded sensitivity |
| W2 | Plant / passing vehicle | identical | identical | excluded by scope (STMS retained) |

Setup and removal of the common traffic management is identical across strategies and
cancels from the difference.

---

## The central modelling argument: violation and opposing presence are not independent

Published violation rates at unattended portable signals are high: 3.1% of facing vehicles
in Kansas (3.7% facing-adjusted), about 2% at UK urban shuttle-lane signals, about 3.5% in
Texas, 7.9% in Ohio. A naive accounting multiplies that rate by the probability that the
single-lane section contains an opposing vehicle, and calls the product the conflict rate.

That product is wrong, and it is wrong by orders of magnitude.

Every one of those rates is a count of **observed entries past a red aspect**. Entry is a
decision, taken by a driver who is stopped or slowing at a stop line, looking down the
single-lane section as far as the alignment lets him see. The measured rate is therefore
already conditioned on the state of the section APPEARING clear. Multiplying it by the
marginal probability that the section is occupied multiplies a conditional probability by
the probability of its own conditioning event, and overstates conflicts by roughly the
reciprocal of the driver's aversion to entering against a vehicle he can see.

The field record carries the signature of this directly. Red-running at portable signals
clusters in the first seconds after red onset (Yousif 2014). Red onset is precisely the
moment the section has just been vacated by the violator's own platoon, and is therefore
the moment it is emptiest and looks safest.

Two things the conditioning does NOT deliver, and the tree carries them explicitly, because
they are where the residual risk actually lives:

1. **"Appears clear" is not "is clear."** The driver can confirm the section only to the
   mutual sight distance the alignment provides (crest, curve, vegetation, glare). An
   opposing vehicle beyond that line neither deters his entry nor is deterred by him; the
   pair discover each other mid-section, with the time available to avoid set by the sight
   distance, not by the section length. Unless the site has end-to-end intervisibility
   between the two signal heads, a clear-looking entry can still become a head-on conflict.

2. **"Clear now" is not "clear for the transit."** The clearance interval is sized for the
   last legitimate vehicle, which crossed at red onset; a violator crossing later is
   protected only if the REMAINING clearance covers his own transit. A violator still inside
   at the opposing release meets the released queue, and a violator entering a genuine gap
   during the opposing green is met by the next arrival. Violations are therefore never
   harmless merely because an all-red exists: the all-red protects a specific, computable
   subset of entry times, and the tree computes it.

The consequence for the ledger is that the violation-conflict pathway cannot be assembled as
a chain of independent factors. It must be assembled as an event tree in which the driver's
decision to enter is conditioned on what he can SEE, the opposing driver's decision is
conditioned on what HE can see, the discovery of a conflict is conditioned on the sight
distance, and the collision probability is conditioned on the time available to avoid. Each
conditional is computable from a discrete-event representation of the cycle plus one site
characteristic, the intervisibility. None of them is free.

An immediate corollary is a hard external check on the model, stated in `docs/prespec.md`
as a blocking gate. A model of this pathway implies a head-on collision frequency per
operation-day at a single site. Portable signals have been the shuttle-lane default across
the United Kingdom for decades and are in wide use in New Zealand and Australia. Any model
whose implied frequency is not consistent with that record is disqualified from answering the
research question, in either direction, before its output is read.

---

## Cycle / queue layer (single source of truth)

Deterministic alternating one-lane control, symmetric demand. Two quantities that a
capacity analysis conflates are kept separate here, because the safety question turns on
their difference:

- **Section transit** `tau = L_s / v_p`: the time a vehicle at platoon speed takes to
  traverse the controlled section.
- **Clearance interval** `C`: the all-red the control form actually runs.
  - S0 (MTC, adaptive): `C_0 = tau + t_confirm`. The controller releases only after
    confirming by radio that the section is observed clear; `t_confirm` covers observation
    and radio exchange.
  - S1a / S1b (PTS): `C_1 = k * tau`, with `k >= 1` the clearance margin implied by the
    governing code of practice, which sizes the all-red from the section length at a
    conservative assumed speed rather than the actual operating speed.

Setting `C = tau` is the minimum-feasible convention of one-lane capacity analysis
(Schonfeld-type models). It is the correct convention for computing capacity and an
inadmissible one for computing conflict, because it collapses the safe-entry window to the
startup lost time alone. `k` and `t_confirm` are inputs, not conventions.

Greens: S0 adaptive (clear the standing queue plus an operating margin); S1a fixed-time
(S0 greens scaled by `f_cycle_a`); S1b actuated (scaled by `f_cycle_b`). Cycle length,
red duration, facing counts, stopped counts, standing queue and cycles/day all descend
from this one layer, with the strategy's own clearance. No separate queue multiplier
exists anywhere.

Phase convention for a direction's red, `R = 2C + G_opp`:

```
t = 0                red onset (this direction's green ends)
[0, C)               all-red: this direction's platoon vacates the section
[C, C + G_opp)       opposing green: queue discharge at saturation headway after
                     startup lost time, then free arrivals
[C + G_opp, R)       all-red: opposing platoon vacates
```
Opposing vehicles enter the far end at explicit times `t_j >= C + startup_lost`, and
accelerate from rest at `a_veh` up to platoon speed. A vehicle's position in the section is
therefore known at every instant, and so is what any driver at either stop line can see.

---

## W5 event tree

Initiating event: a vehicle arrives at a stop line facing red at `t_a ~ U(0, R)`.

**1. Violate?**
`P(violate | t_a) = r_base * w(t_a)`, where `w(t_a) = 1` if no opposing vehicle is VISIBLE
from the stop line at `t_a` (the section is clear, or occupied only beyond the sight line),
and `w(t_a) = w_occ * d/s` when one is visible at distance `d` within sight `s`. `w_occ` is a
contested prior. `r_base` is solved per iteration so that the red-averaged violation rate
reproduces the mode's literature-measured rate exactly (`r_v0` for MTC, `r_v1a` for PTS): the
measured quantity is preserved, and only its *timing* becomes endogenous. Only the vehicle at
the stop line can enter; those queued behind it are physically blocked. A violation is an
ONSET entry at speed (share `w_onset`) or a STANDING departure from rest by the queue's lead
vehicle. This is the mechanism by which the model declines to multiply a conditional by its
own condition, without ever assuming the section actually is clear.

**2. Detection hold.** If the violation precedes the opposing release, an S0 radio hold or
an S1b violation-aware all-red extension fires with probability `p_detect`, holding the
opposing release until the violator clears. A violator entering after the release meets
whatever is already in the section regardless: the human advantage is a detection-timing
window whose size falls out of the cycle mechanics.

**3. Opposing entrant yields?** Any opposing vehicle whose stop-line crossing falls inside
the violator's transit is an entrant against him: the released queue lead if the violation
preceded the release, or the next free arrival if the violator entered a gap during the
opposing green. If the violator is within the entrant's sight at that moment, the entrant
enters anyway with probability `q_lead * d/s` (a residual sight/judgement failure, distance-
scaled), else he holds and the event terminates as DELAY. If the violator is BEYOND the
entrant's sight line, the entrant enters unknowingly, with probability one.

**4. Conflict.** The pair close head-on. Discovery occurs at the smaller of the current
separation and the sight distance; the model computes the closing speed at that instant, with
each vehicle at its actual (accelerating or cruising) speed, giving the time-to-collision
`TTC` available to the pair. Restricted sight therefore shortens `TTC` directly, which is the
mechanism by which intervisibility governs this pathway.

**5. Collision?** Either driver avoiding is sufficient on a single lane with a shoulder, so
`P(collision | TTC) = q(TTC)^2`, where `q(TTC) = 1 / (1 + exp((TTC - ttc50) / s_ttc))` is
the probability that one driver fails to avoid within the time available. `ttc50` and `s_ttc`
are contested priors set from the perception-reaction and evasive-manoeuvre literature.
Independence of the two drivers' failures given TTC is a disclosed simplification.

**6. Harm.** Severity uses the NHTSA delta-V injury curves for the occupants of both
vehicles at the closing speed from step 4, scaled by the collision-conditional impact
retention fraction `impact_speed_frac` (a collision implies evasion failed, so full-sight
braking kinematics cannot be assumed). Closing speed is split between vehicles by momentum;
occupancy is sampled per vehicle; `P(>=1 DSI) = 1 - prod(1 - p_i)`.

**7. W5b, successful evasion that still harms (bounded sensitivity).** The `1 - P(collision)`
branch is not terminal. An evading vehicle can reach the work crew, leave the carriageway,
or be struck from behind. Carried as `p_evade_harm` per successful evasion with worker-curve
severity at the operating speed, reported as a bounded band, not in the primary ledger.

The tree is exhaustive at every node and its branches are mutually exclusive. Terminal
states: no violation; violation held by detection; violation yielded to; conflict avoided
cleanly; conflict avoided with secondary harm (W5b); collision without DSI; collision with
DSI (the counted event).

---

## Severity engines, and the speed response

Two curve families, because a struck pedestrian and a restrained occupant have different
injury thresholds by roughly a factor of three in speed.

- **Worker struck**: Rosen (2010) GIDAS pedestrian MAIS3+ logistic in impact speed,
  `logit p = -4.6 + 0.078 v` (km/h).
- **Vehicle occupant**: Wang (2022, NHTSA DOT HS 813 219) MAIS3+ logistic in delta-V,
  `logit p = -6.954 + 0.1637 dv` (mph).

Per person, a worker struck at 30.8 km/h carries the same MAIS3+ risk as an occupant at
delta-V 46.8 km/h, i.e. a head-on with 93.5 km/h closing speed. Per EVENT, in the ledger's
own unit, the asymmetry largely cancels and then reverses above about 45 km/h, because a
head-on exposes two vehicles carrying a mean 1.56 occupants each while a controller strike
exposes one person. Both facts are reported.

**W3 severity responds to operating speed.** The panel elicited `C.SEV3` = P(>=1 DSI |
controller struck) under Scenario C, whose stipulated platoon operating speed is 50 km/h.
The model preserves that value at 50 km/h and gives it the worker curve's speed elasticity
by a logit shift:

```
sev3(v) = logistic( logit(sev3_elicited) + 0.078 * (v - 50) )
```

At v = 50 km/h the elicited quantity is reproduced exactly. Without this, the only
speed-responsive severity in the ledger would be the head-on, and faster traffic would
make the device look worse while leaving the removed worker pathway untouched, which is
not physical. (Inverting the worker curve on the panel's elicited median of 0.625 recovers
an implied strike speed of 65.5 km/h, above the sampled platoon band; this is reported as a
coherence observation, and the anchor is held at the scenario's stipulated 50 km/h.)

**W1 severity is not speed-anchored.** The queue tail lies upstream of both control forms,
its approach speed is identical across strategies, and `W1(S1a) - W1(S0)` is a small
fraction of `W1(S0)`, so any speed response cancels from the difference. Disclosed.

**W4d** uses the encroachment-based deployment machinery of the companion advance-warning
model, with worker severity from the same Rosen curve at the deployment-period approach speed.

---

## SEJ prior consumption
Per-expert equal-weight mixture (fit_re_log10normal + fit_sev_beta per expert; RE and SEV
coupled through the same expert draw; independent uniform streams), from Round-2 Scenario C
responses. C.RE3 anchors W3 as a TOTAL, consumed whole, with no decomposition reuse: the W5
violation rates are independent literature priors for both modes. D15 is consumed as a
per-expert lognormal mixture for the coherence check.

---

## Outputs
- `dH = H(S1x) - H(S0)` per operation-day; `P(dH < 0)` with Wilson 95% CI; median/mean dH,
  separately for S1a and S1b.
- Grid: Q in {100, 200, 300, 450, 600, 800, 1000} veh/h/dir x section {150, 250, 500, 1000,
  2000} m. Baseline (300, 250).
- **Implied head-on collision frequency per operation-day**, reported for every cell, and
  confronted with the crash record. This is a validity constraint on the model, not an output.
- **Observational calibration curve**: `P(dH < 0)` as a function of the implied head-on
  collision frequency, so the decision can be read against a quantity a crash database or a
  site supervisor can observe, without requiring any contested parameter to be believed.
- Closed-form break-even violation frontier per iteration.
- Operating-speed sweep at the baseline cell (a decision axis, not a nuisance parameter).
- PRCC on dH with bootstrap intervals; convergence, seeds, per-iteration traces.
- Coherence check (NOT validation) against the panel's directly elicited D15 multiplier:
  frame-matched ratio and full-mechanism ratio.

## Reproducibility
Python/NumPy, fixed PCG64 seeds, inverse-CDF sampling from portable generators, pytest suite
pinning the structural identities (the accounting reduces exactly to the controller-pathway
difference when the strategies are behaviourally identical), the anchor reproduction, the
event tree's exhaustiveness and mutual exclusivity at every node, the TTC and yield
monotonicities, the oversaturation guard, and bit-level reproducibility. Config-driven grid,
per-iteration traces, results digest into the numeric manifest.

## Honest-limits register (seed for Limitations)
1. SEJ priors are judged, not measured; one NZ panel (n=12); companion paper in review.
2. Violation-rate evidence is short-duration and US/UK-dominant; transferability to the NZ
   rural construct is an assumption the break-even frontier makes inspectable.
3. The tree's behavioural conditionals (`w_occ`, `p_yield`, `ttc50`, `s_ttc`) are argued from
   mechanism and from the driver-behaviour literature; none has been measured at a portable
   signal. They are the model's contested core and the calibration curve exists because of them.
4. Head-on severity uses per-occupant curves at a derived delta-V for a simplified collision
   geometry; independence across persons given delta-V is assumed.
5. No configuration-level crash outcome data exists to validate against at the site level.
   The model is decision support under uncertainty, not prediction.
