"""
Do Myxo stay with the pack at a colony, or leave along slime highways? The same grown colony
and Myxo drops as check_penetration.py, run under rule variants that might hold cells at the
prey. Reports kills, Myxo near the colony at the end, and rippling cells.

Usage (from predation-sim/):  python checks/check_staying.py [grow_real_min] [attack_real_min]
Writes checks/output/staying_test.png.
"""
import copy
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
import state                                                 # noqa: E402
from check_live_world import draw_world                     # noqa: E402
from check_penetration import attack, grown_colony          # noqa: E402
from check_predation import colony_centre_and_radius        # noqa: E402

OUT = os.path.join(HERE, "output")
VARIANTS = {                                                 # name → setting changes (B77)
    "now (B76)": {},
    "smell 5x stronger": {"chemo_strength": 10.0},
    "ripple threshold halved": {"matrix_ripple_threshold": 0.15},
    "trails fade in 1 bio-h": {"eps_fade_time": 60.0},
    "smell 5x + threshold halved": {"chemo_strength": 10.0, "matrix_ripple_threshold": 0.15},
}


def near_colony(world, centre, radius, margin=10.0):
    """Myxo whose centre is inside the colony's starting outline or within `margin` µm of it."""
    c = np.mod(world.myxo.nodes.mean(axis=1), world.settings.box) - centre
    c -= world.settings.box * np.round(c / world.settings.box)
    return int((np.linalg.norm(c, axis=1) < radius + margin).sum())


def main():
    """Grow once, then run every variant from an identical copy of the world."""
    grow = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
    t0 = time.time()
    base = grown_colony(grow)
    centre, radius = colony_centre_and_radius(base.world)
    print(f"colony grown: {state.count(base.world.ecoli)} E. coli, radius {radius:.0f} µm, "
          f"{state.count(base.world.myxo)} Myxo at its edge | {time.time() - t0:.0f} s", flush=True)
    fig, axes = plt.subplots(1, len(VARIANTS), figsize=(5.2 * len(VARIANTS), 5.8), dpi=90)
    for ax, (name, changes) in zip(axes, VARIANTS.items()):
        sim = copy.deepcopy(base)
        kills, killing = attack(sim, minutes, changes)
        near = near_colony(sim.world, centre, radius)
        total = state.count(sim.world.myxo)
        rippling = int(align.ripple_mask(sim.world, sim.world.myxo.nodes[:, 0]).sum())
        print(f"{name:30s} | kills {kills:4d} | killing at a time {killing:4.1f} | "
              f"with the pack {near:3d} of {total} ({near / total:4.0%}) | rippling {rippling:3d} | "
              f"E. coli left {state.count(sim.world.ecoli)} | {time.time() - t0:.0f} s", flush=True)
        draw_world(ax, sim.world)
        ax.set_xlabel(f"{name}\nkills {kills} | with the pack {near / total:.0%} | rippling {rippling}",
                      fontsize=10)
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "staying_test.png")
    fig.savefig(path)
    print("saved", path)


if __name__ == "__main__":
    main()
