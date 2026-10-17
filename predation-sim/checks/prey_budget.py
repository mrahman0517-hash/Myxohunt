"""
Where do the prey go? For each window of a population run: E. coli births, kills by Myxo,
starvation deaths and the net change, all per bio-hour.

How it's worked out from the stats file:
- Every bursting E. coli (killed, or starved and burst) leaves 1 unit of matrix (`matrix_per_ghost`),
  which fades with a 12 bio-h half-life, so bursts per bio-h = dM/dt + fade rate × M.
- A starved cell bursts 2 bio-h after it dies (`starved_lysis_delay`), so the dead-but-intact cells
  are the last 2 bio-h of starvation deaths: starvation deaths per bio-h ≈ dead intact / 2.
- Kills = bursts − starved bursts. Births = net change + kills + starvation deaths.

Usage (from predation-sim/):  python checks/prey_budget.py name [name ...] [--every hours]
Reads checks/output/<name>_stats.csv (written by check_populations.py).
"""
import os
import sys

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
MATRIX_FADE = np.log(2) / 12.0      # per bio-h (matrix_half_life 720 bio-min)
LYSIS_DELAY = 2.0                   # bio-h from starvation death to burst (starved_lysis_delay)


def load(name):
    """The stats of run `name` as a dict of columns, with bio-hours added as 'h'."""
    data = np.genfromtxt(os.path.join(OUT, name + "_stats.csv"), delimiter=",", names=True)
    out = {k: data[k] for k in data.dtype.names}
    out["h"] = data["bio_t"] / 60.0
    return out


def window(s, t0, t1):
    """Births, kills, starvation deaths and net change per bio-h between t0 and t1, plus the mean
    numbers of E. coli and Myxo and the dormant share."""
    i, j = np.searchsorted(s["h"], t0), np.searchsorted(s["h"], t1) - 1
    k = slice(i, j + 1)
    dt = s["h"][j] - s["h"][i]
    bursts = (s["matrix"][j] - s["matrix"][i]) / dt + MATRIX_FADE * s["matrix"][k].mean()
    starved = s["ecoli_dead_intact"][k].mean() / LYSIS_DELAY
    kills = bursts - starved
    net = (s["ecoli"][j] - s["ecoli"][i]) / dt
    return dict(E=s["ecoli"][k].mean(), dormant=s["ecoli_dormant"][k].sum() / max(s["ecoli"][k].sum(), 1),
                births=net + kills + starved, kills=kills, starved=starved, net=net, H=s["myxo"][k].mean())


def table(s, every):
    """One line per window of `every` bio-hours."""
    print(" window      E.coli  dorm%   births   kills  starved     net   Myxo")
    for t0 in np.arange(0, s["h"].max() - every + 1e-9, every):
        r = window(s, t0, t0 + every)
        print(f" {t0:5.0f}-{t0 + every:<5.0f} {r['E']:6.0f}  {r['dormant']:5.0%} {r['births']:8.1f} {r['kills']:7.1f}"
              f" {r['starved']:8.1f} {r['net']:7.1f} {r['H']:6.0f}")


def main():
    """Print the budget of every run named on the command line."""
    args = sys.argv[1:]
    every = 10.0
    if "--every" in args:
        k = args.index("--every")
        every = float(args[k + 1])
        args = args[:k] + args[k + 2:]
    for name in args:
        print(f"== {name} (per bio-h)")
        table(load(name), every)


if __name__ == "__main__":
    main()
