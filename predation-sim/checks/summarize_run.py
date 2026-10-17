"""
Summarise one or more population runs from their stats files: a row every few bio-hours, then
each run's highs and lows.

Usage (from predation-sim/):  python checks/summarize_run.py name [name ...] [--every hours]
Reads checks/output/<name>_stats.csv (written by check_populations.py).
"""
import os
import sys

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def load(name):
    """The stats of run `name` as a dict of columns."""
    path = os.path.join(OUT, name + "_stats.csv")
    data = np.genfromtxt(path, delimiter=",", names=True)
    return {k: data[k] for k in data.dtype.names}


def rows(s, every):
    """One line of the main numbers every `every` bio-hours."""
    h = s["bio_t"] / 60.0
    print(f"{'bio h':>6} {'E.coli':>6} {'Myxo':>5} {'string':>6} {'scout':>5} {'@prey':>5} {'rippl':>5} "
          f"{'store':>5} {'lysed':>5} {'spores':>6} {'food':>7} {'scraps':>7}")
    for target in np.arange(0, h.max() + 1e-9, every):
        i = int(np.argmin(np.abs(h - target)))
        n = max(s["myxo"][i], 1)
        print(f"{h[i]:6.1f} {s['ecoli'][i]:6.0f} {s['myxo'][i]:5.0f} {100 * s['myxo_stringent'][i] / n:5.0f}% "
              f"{s['myxo_scouts'][i]:5.0f} {s['myxo_at_prey'][i]:5.0f} {s['myxo_rippling'][i]:5.0f} "
              f"{s['myxo_energy'][i]:5.0f} {s['myxo_lysed'][i]:5.0f} {s['myxo_spores'][i]:6.0f} "
              f"{s['food'][i]:7.0f} {s['scraps'][i]:7.0f}")


def extremes(s):
    """Highest prey and Myxo numbers and when they happened."""
    h = s["bio_t"] / 60.0
    for col in ("ecoli", "myxo"):
        i = int(np.argmax(s[col]))
        print(f"  highest {col}: {s[col][i]:.0f} at {h[i]:.1f} bio-h")


def main():
    """Print the summary of every run named on the command line."""
    args = sys.argv[1:]
    every = 4.0
    if "--every" in args:
        k = args.index("--every")
        every = float(args[k + 1])
        args = args[:k] + args[k + 2:]
    for name in args:
        print(f"== {name}")
        s = load(name)
        rows(s, every)
        extremes(s)


if __name__ == "__main__":
    main()
