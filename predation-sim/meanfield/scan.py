"""
meanfield/scan.py — try many combinations of the flexible settings in the average-world model and
mark the ones that keep E. coli and Myxo inside a target range after the first wave.

Flexible settings scanned (all tuned or assumed, or measured only as a range):
  refill   how fast bare ground refills (multiplies nutrient_regrow_rate; tuned)
  rich     how rich the ground can be (multiplies richness_min and richness_max; assumed)
  eff      Myxo's share of eaten food kept (efficiency; measured range 5–60%)
  wake     food under a dormant E. coli that ends its dormancy (dormant_threshold; assumed)
Everything measured or from the paper stays as it is (starvation death 0.69/day, persisters 5%).

For each combination the model runs 300 bio-h. Reported, from 60 bio-h on: the lowest, mean and
highest numbers of E. coli and Myxo, and whether they still swing at the end (sustained cycles)
or have settled. A combination is "in range" when, from 60 bio-h on, E. coli stay within
prey_range and Myxo within myxo_range.

Usage (from predation-sim/):  python meanfield/scan.py [prey_lo prey_hi myxo_lo myxo_hi] [--search k]
--search k multiplies the fitted kill scale a by k: hunters k times better at finding and killing
prey than in today's sim (not a setting of the sim; a question for it). Writes
checks/output/meanfield_scan[_search_k].png and .csv; prints the best combinations.
"""
import csv
import itertools
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                 # noqa: E402
import numpy as np                                              # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as mf                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "checks", "output")
REFILLS = np.round(np.geomspace(1 / 40, 2.0, 22), 4)
RICHES = (0.7, 1.0)
EFFS = (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
WAKES = (0.01, 0.03, 0.1, 0.3)
PLOT_RICH = 1.0
HOURS, SETTLE = 300.0, 60.0


def load_fitted():
    """The fitted numbers from fit.py."""
    with open(os.path.join(HERE, "fitted.json"), encoding="utf8") as fh:
        return mf.Fitted(**json.load(fh)["fitted"])


def summarise(out):
    """Lowest, mean and highest E. coli and Myxo from SETTLE on, and the size of the last swings
    (the spread over the last 60 bio-h as a share of the mean: near 0 = settled)."""
    after = out["h"] >= SETTLE
    last = out["h"] >= HOURS - 60
    row = {}
    for key in ("E", "H"):
        x = out[key][after]
        row[key + "_min"], row[key + "_mean"], row[key + "_max"] = x.min(), x.mean(), x.max()
        tail = out[key][last]
        row[key + "_swing"] = (tail.max() - tail.min()) / max(tail.mean(), 1e-9)
    return row


def scan(fitted, prey_range, myxo_range):
    """Run every combination; return a list of result rows."""
    rows = []
    for refill, rich, eff, wake in itertools.product(REFILLS, RICHES, EFFS, WAKES):
        w = mf.World(regrow=mf.REGROW_REF * refill, rich=0.65 * rich, efficiency=eff, wake_level=wake)
        out = mf.simulate(w, fitted, hours=HOURS, step=0.5)
        row = dict(refill=refill, rich=rich, eff=eff, wake=wake, ok=out["ok"])
        row.update(summarise(out))
        row["in_range"] = bool(out["ok"] and prey_range[0] <= row["E_min"] and row["E_max"] <= prey_range[1]
                               and myxo_range[0] <= row["H_min"] and row["H_max"] <= myxo_range[1])
        rows.append(row)
    return rows


def save_csv(rows, path):
    """All result rows as a CSV file."""
    with open(path, "w", newline="", encoding="utf8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def draw(rows, prey_range, myxo_range, path):
    """For each wake level (ground ×PLOT_RICH): mean E. coli and mean Myxo (from 60 bio-h on) over
    refill × efficiency, with the in-range combinations outlined."""
    fig, axes = plt.subplots(2, len(WAKES), figsize=(4.2 * len(WAKES), 7.5), dpi=100, squeeze=False)
    for col, wake in enumerate(WAKES):
        sub = [r for r in rows if r["rich"] == PLOT_RICH and r["wake"] == wake]
        for row_i, (key, label, rng) in enumerate((("E_mean", "mean E. coli", prey_range),
                                                    ("H_mean", "mean Myxo", myxo_range))):
            grid = np.array([[next(r[key] for r in sub if r["refill"] == f and r["eff"] == e) for f in REFILLS]
                             for e in EFFS])
            ok = np.array([[next(r["in_range"] for r in sub if r["refill"] == f and r["eff"] == e)
                            for f in REFILLS] for e in EFFS])
            ax = axes[row_i, col]
            im = ax.pcolormesh(np.arange(len(REFILLS) + 1), np.arange(len(EFFS) + 1),
                               np.log10(np.maximum(grid, 1)), cmap="Blues", vmin=0, vmax=3.5)
            ys, xs = np.nonzero(ok)
            ax.scatter(xs + 0.5, ys + 0.5, marker="s", s=30, facecolors="none", edgecolors="#eb6834", lw=1.4)
            ax.set_xticks(np.arange(0, len(REFILLS), 4) + 0.5)
            ax.set_xticklabels([f"{f:.2g}" for f in REFILLS[::4]], fontsize=8)
            ax.set_yticks(np.arange(len(EFFS)) + 0.5)
            ax.set_yticklabels([f"{e:.0%}" for e in EFFS], fontsize=8)
            ax.set_title(f"{label}, wake level {wake}", loc="left", fontsize=10)
            if col == 0:
                ax.set_ylabel("efficiency")
            if row_i == 1:
                ax.set_xlabel("refill speed (× today's)")
        fig.colorbar(im, ax=axes[:, col], shrink=0.6, label="log10 cells")
    fig.suptitle(f"Average-world model, ground ×{PLOT_RICH}, from 60 bio-h on (orange squares: E. coli within "
                 f"{prey_range}, Myxo within {myxo_range})", fontsize=11)
    fig.savefig(path)


def main():
    """Scan, save the table and picture, and print the best in-range combinations."""
    argv = sys.argv[1:]
    search = 1.0
    if "--search" in argv:
        k = argv.index("--search")
        search = float(argv[k + 1])
        argv = argv[:k] + argv[k + 2:]
    args = [float(a) for a in argv[:4]]
    prey_range = tuple(args[:2]) if len(args) >= 2 else (100.0, 600.0)
    myxo_range = tuple(args[2:4]) if len(args) >= 4 else (30.0, 250.0)
    fitted = load_fitted()
    fitted.a *= search
    tag = "" if search == 1.0 else f"_search_{search:g}"
    rows = scan(fitted, prey_range, myxo_range)
    save_csv(rows, os.path.join(OUT, f"meanfield_scan{tag}.csv"))
    draw(rows, prey_range, myxo_range, os.path.join(OUT, f"meanfield_scan{tag}.png"))
    good = sorted((r for r in rows if r["in_range"]), key=lambda r: -r["H_swing"] - r["E_swing"])
    print(f"{len(good)} of {len(rows)} combinations in range (E. coli {prey_range}, Myxo {myxo_range}):")
    for r in good[:15]:
        print(f"  refill ×{r['refill']:<7.4g} ground ×{r['rich']:<4} eff {r['eff']:.0%} wake {r['wake']:<5}:  E. coli "
              f"{r['E_min']:.0f}–{r['E_max']:.0f} (mean {r['E_mean']:.0f}), Myxo {r['H_min']:.0f}–{r['H_max']:.0f} "
              f"(mean {r['H_mean']:.0f}); still swinging: E ±{r['E_swing'] / 2:.0%}, H ±{r['H_swing'] / 2:.0%}")


if __name__ == "__main__":
    main()
