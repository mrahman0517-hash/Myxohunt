"""
Milestone 4 check: Myxo placed at the edge of a grown colony kill their way in.

Grows one E. coli colony alone, puts four drops of Myxo at its edge, runs on, and saves
snapshots plus the measured share of touches that end in a kill (Seef 2021: about 26%).

Usage (from predation-sim/):  python checks/check_predation.py [grow_real_min] [attack_real_min] [seed]
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
import seeding                                               # noqa: E402
import state                                                 # noqa: E402
from check_live_world import draw_world                     # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import make_settings                           # noqa: E402

OUT = os.path.join(HERE, "output")


def colony_centre_and_radius(world):
    """Centre (circular mean, safe across the wrap-around edges) and outer radius of the E. coli."""
    box, c = world.settings.box, world.ecoli.centre
    ang = c / box * 2 * np.pi
    centre = (np.arctan2(np.sin(ang).mean(0), np.cos(ang).mean(0)) % (2 * np.pi)) / (2 * np.pi) * box
    d = c - centre
    d -= box * np.round(d / box)
    return centre, np.linalg.norm(d, axis=1).max()


def add_attackers(world, groups=4, size=20):
    """Drops of Myxo just outside the colony edge, at evenly spaced points around it."""
    centre, radius = colony_centre_and_radius(world)
    for k in range(groups):
        a = 2 * np.pi * k / groups
        spot = centre + (radius + 4.0) * np.array([np.cos(a), np.sin(a)])
        state.append_rows(world.myxo, seeding.myxo_group(world, spot, size))


class TouchTracker:
    """Follows every Myxo–E. coli touch from its first to its last tick and notes whether it
    led to a pause and to a kill."""

    def __init__(self):
        """Nothing tracked yet."""
        self.started = {}                       # open touch → tick it began
        self.durations, self.pauses, self.kills = [], 0, 0
        self.paused_pairs, self.tick = set(), 0
        self.episodes = self.episodes_paused = 0

    def update(self, sim):
        """Record this tick's touches, pauses and kills; close touches that ended."""
        w, t, self.tick = sim.world, sim.touches, self.tick + 1
        now = {(int(w.myxo.uid[a]), int(w.ecoli_uid_before[b])) for a, b in t} if len(t) else set()
        rows, targets = sim.new_pauses
        self.pauses += len(rows)
        self.kills += len(sim.kills[1])
        self.paused_pairs |= {(int(w.myxo.uid[r]), int(u)) for r, u in zip(rows, targets)}
        for pair in now - self.started.keys():
            self.started[pair] = self.tick
        for pair in set(self.started) - now:
            self.durations.append((self.tick - self.started.pop(pair)) * w.settings.dt)
            self.episodes += 1
            self.episodes_paused += pair in self.paused_pairs

    def report(self):
        """Touch durations, share of touches that led to a pause, pauses that killed, kills per touch."""
        d = np.array(self.durations) if self.durations else np.zeros(1)
        return (f"touches {self.episodes} | median touch {np.median(d) * 60:.0f} s, mean {d.mean() * 60:.0f} s | "
                f"touches with a pause {self.episodes_paused / max(self.episodes, 1):.1%} | "
                f"pauses that killed {self.kills / max(self.pauses, 1):.1%} | "
                f"kills per touch {self.kills / max(self.episodes, 1):.1%}")


def run_attack(sim, minutes, snap_every):
    """Run while tracking touches; return snapshots (as pictures) and the tracker."""
    tracker, snaps, w = TouchTracker(), [], sim.world
    every = int(round(snap_every / w.settings.dt))
    for i in range(int(round(minutes / w.settings.dt)) + 1):
        if i % every == 0:
            fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
            draw_world(ax, w)
            fig.canvas.draw()
            snaps.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
            plt.close(fig)
        w.ecoli_uid_before = w.ecoli.uid.copy()          # touch rows refer to this tick's order
        sim.step()
        tracker.update(sim)
    return snaps, tracker


def main():
    """Grow, attack, save the picture strip and print the touch statistics."""
    grow = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    attack = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    s = make_settings("live", seed=seed, start_colonies=1, myxo_groups=0, myxo_singles=0)
    sim, t0 = Simulation(s), time.time()
    sim.run_for(real_minutes=grow)
    start_cells = state.count(sim.world.ecoli)
    add_attackers(sim.world)
    snaps, tr = run_attack(sim, attack, snap_every=attack / 3)
    end_cells = state.count(sim.world.ecoli)
    print(f"E. coli {start_cells} → {end_cells} | {tr.report()} | wall {time.time() - t0:.0f} s")
    fig, axes = plt.subplots(1, len(snaps), figsize=(5 * len(snaps), 5.2), dpi=100)
    for ax, img in zip(axes, snaps):
        ax.imshow(img); ax.axis("off")
    fig.suptitle(f"Attack on one colony: E. coli {start_cells} → {end_cells}; "
                 f"{tr.kills} kills from {tr.episodes} touches")
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, "predation_attack.png"))
    print("saved", os.path.join(OUT, "predation_attack.png"))


if __name__ == "__main__":
    main()
