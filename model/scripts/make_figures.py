"""Publication figures.

Print-safe by construction: categorical hues are lightness-ordered and carry a second
encoding (line style, hatch, direct labels) so every figure survives greyscale reproduction.
The decision surface uses a single-hue sequential ramp, never a rainbow. One axis per panel.

Figure sizes: where the owner resized a figure in his v1.1 review, that size is the
canonical figsize here (inches) and must not be changed without his direction.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

MODEL = Path(__file__).resolve().parents[1]
DIST = max((MODEL / "outputs" / "dist").glob("*_2026*"), key=lambda d: d.stat().st_mtime)
FIG = MODEL / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# validated categorical slots (dataviz palette, light surface); lightness-ordered
BLUE, AQUA, GOLD = "#2a78d6", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1a1a19", "#5b5b58", "#d9d9d6"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
STRAT = {"S0": (INK, "-", ""), "S1a": (BLUE, "--", "///"), "S1b": (AQUA, ":", "\\\\\\")}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8,
    "axes.titlesize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.labelcolor": INK, "grid.color": GRID, "grid.linewidth": 0.5,
    "figure.dpi": 400, "savefig.dpi": 400, "savefig.bbox": "tight",
})


def _clean(ax, grid_axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=grid_axis, alpha=0.7, zorder=0)
    ax.set_axisbelow(True)


def load_csv(name):
    with open(DIST / name) as fh:
        return list(csv.DictReader(fh))


def med(x):
    return float(np.nanmedian(np.asarray(x, float)))


# ----------------------------------------------------------------- FIGURE 1 (model structure)
def fig0_model_flow():
    """Model structure: inputs through the computation to the outputs, with the
    record checks shown where they act. Plain labels only."""
    fig, ax = plt.subplots(figsize=(6.54, 2.57))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, lines, fc="#f5f7fa", ec=MUTED, lw=0.8, fs=6.8):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=3))
        ax.text(x + w / 2, y + h / 2, lines, ha="center", va="center", fontsize=fs,
                color=INK, zorder=4, linespacing=1.35)

    def arrow(x0, y0, x1, y1, color=INK, lw=1.1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                    shrinkA=1, shrinkB=1), zorder=2)

    # main computation row
    ry, rh = 5.2, 3.4
    box(0.05, ry, 2.00, rh, "inputs\n\nmeasured rates,\nstandards tables,\nelicited quantities,\nTable 1 priors")
    box(2.60, ry, 1.85, rh, "sampling\n\n1 value of every\nuncertain quantity,\n20,000 draws")
    box(4.97, ry, 2.0, rh, "cycle and queue\ncalculation\n\nsignal timings, queues,\nvehicles facing red", fs=6.3)
    box(7.45, ry, 2.50, rh, "harm mechanisms\n\nevent tree for red\nrunning; rates for the\nother risks; injury curves")
    arrow(2.05, ry + rh / 2, 2.60, ry + rh / 2)
    arrow(4.45, ry + rh / 2, 5.00, ry + rh / 2)
    arrow(6.90, ry + rh / 2, 7.45, ry + rh / 2)

    # outputs row
    oy, oh = 0.55, 3.1
    box(0.05, oy, 4.60, oh,
        "checks against independent records\n\nimplied head-on rate vs the crash registers;\n"
        "implied strike rate vs the injury record", fc="#fdf6e3", ec=GOLD, fs=6.6)
    box(5.15, oy, 2.20, oh, "per-draw totals\n\nH(S0), H(S1), and\nΔH = H(S1) − H(S0)")
    box(7.85, oy, 2.10, oh, "outputs\n\nP(ΔH < 0),\nbreak-even line,\nPRCC sensitivity")
    arrow(8.70, ry, 6.60, oy + oh, color=INK)
    arrow(4.65, oy + oh / 2, 5.15, oy + oh / 2, color=GOLD)
    arrow(7.35, oy + oh / 2, 7.85, oy + oh / 2)

    fig.savefig(FIG / "fig0_model_flow.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 2 (strategies)
def fig_strategies():
    fig, ax = plt.subplots(figsize=(6.42, 1.59))
    ax.set_xlim(0, 10); ax.set_ylim(0.55, 3.45); ax.axis("off")
    for x0, title, dev in ((0.1, "S0   two manual traffic controllers", "MTC"),
                           (5.2, "S1   portable traffic signal pair", "PTS")):
        col = BLUE if dev == "PTS" else INK
        ax.add_patch(Rectangle((x0, 1.2), 4.6, 0.9, fc="#eef0f2", ec=MUTED, lw=0.6))
        ax.add_patch(Rectangle((x0 + 1.35, 1.22), 1.95, 0.44, fc="white", ec=GOLD,
                               lw=0.8, hatch="///"))
        ax.text(x0 + 2.32, 0.92, "closed lane: equipment + crew", ha="center", va="center",
                fontsize=7.4, color=INK)
        ax.annotate("", xy=(x0 + 1.15, 1.88), xytext=(x0 + 0.3, 1.88),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
        ax.annotate("", xy=(x0 + 3.45, 1.88), xytext=(x0 + 4.3, 1.88),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.0))
        for xx in (x0 + 0.55, x0 + 4.05):
            ax.plot([xx], [2.42], marker="o", ms=4.5, color=col)
            ax.plot([xx, xx], [2.12, 2.38], color=col, lw=1.0)
            ax.text(xx, 2.56, dev, ha="center", fontsize=7.6, color=col)
        ax.text(x0 + 2.3, 3.12, title, ha="center", fontsize=8.4, color=INK)
        if dev == "MTC":
            ax.annotate("", xy=(x0 + 3.9, 2.66), xytext=(x0 + 0.7, 2.66),
                        arrowprops=dict(arrowstyle="<|-|>", color=MUTED, lw=0.7))
            ax.text(x0 + 2.3, 2.78, "radio hold", ha="center", fontsize=7.2, color=MUTED)
    fig.savefig(FIG / "fig_strategies.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 3 (event tree)
def fig_tree(tr):
    """Decision-tree staircase in the coauthor's visual grammar: bold question text
    (no boxes) cascading down the page, one straight drop to a terminal count per
    question, one elbow connector to the next question, every terminal on a shared
    baseline."""
    fig, ax = plt.subplots(figsize=(5.95, 2.21))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    face = med(tr["diag_S1a_facing_per_day"])
    v = med(tr["diag_S1a_violations_per_day"])
    cf = med(tr["diag_S1a_conflicts_per_day"])
    cl = med(tr["diag_S1a_collisions_per_day"])
    hm = med(tr["part_S1a_W5"])

    def sci(x):
        if x >= 10:
            return f"{x:,.0f}"
        if x >= 0.01:
            return f"{x:.2f}"
        e = int(np.floor(np.log10(x)))
        return rf"${x/10**e:.1f}\times10^{{{e}}}$"

    QY = [9.0, 7.15, 5.3, 3.45]         # question baselines, cascading down
    QX = [1.30, 3.45, 5.55, 7.65]       # question centres, cascading right
    BASE = 1.15                          # terminal number baseline

    questions = [
        "does the vehicle\nfacing red enter?",
        "does it meet an\nopposing vehicle?",
        "do they\ncollide?",
        "is anyone\nseriously hurt?",
    ]
    # (terminal value, terminal caption) for each question's "No" drop
    terminals = [
        (sci(face - v), "do not enter"),
        (sci(v - cf), "cross empty"),
        (sci(cf - cl), "avoided in time"),
        (sci(cl - hm), "no serious injury"),
    ]
    counts_on = [None, sci(v), sci(cf), sci(cl)]  # count beside each elbow into Q2..Q4

    # lead-in count above the first question
    ax.text(QX[0], QY[0] + 0.95, f"{face:,.0f} face a red each day",
            ha="center", va="bottom", fontsize=6.3, color=MUTED)

    for i, q in enumerate(questions):
        ax.text(QX[i], QY[i], q, ha="center", va="center", fontsize=7.2,
                color=INK, fontweight="bold", linespacing=1.25, zorder=4)
        # straight drop to the terminal ("No" branch)
        ax.annotate("", xy=(QX[i], BASE + 0.75), xytext=(QX[i], QY[i] - 0.85),
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9,
                                    shrinkA=0, shrinkB=0))
        ax.text(QX[i] + 0.12, (QY[i] - 0.85 + BASE) / 2 + 0.3, "No",
                ha="left", va="center", fontsize=6.6, color=INK)
        val, cap = terminals[i]
        ax.text(QX[i], BASE, val, ha="center", va="center", fontsize=7.2,
                color=INK, fontweight="bold")
        ax.text(QX[i], BASE - 0.75, cap, ha="center", va="center", fontsize=6.0,
                color=MUTED)
        # elbow connector to the next question ("Yes" branch): right, then down
        if i < 3:
            x_start = QX[i] + 1.30
            x_end = QX[i + 1]
            y_run = QY[i]
            ax.plot([x_start, x_end], [y_run, y_run], color=INK, lw=0.9,
                    solid_capstyle="butt", zorder=2)
            ax.annotate("", xy=(x_end, QY[i + 1] + 0.85), xytext=(x_end, y_run),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9,
                                        shrinkA=0, shrinkB=0))
            ax.text(x_end + 0.12, (y_run + QY[i + 1] + 0.85) / 2, "Yes",
                    ha="left", va="center", fontsize=6.6, color=INK)
            if counts_on[i + 1]:
                ax.text((x_start + x_end) / 2, y_run + 0.30, counts_on[i + 1],
                        ha="center", va="bottom", fontsize=6.4, color=MUTED)
        else:
            # final "Yes": elbow right then down to the last terminal
            x_start = QX[i] + 1.30
            x_end = 9.35
            ax.plot([x_start, x_end], [QY[i], QY[i]], color=INK, lw=0.9,
                    solid_capstyle="butt", zorder=2)
            ax.annotate("", xy=(x_end, BASE + 0.75), xytext=(x_end, QY[i]),
                        arrowprops=dict(arrowstyle="-|>", color=INK, lw=0.9,
                                        shrinkA=0, shrinkB=0))
            ax.text(x_end + 0.12, (QY[i] + BASE) / 2 + 0.3, "Yes",
                    ha="left", va="center", fontsize=6.6, color=INK)
            ax.text(x_end, BASE, sci(hm), ha="center", va="center", fontsize=7.2,
                    color=INK, fontweight="bold")
            ax.text(x_end, BASE - 0.75, "death or\nserious injury", ha="center",
                    va="top", fontsize=6.0, color=MUTED, linespacing=1.15)

    fig.savefig(FIG / "fig_tree.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 4 (code all-red)
def fig_allred():
    """The code all-red rules alone (was panel b of the retired 3-panel stack)."""
    fig, ax = plt.subplots(figsize=(4.2, 1.95))
    L = np.linspace(50, 300, 120)
    ax.step([0, 50, 100, 150, 200, 250, 300], [5, 10, 15, 20, 25, 30, 30],
            where="post", color=BLUE, lw=1.7)
    ax.text(255, 31.6, "NZ M23 / UK", fontsize=7.2, color=BLUE, ha="center")
    ax.plot(L, L / (20 / 3.6), color=AQUA, lw=1.4, ls="-")
    ax.text(88, 24.5, "NSW at 20 km/h", fontsize=7.2, color=AQUA, rotation=44)
    ax.plot(L, L / (40 / 3.6), color=AQUA, lw=1.4, ls="--")
    ax.text(297, 21.0, "NSW at 40 km/h", fontsize=7.2, color=AQUA, ha="right", va="top")
    ax.plot(L, L / (32.2 / 3.6) + 4.0, color=GOLD, lw=1.5, ls="--")
    ax.text(163, 26.5, "Texas 20 mph + 4 s", fontsize=7.2, color=GOLD, rotation=33)
    ax.set_xlabel("distance between stop lines (m)")
    ax.set_ylabel("all-red clearance (s)")
    ax.set_ylim(0, 56)
    ax.set_xlim(0, 310)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_allred.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 5 (avoidance priors)
def fig_avoidance():
    """The avoidance-probability prior family alone (was panel c of the retired stack)."""
    fig, ax = plt.subplots(figsize=(4.2, 1.95))
    ttc = np.linspace(0, 8, 240)
    for t50, s, c, ls in ((1.0, 0.3, SEQ[1], ":"), (1.75, 0.65, BLUE, "-"),
                          (2.5, 1.0, SEQ[5], "--")):
        ax.plot(ttc, 1 / (1 + np.exp((ttc - t50) / s)), color=c, ls=ls, lw=1.5)
    ax.text(4.0, 0.72, "prior bounds on the\nmidpoint and slope", fontsize=7.2, color=MUTED)
    ax.axvline(1.5, color=MUTED, lw=0.7, ls="-.")
    ax.text(1.62, 0.13, "surprise-hazard\nresponse, 1.5 s", fontsize=7.2, color=MUTED)
    ax.set_xlabel("time to collision at first mutual sight (s)")
    ax.set_ylabel("P(one driver\nfails to avoid)")
    ax.set_ylim(0, 1.02)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_avoidance.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 6 (injury curves)
def fig_injury():
    """The two injury curves and what they mean per event. Panel (a): each struck
    person's risk on the two published curves. Panel (b): the per-event probability
    at a given operating speed, where a head-on closes at twice that speed and
    exposes both cars' occupants."""
    from mtcpts.severity import p_worker, p_occupant

    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.15))

    ax = axes[0]
    v = np.linspace(0, 120, 240)
    ax.plot(v, p_worker(v), color=INK, lw=1.7,
            label="worker on foot, at impact speed (GIDAS)")
    ax.plot(v, p_occupant(v), color=BLUE, lw=1.7, ls="--",
            label="belted occupant, at delta-V (NHTSA)")
    # equal-risk pair: worker at 31 km/h = occupant at delta-V 47 km/h
    pw = float(p_worker(np.array([31.0]))[0])
    ax.plot([31, 47], [pw, pw], color=MUTED, lw=0.8, ls=":")
    ax.plot([31], [pw], marker="o", ms=4.5, mfc="white", mec=INK, mew=1.1, zorder=5)
    ax.plot([47], [pw], marker="o", ms=4.5, mfc="white", mec=BLUE, mew=1.1, zorder=5)
    ax.annotate("same risk:\n31 vs 47 km/h", xy=(39, pw), xytext=(20, 0.42),
                fontsize=6.8, color=MUTED, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    ax.set_xlabel("impact speed or delta-V (km/h)")
    ax.set_ylabel("P(MAIS3+) per person")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, 120)
    ax.legend(loc="upper left", fontsize=6.4, handlelength=1.6, frameon=True, facecolor="white", edgecolor="none", framealpha=1.0)
    ax.set_title("(a)   each person's risk", loc="left")
    _clean(ax)

    ax = axes[1]
    vop = np.linspace(10, 80, 200)
    p_strike_event = p_worker(vop)                       # one worker struck at vop
    dv = vop  # closing speed 2*vop, equal masses: delta-V per vehicle = vop
    p_occ = p_occupant(dv)
    occ = 1.56
    p_headon_event = 1.0 - (1.0 - p_occ) ** (2 * occ)    # >=1 of both cars' occupants
    ax.plot(vop, p_strike_event, color=INK, lw=1.7, label="worker struck at this speed")
    ax.plot(vop, p_headon_event, color=BLUE, lw=1.7, ls="--",
            label="head-on between two vehicles\nboth travelling at this speed")
    ax.axvline(45, color=MUTED, lw=0.7, ls="-.")
    ax.text(46.5, 0.06, "above about 45 km/h the\nhead-on is the worse event",
            fontsize=6.8, color=MUTED)
    ax.set_xlabel("operating speed (km/h)")
    ax.set_ylabel("P(serious-harm event)")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(10, 80)
    ax.legend(loc="upper left", fontsize=6.4, handlelength=1.6, frameon=True, facecolor="white", edgecolor="none", framealpha=1.0)
    ax.set_title("(b)   per event, at one operating speed", loc="left")
    _clean(ax)

    fig.tight_layout()
    fig.savefig(FIG / "fig_injury.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 7 (input origins)
def fig_inputs():
    """Where every model input comes from and where it enters the model."""
    fig, ax = plt.subplots(figsize=(6.0, 2.35))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, title, lines, fc, ec, fs=6.4):
        ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=0.9, zorder=3))
        ax.text(x + 0.16, y + h - 0.28, title, ha="left", va="top", fontsize=7.0,
                color=INK, zorder=4, fontweight="bold")
        ax.text(x + 0.16, y + 0.22, lines, ha="left", va="bottom", fontsize=fs,
                color=INK, zorder=4, linespacing=1.4)

    # origins, left column
    box(0.05, 7.55, 4.35, 2.40, "Field measurements",
        "violation rates at signals and at flaggers;\nentry timing within the red; operating speed",
        "#eef4fc", BLUE)
    box(0.05, 5.00, 4.35, 2.40, "Expert panel (companion study)",
        "controller-strike rate and its severity;\nqueue-tail crash rate and its severity",
        "#eef9f4", AQUA)
    box(0.05, 2.45, 4.35, 2.40, "Standards",
        "all-red tables and their assumed speeds;\ntemporary speed limit; sight-distance rules",
        "#fdf6e3", GOLD)
    box(0.05, 0.05, 4.35, 2.25, "Assumed ranges (Table 1)",
        "10 quantities never measured at a portable\nsignal, each given a wide prior",
        "#f4f4f2", MUTED)

    # model stages, right column
    box(6.55, 6.85, 3.40, 2.55, "Signal cycle and queues",
        "red and green times, all-red,\nqueues, vehicles facing red", "#f5f7fa", MUTED)
    box(6.55, 3.85, 3.40, 2.55, "Red-running event tree",
        "enter, meet, collide\n(Figure 3)", "#f5f7fa", MUTED)
    box(6.55, 0.55, 3.40, 2.85, "Strike and queue-tail terms;\ninjury step",
        "rate × severity for each;\ninjury curves (Figure 6)", "#f5f7fa", MUTED)

    def arrow(y0, y1, color):
        ax.annotate("", xy=(6.55, y1), xytext=(4.40, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                                    shrinkA=2, shrinkB=2), zorder=2)

    arrow(9.10, 5.60, BLUE)    # field -> tree (violation rates, timing)
    arrow(8.40, 8.60, BLUE)    # field (operating speed) -> cycle
    arrow(6.20, 1.90, AQUA)    # panel -> strike/queue-tail terms
    arrow(3.95, 7.80, GOLD)    # standards -> cycle
    arrow(3.30, 1.40, GOLD)    # standards (speed limit) -> injury
    arrow(1.20, 4.90, MUTED)   # assumed -> tree
    ax.text(5.45, 9.55, "feeds", ha="center", fontsize=6.2, color=MUTED)

    fig.savefig(FIG / "fig_inputs.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 9 (decision surface)
def fig3_decision_surface(gates, bands):
    s = np.load(DIST / "decision_surface.npz")
    x, y, P = s["headon_dsi_per_day"], s["controller_dsi_per_day"], s["p_grid"]

    fig, ax = plt.subplots(figsize=(4.44, 3.13))
    cf = ax.contourf(x, y, P, levels=np.linspace(0, 1, 11),
                     colors=["#ffffff", *SEQ[:6], *([SEQ[6]] * 3)])
    ax.contour(x, y, P, levels=[0.5], colors=[INK], linewidths=[1.4], zorder=5)
    lbl = ax.text(3.3e-6, 1.15e-5, "break-even (P = 0.5)", fontsize=7.0, color="white",
                  rotation=38, ha="center", va="center", zorder=7)
    lbl.set_path_effects([pe.withStroke(linewidth=1.6, foreground="#184f95")])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(x.min(), x.max()); ax.set_ylim(y.min(), y.max())

    hb, sb = bands["headon_dsi_per_op_day_band"], bands["dsi_per_op_day_band"]
    ax.add_patch(Rectangle((hb[0], sb[0]), hb[1] - hb[0], sb[1] - sb[0],
                           fc="none", ec=GOLD, lw=1.6, zorder=6))
    ax.add_patch(Rectangle((hb[0], sb[0]), hb[1] - hb[0], sb[1] - sb[0],
                           fc=GOLD, alpha=0.30, lw=0, zorder=4))
    ax.annotate("range both records support", (hb[0], sb[0]), textcoords="offset points",
                xytext=(2, -30), fontsize=7.2, color=INK, ha="left")

    ax.plot([float(s["w5_median"])], [float(s["w3_median"])], marker="o", ms=6.5,
            mfc="white", mec=INK, mew=1.4, zorder=6)
    ax.annotate("panel's value", (float(s["w5_median"]), float(s["w3_median"])),
                textcoords="offset points", xytext=(-12, -3), fontsize=7.2, color="white", ha="right")
    ax.annotate("", (float(s["w5_median"]), float(s["w3_median"])),
                xytext=(float(s["w5_median"]), 1.0e-5),
                arrowprops=dict(arrowstyle="<|-|>", color="white", lw=0.8, mutation_scale=7))
    factor = float(s["w3_median"]) / 1.0e-5
    ax.text(float(s["w5_median"]) * 1.18, 2.6e-4, f"{factor:.0f}×", fontsize=7.2,
            color="white", ha="left", va="center")

    ax.set_xlabel("head-on serious-harm events per operation day (introduced)")
    ax.set_ylabel("controller serious-harm events\nper operation day (removed)")
    ax.set_title("P(portable signals reduce the risk of serious harm)", loc="left")
    cb = fig.colorbar(cf, ax=ax, pad=0.02, fraction=0.045)
    cb.set_label("P($\\Delta H$ < 0)", fontsize=7.4)
    cb.ax.tick_params(labelsize=7.2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(FIG / "fig3_decision_surface.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 8 (decomp + PRCC)
def fig4_decomposition_prcc(tr):
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.41))

    ax = axes[0]
    paths = ["W1", "W3", "W5", "W4d"]
    labels = ["rear-end", "strike", "head-on", "placement"]
    xs = np.arange(len(paths))
    for i, st in enumerate(("S0", "S1a", "S1b")):
        c, _, hatch = STRAT[st]
        vals = [med(tr[f"part_{st}_{p}"]) for p in paths]
        xs_nz = [x + (i - 1) * 0.27 for x, v in zip(xs, vals) if v > 1e-11]
        vs_nz = [v for v in vals if v > 1e-11]
        ax.bar(xs_nz, vs_nz, width=0.25, color=c, edgecolor="white",
               lw=0.5, hatch=hatch, label=st)
    ax.set_yscale("log")
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=7.4)
    ax.set_ylabel("serious-harm events\nper operation day")
    ax.set_title("(a)   harm by kind and strategy", loc="left")
    ax.legend(frameon=False, ncol=1, loc="upper right", handlelength=1.3, labelspacing=0.3)
    _clean(ax)

    ax = axes[1]
    NAMES = {
        "re3_rate": "controller-strike rate",
        "sev3_p": "controller-strike severity",
        "platoon_speed_kmh": "operating speed",
        "f_cycle_a": "fixed-time green ratio",
        "re1_rate": "queue-tail crash rate",
        "sev1_p": "queue-tail severity",
        "q_lead": "sighted entrant enters anyway",
        "impact_speed_frac": "impact speed retention",
        "startup_lost_s": "startup lost time",
        "w_onset": "onset violation share",
        "ttc50": "avoidance midpoint TTC",
        "d_sight_m": "mutual sight distance",
        "w_occ": "entry against visible vehicle",
    }
    rows = load_csv("prcc_baseline_s1a.csv")[:9][::-1]
    vals = [float(r["prcc"]) for r in rows]
    labels = [NAMES.get(r["input"], r["input"]) for r in rows]
    ax.barh(labels, vals, height=0.62,
            edgecolor="white", lw=0.4, color=[BLUE if v > 0 else INK for v in vals])
    for i, v in enumerate(vals):
        if v < -0.5:
            ax.text(v + 0.02, i, f"{v:.2f}", ha="left", va="center", fontsize=7.0,
                    color="white")
        elif v < 0:
            ax.text(v - 0.02, i, f"{v:.2f}", ha="right", va="center", fontsize=7.0,
                    color=INK)
        else:
            ax.text(v + 0.02, i, f"+{v:.2f}", ha="left", va="center", fontsize=7.0,
                    color=INK)
    ax.set_xlim(-1.06, 0.14)
    ax.axvline(0, color=MUTED, lw=0.7)
    ax.set_xlabel("partial rank correlation with $\\Delta H$")
    ax.set_title("(b)   partial rank correlations", loc="left")
    ax.tick_params(axis="y", labelsize=7.0)
    _clean(ax, "x")

    fig.tight_layout()
    fig.savefig(FIG / "fig4_decomp_prcc.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 11 (curves)
def fig5_calibration_and_sight():
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.40))
    tr = np.load(DIST / "baseline_traces.npz")
    W3 = tr["part_S0_W3"]; W4 = tr["part_S1a_W4d"]
    W5g = tr["part_S1a_W5"] - tr["part_S0_W5"]
    w3_med = float(np.nanmedian(W3))

    ax = axes[0]
    xs = np.geomspace(1e-6, 1e-2, 80)
    ps = []
    for x in xs:
        dh = W4 - (x / w3_med) * W3 + W5g
        dh = dh[np.isfinite(dh)]
        ps.append((dh < 0).mean())
    ax.plot(xs, ps, color=BLUE, lw=1.8)
    ax.axvspan(5e-6, 2e-5, color=GOLD, alpha=0.25, lw=0)
    ax.text(1e-5, 0.06, "injury\nrecord", fontsize=7.2, color=INK, ha="center")
    ax.plot([w3_med], [np.interp(np.log(w3_med), np.log(xs), ps)], marker="o", ms=6,
            mfc="white", mec=INK, mew=1.3, zorder=5)
    ax.annotate("panel value", (w3_med, np.interp(np.log(w3_med), np.log(xs), ps)),
                textcoords="offset points", xytext=(-4, -14), fontsize=7.2, ha="right")
    ax.axhline(0.5, color=MUTED, lw=0.7, ls=":")
    ax.set_xscale("log"); ax.set_ylim(0, 1.03)
    ax.set_xlabel("controller serious harm per operation day")
    ax.set_ylabel("P($\\Delta H$ < 0)")
    ax.set_title("(a)   probability against the strike rate", loc="left")
    _clean(ax)

    ax = axes[1]
    rows = load_csv("sight_sweep.csv")
    for L, c, ls, mk in ((250, BLUE, "-", "o"), (1000, SEQ[5], "--", "s")):
        sub = [r for r in rows if int(r["section_m"]) == L]
        x = [float(r["sight_m"]) for r in sub]
        y = [float(r["w5_s1a_median"]) for r in sub]
        ax.plot(x, y, color=c, ls=ls, lw=1.7, marker=mk, ms=3.5, label=f"{L} m section")
    ax.axhspan(6e-6, 2e-5, color=GOLD, alpha=0.25, lw=0)
    ax.text(940, 8.5e-6, "record range", fontsize=7.2, color=INK, ha="right")
    ax.set_yscale("log")
    ax.set_yticks([1e-6, 1e-5])
    ax.set_xticks([150, 500, 1000])
    ax.set_xticklabels(["150", "500", "1000"], fontsize=7.2)
    ax.set_xlabel("how far the two ends can see each other (m)")
    ax.set_ylabel("red-running serious harm\nper operation day")
    ax.set_title("(b)   sight between the ends", loc="left")
    ax.legend(loc="lower left", fontsize=7.0, frameon=True, facecolor="white", edgecolor="none", framealpha=1.0)
    _clean(ax)

    fig.tight_layout()
    fig.savefig(FIG / "fig5_calibration_speed.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 10 (spread vs margin)
def fig_spread():
    import json as _json
    tr = np.load(DIST / "baseline_traces.npz")
    bands = _json.loads((MODEL.parent / "research" / "controller-strike-band.json").read_text())
    W3 = tr["part_S0_W3"]; W4 = tr["part_S1a_W4d"]
    W5g = tr["part_S1a_W5"] - tr["part_S0_W5"]
    w3_med = float(np.nanmedian(W3))
    w5_med = float(np.nanmedian(tr["part_S1a_W5"]))
    margin = 4.0e-5

    def read(hc, sc):
        dh = W4 + (hc / w5_med) * W5g - (sc / w3_med) * W3
        return dh[np.isfinite(dh)]

    rows = [
        ("records at\nmid-range", read(1.2e-5, 1.0e-5)),
        ("both records at the\ntop of their ranges", read(bands["headon_dsi_per_op_day_band"][1],
                                                        bands["dsi_per_op_day_band"][1])),
    ]
    fig, ax = plt.subplots(figsize=(6.5, 1.79))
    ax.axvspan(-margin, margin, color=GOLD, alpha=0.22, lw=0)
    ax.axvline(0, color=MUTED, lw=0.8)
    for i, (lab, dh) in enumerate(rows):
        y = 1.15 - i
        q5, q25, q50, q75, q95 = np.quantile(dh, [0.05, 0.25, 0.5, 0.75, 0.95])
        p_in = (np.abs(dh) <= margin).mean()
        ax.plot([q5, q95], [y, y], color=MUTED, lw=1.6, solid_capstyle="butt")
        ax.plot([q25, q75], [y, y], color=BLUE, lw=5.0, solid_capstyle="butt")
        ax.plot([q50], [y], marker="o", ms=6.5, mfc="white", mec=INK, mew=1.3, zorder=5)
        ax.text(4.05e-4, y, f"{p_in:.2f} of the spread\nwithin the margin",
                fontsize=7.2, color=INK, va="center", ha="right",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none"))
    ax.text(-margin - 4e-6, 1.72, "harm falls with signals", fontsize=7.2, color=MUTED, ha="right")
    ax.text(margin + 4e-6, 1.72, "harm rises with signals", fontsize=7.2, color=MUTED, ha="left")
    ax.text(0, 0.62, "margin: 1 event per 100 site-years either way", fontsize=7.0,
            color=INK, ha="center", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    ax.set_yticks([1.15, 0.15])
    ax.set_yticklabels([r[0] for r in rows], fontsize=7.4)
    ax.set_ylim(-0.45, 1.95)
    ax.set_xlim(-2.6e-4, 4.15e-4)
    ax.set_xticks([-2e-4, -1e-4, 0, 1e-4, 2e-4, 3e-4])
    ax.set_xticklabels(["-2", "-1", "0", "1", "2", "3"])
    ax.set_xlabel("change in serious-harm events per operation day (signals minus controllers, ×10$^{-4}$)")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(left=False)
    fig.tight_layout()
    fig.savefig(FIG / "fig_spread.png")
    plt.close(fig)


# ----------------------------------------------------------------- FIGURE 12 (speed)
def fig_speed():
    fig, ax = plt.subplots(figsize=(5.17, 2.47))
    rows = load_csv("speed_sweep.csv")
    v = np.array([float(r["platoon_speed_kmh"]) for r in rows])
    w5 = np.array([float(r["w5_s1a_median"]) for r in rows])
    w3 = np.array([float(r["w3_median"]) for r in rows])
    ax.plot(v, w3, color=INK, ls="--", lw=1.8, marker="s", ms=3.5,
            label="controller struck (manual control)")
    ax.plot(v, w5, color=BLUE, ls="-", lw=1.8, marker="o", ms=3.5,
            label="head-on from red running (signals)")
    ax.annotate("about 10× over this range", xy=(46, 5.2e-5), fontsize=7.2, color=BLUE)
    ax.annotate("about 2.3×", xy=(72, 3.3e-3), fontsize=7.2, color=INK)
    ax.set_yscale("log")
    ax.set_xlabel("operating speed through the works (km/h)")
    ax.set_ylabel("serious-harm events\nper operation day")
    ax.legend(loc="center right", fontsize=7.2, frameon=True, facecolor="white", edgecolor="none", framealpha=1.0)
    _clean(ax)
    fig.tight_layout()
    fig.savefig(FIG / "fig_speed.png")
    plt.close(fig)


def main():
    tr = np.load(DIST / "baseline_traces.npz")
    gates = json.loads((DIST / "validity_gates.json").read_text())
    bands = json.loads((MODEL.parent / "research" / "controller-strike-band.json").read_text())
    fig0_model_flow()
    fig_strategies()
    fig_tree(tr)
    fig_allred()
    fig_avoidance()
    fig_injury()
    fig_inputs()
    fig3_decision_surface(gates, bands)
    fig4_decomposition_prcc(tr)
    fig5_calibration_and_sight()
    fig_spread()
    fig_speed()
    print(f"figures -> {FIG}  (from {DIST.name})")


if __name__ == "__main__":
    main()
