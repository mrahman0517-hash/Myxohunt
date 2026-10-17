"""
meanfield/hunting.py — how good are the hunters at finding and killing prey in a run? Reads each
run's kills per 2 bio-h window and divides by what the average-world model expects from the prey,
the hunters and the ground at that time:

    search = kills / (E^alpha × H^eta × (n/rich)^lam)        (alpha, eta, lam from fitted.json)

so the result is the model's kill scale `a` for that run. Runs are compared with the first one
named (e.g. today's settings), as a ratio: 4 would mean hunters four times better at finding prey.

Usage (from predation-sim/):  python meanfield/hunting.py base_run other_run ... [--from 10] [--rich 0.65]
Reads checks/output/<run>_stats.csv.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "checks", "output")
STEP = 2.0
MATRIX_FADE = np.log(2) / 12.0        # per bio-h: prey remains fade with a 12 bio-h half-life


def load(name):
    """The run's statistics as a dict of arrays (hours added as 'h')."""
    d = np.genfromtxt(os.path.join(OUT, name + "_stats.csv"), delimiter=",", names=True)
    out = {k: d[k] for k in d.dtype.names}
    out["h"] = d["bio_t"] / 60.0
    return out


def windows(d, start):
    """Kills, E. coli, Myxo and ground per STEP-hour window from `start` on."""
    rows = []
    for t0 in np.arange(start, d["h"].max() - STEP + 1e-9, STEP):
        i, j = np.searchsorted(d["h"], t0), np.searchsorted(d["h"], t0 + STEP) - 1
        k = slice(i, j + 1)
        dt = d["h"][j] - d["h"][i]
        kills = (d["matrix"][j] - d["matrix"][i]) / dt + MATRIX_FADE * d["matrix"][k].mean()
        rows.append(dict(t=t0, K=kills, E=d["ecoli"][k].mean(), H=d["myxo"][k].mean(), n=d["nutrients"][k].mean()))
    return rows


def search_scale(rows, f, rich):
    """The model's kill scale `a` in each window (only windows with prey, hunters and kills)."""
    out = []
    for r in rows:
        if r["K"] > 0.5 and r["E"] > 10 and r["H"] > 10 and r["n"] > 0:
            out.append(r["K"] / (r["E"] ** f["alpha"] * r["H"] ** f["eta"] * (r["n"] / rich) ** f["lam"]))
    return np.array(out)


def main():
    """Print each run's search scale, its ratio to the first run, and its totals."""
    args = sys.argv[1:]
    start, rich = 10.0, 0.65
    if "--from" in args:
        k = args.index("--from")
        start = float(args[k + 1])
        args = args[:k] + args[k + 2:]
    if "--rich" in args:
        k = args.index("--rich")
        rich = float(args[k + 1])
        args = args[:k] + args[k + 2:]
    with open(os.path.join(HERE, "fitted.json"), encoding="utf8") as fh:
        f = json.load(fh)["fitted"]
    base = None
    print(f"search scale from {start:g} bio-h on (median over {STEP:g} bio-h windows; ratio to {args[0]}):")
    for name in args:
        d = load(name)
        scale = search_scale(windows(d, start), f, rich)
        med = np.median(scale) if len(scale) else float("nan")
        base = med if base is None else base
        kills = sum(r["K"] * STEP for r in windows(d, 0.0))
        print(f"  {name:22s} a = {med:.3g}  (×{med / base:.2f}; windows {len(scale)})  | by {d['h'][-1]:.0f} bio-h: "
              f"kills ≈ {kills:.0f}, E. coli {d['ecoli'][-1]:.0f}, Myxo {d['myxo'][-1]:.0f}, "
              f"at prey {d['myxo_at_prey'][-1]:.0f}")


if __name__ == "__main__":
    main()
