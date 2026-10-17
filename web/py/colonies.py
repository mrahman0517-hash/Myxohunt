"""
colonies.py — colony bookkeeping only (there is no reseeding, B44, B50).
"""
import numpy as np


def living_colonies(world):
    """IDs of colonies that still have at least one living cell."""
    e = world.ecoli
    return np.unique(e.colony[e.lysis_timer < 0])


def colony_sizes(world):
    """Number of living cells per colony, as {colony ID: count}."""
    e = world.ecoli
    ids, counts = np.unique(e.colony[e.lysis_timer < 0], return_counts=True)
    return dict(zip(ids.tolist(), counts.tolist()))
