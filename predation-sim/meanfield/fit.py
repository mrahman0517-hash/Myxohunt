"""
meanfield/fit.py — learn the average-world model's fitted numbers from the full simulation's runs.

For each training run the model is run with that run's settings, and its curves (living E. coli,
Myxo, mean ground nutrient) are compared with the run's own, hour by hour. The
numbers are adjusted until the differences are as small as possible (least squares on log counts).

Usage (from predation-sim/):  python meanfield/fit.py [--holdout name ...]
Writes meanfield/fitted.json and prints how well each run is matched. By default the newest run
(b85_refill6_eff50_s1) is held out, so the model can be tested on a run it never saw.
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as mf                                              # noqa: E402
import runs as mr                                               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FREE = ["c1", "c2", "a", "alpha", "eta", "lam", "chi", "mu"]
BOUNDS = {"c1": (0.5, 30.0), "c2": (2.0, 200.0), "a": (1e-5, 0.2), "alpha": (0.3, 1.3),
          "eta": (0.3, 1.3), "lam": (0.0, 3.0), "chi": (0.05, 1.5), "mu": (0.001, 0.08)}
WEIGHTS = {"E": 1.0, "H": 1.0, "n": 0.5}
SKIP_HOURS = 4.0                       # the first hours hold only a handful of cells


def sim_series(run):
    """The run's curves sampled once per bio-hour (after the first few hours)."""
    d = mr.load(run)
    hours = np.arange(SKIP_HOURS, np.floor(d["h"][-1]) + 1e-9, 1.0)
    pick = np.searchsorted(d["h"], hours).clip(0, len(d["h"]) - 1)
    return hours, {k: d[k][pick] for k in ("E", "H", "n")}


def residuals_for(run, fitted, data):
    """Weighted differences between the model and one run (log counts; ground in units of 0.05)."""
    hours, sim = data
    out = mf.simulate(mf.world_for(run), fitted, hours=hours[-1], step=1.0)
    pick = np.searchsorted(out["h"], hours).clip(0, len(out["h"]) - 1)
    res = []
    for key in ("E", "H"):
        res.append(WEIGHTS[key] * (np.log1p(out[key][pick]) - np.log1p(sim[key])))
    res.append(WEIGHTS["n"] * (out["n"][pick] - sim["n"]) / 0.05)
    return np.concatenate(res)


def fitted_from(vector, base):
    """A Fitted with the free numbers replaced by `vector`."""
    values = base.to_dict()
    values.update(dict(zip(FREE, vector)))
    return mf.Fitted(**values)


def fit(train):
    """Least-squares fit of the free numbers over the training runs."""
    base = mf.Fitted()
    data = {r.name: sim_series(r) for r in train}
    x0 = np.array([getattr(base, k) for k in FREE])
    lo = np.array([BOUNDS[k][0] for k in FREE])
    hi = np.array([BOUNDS[k][1] for k in FREE])

    def all_residuals(x):
        f = fitted_from(x, base)
        return np.concatenate([residuals_for(r, f, data[r.name]) for r in train])

    result = least_squares(all_residuals, np.clip(x0, lo, hi), bounds=(lo, hi), x_scale="jac",
                           diff_step=1e-3, max_nfev=400, verbose=0)
    return fitted_from(result.x, base), result


def report(runs_, fitted, tag):
    """Print, per run, the typical factor by which the model is off for each curve."""
    for r in runs_:
        hours, sim = sim_series(r)
        out = mf.simulate(mf.world_for(r), fitted, hours=hours[-1], step=1.0)
        pick = np.searchsorted(out["h"], hours).clip(0, len(out["h"]) - 1)
        parts = []
        for key in ("E", "H"):
            rms = np.sqrt(np.mean((np.log1p(out[key][pick]) - np.log1p(sim[key])) ** 2))
            parts.append(f"{key} ×{np.exp(rms):.2f}")
        nerr = np.sqrt(np.mean((out["n"][pick] - sim["n"]) ** 2))
        print(f"  {tag:5s} {r.label:28s} " + "  ".join(parts) + f"  ground ±{nerr:.3f}")


def main():
    """Fit on all runs but the held-out ones, report the match, save the numbers."""
    args = sys.argv[1:]
    holdout = args[args.index("--holdout") + 1:] if "--holdout" in args else ["b85_refill6_eff50_s1"]
    runs_ = [r for r in mr.available() if r.fit]
    train = [r for r in runs_ if r.name not in holdout]
    test = [r for r in runs_ if r.name in holdout]
    fitted, result = fit(train)
    print(f"fitted on {len(train)} runs (cost {result.cost:.1f}, {result.nfev} model batches):")
    for k in FREE:
        print(f"  {k:6s} {getattr(fitted, k):.4g}")
    print("typical mismatch (×1.00 = perfect):")
    report(train, fitted, "fit")
    report(test, fitted, "test")
    with open(os.path.join(HERE, "fitted.json"), "w", encoding="utf8") as fh:
        json.dump(dict(fitted=fitted.to_dict(), trained_on=[r.name for r in train],
                       held_out=[r.name for r in test]), fh, indent=2)
    print("saved meanfield/fitted.json")


if __name__ == "__main__":
    main()
