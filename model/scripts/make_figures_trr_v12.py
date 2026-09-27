"""Build the TRR displays from the entry-cap-corrected capfix_20260927 outputs.

Run: python3 model/scripts/make_figures_trr_v12.py
For PNG-only layout edits: python3 model/scripts/make_figures_trr_v12.py --png-only
No sampling, model execution, prior changes, or newest-directory selection occurs.
Only the nine explicitly named PNGs are written in manuscript/figures. Vector
copies and a provenance/print-size audit are also written unless --png-only is set.
Asset names retain the blueprint identifiers. Round 10 places the signed-change
display before the device comparison and reserves the avoidance-model display
for the supplement; manuscript captions supply the current display numbers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/trr-v12-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text as mtext
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "model/outputs/dist/capfix_20260927"
OUT = ROOT / "trr/manuscript/figures"
BUILD = DIST / "figures"
AUDIT = DIST / "figure-audit.json"
WIDTH, DPI, MIN_FONT_PT = 6.5, 400, 9.0

# Reused from make_figures_trr.py: typeface, ink/grey/grid colours, spine and
# grid weights, and 400 dpi. Use a 10 pt default and a fixed canvas instead of
# bbox='tight': 9 pt must remain 9 pt when the PNG is placed at 6.5 inches.
INK, MUTED, GRID = "#1a1a19", "#5b5b58", "#d9d9d6"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.labelsize": 9,
    "axes.titlesize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.fontsize": 9, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.labelcolor": INK, "grid.color": GRID, "grid.linewidth": 0.5,
    "figure.dpi": DPI, "savefig.dpi": DPI, "savefig.bbox": None,
    "pdf.fonttype": 42, "axes.unicode_minus": True,
    "mathtext.fontset": "dejavusans", "axes.formatter.use_mathtext": True,
})

# One naming, ordering and visual contract throughout the new display set.
# Matching conventions use solid/dashed ECDFs only in Figure 4, where the
# two panels are pathway distributions, not competing strategies.
STRATEGIES = {
    "S0": dict(name="manual control", color=INK, ls="-", marker="o", fill="white"),
    "S1a": dict(name="fixed-time signals", color=INK, ls="-", marker="o", fill=INK),
    "S1b": dict(name="monitored signals", color="#555555", ls=":", marker="^", fill="white"),
    "S2": dict(name="attended device", color="#666666", ls="--", marker="s", fill="white"),
}
FILES = (
    "fig1_substitution.png", "fig2_event_chain.png", "fig4_calibration.png",
    "fig5_signal_maps.png", "fig6_device_exposure.png", "fig7_change_intervals.png",
    "fig8_model_form.png", "fig9_sight.png", "figS6_grid.png",
)
INPUTS = (
    "baseline_traces.npz", "review_reads.json", "decision_summary_s2.json",
    "operator_reference_variants.json", "welfare_summary.json", "validity_gates.json",
    "decision_surface.npz", "model_form_sensitivity.csv", "sight_sweep.csv",
    "grid_results_primary.csv", "figure_checks.json",
)


def read_json(name):
    return json.loads((DIST / name).read_text())


def read_csv(name):
    with (DIST / name).open() as f:
        return list(csv.DictReader(f))


def close(actual, expected, name, rtol=1e-10, atol=1e-14):
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        raise AssertionError(f"{name}: {actual!r} != saved {expected!r}")


def sci(x, digits=2):
    """Print notation, preserving the original mantissa precision."""
    mantissa, exponent = f"{x:.{digits}e}".split("e")
    return rf"${mantissa}\times 10^{{{int(exponent)}}}$"


def scaled_sci(x, exponent=-5, digits=2):
    """The same rounded value as sci(), expressed under a shared axis factor."""
    from decimal import Decimal
    return format(Decimal(f"{x:.{digits}e}").scaleb(-exponent), "f")


def canvas(height):
    fig = plt.figure(figsize=(WIDTH, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, WIDTH), ylim=(0, height))
    ax.axis("off")
    return fig, ax


def text(ax, x, y, s, size=9, ha="left", va="center", **kwargs):
    return ax.text(x, y, s, fontsize=size, ha=ha, va=va, linespacing=1.22, **kwargs)


def box(ax, x, y, w, h, label, size=9, fc="white", ec=MUTED):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=.8))
    text(ax, x+w/2, y+h/2, label, size, ha="center")


def arrow(ax, start, end, dashed=False, both=False, color=INK, lw=1):
    p = FancyArrowPatch(start, end, arrowstyle="<->" if both else "-|>",
                        mutation_scale=9, linewidth=lw, color=color,
                        linestyle="--" if dashed else "-", shrinkA=2, shrinkB=2)
    ax.add_patch(p)
    return p


def clean(ax, grid_axis="x"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis=grid_axis, color=GRID, linewidth=.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", length=3, pad=3)


def person(ax, x, y):
    ax.add_patch(Circle((x, y+.045), .024, facecolor=INK, edgecolor=INK))
    ax.plot([x, x], [y+.02, y-.06], c=INK, lw=1)
    ax.plot([x-.04, x, x+.04], [y-.10, y-.055, y-.10], c=INK, lw=1)
    ax.plot([x-.042, x+.042], [y-.012, y-.012], c=INK, lw=1)


def strategy_handle(s):
    d = STRATEGIES[s]
    return Line2D([], [], color=d["color"], ls=d["ls"], marker=d["marker"],
                  markerfacecolor=d["fill"], markersize=4, lw=1.3, label=d["name"])


class Data:
    def __init__(self):
        self.d = read_json("decision_summary_s2.json")
        self.r = read_json("review_reads.json")
        self.variants = read_json("operator_reference_variants.json")["variants"]
        self.welfare = read_json("welfare_summary.json")
        self.gates = read_json("validity_gates.json")
        with np.load(DIST / "baseline_traces.npz") as saved:
            self.b = {k: saved[k] for k in saved.files}
        needed = [f"part_{s}_{w}" for s in STRATEGIES for w in ("W3", "W4d", "W5")]
        needed += ["draw_reach_alpha", "draw_offset_op_m"]
        self.finite = np.logical_and.reduce([np.isfinite(self.b[k]) for k in needed])
        self.b = {k: v[self.finite] if v.shape == self.finite.shape else v
                  for k, v in self.b.items()}
        self.w = self.b["part_S0_W3"]
        self.v = {s: self.b[f"part_{s}_W5"] for s in STRATEGIES}
        self.a = {s: self.b[f"part_{s}_W4d"] for s in STRATEGIES}
        self.c, self.h = 1e-5, 1.2e-5  # R13 / R24 / R43 / R64
        self.cband, self.hband = self.d["strike_record_band"], self.d["headon_record_band"]
        self.rows = [
            ("signals_median", "S1a", "medians matched", self.delta("S1a")),
            ("signals_mean", "S1a", "means matched", self.delta("S1a", match="mean")),
            ("device_tied_0m", "S2", "tied exposure, 0 m", self.delta("S2", mode="tied", ref=0)),
            ("device_tied_1m", "S2", "tied exposure, 1 m", self.delta("S2", mode="tied", ref=1)),
            ("device_encroachment", "S2", "encroachment", self.delta("S2")),
            ("device_independent_0m", "S2", "independent scaling, 0 m", self.delta("S2", mode="independent")),
        ]
        self.check_saved_values()

    def delta(self, s, c=None, h=None, match="median", mode="encroachment", ref=0, own=False):
        c, h = self.c if c is None else c, self.h if h is None else h
        centre = np.median if match == "median" else np.mean
        l3 = c / centre(self.w)
        l5 = h / centre(self.v["S2" if own else "S1a"])
        operator = 0
        if s == "S2":
            if mode == "tied":
                operator = l3*self.w*np.exp(-self.b["draw_reach_alpha"]*(self.b["draw_offset_op_m"]-ref))
            elif mode == "independent":
                k = self.variants[f"like_for_like_ref_{ref:.1f}m_two_operators"]["k_op"]
                operator = k*self.b["part_S2_W3"]*(c/self.c)
            else:
                operator = self.b["part_S2_W3"]
        return self.a[s] + operator - l3*self.w + l5*(self.v[s]-self.v["S0"])

    def summary(self, arr):
        q = np.quantile(arr, [.05, .25, .5, .75, .95])
        return dict(zip(("q05", "q25", "median", "q75", "q95"), map(float, q)),
                    mean=float(np.mean(arr)), p_lower=float(np.mean(arr < 0)))

    def corners(self, **kwargs):
        p = [float(np.mean(self.delta(c=c, h=h, **kwargs) < 0))
             for c in self.cband for h in self.hband]
        return [min(p), max(p)]

    def check_saved_values(self):
        d, r = self.d, self.r
        for s in ("S1a", "S1b", "S2"):
            a = self.delta(s)
            close(np.mean(a < 0), d[f"{s.lower()}_p_at_record_central"], f"{s} probability")
        for s in ("S1a", "S2"):
            a = self.delta(s)
            close(np.median(a), d[f"{s.lower()}_dh_median_at_record"], f"{s} median")
            close(np.mean(a), self.welfare[s]["primary_dh_mean"], f"{s} mean")
        a = self.delta("S1a", match="mean")
        close(np.mean(a < 0), r["R56_mean_matched"]["S1a"], "R56")
        for stat in ("mean", "median"):
            close(getattr(np, stat)(a), self.welfare["S1a"][f"mean_matched_dh_{stat}"], f"R62 {stat}")
        for ref in (0, 1):
            a = self.delta("S2", mode="tied", ref=ref)
            row = r["R71_R75_tied_operator"][f"reference_{ref}m"]
            close(np.mean(a < 0), row["p"], f"R75 {ref}m")
            close(self.corners(s="S2", mode="tied", ref=ref), row["p_corners_min_max"], "R75 corners")
            close(np.mean(a < self.delta("S1a")), row["p_s2_below_s1a"], "R75 device vs signals")
            for stat in ("median", "mean"):
                close(getattr(np, stat)(a), r["R83_tied_device_priced"][f"reference_{ref}m"][f"dh_{stat}"], "R83")
        for ref in (0, 1):
            row = self.variants[f"like_for_like_ref_{ref:.1f}m_two_operators"]
            a = self.delta("S2", mode="independent", ref=ref)
            close(np.mean(a < 0), row["p"], "R68")
            close(self.corners(s="S2", mode="independent", ref=ref), row["p_corners_min_max"], "R68 corners")
        close(self.corners(s="S2"), self.variants["pre_specified_two_operators"]["p_corners_min_max"], "R68 fixed operator")
        close(np.median(self.w), d["w3_anchor_s0_median"], "controller anchor")
        close(np.median(self.v["S1a"]), d["w5_anchor_s1a_median"], "head-on anchor")
        close(np.quantile(self.w*self.c/np.median(self.w), [.05, .95]),
              d["scaled_strike_q05_q95"], "R45 strike interval")
        close(np.quantile(self.v["S1a"]*self.h/np.median(self.v["S1a"]), [.05, .95]),
              d["scaled_headon_q05_q95"], "R45 head-on interval")
        self.intervals = {key: self.summary(arr) for key, _, _, arr in self.rows}


def fig1(data):
    fig, ax = canvas(4.0)
    ax.set_ylim(.4, 4.4)
    text(ax, .18, 4.23, "Same site: 300 vehicles/hour/direction · 250 m between stop lines · 8-hour day")
    xs = [2.12, 3.82, 5.52]
    for x, s in zip(xs, ("S0", "S1a", "S2")):
        text(ax, x, 3.95, STRATEGIES[s]["name"], ha="center", size=9.5, weight="bold")
        # Identical road/closure geometry; both human roles remain on the shoulder.
        ax.add_patch(Rectangle((x-.23, 2.67), .46, 1.06, fc="#f3f3f3", ec=MUTED, lw=.7))
        ax.plot([x, x], [2.67, 3.73], c=MUTED, ls=":", lw=.7)
        ax.add_patch(Rectangle((x+.025, 2.95), .19, .48, fc="#dddddd", hatch="////", ec=MUTED, lw=.6))
        ax.plot([x-.23, x], [2.80, 2.80], c=INK, lw=1.5)
        ax.plot([x, x+.23], [3.60, 3.60], c=INK, lw=1.5)
        arrow(ax, (x-.12, 2.96), (x-.12, 3.20), lw=.8)
        arrow(ax, (x-.12, 3.51), (x-.12, 3.27), lw=.8)
        if s == "S0":
            person(ax, x-.34, 2.82)
            person(ax, x+.34, 3.61)
        else:
            for dx, y in ((-.24, 2.81), (.24, 3.60)):
                if s == "S1a":
                    ax.add_patch(Circle((x+dx, y), .045, fc=INK))
                else:
                    ax.add_patch(Rectangle((x+dx-.038, y-.038), .076, .076, ec=INK, fc="white"))
                    ax.plot([x+dx, x+dx+(.22 if dx < 0 else -.22)], [y, y], c=INK, lw=1.5)
            if s == "S2":
                person(ax, x-.50, 2.82)
                person(ax, x+.50, 3.61)
    text(ax, .18, 3.51, "Schematic plans")
    text(ax, .18, 3.20, "Hatching:\nclosure")
    text(ax, .18, 2.89, "People on\nthe shoulder")
    for x, t in zip(xs, ("Radio hold", "Scheduled release", "Operator hold")):
        text(ax, x, 2.47, t, ha="center")
    labels = ["Person exposure", "Place/retrieve units", "Red-running head-ons", "Queue-tail difference", "Release control"]
    cells = [
        ["Controller retained", "Controller removed", "Two operators retained\nfurther from lane"],
        ["Not added", "Added", "Added"],
        ["Retained", "Changed", "Changed"],
        ["Reference", "Excluded", "Cancels"],
        ["Human confirmation", "Fixed schedule", "Human confirmation"],
    ]
    y = 2.27
    for i, (lab, vals) in enumerate(zip(labels, cells)):
        step = .40 if i == 0 else .29
        ax.plot([.17, 6.32], [y, y], c=GRID, lw=.6)
        text(ax, .18, y-step/2, lab)
        for x, value in zip(xs, vals):
            text(ax, x, y-step/2, value, ha="center")
        y -= step
    ax.plot([.17, 6.32], [y, y], c=GRID, lw=.6)
    return fig


def fig2(data):
    fig, ax = canvas(4.3)
    ax.set_ylim(.5, 4.8)
    b = data.b
    vals = [np.median(b[f"diag_S1a_{k}"]) for k in ("facing_per_day", "violations_per_day", "conflicts_per_day", "collisions_per_day")]
    vals += [np.median(data.v["S1a"])]
    # R8 precision; do not sum/subtract marginal medians or imply observed conversion.
    ladder = [f"{vals[0]:,.0f}", f"{vals[1]:.0f}", f"{vals[2]:.3f}", sci(vals[3]), sci(vals[4])]
    close(vals[3], data.gates["headon_collisions_per_op_day"], "R8 collisions")
    text(ax, .18, 4.60, "a   Fixed-time signals · marginal medians / operation day (before calibration)", weight="bold")
    stages = ["Facing red", "Entries", "Encounters", "Collisions", "Serious harm"]
    xs = np.linspace(.18, 5.30, 5)
    for i, (x, name, val) in enumerate(zip(xs, stages, ladder)):
        box(ax, x, 3.94, 1.02, .45, name+"\n"+val)
        if i < 4:
            arrow(ax, (x+1.02, 4.165), (xs[i+1], 4.165))
    no = ["No entry", "Empty\ncrossing", "Successful\navoidance", "No serious\ninjury"]
    for x, lab in zip(xs[:4], no):
        arrow(ax, (x+.51, 3.94), (x+.51, 3.71), color=MUTED)
        text(ax, x+.51, 3.55, lab, ha="center")
    arrow(ax, (xs[2]+.51, 3.34), (4.12, 3.10), dashed=True, color=MUTED)
    text(ax, 4.20, 3.10, "Avoidance harm\nseparately assessed")
    ax.plot([.18, 6.32], [2.73, 2.73], c=GRID, lw=.7)
    text(ax, .18, 2.55, "b   Time since red onset · schematic timing", weight="bold")
    start, release, end = 1.70, 4.37, 5.94
    for y, lab, entry, leave in ((2.10, "Early entry", 2.03, 3.70), (1.47, "Later entry", 3.03, 5.23)):
        text(ax, .18, y, lab)
        ax.add_patch(Rectangle((start, y-.12), release-start, .24, fc="#eeeeee", ec="none"))
        arrow(ax, (start, y), (end, y), color=MUTED, lw=.7)
        ax.plot([entry, leave], [y, y], c=INK, lw=2)
        ax.plot([entry, leave], [y, y], ls="", marker="|", c=INK, ms=9)
        text(ax, entry, y+.23, "entry", ha="center")
        text(ax, leave, y+.23, "exit", ha="center")
        text(ax, start, y-.23, "0", ha="center")
    ax.plot([release, release], [1.30, 2.29], c=INK, ls=":", lw=.9)
    text(ax, 4.55, 2.34, "Opposing release", ha="center")
    text(ax, 2.17, 1.80, "All-red", ha="center")
    arrow(ax, (release, 1.15), (5.55, 1.15), dashed=True)
    text(ax, 4.70, .97, "Human hold, only if effective", ha="center")
    text(ax, 2.68, 1.16, "Mutual sight\nat encounter", ha="center")
    arrow(ax, (3.28, 1.29), (4.77, 1.48), color=MUTED, lw=.7)
    clearance = np.median(b["diag_S1a_clearance_s"])
    safe = np.median(b["diag_S1a_p_safe_window"])
    # p_safe_window integrates the no-occupancy/no-next-encounter indicator
    # against onset/standing candidate weights, BEFORE visible-entry weighting.
    # It is neither an elapsed-red fraction nor protection before release.
    text(ax, .18, .73, f"Median all-red: {clearance:.1f} s; encounter-free candidate-entry share: {safe:.0%}.")
    return fig


def fig4(data):
    fig, ax = canvas(4.6)
    box(ax, .18, 3.85, 1.72, .50, "Occupational counts\nand assumed exposure")
    arrow(ax, (1.90, 4.10), (2.16, 4.10))
    box(ax, 2.16, 3.85, 1.80, .50, "Controller-strike\nreference level")
    box(ax, .18, 3.18, 1.72, .50, "Roadworks counts\nand assumed exposure")
    arrow(ax, (1.90, 3.43), (2.16, 3.43))
    box(ax, 2.16, 3.18, 1.80, .50, "Assumed signal\nhead-on level")
    arrow(ax, (3.96, 3.43), (4.22, 3.43))
    box(ax, 4.22, 3.18, 2.10, .50, "One multiplier for all\nhead-on branches")
    text(ax, .18, 2.89, "Constructed reference levels set the scale; relative rates come from the event tree.")
    axes = [fig.add_axes([.105, .22, .365, .29]), fig.add_axes([.59, .22, .365, .29])]
    curves = []
    for arr, anchor in ((data.w, data.c), (data.v["S1a"], data.h)):
        curves.extend([arr*anchor/np.median(arr), arr*anchor/np.mean(arr)])
    limits = [min(np.quantile(a, .005) for a in curves), max(np.quantile(a, .995) for a in curves)]
    limits = (10**np.floor(np.log10(limits[0])), 10**np.ceil(np.log10(limits[1])))
    for i, (plot, arr, central, band, lab) in enumerate(zip(axes, (data.w, data.v["S1a"]), (data.c, data.h), (data.cband, data.hband), ("Controller harm", "Signal head-on harm"))):
        plot.axvspan(*band, fc="#dddddd", zorder=0)
        plot.axvline(central, color=MUTED, ls=":", lw=1)
        for method, ls in ((np.median, "-"), (np.mean, "--")):
            x = np.sort(arr*central/method(arr))
            plot.step(x, np.arange(1, len(x)+1)/len(x), where="post", c=INK, ls=ls, lw=1.15)
        plot.set(xscale="log", xlim=limits, ylim=(0, 1), yticks=[0, .5, 1])
        plot.set_xticks(10.0**np.arange(int(np.log10(limits[0])), int(np.log10(limits[1]))+1, 2))
        plot.xaxis.set_minor_locator(ticker.NullLocator())
        plot.xaxis.set_major_formatter(ticker.LogFormatterSciNotation())
        clean(plot, "y")
        plot.text(.02, 1.08, lab, transform=plot.transAxes, fontsize=9, weight="bold")
        inside = np.mean((arr*central/np.median(arr) >= band[0]) & (arr*central/np.median(arr) <= band[1]))
        key = "share_of_scaled_strike_draws_inside_band" if i == 0 else "share_of_scaled_headon_draws_inside_band"
        close(inside, data.d[key], "R45 band share")
        plot.text(.03, .90, f"{inside:.0%} inside band\n(medians matched)", transform=plot.transAxes, fontsize=9, va="top")
    axes[0].set_ylabel("Cumulative share of draws", labelpad=4)
    fig.text(.53, .145, "Serious-harm events / operation day (log scale)", fontsize=9, ha="center")
    handles = [Line2D([], [], c=INK, lw=1.2, ls="--", label="Means matched"), Line2D([], [], c=INK, lw=1.2, label="Medians matched (sensitivity)"), Rectangle((0, 0), 1, 1, fc="#dddddd", label="Constructed reference band"), Line2D([], [], c=MUTED, ls=":", label="Reference central")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.5, .015), ncol=2, frameon=False, columnspacing=1.8)
    return fig


def log_axis(lo, hi, centre):
    vals = np.geomspace(lo, hi, 61)
    vals[np.argmin(abs(vals-centre))] = centre
    return np.sort(vals)


def maps(data):
    hs = log_axis(*data.hband, data.h)
    cs = log_axis(*data.cband, data.c)
    grids = {}
    # All points are a re-read of the same saved finite draw pairs. No RNG.
    for match, reducer in (("median", np.median), ("mean", np.mean)):
        removed = data.w/reducer(data.w)
        headon = (data.v["S1a"]-data.v["S0"])/reducer(data.v["S1a"])
        grid = np.empty((len(cs), len(hs)))
        for i, c in enumerate(cs):
            grid[i] = np.mean(data.a["S1a"][None, :] - c*removed + hs[:, None]*headon < 0, axis=1)
        close(grid[np.where(cs == data.c)[0][0], np.where(hs == data.h)[0][0]],
              np.mean(data.delta("S1a", match=match) < 0), "surface centre")
        grids[match] = grid
    # Independently check selected coordinates of the original saved median map.
    with np.load(DIST / "decision_surface.npz") as old:
        close(old["w5_median"], np.median(data.v["S1a"]), "original surface anchor")
        for i, j in ((0, 0), (20, 40), (30, 30), (60, 60)):
            actual = np.mean(data.delta("S1a", c=old["controller_dsi_per_day"][i], h=old["lam_w5"][j]*old["w5_median"]) < 0)
            close(actual, old["p_grid"][i, j], "original surface grid", atol=5e-5)
    return hs, cs, grids


def fig5(data):
    fig = plt.figure(figsize=(WIDTH, 3.8))
    axes = [fig.add_axes([.175, .36, .305, .47]), fig.add_axes([.63, .36, .305, .47])]
    hs, cs, grids = data.maps
    for ax, method, lab in zip(axes, ("mean", "median"), ("Means matched", "Medians matched (sensitivity)")):
        im = ax.pcolormesh(hs, cs, grids[method], cmap="Greys", vmin=0, vmax=1, shading="nearest")
        ax.contour(hs, cs, grids[method], levels=[.5], colors="white", linewidths=2.6)
        ct = ax.contour(hs, cs, grids[method], levels=[.5], colors=INK, linewidths=.9)
        ax.clabel(ct, fmt={.5: "0.5"}, fontsize=9, inline=True)
        ax.plot(data.h, data.c, "o", ms=5, mfc="white", mec=INK)
        offset, align = ((7, -15), "left") if method == "median" else ((-7, 8), "right")
        ax.annotate(f"{np.mean(data.delta('S1a', match=method) < 0):.2f}", (data.h, data.c), xytext=offset, ha=align, textcoords="offset points", fontsize=10, weight="bold", bbox=dict(fc="white", ec="none", pad=1.2))
        ax.set(xscale="log", yscale="log", xlim=data.hband, ylim=data.cband)
        ax.set_xticks([6e-6, 1.2e-5, 2e-5])
        ax.set_yticks([5e-6, 1e-5, 2e-5])
        ax.xaxis.set_major_formatter(ticker.LogFormatterSciNotation(minor_thresholds=(np.inf, np.inf)))
        ax.yaxis.set_major_formatter(ticker.LogFormatterSciNotation(minor_thresholds=(np.inf, np.inf)))
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.yaxis.set_minor_locator(ticker.NullLocator())
        ax.text(.5, 1.10, lab, ha="center", transform=ax.transAxes, fontsize=10, weight="bold")
        if method == "median":
            corners = list(data.d["s1a_p_at_record_corners"].values())
            ax.text(.04, .04, f"Corners: {min(corners):.2f} to {max(corners):.2f}", transform=ax.transAxes,
                    fontsize=9, bbox=dict(fc="white", ec="none", pad=1.2))
    axes[0].set_ylabel("Constructed controller reference\n(events / operation day)", labelpad=4)
    fig.text(.53, .26, "Assumed signal head-on reference (serious-harm events / operation day)", ha="center", fontsize=9)
    cax = fig.add_axes([.29, .145, .39, .025])
    colorbar = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[0, .5, 1])
    colorbar.solids.set_rasterized(False)
    fig.text(.5, .20, "Share of draws favouring fixed-time signals over manual control", ha="center", fontsize=9)
    fig.text(.5, .049, "Selected reference ranges; 0.5 marks half the parameter draws.", fontsize=9, ha="center")
    return fig


def device_rows(data):
    rows = []
    for ref in (0, 1):
        rows.append((f"Tied exposure, {ref} m", data.r["R71_R75_tied_operator"][f"reference_{ref}m"], True))
    for label, key in (("Encroachment", "pre_specified_two_operators"), ("Independent scaling, 0 m", "like_for_like_ref_0.0m_two_operators"), ("Independent scaling, 1 m", "like_for_like_ref_1.0m_two_operators")):
        rows.append((label, data.variants[key], False))
    d = data.d
    rows.append(("Own anchor + encroachment", dict(p=d["s2_own_anchor_p_at_record_central"], p_corners_min_max=d["s2_own_anchor_p_worst_best"], p_s2_below_s1a=d["s2_own_anchor_vs_s1a_p_s2_lower"]), False))
    a = data.delta("S2", mode="independent", own=True)
    joint = dict(p=float(np.mean(a < 0)), p_corners_min_max=data.corners(s="S2", mode="independent", own=True), p_s2_below_s1a=float(np.mean(a < data.delta("S1a")) ))
    # Check the selected run's independently regenerated scratch reading.
    registered = read_json("figure_checks.json")["R49"]
    close(joint["p"], registered["p"], "R49")
    close(joint["p_corners_min_max"], registered["corners_min_max"], "R49 corners")
    close(joint["p_s2_below_s1a"], registered["p_s2_below_s1a"], "R49 against signals")
    rows.append(("Own anchor + independent, 0 m", joint, False))
    return rows


def fig6(data):
    fig, ax = canvas(5.4)
    text(ax, .18, 5.16, "Manual control → attended device (two operators)", weight="bold")
    ax.add_patch(Rectangle((.20, 3.95), 1.25, .70, fc="#ededed", ec="none"))
    text(ax, .82, 4.30, "Travelled lane", ha="center")
    ax.plot([1.45, 1.45], [3.84, 4.66], c=INK, lw=1.2)
    text(ax, 1.45, 3.70, "Edge", ha="center")
    person(ax, 1.55, 4.25)
    person(ax, 2.47, 4.25)
    person(ax, 4.70, 4.25)
    text(ax, 2.12, 4.85, "Reference: 0 or 1 m", ha="center")
    text(ax, 4.73, 4.85, "Operator: sampled 1.5 to 6 m", ha="center")
    arrow(ax, (2.73, 4.23), (4.44, 4.23))
    retained = data.r["R82_queue_tail_share_and_retained_exposure"]["tied_retained_fraction_ref_0m"]["median"]
    text(ax, 3.80, 3.83, f"Tied 0 m: {retained:.0%} exposure retained\n(median draw)", ha="center")
    rows = data.device_rows[:3]  # Adopted references and original encroachment sensitivity.
    plot = fig.add_axes([.405, .155, .37, .445])
    ys = [2, 1, 0]
    for y, (label, row, adopted) in zip(ys, rows):
        lo, hi = row["p_corners_min_max"]
        plot.plot([lo, hi], [y, y], color=STRATEGIES["S2"]["color"], ls="--", lw=1.1)
        plot.plot([lo, hi], [y, y], ls="", marker="|", c=MUTED, ms=6)
        plot.plot(row["p"], y, "s", mec=INK, mfc="white", ms=5)
        plot.annotate(f"{row['p']:.2f}", (row["p"], y), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=9, weight="bold" if adopted else "normal", bbox=dict(fc="white", ec="none", pad=.2))
        plot.text(-.07, y, label, transform=plot.get_yaxis_transform(), ha="right", va="center", fontsize=9, weight="bold" if adopted else "normal")
        plot.text(1.32, y, f"{row['p_s2_below_s1a']:.3f}", transform=plot.get_yaxis_transform(), ha="center", va="center", fontsize=9)
    plot.set(xlim=(0, 1), ylim=(-.6, 2.9), xticks=[0, .5, 1], yticks=[])
    plot.axvline(.5, c=GRID, lw=.8, zorder=0)
    plot.text(.5, 1.03, "Share below\nmanual control", ha="center", va="bottom", transform=plot.transAxes, fontsize=9)
    plot.text(1.32, 1.03, "Share below\nfixed-time signals", ha="center", va="bottom", transform=plot.transAxes, fontsize=9)
    clean(plot)
    plot.spines["left"].set_visible(False)
    text(ax, .18, .25, "Medians matched; whiskers: selected calibration corners. Distances schematic.")
    return fig


def fig7(data):
    fig = plt.figure(figsize=(WIDTH, 4.4))
    left, right = fig.add_axes([.35, .22, .26, .60]), fig.add_axes([.675, .22, .29, .60])
    display_keys = ("signals_mean", "signals_median", "device_tied_0m", "device_tied_1m")
    rows = [next(row for row in data.rows if row[0] == key) for key in display_keys]
    allstats = [data.intervals[key] for key in display_keys]
    full = (min(s["q05"] for s in allstats)*1.08, max(s["q95"] for s in allstats)*1.08)
    ranges = (full, (-1e-5, 1e-5))
    for panel, (ax, limits) in enumerate(zip((left, right), ranges)):
        for y, (key, strategy, label, arr) in enumerate(rows):
            row = data.intervals[key]
            sty = STRATEGIES[strategy]
            lo, hi = limits
            ax.plot([max(lo, row["q05"]), min(hi, row["q95"])], [y, y], c=sty["color"], ls=sty["ls"], lw=.9)
            ax.plot([max(lo, row["q25"]), min(hi, row["q75"])], [y, y], c=sty["color"], ls=sty["ls"], lw=3)
            if panel:
                for q, edge, mark in (("q05", lo, "<"), ("q95", hi, ">")):
                    if row[q] < lo or row[q] > hi:
                        ax.plot(edge, y, marker=mark, color=sty["color"], ms=4, clip_on=False)
            ax.plot(row["median"], y, marker="o", mec=INK, mfc="white", ms=4, zorder=5)
            if lo <= row["mean"] <= hi:
                ax.plot(row["mean"], y, marker="D", mec=INK, mfc=INK, ms=3.5, zorder=4)
            elif panel:
                positive = row["mean"] > hi
                ax.annotate("mean →" if positive else "← mean", (hi if positive else lo, y),
                            xytext=(-2 if positive else 2, 7), textcoords="offset points",
                            ha="right" if positive else "left", fontsize=9)
        ax.axvline(0, c=MUTED, ls=":", lw=1)
        ax.set(xlim=limits, ylim=(3.65, -.65), yticks=[])
        clean(ax)
        ax.spines["left"].set_visible(False)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(3))
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: "0" if v == 0 else f"{v/1e-5:g}".replace("-", "−")))
        ax.text(.5, 1.12, "Full 5th to 95th span" if panel == 0 else "Enlargement", transform=ax.transAxes, ha="center", fontsize=9, weight="bold")
    right.set_xticks([-1e-5, 0, 1e-5])
    left.set_xticks([-5e-5, 0, 5e-5, 1e-4])
    left.set_xlim(full)
    for y, (key, strategy, label, _) in enumerate(rows):
        prefix = STRATEGIES[strategy]["name"]
        left.text(-.08, y, prefix+"\n"+label, transform=left.get_yaxis_transform(), ha="right", va="center", fontsize=9)
    fig.text(.64, .125, r"Change in serious-harm events / operation day ($\times 10^{-5}$)", ha="center", fontsize=9)
    handles = [Line2D([], [], c=INK, lw=.9, label="5th to 95th"), Line2D([], [], c=INK, lw=3, label="25th to 75th"), Line2D([], [], c=INK, marker="o", mfc="white", ls="", label="Median"), Line2D([], [], c=INK, marker="D", ls="", label="Mean")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.58, .98), ncol=4, frameon=False, columnspacing=1.0, handlelength=1.4)
    fig.text(.5, .045, "Negative: harm falls; arrows: off-scale intervals or means.", ha="center", fontsize=9)
    return fig


def fig8(data):
    fig = plt.figure(figsize=(WIDTH, 3.6))
    axes = [fig.add_axes([.32, .23, .28, .54]), fig.add_axes([.69, .23, .28, .54])]
    rows = read_csv("model_form_sensitivity.csv")
    forms = list(dict.fromkeys(r["form"] for r in rows))
    labels = ["Independent failures", "Common cause, 0.5", "Common cause, 1.0", "Threshold", "Log-logistic"]
    axes[0].axvspan(1e-5, 1e-4, fc="#e6e6e6", zorder=0)
    ceiling = data.gates["gate1_band"][1]
    axes[0].axvline(ceiling, c=MUTED, ls=":", lw=1)
    for i, form in enumerate(forms):
        for s, dy in (("S1a", -.12), ("S2", .12)):
            row = next(r for r in rows if r["form"] == form and r["strategy"] == s)
            sty = STRATEGIES[s]
            collision = float(row["implied_collisions_per_op_day"])
            for ax, x in zip(axes, (collision, float(row["p_dh_neg_record_central"]))):
                ax.plot(x, i+dy, marker=sty["marker"], ms=4.5, mfc=sty["fill"], mec=sty["color"], ls="")
            if collision > ceiling:
                axes[0].plot(collision, i+dy, "x", ms=8, c=INK, mew=1)
    for ax in axes:
        ax.set(ylim=(4.6, -.65), yticks=[])
        clean(ax)
        ax.spines["left"].set_visible(False)
    for i, label in enumerate(labels):
        axes[0].text(-.05, i, label, transform=axes[0].get_yaxis_transform(), ha="right", va="center", fontsize=9)
    axes[0].set(xscale="log", xlim=(8e-6, 2.4e-3))
    axes[0].set_xticks([1e-5, 1e-4, 1e-3])
    axes[0].xaxis.set_major_formatter(ticker.LogFormatterSciNotation())
    axes[0].xaxis.set_minor_locator(ticker.NullLocator())
    axes[1].set(xlim=(0, 1), xticks=[0, .5, 1])
    axes[0].set_xlabel("Collisions / operation day", labelpad=5)
    axes[1].set_xlabel("Share below manual control", labelpad=5)
    axes[0].text(.5, 1.12, "Before calibration", ha="center", transform=axes[0].transAxes, fontsize=9, weight="bold")
    axes[1].text(.5, 1.12, "Matched to reference levels", ha="center", transform=axes[1].transAxes, fontsize=9, weight="bold")
    handles = [strategy_handle(s) for s in ("S1a", "S2")]
    handles[1].set_label("Attended device: encroachment sensitivity")
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.55, 1.0), ncol=1, frameon=False)
    fig.text(.025, .040, r"Grey: constructed collision reference; dotted: $10^{-3}$ ceiling; cross: failed check.", fontsize=9)
    return fig


def fig9(data):
    fig = plt.figure(figsize=(WIDTH, 3.4))
    axes = [fig.add_axes([.12, .24, .34, .56]), fig.add_axes([.60, .24, .34, .56])]
    rows = read_csv("sight_sweep.csv")
    for ax, length in zip(axes, (250, 1000)):
        rr = [r for r in rows if int(r["section_m"]) == length]
        x = np.array([float(r["sight_m"]) for r in rr])
        for s in ("S1a", "S2"):
            sty = STRATEGIES[s]
            y = np.array([float(r[f"w5_{s.lower()}_median"]) for r in rr])
            collisions = np.array([float(r[f"collisions_day_{s.lower()}"]) for r in rr])
            ax.plot(x, y, color=sty["color"], ls=sty["ls"], marker=sty["marker"], mfc=sty["fill"], ms=4, lw=1.2, clip_on=False)
            bad = collisions > data.gates["gate1_band"][1]
            ax.plot(x[bad], y[bad], "x", ms=9, c=INK, mew=1)
            offset = ((24 if length == 1000 else 16) if s == "S1a"
                      else (-10 if length == 1000 else -20))
            ax.annotate(sty["name"], (x[-1], y[-1]), xytext=(-3, offset), textcoords="offset points", ha="right", fontsize=9)
        ax.set(yscale="log", ylim=(1e-7, 3.4e-5), xlim=(145 if length == 250 else 120, length), xlabel="Mutual sight along section (m)")
        ax.set_xticks([150, 200, 250] if length == 250 else [150, 500, 1000])
        ax.set_yticks([1e-7, 1e-6, 1e-5])
        ax.yaxis.set_major_formatter(ticker.LogFormatterSciNotation())
        ax.yaxis.set_minor_locator(ticker.NullLocator())
        ax.text(.5, 1.10, f"{length:,} m section", transform=ax.transAxes, ha="center", fontsize=10, weight="bold")
        clean(ax, "y")
    axes[0].set_ylabel("Head-on serious-harm events\n/ operation day", labelpad=4)
    fig.text(.5, .045, "Cross: collision check fails; lines connect saved points.", ha="center", fontsize=9)
    return fig


def figS6(data):
    fig = plt.figure(figsize=(WIDTH, 3.5))
    axes = [fig.add_axes([.105, .32, .405, .48]), fig.add_axes([.565, .32, .405, .48])]
    rows = read_csv("grid_results_primary.csv")
    demands = sorted({int(r["q_vph_dir"]) for r in rows})
    lengths = sorted({int(r["section_m"]) for r in rows}, reverse=True)
    bands = data.gates["gate1_band"]
    failed = {}
    for ax, s in zip(axes, ("S1a", "S2")):
        count = 0
        for i, length in enumerate(lengths):
            for j, demand in enumerate(demands):
                row = next(r for r in rows if int(r["section_m"]) == length and int(r["q_vph_dir"]) == demand)
                stable = float(row["stable_frac"])
                value = float(row[f"collisions_day_{s}"])
                ax.add_patch(Rectangle((j, i), 1, 1, ec=GRID, fc="#aaaaaa" if stable == 0 else "white", lw=.7))
                if stable:
                    if value < bands[0] or value > bands[1]:
                        count += 1
                        ax.add_patch(Rectangle((j+.025, i+.025), .95, .95, ec=MUTED, fc="none", hatch="////", lw=.5))
                        ax.add_patch(Rectangle((j+.10, i+.10), .8, .8, ec="none", fc="white"))
                    if stable < 1:
                        ax.add_patch(Polygon([(j, i), (j+.25, i), (j, i+.30)], fc="white", ec=MUTED, hatch="....", lw=.5))
                    # A shared factor preserves the original three significant figures
                    # without squeezing a mantissa and exponent into every narrow cell.
                    ax.text(j+.50, i+.51, scaled_sci(value), ha="center", va="center", fontsize=9)
                else:
                    ax.text(j+.50, i+.51, "None", ha="center", va="center", fontsize=9)
                if demand == 300 and length == 250:
                    ax.add_patch(Rectangle((j+.025, i+.025), .95, .95, ec=INK, fc="none", lw=1.7))
        failed[s] = count
        ax.set(xlim=(0, 7), ylim=(5, 0), xticks=np.arange(7)+.5, yticks=np.arange(5)+.5)
        ax.set_xticklabels([f"{x:,}" for x in demands])
        ax.set_yticklabels([f"{x:,}" for x in lengths] if s == "S1a" else [])
        ax.tick_params(length=0, pad=4)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.text(.5, 1.10, STRATEGIES[s]["name"], ha="center", transform=ax.transAxes, fontsize=10, weight="bold")
    registered = read_json("figure_checks.json")["R59"]
    close([failed[s] for s in ("S1a", "S2")],
          [registered[s]["count_above_ceiling"] for s in ("S1a", "S2")], "R59 grid failures")
    axes[0].set_ylabel("Section length (m)", labelpad=3)
    fig.text(.53, .215, "Demand (vehicles / hour / direction)", fontsize=9, ha="center")
    fig.text(.53, .955, r"Cell values: median head-on collisions / operation day ($\times 10^{-5}$)", ha="center", fontsize=9)
    handles = [Rectangle((0, 0), 1, 1, fc="white", ec=MUTED, hatch="////", label="Outside gate"), Rectangle((0, 0), 1, 1, fc="#aaaaaa", label="Infeasible"), Rectangle((0, 0), 1, 1, fc="white", ec=MUTED, hatch="....", label="Partly stable"), Rectangle((0, 0), 1, 1, fc="white", ec=INK, lw=1.7, label="Baseline")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.51, .108), ncol=4, frameon=False, handlelength=1.25, columnspacing=1)
    fig.text(.5, .035, r"Gate: $10^{-6}$ to $10^{-3}$ collisions / operation day.", ha="center", fontsize=9)
    return fig


def save(fig, name, png_only=False):
    assert name in FILES
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    labels = [t for t in fig.findobj(mtext.Text) if t.get_visible() and t.get_text().strip()]
    forbidden = [t.get_text() for t in labels
                 if re.search(r"[\u2013\u2014]|\d(?:\.\d+)?\s*[eE][+\-\u2212]?\d|\b[eE][+\-\u2212]\d", t.get_text())]
    assert not forbidden, (name, "Non-print notation or dash", forbidden)
    min_font = min(t.get_fontsize() for t in labels)
    actual_width = fig.get_figwidth()
    printed_min = min_font * WIDTH / actual_width
    assert printed_min >= MIN_FONT_PT, (name, printed_min)
    bounds = fig.bbox
    clipped = []
    for t in labels:
        bb = t.get_window_extent(renderer)
        if bb.x0 < bounds.x0-1 or bb.y0 < bounds.y0-1 or bb.x1 > bounds.x1+1 or bb.y1 > bounds.y1+1:
            clipped.append(t.get_text())
    if clipped:
        raise AssertionError(f"{name}: text outside canvas: {clipped}")
    overlaps = []
    boxes = [t.get_window_extent(renderer) for t in labels]
    tolerance = DPI/72 * .5  # Ignore sub-half-point antialiasing/bounding-box touches.
    for i, a in enumerate(boxes):
        for j in range(i+1, len(boxes)):
            b = boxes[j]
            if min(a.x1, b.x1)-max(a.x0, b.x0) > tolerance and min(a.y1, b.y1)-max(a.y0, b.y0) > tolerance:
                overlaps.append([labels[i].get_text(), labels[j].get_text()])
    if overlaps:
        raise AssertionError(f"{name}: overlapping text: {overlaps}")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=DPI, bbox_inches=None, facecolor="white")
    if not png_only:
        BUILD.mkdir(parents=True, exist_ok=True)
        fig.savefig(BUILD / name.replace(".png", ".pdf"), bbox_inches=None, facecolor="white")
    from PIL import Image
    with Image.open(OUT/name) as im:
        assert im.width == round(WIDTH*DPI)
        # Every RGB pixel is grey: greyscale legibility is intrinsic, not a colour simulation.
        rgb = np.asarray(im.convert("RGB"))
        # INK/MUTED/GRID from the existing style differ by at most three RGB levels.
        assert int(np.max(np.ptp(rgb.astype(int), axis=2))) <= 3
        pixels = list(im.size)
    result = dict(width_inches=actual_width, height_inches=fig.get_figheight(), dpi=DPI,
                  pixels=pixels, minimum_font_pt_at_6_5_inches=printed_min,
                  text_count=len(labels), clipped_text=clipped, overlapping_text=overlaps,
                  sha256=hashlib.sha256((OUT/name).read_bytes()).hexdigest())
    plt.close(fig)
    print(f"{name}: {pixels[0]} × {pixels[1]} px; minimum {printed_min:.1f} pt; no clipped text", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=FILES, nargs="+", help="Rebuild selected displays during layout review")
    parser.add_argument("--png-only", action="store_true", help="Leave vector copies and the provenance audit unchanged")
    args = parser.parse_args()
    # Hash all other figure files and every consumed output; prove neither changed.
    protected = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name not in FILES}
    sources = {name: hashlib.sha256((DIST/name).read_bytes()).hexdigest() for name in INPUTS}
    data = Data()
    data.maps = maps(data)
    data.device_rows = device_rows(data)
    previous = json.loads(AUDIT.read_text()) if AUDIT.exists() and args.only else {}
    reports = previous.get("figures", {})
    builders = (fig1, fig2, fig4, fig5, fig6, fig7, fig8, fig9, figS6)
    for name, build in zip(FILES, builders):
        if not args.only or name in args.only:
            reports[name] = save(build(data), name, png_only=args.png_only)
    for p, digest in protected.items():
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"Changed protected figure: {p}"
    for name, digest in sources.items():
        assert hashlib.sha256((DIST/name).read_bytes()).hexdigest() == digest, f"Changed source: {name}"
    hs, cs, grids = data.maps
    result = dict(source_directory=str(DIST.relative_to(ROOT)), input_sha256=sources,
                  finite_draws=int(data.finite.sum()), excluded_nonfinite_draws=int((~data.finite).sum()),
                  record_anchors=dict(controller=data.c, signal_headon=data.h, controller_band=data.cband, headon_band=data.hband),
                  interval_summaries=data.intervals,
                  signal_maps=dict(headon_axis=hs.tolist(), controller_axis=cs.tolist(),
                                   median_matched=grids["median"].tolist(), mean_matched=grids["mean"].tolist()),
                  device_rows=[dict(label=label, adopted=adopted, **row) for label, row, adopted in data.device_rows],
                  grid_rows=read_csv("grid_results_primary.csv"),
                  model_form_rows=read_csv("model_form_sensitivity.csv"),
                  sight_rows=read_csv("sight_sweep.csv"),
                  event_chain_medians={key: float(np.median(data.b[f"diag_S1a_{key}"]))
                                       for key in ("facing_per_day", "violations_per_day", "conflicts_per_day", "collisions_per_day", "clearance_s", "p_safe_window")},
                  strategy_styles=STRATEGIES, figures=reports,
                  protected_figure_count=len(protected), protected_figures_unchanged=True,
                  sources_unchanged=True)
    if not args.png_only:
        AUDIT.write_text(json.dumps(result, indent=2)+"\n")
        print(f"Audit: {AUDIT.relative_to(ROOT)}")
    print(f"Frozen outputs and {len(protected)} other figures unchanged")


if __name__ == "__main__":
    main()
