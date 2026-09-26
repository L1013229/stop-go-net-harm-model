# Avoidance and severity basis (evidence for `ttc50`, `s_ttc`, and the speed response)

## 1. Why the Power Model cannot occupy the severity node

Nilsson's power model relates a change in the **mean speed of a traffic stream** to a change
in **aggregate crash and casualty counts** by severity. It is not a conditional injury-risk
function given that a crash has occurred at a given impact speed, and it cannot be used as
one without double-counting the frequency response that the model's own upstream nodes
already carry.

Nilsson himself frames it this way, unprompted, in the preface of the primary thesis
(*Traffic Safety Dimensions and the Power Model to Describe the Effect of Speed on Safety*,
Bulletin 221, Lund Institute of Technology, 2004, p.4): "the power model... tries to present
the relationship between speed and safety on **an aggregated level**."

Theoretical exponents (pp.57-58): injury accidents 2, fatal accidents 4, fatal-and-serious 3.
The 3 is explicitly a judgement, not a derivation (p.58): "the exponent of the power model
should for these accidents be somewhere between 2 and 4[;] the exponent of 3 has been the
choice." Nilsson's own eq. 5.3 shows the injured-count model is algebraically a **mixture** of
a squared frequency term and a squared severity-per-crash term, which together give the
fourth power. The bundling is in the derivation.

Elvik's re-parameterisation (*Accident Analysis & Prevention* 50:854-860, 2013) keeps the
aggregate framing ("the mean speed of traffic") and makes the exponent depend on initial speed
by fitting an exponential in the speed **difference** rather than a power in the speed ratio.
Elvik (2009, TØI 1034/2009) gives rural exponents of about 4.1 for fatal accidents (95% CI
2.9 to 5.3), 4.6 for fatalities, 2.6 for serious-injury accidents (CI straddles zero), and 1.6
for all injury accidents. **These CIs were read from a secondary FHWA citation; the primary
TØI PDF returned 403 on three attempts and must be pulled before any of these numbers becomes
load-bearing in the manuscript.**

Hauer (*TRR* 2103:10-17, 2009) argues the exponential form is the better description precisely
because a power law implies a given *relative* speed change has the same effect at any
baseline speed, which is false. Ambros & Kieć (*ETRR* 17:59, 2025) find the power and
exponential forms hold for only about half of low-speed traffic-calming categories tested, so
validity degrades in exactly the speed range a 30 km/h temporary speed limit occupies.

**Where the power model does belong in this paper.** Elvik (2013) cross-checks his fitted
fatality coefficient, about 0.069 per km/h, against Rosén & Sander's individual pedestrian
impact-speed fatality curve (*AA&P* 41(3):536-542, 2009) and finds them consistent. That is
the citable warrant for giving the elicited controller-strike severity the Rosen curve's
speed elasticity: the aggregate and individual descriptions of the speed-severity
relationship agree in magnitude. Elvik, Vadeby, Hels & van Schagen (*AA&P* 123:114-122, 2019)
is the direct treatment of the aggregate-versus-individual distinction and should be read in
full. Kloeden et al. (CR 172, Federal Office of Road Safety, 1997) is the individual-level
analogue to set beside Nilsson.

The model's implied elasticity of P(>=1 DSI | collision) with respect to impact speed runs
from 1.53 at the device-favourable impact fraction to 5.09 at full closing speed, 3.31 at the
median. The Rosen worker curve gives 2.34, 3.90 and 5.46 at 30, 50 and 70 km/h. Both are
steeper than the residual obtained by removing an injury-crash frequency exponent of about 2
from Nilsson's serious and fatal exponents. The conditional severity curves used here are
therefore not conservatively low. Reported as a coherence check.

## 2. Avoidance as a function of time-to-collision

**No P(avoidance | TTC) curve has ever been fitted for a head-on or opposing-direction
conflict on a straight rural road, and none exists for any work-zone context.** The TTC
literature that fits curves is rear-end (Kusano & Gabler; SHRP2 steer-versus-brake work). The
nearest opposing-direction analogue, Dinakar & Muttart (SAE 2019-01-0414), is an intersection
turn-across-path geometry. Wrong-way-driving literature (Das et al., *AA&P* 111:43-55, 2018;
NTSB SIR-12/01) is post-hoc crash-pattern analysis with no denominator of avoided encounters,
so no avoidance curve can be recovered from it. This is a genuine and unfilled gap sitting
directly beneath the model's collision node.

Perception-response to genuinely unexpected hazards:

| Source | Condition | Value |
|---|---|---|
| Olson & Sivak (*Human Factors* 28(1):91-96, 1986) | unalerted, obstacle over a crest | 50th pct 1.1 s; 95th pct 1.6 s |
| Green (*Transportation Human Factors* 2(3):195-216, 2000) | surprise, object suddenly in path | ~1.5 s |
| Green (2000) | unexpected but common (lead-car brake lights) | ~1.25 s |
| Summala (*Human Factors* 23(6):683-692, 1981) | covert field, door opening in path, n=1,326 | steering latency ~1.5 s |
| Fambro et al. (NCHRP 400, TRB, 1997) | design envelope, simple-to-moderate complexity | 2.5 s (~90th pct) |

The 2.5 s design value is an envelope, not an empirical surprise-event distribution; the two
are routinely conflated and are kept distinct here.

Manoeuvre execution: Brännström, Coelingh & Sjöberg (*IJVS* 7(1):87-106, 2014) show the
kinematic availability of braking versus steering escape depends on both TTC and speed, with
braking the only feasible escape below about 50 km/h. Lechner & Malaterre (SAE 910016, 1991,
n=49, unalerted junction intrusion) found **only 1 in 5 drivers avoided the collision**, most
braking only. Li, Rakotonirainy & Yan (*J. Safety Research* 70:89-96, 2019) ran an explicit
head-on simulator scenario: brake-only dominated, brake-plus-swerve was second, and long brake
reaction time plus swerving toward the threat were the two dominant predictors of collision;
no TTC-parameterised curve is reported.

Markkula et al. (*AA&P* 95(A):209-226, 2016), on 116 crashes and 241 near-crashes, show brake
onset is not a fixed delay after hazard onset but occurs under a second after a kinematic
looming threshold is crossed, with onset and deceleration ramp scaling with urgency. That
motivates a sigmoid in TTC. It is also, by its own title, a caution against over-trusting any
two-parameter reduction of driver response, and is cited as such.

**Adopted form.** `P(one driver fails to avoid | TTC) = 1 / (1 + exp((TTC - ttc50) / s_ttc))`.
Either driver avoiding is sufficient on a single lane with a shoulder, so
`P(collision | TTC) = q(TTC)^2`, with independence given TTC a disclosed simplification.

`ttc50 ~ Uniform(1.0, 2.5)` s: bounded below by the fastest measured surprise-hazard medians
(Olson & Sivak 1.1 s) and above by the NCHRP 400 envelope (2.5 s).
`s_ttc ~ Uniform(0.3, 1.0)` s: the empirical spread of perception-response distributions
(Olson & Sivak 50th to 95th spans ~0.5 s) plus manoeuvre-execution variance.

**This functional form is a synthesis across adjacent literatures. No cited paper fits or
validates it on head-on data.** It is stated as such in the manuscript, it is a rule-3
contested prior, and the decision surface exists so that the paper's conclusion does not
depend on believing it.

## 3. Evasion that itself causes harm

Spainhour & Mishra (*TRR* 2069:1-8, 2008) analyse 579 fatal run-off-road crashes involving
overcorrection but never link the overcorrection to an originating conflict, so no
conditional rate is recoverable. **No study connects an avoided conflict to a downstream
run-off-road, crew-strike, or struck-from-behind outcome.** `p_evade_harm ~ LogUniform(1e-5,
1e-3)` is therefore a bounded band reported separately, never in the primary ledger.
