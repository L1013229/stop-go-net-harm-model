#!/usr/bin/env python3
"""Journal figures for the v1.5 manuscript, built from the saved production outputs.

Run: python3 model/scripts/make_figures_v15.py [--only NAME ...]

Writes into trr/manuscript/figures/:
  fig_tree.png               Figure 3: the four questions with the surviving counts
  fig3_decision_surface.png  Figure 4: break-even maps, signals and the device (tied operator exposure)
  fig_spread.png             Figure 5: change against the margin, three rows
  fig9_sight.png             Figure 6: head-on harm against mutual sight
  fig_injury_speed.png       Figure 7: injury curves and the speed sweep

Every value is a re-read of the saved draws in baseline_traces.npz or of the saved
summaries; nothing is sampled and no prior changes. Colour is used where it separates
series, and every figure is checked in greyscale for legibility by construction (line
styles and markers differ as well as hue). Every text object is at least 9 pt at the
print width of 6.5 inches and no two text objects overlap.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/trr-v15-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text as mtext
import matplotlib.ticker as ticker
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model" / "src"))
DIST = ROOT / "model/outputs/dist/capfix_20260927"
OUT = ROOT / "model/outputs/figures_trr"
WIDTH, DPI, MIN_FONT_PT = 6.5, 400, 9.0

INK, MUTED, GRID = "#1a1a19", "#5b5b58", "#d9d9d6"
BLUE, GREEN, GOLD, PLUM = "#2a5fb8", "#1b8f6a", "#d98a00", "#7a4f9c"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.labelsize": 9.5,
    "axes.titlesize": 10, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "legend.fontsize": 9, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.labelcolor": INK, "grid.color": GRID, "grid.linewidth": 0.5,
    "figure.dpi": DPI, "savefig.dpi": DPI, "savefig.bbox": None,
    "mathtext.fontset": "dejavusans", "axes.unicode_minus": True,
})

# Recorded rates (serious-harm events per operation day) and their ranges, as in the text.
H_CENTRE, H_BAND = 1.2e-5, (6e-6, 2e-5)
C_CENTRE, C_BAND = 1e-5, (5e-6, 2e-5)
MARGIN = 4e-5


def read_json(name):
    return json.loads((DIST / name).read_text())


def read_csv(name):
    with (DIST / name).open() as f:
        return list(csv.DictReader(f))


def sci(x, digits=1):
    m, e = f"{x:.{digits}e}".split("e")
    return rf"${m}\times 10^{{{int(e)}}}$"


def clean(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=grid_axis, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)


def check_and_save(fig, name):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    labels = [t for t in fig.findobj(mtext.Text) if t.get_visible() and t.get_text().strip()]
    printed_min = min(t.get_fontsize() for t in labels) * WIDTH / fig.get_figwidth()
    assert printed_min >= MIN_FONT_PT, (name, f"smallest text {printed_min:.1f} pt")
    boxes = [t.get_window_extent(renderer) for t in labels]
    tol = DPI / 72 * 0.5
    overlaps = []
    for i, a in enumerate(boxes):
        for j in range(i + 1, len(boxes)):
            b = boxes[j]
            if min(a.x1, b.x1) - max(a.x0, b.x0) > tol and min(a.y1, b.y1) - max(a.y0, b.y0) > tol:
                overlaps.append((labels[i].get_text(), labels[j].get_text()))
    assert not overlaps, (name, "overlapping text", overlaps)
    for t, bb in zip(labels, boxes):
        if bb.x0 < fig.bbox.x0 - 1 or bb.x1 > fig.bbox.x1 + 1 or bb.y0 < fig.bbox.y0 - 1 or bb.y1 > fig.bbox.y1 + 1:
            raise AssertionError((name, "text outside canvas", t.get_text()))
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"{name}: smallest text {printed_min:.1f} pt; {len(labels)} text objects; no overlap")


# ------------------------------------------------------------------ saved draws and readings

class Data:
    def __init__(self):
        b = np.load(DIST / "baseline_traces.npz")
        self.b = b
        self.W = b["part_S0_W3"]                       # controller-strike harm, manual control
        self.V = {s: b[f"part_{s}_W5"] for s in ("S0", "S1a", "S2")}   # head-on harm
        self.A = {s: b[f"part_{s}_W4d"] for s in ("S1a", "S2")}        # placement harm
        self.alpha = b["draw_reach_alpha"]
        self.offset = b["draw_offset_op_m"]
        finite = np.isfinite(self.W) & np.isfinite(self.V["S1a"]) & np.isfinite(self.V["S0"]) & np.isfinite(self.V["S2"])
        self.finite = finite
        self.reads = read_json("registered_reads.json")

    def delta(self, strategy, h=H_CENTRE, c=C_CENTRE, ref_m=0.0):
        """Change in serious harm, substitute minus manual control, medians matched."""
        f = self.finite
        l3 = c / np.median(self.W[f])
        l5 = h / np.median(self.V["S1a"][f])
        removed = l3 * self.W[f]
        headon = l5 * (self.V[strategy][f] - self.V["S0"][f])
        operator = 0.0
        if strategy == "S2":
            operator = removed * np.exp(-self.alpha[f] * (self.offset[f] - ref_m))
        return self.A[strategy][f] + operator - removed + headon


def surface(data, strategy, ref_m=0.0, n=61):
    hs = np.geomspace(*H_BAND, n)
    cs = np.geomspace(*C_BAND, n)
    hs[np.argmin(abs(hs - H_CENTRE))] = H_CENTRE
    cs[np.argmin(abs(cs - C_CENTRE))] = C_CENTRE
    grid = np.empty((n, n))
    for i, c in enumerate(cs):
        for j, h in enumerate(hs):
            grid[i, j] = np.mean(data.delta(strategy, h=h, c=c, ref_m=ref_m) < 0)
    return hs, cs, grid


# ------------------------------------------------------------------ Figure 3: the four questions

def fig_tree(data):
    b = data.b
    med = lambda k: float(np.nanmedian(b[k]))
    face = med("diag_S1a_facing_per_day")
    v = med("diag_S1a_violations_per_day")
    cf = med("diag_S1a_conflicts_per_day")
    cl = med("diag_S1a_collisions_per_day")
    hm = med("part_S1a_W5")

    def fmt(x):
        if x >= 10:
            return f"{x:,.0f}"
        if x >= 0.01:
            return f"{x:.2f}"
        return sci(x)

    fig, ax = plt.subplots(figsize=(WIDTH, 2.7))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10.9); ax.axis("off")
    QY = [9.0, 7.15, 5.3, 3.45]
    QX = [1.30, 3.45, 5.55, 7.65]
    BASE = 1.25
    questions = ["does the vehicle\nfacing red enter?", "does it meet an\nopposing vehicle?",
                 "do they\ncollide?", "is anyone\nseriously hurt?"]
    no_caps = ["does not enter", "crosses an\nempty section", "avoided", "no serious\ninjury"]
    counts_on = [None, fmt(v), fmt(cf), fmt(cl)]
    ax.text(QX[0] - 0.9, 10.35, f"{face:,.0f} vehicles face a red each operation day",
            ha="left", va="center", fontsize=9.5, color=MUTED)
    for i, q in enumerate(questions):
        ax.text(QX[i], QY[i], q, ha="center", va="center", fontsize=9.5, color=INK,
                fontweight="bold", linespacing=1.25, zorder=4)
        ax.annotate("", xy=(QX[i], BASE + 0.75), xytext=(QX[i], QY[i] - 0.85),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9, shrinkA=0, shrinkB=0))
        ax.text(QX[i] + 0.12, (QY[i] - 0.85 + BASE) / 2 + 0.3, "No", ha="left", va="center",
                fontsize=9, color=MUTED)
        ax.text(QX[i], BASE - 0.15, no_caps[i], ha="center", va="top", fontsize=9, color=MUTED,
                linespacing=1.15)
        x_start = QX[i] + 1.30
        x_end = QX[i + 1] if i < 3 else 9.35
        ax.plot([x_start, x_end], [QY[i], QY[i]], color=INK, lw=1.0, zorder=2)
        y_to = QY[i + 1] + 0.85 if i < 3 else BASE + 0.75
        ax.annotate("", xy=(x_end, y_to), xytext=(x_end, QY[i]),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0, shrinkA=0, shrinkB=0))
        ax.text(x_end + 0.12, (QY[i] + y_to) / 2, "Yes", ha="left", va="center", fontsize=9, color=INK)
        if i < 3:
            ax.text((x_start + x_end) / 2, QY[i] + 0.30, counts_on[i + 1], ha="center", va="bottom",
                    fontsize=9.5, color=INK, fontweight="bold")
        else:
            ax.text(x_end, BASE, fmt(hm), ha="center", va="center", fontsize=9.5, color=INK, fontweight="bold")
            ax.text(x_end, BASE - 0.75, "death or\nserious injury", ha="center", va="top", fontsize=9,
                    color=MUTED, linespacing=1.15)
    check_and_save(fig, "fig_tree.png")
    return dict(face=face, entries=v, encounters=cf, collisions=cl, serious=hm)


# ------------------------------------------------------------------ Figure 4: break-even maps

def fig_maps(data):
    fig = plt.figure(figsize=(WIDTH, 3.7))
    axes = [fig.add_axes([.17, .35, .31, .50]), fig.add_axes([.62, .35, .31, .50])]
    results = {}
    for ax, (strategy, ref_m, title) in zip(axes, (("S1a", 0.0, "(a)  signals"), ("S2", 0.0, "(b)  the attended device"))):
        hs, cs, grid = surface(data, strategy, ref_m)
        im = ax.pcolormesh(hs, cs, grid, cmap="viridis", vmin=0, vmax=1, shading="nearest")
        ax.contour(hs, cs, grid, levels=[.5], colors="white", linewidths=2.6)
        ct = ax.contour(hs, cs, grid, levels=[.5], colors=INK, linewidths=.9)
        ax.clabel(ct, fmt={.5: "0.5"}, fontsize=9, inline=True)
        ax.add_patch(Rectangle((H_BAND[0], C_BAND[0]), H_BAND[1] - H_BAND[0], C_BAND[1] - C_BAND[0],
                               fc="none", ec=GOLD, lw=1.6, zorder=6))
        centre = float(np.mean(data.delta(strategy, ref_m=ref_m) < 0))
        corners = [float(np.mean(data.delta(strategy, h=h, c=c, ref_m=ref_m) < 0)) for h in H_BAND for c in C_BAND]
        results[strategy] = dict(centre=centre, corners=corners)
        ax.plot(H_CENTRE, C_CENTRE, "o", ms=5.5, mfc="white", mec=INK, zorder=7)
        ax.annotate(f"{centre:.2f}", (H_CENTRE, C_CENTRE), xytext=(7, 6), textcoords="offset points",
                    fontsize=10, weight="bold", bbox=dict(fc="white", ec="none", pad=1.2), zorder=8)
        ax.text(.03, .05, f"corners {min(corners):.2f} to {max(corners):.2f}", transform=ax.transAxes,
                fontsize=9, bbox=dict(fc="white", ec="none", pad=1.2), zorder=8)
        ax.set(xscale="log", yscale="log", xlim=H_BAND, ylim=C_BAND)
        ax.set_xticks([6e-6, 1.2e-5, 2e-5]); ax.set_yticks([5e-6, 1e-5, 2e-5])
        fmt_ = ticker.FuncFormatter(lambda v, _: sci(v))
        ax.xaxis.set_major_formatter(fmt_); ax.yaxis.set_major_formatter(fmt_)
        ax.xaxis.set_minor_locator(ticker.NullLocator()); ax.yaxis.set_minor_locator(ticker.NullLocator())
        ax.set_title(title, loc="left", fontsize=9.5, pad=6)
        ax.set_xlabel("recorded head-on rate", fontsize=9)
    axes[0].set_ylabel("recorded controller-strike rate", fontsize=9)
    fig.text(.51, .215, "both axes in serious-harm events per operation day", ha="center", fontsize=9, color=MUTED)
    cax = fig.add_axes([.30, .11, .40, .03])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[0, .5, 1])
    cb.set_label("probability that the substitute reduces serious harm", fontsize=9)
    check_and_save(fig, "fig3_decision_surface.png")
    return results


# ------------------------------------------------------------------ Figure 5: change against the margin

def fig_spread(data):
    reads = data.reads["R100"]["interval_summaries"]
    rows = [("signals_median", "signals", INK, "-"),
            ("device_tied_0m", "the device, reference\ncontroller at the edge line", PLUM, "--"),
            ("device_tied_1m", "the device, reference\ncontroller 1 m back", PLUM, "--")]
    fig = plt.figure(figsize=(WIDTH, 3.0))
    left = fig.add_axes([.34, .25, .27, .56]); right = fig.add_axes([.68, .25, .29, .56])
    full = (-5e-5, 1.5e-4)
    for panel, (ax, limits) in enumerate(((left, full), (right, (-1.2e-5, 1.2e-5)))):
        lo, hi = limits
        ax.axvspan(-MARGIN, MARGIN, color=GOLD, alpha=0.12, lw=0, zorder=0)
        for y, (key, label, colour, ls) in enumerate(rows):
            r = reads[key]
            ax.plot([max(lo, r["q05"]), min(hi, r["q95"])], [y, y], c=colour, ls=ls, lw=.9)
            ax.plot([max(lo, r["q25"]), min(hi, r["q75"])], [y, y], c=colour, ls="-", lw=3)
            if panel:
                for q, edge, mark in (("q05", lo, "<"), ("q95", hi, ">")):
                    if r[q] < lo or r[q] > hi:
                        ax.plot(edge, y, marker=mark, color=colour, ms=4, clip_on=False)
            ax.plot(r["median"], y, marker="o", mec=INK, mfc="white", ms=4.5, zorder=5)
            if lo <= r["mean"] <= hi:
                ax.plot(r["mean"], y, marker="D", mec=INK, mfc=INK, ms=3.5, zorder=4)
            elif panel:
                ax.annotate("mean →", (hi, y), xytext=(-2, 7), textcoords="offset points", ha="right", fontsize=9)
        ax.axvline(0, c=MUTED, ls=":", lw=1)
        ax.set(xlim=limits, ylim=(2.65, -.65), yticks=[])
        clean(ax, "x"); ax.spines["left"].set_visible(False)
        ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: "0" if v == 0 else f"{v/1e-5:g}".replace("-", "−")))
        ax.text(.5, 1.10, "full 5th to 95th span" if panel == 0 else "enlargement", transform=ax.transAxes,
                ha="center", fontsize=9, weight="bold")
    left.set_xticks([-5e-5, 0, 5e-5, 1e-4, 1.5e-4]); right.set_xticks([-1e-5, 0, 1e-5])
    for y, (key, label, colour, ls) in enumerate(rows):
        left.text(-.06, y, label, transform=left.get_yaxis_transform(), ha="right", va="center", fontsize=9)
    fig.text(.655, .10, r"change in serious-harm events per operation day ($\times 10^{-5}$)",
             ha="center", fontsize=9)
    handles = [Line2D([], [], c=INK, lw=.9, label="5th to 95th"), Line2D([], [], c=INK, lw=3, label="25th to 75th"),
               Line2D([], [], c=INK, marker="o", mfc="white", ls="", label="median"),
               Line2D([], [], c=INK, marker="D", ls="", label="mean"),
               Rectangle((0, 0), 1, 1, fc=GOLD, alpha=0.25, ec="none", label="margin")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.62, 1.0), ncol=5, frameon=False,
               columnspacing=1.0, handlelength=1.4)
    check_and_save(fig, "fig_spread.png")


# ------------------------------------------------------------------ Figure 6: sight

def fig_prcc(data):
    """Figure 6: the eight largest partial rank correlations with the change in harm at the recorded rates."""
    names = {"re3_rate": "controller-strike rate", "sev3_p": "controller-strike severity",
             "q_lead": "released driver enters against a vehicle it can see",
             "r_v1a": "entry rate at the signal", "w_occ": "entering driver enters against a visible vehicle",
             "impact_speed_frac": "share of closing speed kept at impact", "ttc50": "time to collision at even odds of avoiding",
             "w_onset": "share of entries made just after the red starts", "d_sight_m": "mutual sight distance",
             "platoon_speed_kmh": "operating speed", "f_cycle_a": "fixed-time green ratio"}
    d = json.loads((DIST / "decision_summary_s2.json").read_text())
    top = d["s1a_prcc_at_record_top8"][:8][::-1]
    vals = [float(v) for _, v in top]
    labels = [names.get(k, k) for k, _ in top]
    fig = plt.figure(figsize=(WIDTH, 2.8))
    ax = fig.add_axes([.54, .22, .43, .74])
    ax.barh(labels, vals, height=0.62, color=[BLUE if v > 0 else INK for v in vals], edgecolor="white", lw=.4)
    for i, v in enumerate(vals):
        ax.text(v + (0.02 if v > 0 else -0.02), i, f"{v:+.2f}", ha="left" if v > 0 else "right", va="center", fontsize=9)
    lim = max(abs(v) for v in vals) + 0.22
    ax.set_xlim(-lim, lim); ax.set_xticks([-0.5, 0, 0.5]); ax.axvline(0, color=MUTED, lw=0.7)
    ax.set_xlabel("rank correlation with the change in harm\n(negative favours signals)")
    ax.tick_params(axis="y", labelsize=9)
    clean(ax, "x")
    check_and_save(fig, "fig_prcc_record.png")
    return dict(top=top)


def fig_sight():
    rows = read_csv("sight_sweep.csv")
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.8))
    for ax, section in zip(axes, ("250", "1000")):
        sub = [r for r in rows if r["section_m"] == section]
        sub.sort(key=lambda r: float(r["sight_m"]))
        x = [float(r["sight_m"]) for r in sub]
        for key, colour, ls, marker, label in (("w5_s1a_median", BLUE, "-", "o", "signals"),
                                               ("w5_s2_median", PLUM, "--", "s", "the device")):
            y = [float(r[key]) for r in sub]
            ax.plot(x, y, color=colour, ls=ls, marker=marker, ms=4, lw=1.3, mfc="white", mec=colour)
            ax.text(x[-1], y[-1] * (1.25 if key.endswith("s1a_median") else 0.78), label, ha="right",
                    va="bottom" if key.endswith("s1a_median") else "top", fontsize=9, color=colour)
        for r in sub:
            if float(r["collisions_day_s1a"]) > 1e-3:
                ax.plot(float(r["sight_m"]), float(r["w5_s1a_median"]), marker="x", ms=9, color=BLUE, mew=1.2)
        ax.set_yscale("log"); ax.set_xscale("log")
        ax.set_xticks(x); ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.xaxis.set_minor_locator(ticker.NullLocator())
        ax.set_ylim(1e-7, 5e-5)
        ax.set_yticks([1e-7, 1e-6, 1e-5]); ax.yaxis.set_minor_locator(ticker.NullLocator())
        ax.set_title(f"{int(section):,} m section", loc="left")
        ax.set_xlabel("mutual sight along the section (m)")
        clean(ax)
    axes[0].set_ylabel("head-on serious-harm events\nper operation day")
    fig.text(.5, .01, "cross: collision count above the screening band", ha="center", fontsize=9, color=MUTED)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    check_and_save(fig, "fig9_sight.png")


# ------------------------------------------------------------------ Figure 7: injury and speed

def fig_injury_curves():
    """Figure 4: injury risk per person and per event on the two published curves (Methods)."""
    from mtcpts.severity import p_worker, p_occupant
    fig = plt.figure(figsize=(WIDTH, 2.6))
    a = fig.add_axes([.14, .20, .34, .68]); b = fig.add_axes([.63, .20, .34, .68])
    v = np.linspace(0, 120, 240)
    a.plot(v, p_worker(v), color=INK, lw=1.6)
    a.plot(v, p_occupant(v), color=BLUE, lw=1.6, ls="--")
    pw = float(p_worker(np.array([31.0]))[0])
    a.plot([31, 47], [pw, pw], color=MUTED, lw=0.8, ls=":")
    a.plot([31], [pw], marker="o", ms=4.5, mfc="white", mec=INK, mew=1.1, zorder=5)
    a.plot([47], [pw], marker="o", ms=4.5, mfc="white", mec=BLUE, mew=1.1, zorder=5)
    a.text(2, 0.50, "same risk at\n31 and 47 km/h", fontsize=9, color=MUTED, ha="left", va="bottom")
    a.plot([20, 30], [0.49, pw + 0.03], color=MUTED, lw=0.6)
    a.text(56, 0.68, "worker, at\nimpact speed", fontsize=9, color=INK, ha="right", va="bottom")
    a.text(72, 0.28, "occupant,\nat delta-V", fontsize=9, color=BLUE, ha="left", va="bottom")
    a.set_xlabel("impact speed or delta-V (km/h)"); a.set_ylabel("probability of serious injury\nper person")
    a.set_ylim(0, 1.02); a.set_xlim(0, 120); a.set_yticks([0, .25, .5, .75, 1])
    a.set_title("(a)  each person's risk", loc="left")
    clean(a)

    vop = np.linspace(10, 80, 200)
    p_strike = p_worker(vop)
    p_occ = p_occupant(vop)
    p_headon = 1.0 - (1.0 - p_occ) ** (2 * 1.56)
    b.plot(vop, p_strike, color=INK, lw=1.6)
    b.plot(vop, p_headon, color=BLUE, lw=1.6, ls="--")
    b.axvline(45, color=MUTED, lw=0.7, ls="-.")
    b.text(12, 0.66, "above about\n45 km/h the\nhead-on is the\nworse event", fontsize=9, color=MUTED, va="bottom")
    b.text(11.5, 0.46, "solid: one\nworker struck", fontsize=9, color=INK, ha="left", va="bottom")
    b.text(11.5, 0.20, "dashed:\nhead-on between\ntwo vehicles", fontsize=9, color=BLUE, ha="left", va="bottom")
    b.set_xlabel("operating speed (km/h)"); b.set_ylabel("probability of a serious-harm\nevent per collision or strike")
    b.set_ylim(0, 1.02); b.set_xlim(10, 80); b.set_yticks([0, .25, .5, .75, 1]); b.set_xticks([20, 40, 60, 80])
    b.set_title("(b)  per event at one speed", loc="left")
    clean(b)
    check_and_save(fig, "fig_injury_curves.png")


def fig_speed_sweep():
    """Figure 8: the two harms against operating speed through the works (Results)."""
    fig = plt.figure(figsize=(WIDTH, 2.9))
    c = fig.add_axes([.14, .17, .83, .74])
    rows = read_csv("speed_sweep.csv")
    sp = np.array([float(r["platoon_speed_kmh"]) for r in rows])
    w5 = np.array([float(r["w5_s1a_median"]) for r in rows])
    w3 = np.array([float(r["w3_median"]) for r in rows])
    w5d = np.array([float(r["w5_s2_median"]) for r in rows]) if "w5_s2_median" in rows[0] else None
    c.plot(sp, w3, color=INK, ls="--", lw=1.6, marker="s", ms=3.5)
    c.plot(sp, w5, color=BLUE, ls="-", lw=1.6, marker="o", ms=3.5)
    c.text(31, 8e-3, "controller struck, at the panel's level", fontsize=9, color=INK, va="bottom")
    c.text(31, 1.7e-5, "head-on, signals", fontsize=9, color=BLUE, va="bottom")
    if w5d is not None:
        c.plot(sp, w5d, color=PLUM, ls="-.", lw=1.4, marker="^", ms=3.5)
        c.text(79, 3.2e-6, "head-on, the device", fontsize=9, color=PLUM, ha="right", va="top")
    c.annotate(f"about {w5[-1] / w5[0]:.0f}-fold", xy=(sp[-1], w5[-1]), xytext=(-6, 6), textcoords="offset points", ha="right", fontsize=9, color=BLUE)
    c.annotate(f"about {w3[-1] / w3[0]:.0f}-fold", xy=(sp[-1], w3[-1]), xytext=(-6, 6), textcoords="offset points", ha="right", fontsize=9, color=INK)
    c.axhspan(C_BAND[0], C_BAND[1], color=GOLD, alpha=0.18, lw=0)
    c.text(sp.min() + 0.5, C_BAND[0] * 1.15, "recorded controller-strike range", fontsize=9, color=INK, va="bottom")
    c.set_yscale("log"); c.set_xlabel("operating speed through the works (km/h)")
    c.set_ylim(1e-7, 4e-2); c.set_yticks([1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]); c.yaxis.set_minor_locator(ticker.NullLocator())
    c.set_xlim(sp.min() - 2, sp.max() + 2); c.set_xticks(sp)
    c.set_ylabel("serious-harm events\nper operation day")
    clean(c)
    check_and_save(fig, "fig_speed_sweep.png")
    return dict(headon_fold=float(w5[-1] / w5[0]), strike_fold=float(w3[-1] / w3[0]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="+", default=None)
    args = ap.parse_args()
    data = Data()
    want = lambda n: args.only is None or n in args.only
    out = {}
    if want("fig_tree.png"):
        out["tree"] = fig_tree(data)
    if want("fig3_decision_surface.png"):
        out["maps"] = fig_maps(data)
    if want("fig_spread.png"):
        fig_spread(data)
    if want("fig9_sight.png"):
        out["prcc"] = fig_prcc(data)
    fig_sight()
    if want("fig_injury_speed.png"):
        fig_injury_curves()
    out["speed"] = fig_speed_sweep()
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
