"""
Do Myxo get inside a prey colony? One grown colony, four drops of Myxo at its edge, and the same
attack run under several rule variants (B76). Reports kills, cells killing at a time, and how
many Myxo end up deep inside the colony, and saves one picture per variant.

Usage (from predation-sim/):  python checks/check_penetration.py [grow_real_min] [attack_real_min]
Writes checks/output/penetration_test.png.
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
import fields_update                                         # noqa: E402
import myxo_alignment as align                               # noqa: E402
import state                                                 # noqa: E402
from check_live_world import draw_world                     # noqa: E402
from check_predation import add_attackers, colony_centre_and_radius   # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import make_settings                           # noqa: E402

OUT = os.path.join(HERE, "output")
VARIANTS = {                                                 # name → setting changes
    "before (B75 rules)": {"prey_contact_signal": 0.15, "myxo_crawl_over_prey": False,
                           "ripple_live_prey_weight": 0.0},
    "reversals off + crawl over prey": {"ripple_live_prey_weight": 0.0},
    "+ rippling on living prey (B76)": {},
}


def grown_colony(grow_minutes):
    """One colony grown alone for grow_minutes, with Myxo drops added at its edge."""
    s = make_settings("live", seed=1, start_colonies=1, myxo_groups=0, myxo_singles=0,
                      ecoli_seed_interval=0.0)
    sim = Simulation(s)
    sim.run_for(real_minutes=grow_minutes)
    add_attackers(sim.world)
    return sim


def deep_inside(world, centre, radius):
    """Myxo whose centre lies within the inner 60% of the colony's starting radius."""
    c = np.mod(world.myxo.nodes.mean(axis=1), world.settings.box) - centre
    c -= world.settings.box * np.round(c / world.settings.box)
    return int((np.linalg.norm(c, axis=1) < 0.6 * radius).sum())


def attack(sim, minutes, changes):
    """Run the attack with the given setting changes; count kills and cells killing per tick."""
    for name, value in changes.items():
        setattr(sim.world.settings, name, value)
    fields_update.refresh_sensed_maps(sim.world)
    kills, paused = 0, []
    for _ in range(int(round(minutes / sim.world.settings.dt))):
        sim.step()
        kills += len(sim.kills[1]) if sim.kills is not None else 0
        paused.append(int((sim.world.myxo.pause_left > 0).sum()))
    return kills, float(np.mean(paused))


def main():
    """Grow once, then run every variant from an identical copy of the world."""
    grow = float(sys.argv[1]) if len(sys.argv) > 1 else 40.0
    minutes = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
    t0 = time.time()
    base = grown_colony(grow)
    centre, radius = colony_centre_and_radius(base.world)
    print(f"colony grown: {state.count(base.world.ecoli)} E. coli, radius {radius:.0f} µm, "
          f"{state.count(base.world.myxo)} Myxo at its edge | {time.time() - t0:.0f} s", flush=True)
    fig, axes = plt.subplots(1, len(VARIANTS), figsize=(6 * len(VARIANTS), 6.4), dpi=100)
    for ax, (name, changes) in zip(axes, VARIANTS.items()):
        sim = copy.deepcopy(base)
        kills, killing = attack(sim, minutes, changes)
        inside = deep_inside(sim.world, centre, radius)
        rippling = int(align.ripple_mask(sim.world, sim.world.myxo.nodes[:, 0]).sum())
        print(f"{name:32s} | kills {kills:4d} | killing at a time {killing:4.1f} | "
              f"Myxo deep inside {inside:3d} of {state.count(sim.world.myxo)}, rippling {rippling:3d} | "
              f"E. coli left {state.count(sim.world.ecoli)} | {time.time() - t0:.0f} s", flush=True)
        draw_world(ax, sim.world)
        ax.set_xlabel(f"{name}\nkills {kills} | deep inside {inside} | rippling {rippling}", fontsize=11)
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "penetration_test.png")
    fig.savefig(path)
    print("saved", path)


if __name__ == "__main__":
    main()
