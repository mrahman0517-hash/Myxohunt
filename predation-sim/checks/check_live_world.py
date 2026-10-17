"""
Picture of the default live world after some time: ground, slime, E. coli and Myxo together.
A quick visual check for milestones 3 onward (before the pygame app exists).

Usage (from predation-sim/):  python checks/check_live_world.py [real_minutes] [seed] [name]
Writes checks/output/<name>.png (default name: live_world).
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from matplotlib.collections import LineCollection            # noqa: E402
import numpy as np                                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import geometry as geo                                       # noqa: E402
import state                                                 # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import make_settings                           # noqa: E402

OUT = os.path.join(HERE, "output")


def segments(points, box):
    """Line segments between consecutive points of each cell, folded into the box, dropping
    the pieces that cross an edge."""
    pts = np.mod(points, box)
    seg = np.stack([pts[:, :-1], pts[:, 1:]], axis=2).reshape(-1, 2, 2)
    return seg[np.linalg.norm(seg[:, 0] - seg[:, 1], axis=1) < box / 2]


def draw_world(ax, world):
    """Ground nutrients (brown), slime (grey), E. coli (magenta), Myxo (green) and spores (pale dots)."""
    s, f, e, m = world.settings, world.fields, world.ecoli, world.myxo
    ax.imshow(f.nutrients.T, origin="lower", extent=[0, s.box, 0, s.box], cmap="YlOrBr", vmin=0, vmax=1)
    slime = np.clip((f.eps + f.eps_scout).T / 0.5, 0, 1)
    ax.imshow(np.dstack([np.full_like(slime, 0.35)] * 3 + [0.6 * slime]), origin="lower",
              extent=[0, s.box, 0, s.box])
    px = ax.get_window_extent().width * 72 / ax.figure.dpi / s.box
    rods = geo.rod_points(e.centre, e.angle, e.length, 2, s.ecoli_width)
    ax.add_collection(LineCollection(segments(rods, s.box), colors="#e63ca0", linewidths=px * s.ecoli_width,
                                     capstyle="round"))
    ax.add_collection(LineCollection(segments(m.nodes, s.box), colors="#1f9d3a", linewidths=px * s.disc_diam,
                                     capstyle="round"))
    if len(world.spores):                                    # spores: round dots about 1.5 µm across (B80)
        ax.scatter(world.spores[:, 0], world.spores[:, 1], s=(px * 1.5) ** 2, color="#c8f0a0",
                   edgecolors="#1f9d3a", linewidths=0.3)
    ax.set_xlim(0, s.box); ax.set_ylim(0, s.box); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{world.t:.0f} real min = {world.bio_t:.0f} bio min | E. coli {state.count(e)} | "
                 f"Myxo {state.count(m)}", loc="left", fontsize=10)


def main():
    """Run the default live world and save a picture."""
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    name = sys.argv[3] if len(sys.argv) > 3 else "live_world"
    sim, t0 = Simulation(make_settings("live", seed=seed)), time.time()
    while sim.world.t < minutes - 1e-9:
        sim.run_for(real_minutes=min(5.0, minutes - sim.world.t))
        print(f"t = {sim.world.t:5.1f} min | E. coli {state.count(sim.world.ecoli)} | {time.time() - t0:4.0f} s",
              flush=True)
    os.makedirs(OUT, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 8), dpi=120)
    draw_world(ax, sim.world)
    fig.tight_layout()
    path = os.path.join(OUT, f"{name}.png")
    fig.savefig(path)
    print("saved", path)


if __name__ == "__main__":
    main()
