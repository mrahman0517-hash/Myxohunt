"""
make_figures.py — turn saved runs into the validation figure and a printed summary.

Usage:
    python make_figures.py                         # reads results/*_seed1.npz
    python make_figures.py --ref path/to/authors   # also overlay the authors' own TBRs
"""
import argparse
import glob
import os
import numpy as np

import visualization as viz


def load_results(folder, seed):
    out = {}
    for mode in ("rippling", "swarming"):
        path = os.path.join(folder, f"{mode}_seed{seed}.npz")
        if os.path.exists(path):
            out[mode] = dict(np.load(path, allow_pickle=True))
    return out


def load_reference(folder):
    """tbr.csv files written by the authors' code (last 50 min of their run)."""
    refs = {}
    if folder:
        for mode in ("rippling", "swarming"):
            hits = glob.glob(os.path.join(folder, f"out_{mode}*", "tbr.csv"))
            if hits:
                refs[mode] = np.loadtxt(hits[0], delimiter=",", skiprows=1)[:, 0]
    return refs


def summary(results, refs):
    print(f"{'':10s} {'mean TBR':>9s} {'TBR peaks (min)':>18s} {'top quartile':>13s} "
          f"{'O(5 µm)':>8s} {'O(30 µm)':>9s} {'mean f':>7s}")
    for mode, r in results.items():
        tbr = r["tbr"]
        peaks = ", ".join(f"{x:.1f}" for x in viz.tbr_peaks(tbr))
        o = dict(zip(np.round(r["order_r"], 1), r["order"]))
        f_raw = 2 * r["signal_samples"].mean()            # s is rescaled f/2
        print(f"{mode:10s} {tbr.mean():8.2f}  {peaks:>18s} {r['quartiles'][3]:12.1%} "
              f"{o.get(5.0, np.nan):8.2f} {o.get(30.0, np.nan):9.2f} {f_raw:7.2f}")
        if mode in refs:
            print(f"{'  authors':10s} {refs[mode].mean():8.2f}  "
                  f"{', '.join(f'{x:.1f}' for x in viz.tbr_peaks(refs[mode])):>18s}")
        exp, sim = viz.PAPER_MEAN_TBR[mode]
        print(f"{'  paper':10s} exp {exp:.2f} / sim {sim:.2f}   top quartile exp "
              f"{viz.PAPER_QUARTILES[mode][3]:.1%} / sim ≈{viz.PAPER_SIM_QUARTILES[mode][3]:.0%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--ref", default=None)
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()

    results = load_results(args.results, args.seed)
    refs = load_reference(args.ref)
    summary(results, refs)
    os.makedirs(args.out, exist_ok=True)
    viz.validation_figure(results, refs, os.path.join(args.out, "validation.png"))
    print("saved", os.path.join(args.out, "validation.png"))


if __name__ == "__main__":
    main()
