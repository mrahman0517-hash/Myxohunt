"""
Paired branch comparison (B99): for each seed, the treatment branch (famine lysis 70%) against its
control (20%), both started from the same stopped baseline state. Prints E. coli and Myxo every
10 bio-h from the branch point, and the events per bio-h over the whole branch from the direct
counters; draws checks/output/branch_compare.png.

Usage (from predation-sim/):  python checks/compare_branches.py
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import pandas as pd                                          # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SEEDS = (1, 2, 3, 4)
ARMS = ((("br70L", "br70"), "lysis 70%", "#2a78d6"), (("br20",), "lysis 20% (control)", "#898781"))   # the longest branch that exists
BAND = {"ecoli": (700, 1000), "myxo": (100, 220)}


def branch(name, start):
    """A branch's rows from its start on, with time counted from the branch point (bio-h)."""
    path = os.path.join(OUT, name + "_stats.csv")
    if not os.path.exists(path):
        return None
    d = pd.read_csv(path)
    d = d[d["bio_t"] >= start].copy()
    d["dh"] = (d["bio_t"] - start) / 60.0
    return d


def start_of(seed):
    """The bio min where the seed's baseline stopped (the branch point)."""
    d = pd.read_csv(os.path.join(OUT, f"base_rec_s{seed}_stats.csv"))
    return float(d["bio_t"].iloc[-1])


def rates(d):
    """Events per bio-h over the branch, from the direct counters."""
    span = d["dh"].iloc[-1] - d["dh"].iloc[0]
    r = lambda c: (d[c].iloc[-1] - d[c].iloc[0]) / span if span > 0 else float("nan")
    eaten = r("store_from_kills") + r("store_from_food") + r("store_from_scraps")
    return (f"E born {r('ecoli_divisions') + r('ecoli_founders'):4.1f}, killed {r('ecoli_killed'):4.1f}, "
            f"starved {r('ecoli_starved'):4.1f} | Myxo born {r('myxo_divisions'):4.2f}, lysed {r('famine_lysed'):4.2f}, "
            f"spores {r('famine_spores'):4.2f} | store in {eaten:3.0f}, upkeep {r('store_upkeep'):3.0f}")


def main():
    """Print the table and draw the picture."""
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True, dpi=100)
    for k, seed in enumerate(SEEDS):
        start = start_of(seed)
        print(f"seed {seed}, branched at {start / 60:.0f} bio-h")
        for names, label, colour in ARMS:
            d = next((b for b in (branch(f"{arm}_s{seed}", start) for arm in names) if b is not None), None)
            if d is None or len(d) < 2:
                print(f"  {label}: no data yet")
                continue
            marks = [d.iloc[(d["dh"] - h).abs().argmin()] for h in range(0, int(d["dh"].iloc[-1] + 0.5) + 1, 10)]
            print(f"  {label:20s} " + "  ".join(f"+{r.dh:.0f}h {int(r.ecoli)}/{int(r.myxo)}" for r in marks))
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
    fig.suptitle("Branch test (B99): same starting state, famine lysis 70% vs 20%; grey = target band", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "branch_compare.png"))


if __name__ == "__main__":
    main()
