"""
stats.py — numbers that describe the world at a moment, for the on-screen display and for
plotting a run afterwards (saved as CSV).
"""
import csv

import numpy as np
from scipy.spatial import cKDTree

import colonies
import counters
import geometry as geo
import myxo_alignment as align
import myxo_modes
import state


def myxo_at_prey(world, reach=10.0):
    """Myxo whose centre lies within `reach` µm of a living E. coli: the pack at the prey (B77)."""
    e, m, box = world.ecoli, world.myxo, world.settings.box
    alive = e.lysis_timer < 0
    if not alive.any() or not len(m.uid):
        return 0
    tree = cKDTree(geo.wrap_points(e.centre[alive], box), boxsize=box)
    d, _ = tree.query(geo.wrap_points(m.nodes.mean(axis=1), box), distance_upper_bound=reach)
    return int(np.isfinite(d).sum())


def myxo_rods(world):
    """Starving cells that went through a famine and stayed on as persister-like rods (B80)."""
    s = world.settings
    return int((world.myxo.starve_time >= s.famine_time).sum()) if s.famine_exit else 0


def snapshot(world):
    """A one-line summary of the world right now, as a dict, followed by the running totals of
    events so far (counters.py)."""
    e, m = world.ecoli, world.myxo
    alive = e.lysis_timer < 0
    return dict(
        **now(world, e, m, alive), ecoli_persisters=int((alive & e.persister).sum()), **counters.totals(world))


def now(world, e, m, alive):
    """The state of the world at this moment (the columns every run has had)."""
    return dict(
        t=world.t, bio_t=world.bio_t, ecoli=int(alive.sum()), ecoli_dormant=int((alive & e.dormant).sum()),
        ecoli_dead_intact=int((~alive).sum()), colonies=len(colonies.living_colonies(world)),
        myxo=state.count(m), myxo_store=float(m.energy.sum()), myxo_energy=float(m.energy.mean()) if state.count(m) else float("nan"),
        myxo_paused=int((m.pause_left > 0).sum()), myxo_scouts=int(m.scout.sum()),
        myxo_rippling=int(align.ripple_mask(world, m.nodes[:, 0]).sum()) if state.count(m) else 0,
        myxo_at_prey=myxo_at_prey(world),
        myxo_stringent=int(myxo_modes.stringent(world).sum()),
        myxo_rods=myxo_rods(world), myxo_spores=len(world.spores), myxo_lysed=world.myxo_lysed,
        nutrients=float(world.fields.nutrients.mean()), food=float(world.fields.food.sum()),
        scraps=float(world.fields.scraps.sum()),
        matrix=float(world.fields.matrix.sum()))


class StatsLog:
    """A growing list of snapshots, one per grid update."""

    def __init__(self):
        """Start with no rows."""
        self.rows = []

    def add(self, world):
        """Record the world as it is now."""
        self.rows.append(snapshot(world))

    def column(self, name):
        """All recorded values of one quantity, as an array (for plotting)."""
        return np.array([row[name] for row in self.rows])

    def to_csv(self, path):
        """Save all rows as a CSV file."""
        if not self.rows:
            return
        names = list(dict.fromkeys(k for row in self.rows for k in row))   # rows from before a new column get blanks
        with open(path, "w", newline="", encoding="utf8") as fh:
            writer = csv.DictWriter(fh, fieldnames=names, restval="")
            writer.writeheader()
            writer.writerows(self.rows)
