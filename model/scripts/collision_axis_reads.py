"""Regenerate R64's previously scratch-only collision-axis reads from selected traces.

Keep its original queue-tail sensitivity level (146/400000); R80/R81's later
crash-basis correction is read separately by review_reads and the decision scripts.
"""
from pathlib import Path
import json
import numpy as np
from decision_outputs_s2 import DIST, STRIKE_REC, STRIKE_C, MARGIN


def compute(dist):
    t = np.load(dist / 'baseline_traces.npz')
    p = {s: {k: t[f'part_{s}_{k}'] for k in ('W1', 'W3', 'W5', 'W4d')} for s in ('S0', 'S1a', 'S1b', 'S2')}
    anchor = float(np.median(t['diag_S1a_collisions_per_day']))
    w3 = float(np.median(p['S0']['W3']))
    qs = (146 / 4e5) / float(np.median(p['S0']['W1']))
    def delta(s, c, h, q):
        return q * (p[s]['W1'] - p['S0']['W1']) + p[s]['W4d'] + p[s]['W3'] - h / w3 * p['S0']['W3'] + c / anchor * (p[s]['W5'] - p['S0']['W5'])
    def prob(a):
        return round(float(np.mean(a < 0)), 3)
    out = dict(collision_axis_anchor_s1a_collisions_median=anchor,
               collision_record_band=[1e-5, 1e-4], collision_record_central=3.3e-5)
    for s in ('S1a', 'S1b', 'S2'):
        out[s] = {}
        for name, q in [('qt_excluded', 0), ('qt_panel', 1), ('qt_record_scaled', qs)]:
            d = delta(s, 3.3e-5, STRIKE_C, q)
            corners = {f'c{c}_s{h}': prob(delta(s, c, h, q)) for c in (1e-5, 1e-4) for h in STRIKE_REC}
            out[s][name] = dict(central=prob(d), corners=corners, min=min(corners.values()), max=max(corners.values()),
                               median_dh=float(np.median(d)), p_within_margin=float(np.mean(np.abs(d) <= MARGIN)))
    out['implied_serious_harm_at_signals_when_collisions_pinned'] = {str(c): c / anchor * float(np.median(p['S1a']['W5'])) for c in (1e-5, 3.3e-5, 1e-4)}
    out['s2_vs_s1a_p_s2_lower_collision_axis_central'] = round(float(np.mean(delta('S2', 3.3e-5, STRIKE_C, 0) < delta('S1a', 3.3e-5, STRIKE_C, 0))), 2)
    return out


def main():
    (DIST / 'collision_axis_reads.json').write_text(json.dumps(compute(DIST), indent=2) + '\n')

if __name__ == '__main__':
    main()
