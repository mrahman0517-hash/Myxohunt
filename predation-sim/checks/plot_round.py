"""
A full 4-seed round against the B98 baseline on one picture: E. coli on top, Myxo below, each set of
seeds as its mean with a pale range, the target band as a grey strip and the judged window
(150–300 bio-h) between dashed lines.

Usage (from predation-sim/):  python checks/plot_round.py r6 "lysis 70% + refill ÷6"   → checks/output/r6_compare.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

from plot_baseline import BAND, GRID, HUNT, INK, MUTED, OUT, spread   # noqa: E402

SEEDS = (1, 2, 3, 4)


def panel(ax, column, target, label, rounds):
    """One population: the band, the window, each round's mean and range."""
    ax.axhspan(*target, color=BAND, zorder=0)
    for x in (150, 300):
        ax.axvline(x, color=MUTED, lw=0.9, ls="--", zorder=1)
    for names, colour, name in rounds:
        h, mean, lo, hi = spread(names, column)
        ax.fill_between(h, lo, hi, color=colour, alpha=0.18, lw=0)
        ax.plot(h, mean, color=colour, lw=1.8, label=name)
    ax.set_ylabel(label, color=INK)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=MUTED)


def main():
    """Draw both panels and save the picture."""
    prefix, label = sys.argv[1], sys.argv[2]
    rounds = ((["base_rec_s%d" % s for s in SEEDS], MUTED, "Recommended preset (B98 baseline), 4 seeds"),
              (["%s_s%d" % (prefix, s) for s in SEEDS], HUNT, f"{label}, 4 seeds"))
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(10, 7), sharex=True, dpi=110)
    panel(top, "ecoli", (700, 1000), "living E. coli", rounds)
    panel(bottom, "myxo", (100, 220), "Myxo", rounds)
    top.legend(loc="upper right", frameon=False)
    top.set_title("Mean and range of 4 seeds; grey strip = target band; judged window 150–300 bio-h between the "
                  "dashed lines\n(the baseline was stopped at 195–265 bio-h, so its lines end at 195)",
                  loc="left", fontsize=10, color=INK)
    bottom.set_xlabel("biological time (h)", color=INK)
    bottom.set_xlim(0, 300)
    fig.tight_layout()
    path = os.path.join(OUT, f"{prefix}_compare.png")
    fig.savefig(path)
    print("saved", path)


if __name__ == "__main__":
    main()
