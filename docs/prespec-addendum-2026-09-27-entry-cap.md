# Pre-specification addendum, 27 September 2026: entries cannot exceed arriving vehicles

## Defect

The red-running tree allocates the measured entry total across the red in two types: ONSET entries (vehicles still moving when the red begins, spread uniformly over the onset window with share w_onset) and STANDING entries (the queue's lead vehicle departing against the red, spread over the rest of the red). Nothing constrains the ONSET allocation by the traffic that actually arrives in the onset window. At the baseline case the implied onset entry count exceeds the arriving vehicles in 27.66 per cent of fixed-time signal draws and 26.50 per cent of monitored-signal draws (trr/reviews/round13/entry-allocation-check.md, raised by the round-13 referee). A probability of entry above one is physically impossible.

## Correction (primary from now on)

1. In every draw, control form and grid cell, the ONSET share is capped so that the expected onset entries in the onset window do not exceed the expected arrivals in that window (per-arrival entry probability at most one).
2. The excess share moves to the STANDING type, so the total entry rate stays equal to the measured violation rate. No prior, input or other model element changes.
3. The production suite is re-run with the same seed, draws and priors; every derived output, registered number, figure and manuscript value is regenerated from the corrected run. The uncorrected run (dist e64d394_20260926) is kept as the record of version 1.2.

## Disclosure

This correction was specified after a diagnostic had estimated the effect of this same cap from saved traces (signal favourable shares nearly unchanged; attended-device shares about 0.50 to 0.56 instead of 0.45 to 0.51). The method was chosen as the minimal change that enforces the physical constraint while preserving the measured violation total, not by comparing the results of alternatives. Alternative treatments (widening the onset window; rejecting draws whose inputs are jointly incompatible) are recorded here and are not run as primaries.
