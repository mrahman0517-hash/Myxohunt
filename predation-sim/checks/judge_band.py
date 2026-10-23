"""
Judge population runs against the band the user asked for (review of 23 Oct 2026, B97), seed by
seed, and say whether the setting passes: at least 3 of 4 seeds (75%) must pass.

A seed passes over WINDOW (150–300 bio-h) if
  - its means are 700–1,000 E. coli and 100–220 Myxo;
  - at least 80% of hourly samples lie within 500–1,300 E. coli and 75–300 Myxo;
  - it never drops below 210 E. coli or 45 Myxo;
  - neither population drifts by more than 20% of its mean per 100 bio-h (straight-line fit).
The "look" numbers (rippling, killing, starving, scouts) are reported, not judged (the user's
choice D6). A run still going is judged on what it has so far, with a warning; after 100 bio-h a
seed is flagged "can't pass" if it fell below 45 Myxo or rose above 2,000 E. coli.

Usage (from predation-sim/):  python checks/judge_band.py name1 name2 ...   (checks/output/<name>_stats.csv)
"""
import math
import os
import sys

import numpy as np
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
WINDOW = (150.0, 300.0)
MEAN_E, MEAN_H = (700, 1000), (100, 220)
WIDE_E, WIDE_H, WIDE_SHARE = (500, 1300), (75, 300), 0.8
MIN_E, MIN_H = 210, 45
MAX_DRIFT = 0.20                                  # of the mean, per 100 bio-h
NEED_SHARE = 0.75                                 # 3 of 4 seeds


def hourly(path):
    """A run's stats, one row per bio-hour."""
    d = pd.read_csv(path)
    d["bio_h"] = d["bio_t"] / 60.0
    return d.groupby(d["bio_h"].round()).last()


def drift(h, y):
    """Straight-line change per 100 bio-h, as a share of the mean."""
    if len(h) < 3 or y.mean() == 0:
        return float("nan")
    return float(np.polyfit(h, y, 1)[0] * 100.0 / y.mean())


def inside(y, band):
    """Share of samples within the band."""
    return float(((y >= band[0]) & (y <= band[1])).mean())


def budget(d, lo, hi):
    """Events per bio-hour between lo and hi bio-h, from the direct counters (B97)."""
    part = d[(d.index >= lo) & (d.index <= hi)]
    if "ecoli_killed" not in d:
        return {}
    part = part.dropna(subset=["ecoli_killed"])           # rows from before the counters existed (resumed runs)
    if len(part) < 2:
        return {}
    span = part.index[-1] - part.index[0]
    rate = lambda col: (part[col].iloc[-1] - part[col].iloc[0]) / span
    return {"E births/h": rate("ecoli_divisions") + rate("ecoli_founders"), "E kills/h": rate("ecoli_killed"),
            "E starved/h": rate("ecoli_starved"), "E wakes/h": rate("ecoli_wakes"),
            "H births/h": rate("myxo_divisions"), "H starved dead/h": rate("myxo_starved_dead"),
            "famine lysed/h": rate("famine_lysed"), "spores/h": rate("famine_spores"),
            "persister share": float((part["ecoli_persisters"] / part["ecoli"].clip(lower=1)).iloc[-1])}


def judge(name):
    """The verdict for one seed, with the numbers behind it."""
    d = hourly(os.path.join(OUT, name + "_stats.csv"))
    last = float(d.index[-1])
    w = d[(d.index >= WINDOW[0]) & (d.index <= WINDOW[1])]
    late = d[d.index >= 100]
    cant = bool(len(late) and (late["myxo"].min() < MIN_H or late["ecoli"].max() > 2000))
    r = dict(name=name, last_bio_h=last, complete=last >= WINDOW[1] - 0.5, cant_pass=cant)
    if len(w) < 3:
        r["passes"] = False
        return r
    E, H = w["ecoli"].astype(float), w["myxo"].astype(float)
    r.update(mean_E=E.mean(), mean_H=H.mean(), wide_E=inside(E, WIDE_E), wide_H=inside(H, WIDE_H),
             min_E=E.min(), min_H=H.min(), drift_E=drift(w.index, E), drift_H=drift(w.index, H))
    r["checks"] = {
        "mean E": MEAN_E[0] <= r["mean_E"] <= MEAN_E[1], "mean H": MEAN_H[0] <= r["mean_H"] <= MEAN_H[1],
        "80% in wide band": r["wide_E"] >= WIDE_SHARE and r["wide_H"] >= WIDE_SHARE,
        "minima": r["min_E"] >= MIN_E and r["min_H"] >= MIN_H,
        "drift": abs(r["drift_E"]) <= MAX_DRIFT and abs(r["drift_H"]) <= MAX_DRIFT}
    r["passes"] = all(r["checks"].values())
    n = w["myxo"].clip(lower=1)
    r["look"] = {"rippling (mean cells)": w["myxo_rippling"].mean(), "killing (% of Myxo)": 100 * (w["myxo_paused"] / n).mean(),
                 "starving (% of Myxo)": 100 * (w["myxo_stringent"] / n).mean(), "scouts (% of Myxo)": 100 * (w["myxo_scouts"] / n).mean()}
    r["budget"] = budget(d, *WINDOW)
    return r


def show(r):
    """Print one seed's verdict."""
    head = f"{r['name']}: {'PASS' if r['passes'] else 'fail'} (data to {r['last_bio_h']:.0f} bio-h"
    head += ")" if r["complete"] else ", still running: judged on what there is so far)"
    print(head + ("  [can't pass: below 45 Myxo or above 2,000 E. coli after 100 h]" if r["cant_pass"] else ""))
    if "checks" not in r:
        return
    print(f"  E. coli mean {r['mean_E']:.0f}, min {r['min_E']:.0f}, {100 * r['wide_E']:.0f}% in 500-1,300, drift {100 * r['drift_E']:+.0f}%/100 h")
    print(f"  Myxo    mean {r['mean_H']:.0f}, min {r['min_H']:.0f}, {100 * r['wide_H']:.0f}% in 75-300, drift {100 * r['drift_H']:+.0f}%/100 h")
    print("  checks: " + ", ".join(f"{k} {'ok' if v else 'NO'}" for k, v in r["checks"].items()))
    print("  look: " + ", ".join(f"{k} {v:.1f}" for k, v in r["look"].items()))
    if r["budget"]:
        print("  per bio-h: " + ", ".join(f"{k} {v:.2f}" for k, v in r["budget"].items()))


def main():
    """Judge every named run, then the setting as a whole."""
    results = [judge(name) for name in sys.argv[1:]]
    for r in results:
        show(r)
    passed, need = sum(r["passes"] for r in results), math.ceil(NEED_SHARE * len(results))
    print(f"\n{passed} of {len(results)} seeds pass; the setting {'PASSES' if passed >= need else 'does not pass'} "
          f"(needs {need} of {len(results)}){'' if all(r['complete'] for r in results) else ' (not all runs complete)'}")


if __name__ == "__main__":
    main()
