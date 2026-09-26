# Crash-record bounds on the violation-conflict pathway (model validity gate 1)

The model implies a head-on collision frequency per operation-day at a single shuttle-lane
site. Two independent national registers bound it, and the field-observation record bounds
the conditional probability directly. Neither is used to fit a parameter. Both are used to
disqualify a model.

## 1. Direct bound on P(collision | violation): the numerator is structurally zero

No observational study of stop-controlled work zones has ever recorded a collision, or a
head-on conflict, arising from an observed stop-line violation. The denominators:

| Sample (0 collisions in every one) | Violations observed | Rule-of-three 95% | Jeffreys 97.5% |
|---|---|---|---|
| Kansas PTS-only (Schrock et al. 2016) | 92 | 0.0326 | 0.0269 |
| Kansas all-PTS conditions | 185 | 0.0162 | 0.0135 |
| **All unattended-PTS field observation (+ Yousif UK)** | **355** | **0.0085** | **0.0070** |
| All stop-controlled work zones (+ TTI AFAD, MN, KS flagger, VA) | 433 | 0.0069 | 0.0058 |

**P(collision | violation) < 8.5e-3 at 95% confidence** from directly observed operation.
Kansas alone (n=92) does not constrain much; the pooled sample does. This is a hard ceiling,
independent of any exposure denominator, and it is the tightest thing the micro-data can say.
The true value cannot be point-estimated from direct data at all, only bounded from above,
because no study has ever observed the numerator.

## 2. Population bound on collisions per operation-day

**New Zealand (CAS).** Head-on (movement code B) at all roadworks, all control types, whole
country: 883 crashes over 1990-2025 (49 fatal, 119 serious, 283 minor, 432 non-injury),
recently about **45 per year**. Work-zone status is under-reported in CAS by a factor of
three to six (Blackman, Debnath & Haworth, 2020).

**United Kingdom (STATS19).** Head-on at all GB roadworks: about **50 per year** by a
mid-range definition (21 strict to 156 loose), of which about **1.6 fatal per year**. Fatal
reporting is near-complete, so the fatal count is a hard ceiling.

**Exposure.** UK roadworks with traffic control, from the DfT permit-scheme statistics, about
**1.5 million operation-days per year** (range 0.9M to 2.5M). NZ, inferred from CoPTTM-scale
roadworks volumes, about **0.4 million** (0.15M to 0.75M). Both are order-of-magnitude.

| Jurisdiction | Head-on at roadworks | Exposure (op-days/yr) | Rate per op-day |
|---|---|---|---|
| UK, all severities | ~50/yr | ~1.5M | **3.3e-5** |
| UK, serious + fatal | ~19/yr | ~1.5M | 1.3e-5 |
| NZ, all severities | ~45/yr | ~0.4M | **1.1e-4** |
| NZ, x6 under-report correction | ~270/yr | ~0.4M | 6.8e-4 |

Two structurally independent registers land within a factor of three of each other at
**1e-5 to 1e-4 head-on collisions per operation-day**. Both numerators are **over-counts**:
they include every roadworks type, not only single-lane portable-signal operation, so the
PTS-shuttle-specific rate is lower and the true gap wider.

### The reductio that needs no exposure denominator
A model implying 2.7 head-on collisions per operation-day at one site, run over 250 operation
days, produces 675 head-on crashes a year from a single work zone. That is fifteen times the
entire New Zealand annual total of head-on crashes at all roadworks. On the UK side it would
require all of Great Britain to run about nineteen portable-signal operation-days in a year,
in the jurisdiction where portable signals are the shuttle-lane default.

## 3. The gate

Median implied head-on collisions per operation-day at the baseline cell (300 veh/h/dir,
250 m) must lie within **[1e-6, 1e-3]**. The band admits a high-exposure rural site sitting up
to an order of magnitude above the all-roadworks national average, which is dominated by
low-volume short-section urban street works, and refuses a model producing an implausibly safe
world. The gate is symmetric and blocking.

## 4. Context: head-on is a small share of work-zone crashes

0.63% of worker-involved work-zone crashes (FIU ABC-UTC, 2021, n=14,538; rear-end 46.5%);
at most 3% (Garber & Zhao, *TRR* 1794, 2002, n=1,484, too few to itemise); 2.84% of all GB
collisions by the STATS19 proxy. The definitive two-lane flagging-station crash study
(Theiss, Finley, Rista & Ullman, TTI 0-6998-R1, 2022) pre-filtered to rear-ends and never
tabulated head-on. Queue-end rear-end is the measured hazard at this configuration.

## 5. What the record cannot establish

- **Neither register can isolate portable-signal or shuttle-lane control.** CAS carries one
  undifferentiated "Traffic Signals" value for traffic control; STATS19 has no
  portable/temporary-signal field. Every count above is an all-roadworks over-count.
- **P(collision | violation) can only be bounded above, never estimated**, because no study
  has ever observed a collision given a violation. Below the rule-of-three floor of about
  8.5e-3 the micro-data are silent.
- Exposure denominators are order-of-magnitude, known to about one order.
- STATS19 head-on is a proxy (no native manner-of-collision field; definitions span 21 to 156
  per year at roadworks) and misses damage-only crashes. CAS captures non-injury but
  under-reports work-zone status by three to six times.

## Sources
Schrock, Patil & Fitzsimmons (*TRR* 2555, 2016, DOI 10.3141/2555-09; K-TRAN KS-16-02);
Yousif, Alterawi & Henson (*AA&P* 66:147-157, 2014); Finley et al. (TTI 0-6407-1, 2012);
Finley, Songchitruksa & Jenkins (ODOT, 2015); Carlson et al. (TX, 2015); Garber & Zhao
(*TRR* 1794, 2002); FIU ABC-UTC-2016-C3-FIU03 (2021); Theiss et al. (TTI 0-6998-R1, 2022);
DfT STATS19 open data and STATS20 guidance; NZ CAS (NZTA); Blackman, Debnath & Haworth (2020).
