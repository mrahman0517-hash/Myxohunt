"""
Compare population runs on one picture: E. coli on top, Myxo below, one line per run, against
biological time (both panels share the time axis; each has its own single count axis).

Usage (from predation-sim/):
    python checks/compare_runs.py out_name run[:short[:long]] [run ...] [--targets prey,myxo]
Reads checks/output/<run>_stats.csv (written by check_populations.py) and writes
checks/output/<out_name>.png. `short` labels the line end, `long` the legend; --targets draws
dashed reference lines (e.g. --targets 500,200) or pale bands for ranges (--targets 700-1000,150).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]   # fixed order, validated all-pairs (dataviz reference palette)
INK = {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#898781",
       "grid": "#e1e0d9", "axis": "#c3c2b7", "surface": "#fcfcfb"}


def parse_runs(args):
    """Turn 'run:short:long' arguments into (run, short label, legend label) triples."""
    runs = []
    for arg in args:
        parts = arg.split(":", 2)                            # the legend label may contain colons
        name = parts[0]
        short = parts[1] if len(parts) > 1 else name
        long = parts[2] if len(parts) > 2 else short
        runs.append((name, short, long))
    return runs


def load(name):
    """Biological hours, E. coli and Myxo counts of one run."""
    data = np.genfromtxt(os.path.join(OUT, name + "_stats.csv"), delimiter=",", names=True)
    return data["bio_t"] / 60.0, data["ecoli"], data["myxo"]


def style_axis(ax, ylabel):
    """Recessive grid and axes, text in ink colours."""
    ax.set_facecolor(INK["surface"])
    ax.grid(True, color=INK["grid"], lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK["axis"])
    ax.tick_params(colors=INK["muted"], labelcolor=INK["secondary"])
    ax.set_ylabel(ylabel, color=INK["secondary"])


def end_labels(ax, ends, x_max):
    """Short labels just right of each line's last point; labels ending at about the same time are
    nudged apart so they don't overlap."""
    lo, hi = ax.get_ylim()
    gap = 0.06 * (hi - lo)
    placed = []                                            # (x, y) of labels already drawn
    for short, x, y in sorted(ends, key=lambda e: e[2]):
        for px, py in placed:
            if abs(px - x) < 0.05 * x_max and y < py + gap:
                y = py + gap
        placed.append((x, y))
        ax.text(x + 0.01 * x_max, y, short, color=INK["secondary"], va="center", fontsize=9)


def target_line(ax, value, x_max, what):
    """A dashed reference line for a target number (or a pale band for a target range given as
    (low, high)), labelled at its left end."""
    if isinstance(value, tuple):
        lo, hi = value
        ax.axhspan(lo, hi, color=INK["grid"], alpha=0.6, lw=0, zorder=0)
        ax.text(x_max * 0.005, hi, f" target {lo:,.0f}–{hi:,.0f} {what}", color=INK["muted"], fontsize=8,
                va="bottom")
        return
    ax.axhline(value, color=INK["muted"], lw=1.0, ls=(0, (4, 3)))
    ax.text(x_max * 0.005, value, f" target ~{value:,.0f} {what}", color=INK["muted"], fontsize=8,
            va="bottom")


def parse_target(text):
    """'500' → 500.0 (a line); '700-1000' → (700.0, 1000.0) (a band)."""
    if "-" in text:
        lo, hi = text.split("-")
        return float(lo), float(hi)
    return float(text)


def panel(ax, runs, column, ylabel, target, what):
    """One panel: a line per run for one count column (1 = E. coli, 2 = Myxo)."""
    style_axis(ax, ylabel)
    ends, x_max = [], 0.0
    for k, (name, short, long) in enumerate(runs):
        h, *counts = load(name)
        y = counts[column - 1]
        ax.plot(h, y, color=SERIES[k], lw=1.6, label=long, solid_capstyle="round")
        ends.append((short, h[-1], y[-1]))
        x_max = max(x_max, h[-1])
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, None)
    if target:
        target_line(ax, target, x_max, what)
    end_labels(ax, ends, x_max)


def main():
    """Read the command line, draw both panels and save the picture."""
    args = sys.argv[1:]
    targets = (None, None)
    if "--targets" in args:
        k = args.index("--targets")
        targets = tuple(parse_target(v) for v in args[k + 1].split(","))
        args = args[:k] + args[k + 2:]
    out_name, runs = args[0], parse_runs(args[1:])
    if len(runs) > len(SERIES):
        raise SystemExit(f"at most {len(SERIES)} runs per picture (colour-blind-safe set)")
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 7.5), dpi=110, sharex=True)
    fig.patch.set_facecolor(INK["surface"])
    panel(top, runs, 1, "E. coli (cells)", targets[0], "prey")
    panel(bottom, runs, 2, "Myxo (cells)", targets[1], "hunters")
    bottom.set_xlabel("biological time (h)", color=INK["secondary"])
    top.set_title("Prey and hunters over time", loc="left", color=INK["primary"], fontsize=12)
    top.legend(loc="best", frameon=False, labelcolor=INK["secondary"])
    fig.tight_layout()
    path = os.path.join(OUT, out_name + ".png")
    fig.savefig(path, facecolor=fig.get_facecolor())
    print("saved", path)


if __name__ == "__main__":
    main()
