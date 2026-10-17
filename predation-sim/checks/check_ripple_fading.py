"""
Milestone 5 check: a disc of digested-prey matrix makes Myxo ripple along its axis; as the
matrix fades (B12) the rippling spot shrinks and cells drift back to swarming.

Usage (from predation-sim/):  python checks/check_ripple_fading.py [real_minutes] [seed]
Writes checks/output/ripple_fading.png.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
import numpy as np                                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import myxo_alignment as align                               # noqa: E402
import seeding                                               # noqa: E402
import state                                                 # noqa: E402
from check_live_world import draw_world                     # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import Settings                                # noqa: E402

OUT = os.path.join(HERE, "output")
AXIS = np.radians(30.0)


def build(seed):
    """An 80 µm world, no E. coli: a 25 µm-radius matrix disc (axis 30°) with 300 Myxo on it."""
    s = Settings(box=80.0, seed=seed, start_colonies=0, myxo_groups=0, myxo_singles=0, energy_start=100.0)
    sim = Simulation(s, seed_cells=False)
    f, n = sim.world.fields, sim.world.fields.matrix.shape[0]
    x = (np.arange(n) + 0.5) * f.spacing - 40.0
    disc = (x[:, None] ** 2 + x[None, :] ** 2) <= 25.0 ** 2
    f.matrix[disc] = 1.0
    f.axis_c[disc], f.axis_s[disc] = np.cos(2 * AXIS), np.sin(2 * AXIS)
    r = 22.0 * np.sqrt(sim.world.rng.random(300))
    phi = sim.world.rng.uniform(0, 2 * np.pi, 300)
    starts = 40.0 + np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
    state.append_rows(sim.world.myxo, seeding.make_myxo(sim.world, starts, sim.world.rng.uniform(0, 2 * np.pi, 300)))
    sim.step_grids()                                          # compute the averaged matrix once
    return sim


def rippling_share_and_alignment(world):
    """Share of cells on matrix ground, and how well rippling cells line up with the axis (0–1)."""
    m = world.myxo
    on = align.ripple_mask(world, m.nodes[:, 0])
    axis = np.arctan2(m.nodes[:, 0, 1] - m.nodes[:, -1, 1], m.nodes[:, 0, 0] - m.nodes[:, -1, 0])
    order = np.mean(np.cos(2 * (axis[on] - AXIS))) if on.any() else np.nan
    return on.mean(), order, float(world.fields.matrix_smooth.max())


def main():
    """Run, snapshot five times, and report the rippling share and alignment."""
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    sim, t0 = build(seed), time.time()
    fig, axes = plt.subplots(1, 5, figsize=(25, 5.4), dpi=90)
    for ax, target in zip(axes, np.linspace(0, minutes, 5)):
        if target > sim.world.t:
            sim.run_for(real_minutes=target - sim.world.t)
        share, order, peak = rippling_share_and_alignment(sim.world)
        draw_world(ax, sim.world)
        ax.imshow(sim.world.fields.matrix_smooth.T, origin="lower", extent=[0, 80, 0, 80],
                  cmap="Blues", vmin=0, vmax=1, alpha=0.35)
        ax.set_title(f"{sim.world.bio_t / 60:4.1f} bio h | on matrix {share:.0%} | align {order:.2f} | "
                     f"matrix max {peak:.2f}", fontsize=10, loc="left")
        print(f"bio {sim.world.bio_t / 60:5.1f} h | on matrix {share:.0%} | alignment with axis {order:.2f} | "
              f"matrix max {peak:.2f} | {time.time() - t0:4.0f} s", flush=True)
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "ripple_fading.png"))
    print("saved", os.path.join(OUT, "ripple_fading.png"))


if __name__ == "__main__":
    main()
