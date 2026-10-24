"""
The B97 baseline on one picture (B98): E. coli on top, Myxo below, against biological time. The
four seeds of the Recommended preset are drawn as their mean with a pale range (lowest to highest
seed); the prey-only runs (no Myxo) as a second line; the target band as a grey strip, and the
judged window (150–300 bio-h) between dashed lines.

Usage (from predation-sim/):  python checks/plot_baseline.py   → checks/output/base_rec_compare.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402
import pandas as pd                                          # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
HUNT, PREY_ONLY = "#2a78d6", "#eb6834"
INK, MUTED, GRID, BAND = "#0b0b0b", "#898781", "#e1e0d9", "#ecebe5"


def hourly(name, column):
    """One column of a run, one value per bio-hour, indexed by bio-hour."""
    d = pd.read_csv(os.path.join(OUT, name + "_stats.csv"))
    return d.groupby((d["bio_t"] / 60.0).round())[column].last()


def spread(names, column):
    """Mean, lowest and highest over several runs, on the hours all of them reached."""
    table = pd.concat([hourly(n, column) for n in names], axis=1).dropna()
    return table.index.values, table.mean(axis=1).values, table.min(axis=1).values, table.max(axis=1).values


def panel(ax, column, target, label, hunters, prey_only):
    """One population: the target band, the window, the seeds' mean and range, prey only if given."""
    ax.axhspan(*target, color=BAND, zorder=0)
    for x in (150, 300):
        ax.axvline(x, color=MUTED, lw=0.9, ls="--", zorder=1)
    h, mean, lo, hi = spread(hunters, column)
    ax.fill_between(h, lo, hi, color=HUNT, alpha=0.18, lw=0)
    ax.plot(h, mean, color=HUNT, lw=1.8, label="Recommended preset, 4 seeds (mean and range)")
    if prey_only:
        h, mean, _, _ = spread(prey_only, column)
        ax.plot(h, mean, color=PREY_ONLY, lw=1.8, label="prey only, no Myxo (mean of 2 seeds)")
    ax.set_ylabel(label, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED)


def main():
    """Draw both panels and save the picture."""
    hunters = [f"base_rec_s{s}" for s in (1, 2, 3, 4)]
    prey = ["prey_rec_s1", "prey_rec_s2"]
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, dpi=110)
    panel(top, "ecoli", (700, 1000), "living E. coli", hunters, prey)
    panel(bottom, "myxo", (100, 220), "Myxo", hunters, None)
    top.legend(loc="upper right", frameon=False)
    top.set_title("Baseline of 23–24 Oct 2026 (B98): grey strip = target band; judged window 150–300 bio-h between "
                  "the dashed lines;\nlines end at 195 bio-h, where the slowest seed was stopped",
                  loc="left", fontsize=10, color=INK)
    bottom.set_xlabel("biological time (h)", color=INK)
    bottom.set_xlim(0, 300)
    fig.tight_layout()
    path = os.path.join(OUT, "base_rec_compare.png")
    fig.savefig(path)
    print("saved", path)


if __name__ == "__main__":
    main()
