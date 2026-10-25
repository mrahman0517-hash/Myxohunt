"""
Refill branch comparison (B100): from each lysis-70% branch at +100 bio-h (B99), ground refill ÷6 and
÷4 against ÷8 carried on unchanged, all from the same state. Prints E. coli and Myxo every 10 bio-h
from the branch point, their means over the last 30 bio-h, and the events per bio-h from the direct
counters; draws checks/output/refill_compare.png.

Usage (from predation-sim/):  python checks/compare_refill.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

from compare_branches import BAND, OUT, SEEDS, branch, rates, start_of   # noqa: E402

LONG = 100.0                                                 # bio-h of the 70% branch before this test
ARMS = (("br70L", "refill ÷8 (control)", "#898781"), ("rf6", "refill ÷6", "#2a78d6"), ("rf4", "refill ÷4", "#eb6834"))


def main():
    """Print the table and draw the picture."""
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True, dpi=100)
    for k, seed in enumerate(SEEDS):
        start = start_of(seed) + LONG * 60.0
        print(f"seed {seed}, branched at {start / 60:.0f} bio-h")
        for arm, label, colour in ARMS:
            d = branch(f"{arm}_s{seed}", start)
            if d is None or len(d) < 2:
                print(f"  {label}: no data yet")
                continue
            marks = [d.iloc[(d["dh"] - h).abs().argmin()] for h in range(0, int(d["dh"].iloc[-1] + 0.5) + 1, 10)]
            late = d[d["dh"] >= d["dh"].iloc[-1] - 30]
            print(f"  {label:20s} " + "  ".join(f"+{r.dh:.0f}h {int(r.ecoli)}/{int(r.myxo)}" for r in marks)
                  + f"  | last 30 h: {late['ecoli'].mean():.0f} / {late['myxo'].mean():.0f}")
            print(f"  {'':20s} {rates(d)}")
            for row, col in enumerate(("ecoli", "myxo")):
                axes[row, k].plot(d["dh"], d[col], color=colour, lw=1.6, label=label)
        for row, col in enumerate(("ecoli", "myxo")):
            axes[row, k].axhspan(*BAND[col], color="#ecebe5", zorder=0)
            axes[row, k].set_title(f"seed {seed}: {'E. coli' if col == 'ecoli' else 'Myxo'}", fontsize=10, loc="left")
            for side in ("top", "right"):
                axes[row, k].spines[side].set_visible(False)
    axes[0, 0].legend(frameon=False, fontsize=9)
    for ax in axes[1]:
        ax.set_xlabel("bio-h after the branch")
    fig.suptitle("Refill test (B100): famine lysis 70%, same starting state, ground refill ÷8 / ÷6 / ÷4; grey = target band",
                 x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "refill_compare.png"))


if __name__ == "__main__":
    main()
