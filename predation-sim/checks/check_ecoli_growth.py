"""
Milestone 2 check: E. coli seeds growing into colonies on patchy ground (no Myxo yet).

Usage (from predation-sim/):  python checks/check_ecoli_growth.py [bio_minutes] [seed] [max_cells]
Writes checks/output/ecoli_growth.png and ecoli_growth_stats.csv.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                           # noqa: E402
from matplotlib.collections import LineCollection         # noqa: E402
import numpy as np                                        # noqa: E402

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import geometry as geo                                    # noqa: E402
import state                                              # noqa: E402
from engine import Simulation                             # noqa: E402
from settings import make_settings                        # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "output")


def run(bio_minutes, seed, max_cells):
    """Run the live-size world until `bio_minutes` of biology have passed (or the cell cap)."""
    sim = Simulation(make_settings("live", seed=seed, myxo_groups=0, myxo_singles=0))   # E. coli only
    s, t0 = sim.world.settings, time.time()
    real_minutes = bio_minutes / s.speedup
    while sim.world.t < real_minutes and state.count(sim.world.ecoli) < max_cells:
        sim.run_for(real_minutes=1.0)
        print(f"bio t = {sim.world.bio_t:6.0f} min | E. coli {state.count(sim.world.ecoli):6d} | "
              f"{time.time() - t0:5.0f} s", flush=True)
    return sim


def draw_rods(ax, world):
    """Each E. coli as a thick magenta line on the nutrient map (darker = less food)."""
    s, e = world.settings, world.ecoli
    ax.imshow(world.fields.nutrients.T, origin="lower", extent=[0, s.box, 0, s.box],
              cmap="YlOrBr", vmin=0, vmax=1, alpha=0.9)
    ends = geo.rod_points(e.centre, e.angle, e.length, 2, s.ecoli_width)
    seg = np.mod(ends, s.box)
    keep = np.linalg.norm(seg[:, 0] - seg[:, 1], axis=1) < s.box / 2      # drop edge-crossing rods
    seg, dormant = seg[keep], e.dormant[keep]
    width = ax.get_window_extent().width * 72 / ax.figure.dpi / s.box * s.ecoli_width
    colors = np.where(dormant[:, None], [[0.55, 0.2, 0.45]], [[0.9, 0.24, 0.63]])
    ax.add_collection(LineCollection(seg, colors=colors, linewidths=width, capstyle="round"))
    ax.set_xlim(0, s.box); ax.set_ylim(0, s.box); ax.set_aspect("equal")
    ax.set_title(f"E. coli after {world.bio_t:.0f} bio min ({state.count(e)} cells)", loc="left")


def draw_curves(ax, stats):
    """Cell count (log scale) and mean ground nutrients against biological time."""
    t = stats.column("bio_t")
    ax.semilogy(t, np.maximum(stats.column("ecoli"), 1), color="#e63ca0", label="E. coli (living)")
    ax.semilogy(t, 2 * 2 ** (t / 20.0), color="0.6", ls="--", label="doubling every 20 min")
    ax.set_ylim(1, max(10, stats.column("ecoli").max() * 3))
    ax.set_xlabel("biological time (min)"); ax.set_ylabel("cells"); ax.legend(loc="upper left")
    twin = ax.twinx()
    twin.plot(t, stats.column("nutrients"), color="#b5651d", label="mean nutrients")
    twin.set_ylim(0, 1); twin.set_ylabel("mean ground nutrients")
    ax.set_title("Growth curve", loc="left")


def main():
    """Run, then save the picture and the numbers."""
    bio, seed, cap = (float(sys.argv[1]) if len(sys.argv) > 1 else 300.0,
                      int(sys.argv[2]) if len(sys.argv) > 2 else 1,
                      int(sys.argv[3]) if len(sys.argv) > 3 else 15000)
    sim = run(bio, seed, cap)
    os.makedirs(OUT, exist_ok=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6), dpi=110)
    draw_rods(a, sim.world)
    draw_curves(b, sim.stats)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ecoli_growth.png"))
    sim.stats.to_csv(os.path.join(OUT, "ecoli_growth_stats.csv"))
    print("saved", os.path.join(OUT, "ecoli_growth.png"))


if __name__ == "__main__":
    main()
