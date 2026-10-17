"""
Milestone 6 check: the full live world over time. Do Myxo find prey, feed, multiply and turn the
predator–prey balance (decision-log B58), or starve?

Usage (from predation-sim/):  python checks/check_populations.py [real_minutes] [seed] [name] [setting=value ...]
Writes checks/output/<name>.png (snapshots + population curves) and <name>_stats.csv.
Extra setting=value pairs change settings for variant runs, e.g. nutrient_per_um=6.
Every 30 real minutes the stats so far and a checkpoint (<name>.ckpt) are saved; starting the
same command again after a stop carries on from the checkpoint.
"""
import os
import pickle
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import myxo_modes                                            # noqa: E402
import state                                                 # noqa: E402
import stats                                                 # noqa: E402
from check_live_world import draw_world                     # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import make_settings                           # noqa: E402

OUT = os.path.join(HERE, "output")
SAVE_EVERY = 30.0                                            # real min between checkpoints


def snapshot(world):
    """The world drawn as a small picture (RGB array)."""
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=100)
    draw_world(ax, world)
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return img


def curves(ax, stats, energy_cap):
    """E. coli and Myxo numbers (log scale), Myxo scouts and stringent cells, and mean Myxo
    energy against biological time."""
    t = stats.column("bio_t") / 60.0
    ax.semilogy(t, np.maximum(stats.column("ecoli"), 1), color="#e63ca0", label="E. coli")
    ax.semilogy(t, np.maximum(stats.column("myxo"), 1), color="#1f9d3a", label="Myxo")
    ax.semilogy(t, np.maximum(stats.column("myxo_scouts"), 1), color="#1f9d3a", lw=0.8, ls=":",
                label="Myxo scouting")
    ax.semilogy(t, np.maximum(stats.column("myxo_stringent"), 1), color="#0b4f1c", lw=0.8, ls="-.",
                label="Myxo stringent")
    ax.semilogy(t, np.maximum(stats.column("myxo_at_prey"), 1), color="#d98200", lw=1.0,
                label="Myxo at prey (within 10 µm)")
    ax.semilogy(t, np.maximum(stats.column("myxo_spores"), 1), color="#7b4fa0", lw=1.0, ls="--",
                label="Myxo spores (so far)")
    ax.semilogy(t, np.maximum(stats.column("myxo_lysed"), 1), color="#7b4fa0", lw=0.8, ls=":",
                label="Myxo lysed in famine (so far)")
    ax.set_xlabel("biological time (h)"); ax.set_ylabel("cells"); ax.legend(loc="upper left")
    twin = ax.twinx()
    twin.plot(t, stats.column("myxo_energy"), color="0.5", ls="--")
    twin.set_ylim(0, energy_cap); twin.set_ylabel("mean Myxo store (dashed; 100 = a newborn)")


def parse_overrides(args):
    """Turn 'name=value' arguments into settings changes, each converted to that setting's own type."""
    defaults = make_settings("live")
    out = {}
    for arg in args:
        name, value = arg.split("=", 1)
        kind = type(getattr(defaults, name))
        out[name] = kind(float(value)) if kind in (int, float) else kind(value)
    return out


def status(world, t0):
    """Print one progress line: time, populations, scouts, stringent cells, energy, seconds so far."""
    w, m = world, world.myxo
    n = state.count(m)
    print(f"t {w.t:5.1f} min ({w.bio_t / 60:4.1f} bio h) | E. coli {state.count(w.ecoli):5d} | Myxo {n:4d} "
          f"(scouts {int(m.scout.sum()):3d}, stringent {int(myxo_modes.stringent(w).sum()):3d}, "
          f"at prey {stats.myxo_at_prey(w):3d}, spores {len(w.spores):3d}, lysed {w.myxo_lysed:3d}) | "
          f"energy {np.mean(m.energy) if n else 0:5.1f} | {time.time() - t0:5.0f} s", flush=True)


def save_progress(base, sim, snaps):
    """Write the stats so far and a checkpoint of the whole run, so a run that gets stopped keeps
    its data and can carry on from here."""
    sim.stats.to_csv(base + "_stats.csv")
    with open(base + ".ckpt", "wb") as fh:
        pickle.dump((sim, snaps), fh)


def load_progress(base):
    """The checkpoint of an unfinished earlier run with the same name, or None."""
    if not os.path.exists(base + ".ckpt"):
        return None
    with open(base + ".ckpt", "rb") as fh:
        return pickle.load(fh)


def run_with_saves(sim, snaps, minutes, base, t0):
    """Run to `minutes` real minutes, taking 4 snapshots evenly spread and saving progress every
    SAVE_EVERY real minutes."""
    snap_times = np.linspace(0, minutes, 4)
    half_tick = sim.world.settings.dt / 2
    while True:
        while len(snaps) < len(snap_times) and sim.world.t >= snap_times[len(snaps)] - half_tick:
            snaps.append(snapshot(sim.world))
            status(sim.world, t0)
        if sim.world.t >= minutes - half_tick:
            return
        target = min(sim.world.t + SAVE_EVERY, snap_times[len(snaps)])
        sim.run_for(real_minutes=target - sim.world.t, callback=lambda w: status(w, t0), every_minutes=10.0)
        save_progress(base, sim, snaps)


def main():
    """Run the default live world, then save snapshots and curves. A run stopped part-way carries
    on from its last checkpoint when started again with the same name."""
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    name = sys.argv[3] if len(sys.argv) > 3 else "populations"
    overrides = parse_overrides(sys.argv[4:])
    os.makedirs(OUT, exist_ok=True)
    base = os.path.join(OUT, name)
    resumed = load_progress(base)
    if resumed:
        sim, snaps = resumed
        print(f"carrying on from the checkpoint at {sim.world.t:.1f} real min", flush=True)
    else:
        sim, snaps = Simulation(make_settings("live", seed=seed, **overrides)), []
    run_with_saves(sim, snaps, minutes, base, time.time())
    fig = plt.figure(figsize=(18, 9), dpi=100)
    for k, img in enumerate(snaps):
        ax = fig.add_subplot(2, 4, k + 1); ax.imshow(img); ax.axis("off")
    curves(fig.add_subplot(2, 1, 2), sim.stats, sim.world.settings.energy_cap)
    fig.tight_layout()
    fig.savefig(base + ".png")
    sim.stats.to_csv(base + "_stats.csv")
    if os.path.exists(base + ".ckpt"):
        os.remove(base + ".ckpt")                            # finished: nothing left to carry on from
    print("saved", base + ".png")


if __name__ == "__main__":
    main()
