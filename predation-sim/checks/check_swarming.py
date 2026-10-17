"""
Milestone 3 check: does the new engine still swarm like the validated paper reproduction?

Runs predation-sim at the reproduction's swarming quick-test settings (370 Myxo, 65 µm box, no
E. coli, slime that never fades, no pull toward prey) and compares time between reversals,
frustration quartiles and alignment with paper-reproduction/results (ours and the authors').

Usage (from predation-sim/):  python checks/check_swarming.py [real_minutes] [seed]
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                     # noqa: E402
import numpy as np                                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import seeding                                                      # noqa: E402
from engine import Simulation                                       # noqa: E402
from settings import Settings                                       # noqa: E402

REPRO = os.path.join(HERE, "..", "..", "paper-reproduction")
sys.path.insert(1, REPRO)
import functions as measure                                         # noqa: E402  (validated measurement helpers)
OUT = os.path.join(HERE, "output")


def build(seed):
    """The reproduction's swarming quick test, expressed in predation-sim settings."""
    s = Settings(box=65.0, seed=seed, start_colonies=0, myxo_groups=0, myxo_singles=0,
                 eps_fade_time=float("inf"), chemo_strength=0.0, speedup=1.0)
    sim = Simulation(s, seed_cells=False)
    seeding.uniform_myxo(sim.world, 370)
    return sim


def run(sim, minutes, record_last=50.0):
    """Run and record reversals, signals and snapshots over the last `record_last` minutes."""
    w, s = sim.world, sim.world.settings
    last = np.full(370, np.nan)
    rec = dict(tbr=[], rev_cell=[], rev_signal=[], samples=[], snaps=[])
    start_rec, t0 = minutes - record_last, time.time()
    for i in range(int(round(minutes / s.dt))):
        sim.step()
        idx = np.nonzero(sim.flipped)[0]
        if w.t >= start_rec:
            ok = ~np.isnan(last[idx])
            rec["tbr"].extend((w.t - last[idx][ok]).tolist())
            rec["rev_cell"].extend(idx.tolist())
            rec["rev_signal"].extend(w.myxo.signal[idx].tolist())
            if i % 7 == 0:
                rec["samples"].append(w.myxo.signal.astype(np.float32).copy())
            if i % 1000 == 0:
                rec["snaps"].append(w.myxo.nodes.copy())
        last[idx] = w.t
        if (i + 1) % 2000 == 0:
            print(f"t = {w.t:6.1f} min | {time.time() - t0:5.0f} s", flush=True)
    rec["snaps"].append(w.myxo.nodes.copy())
    return rec


def summarise(rec, box=65.0):
    """Mean TBR, top-quartile share and alignment curve, measured as in the reproduction."""
    edges = np.arange(1.25, box / 2, 2.5)
    orders = [measure.nematic_order(*reversed(measure.cell_axis_and_centre(n, box)), box, edges)
              for n in rec["snaps"]]
    q = measure.quartile_fractions(np.array(rec["samples"]), rec["rev_cell"], rec["rev_signal"])
    return dict(tbr=np.array(rec["tbr"]), quartiles=q, order=np.nanmean(orders, axis=0),
                order_r=0.5 * (edges[1:] + edges[:-1]),
                frust=2 * np.array(rec["samples"]).ravel())


def compare(new):
    """Print and plot the new engine against the reproduction and the authors' code."""
    old = np.load(os.path.join(REPRO, "results", "swarming_seed1.npz"))
    auth = np.load(os.path.join(REPRO, "results", "authors", "swarming_seed1.npz"))
    for name, r in (("predation-sim", new), ("reproduction", old), ("authors' code", auth)):
        f = new["frust"] if r is new else 2 * r["signal_samples"].ravel()
        print(f"{name:14s} TBR mean {r['tbr'].mean():.2f} min (n {r['tbr'].size}) | top quartile "
              f"{r['quartiles'][3]:.1%} | order 2.5/10/20 µm {r['order'][0]:.2f}/{r['order'][3]:.2f}/"
              f"{r['order'][7]:.2f} | frustration median {np.median(f):.3f}")
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), dpi=110)
    bins = np.arange(0, 15.34, 1 / 3)
    ax[0].hist(new["tbr"], bins, density=True, color="#eb6834", alpha=0.8, label="predation-sim")
    ax[0].hist(old["tbr"], bins, density=True, histtype="step", color="k", lw=1.5, label="reproduction")
    ax[0].hist(auth["tbr"], bins, density=True, histtype="step", color="0.5", lw=1.5, ls="--", label="authors' code")
    ax[0].set_xlabel("time between reversals (min)"); ax[0].legend(frameon=False)
    for r, label, style in ((new, "predation-sim", "-"), (old, "reproduction", "--"), (auth, "authors' code", ":")):
        ax[1].plot(r["order_r"], r["order"], style, label=label)
    ax[1].set_xlabel("distance (µm)"); ax[1].set_ylabel("nematic order"); ax[1].legend(frameon=False)
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "swarming_vs_reproduction.png"))


def main():
    """Run the check and report."""
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    sim = build(seed)
    new = summarise(run(sim, minutes))
    if minutes >= 100:
        compare(new)
        print("saved", os.path.join(OUT, "swarming_vs_reproduction.png"))
    else:
        print(f"short run: TBR mean {new['tbr'].mean() if new['tbr'].size else float('nan'):.2f} min")


if __name__ == "__main__":
    main()
