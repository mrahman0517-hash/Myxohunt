"""
predation.py — killing on contact and bursting (B14–B17, B45, B49).

A Myxo touching a living E. coli may stop and assemble its killing machinery (a pause, about
30% of touches); after kill_delay real minutes the prey bursts in 80% of cases (Seef 2021).
The pause remembers its target by the E. coli's permanent ID, because rows shift when cells die.
"""
import numpy as np

import ecoli_body
import ecoli_life
import grids
import myxo_energy
import state


# ---------------------------------------------------------------- pauses and kills
def predation_clock(s):
    """How much faster than measured pauses and kills run: the speed-up if predation is put on
    the biology clock (B66), otherwise 1 (Seef 2021's real-time numbers)."""
    return s.speedup if s.scale_predation else 1.0


def count_down_pauses(world):
    """Advance every killing pause by one tick; return the Myxo whose pause has just ended."""
    m = world.myxo
    paused = m.pause_left > 0
    m.pause_left[paused] -= world.settings.dt
    ended = paused & (m.pause_left <= 1e-12)
    m.pause_left[ended] = 0.0
    return ended


def start_pauses(world, touches, just_ended):
    """Free Myxo touching living prey may start a killing pause (B14, B15).

    Args:
        touches: (T, 2) [myxo row, ecoli row] pairs from this tick's contact search.
        just_ended: (N,) Myxo whose previous pause ended this tick (they move on first).
    Returns:
        (myxo rows, target uids) of the pauses started.
    """
    m, e, s = world.myxo, world.ecoli, world.settings
    if len(touches) == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    alive_prey = e.lysis_timer[touches[:, 1]] < 0
    free = (m.pause_left[touches[:, 0]] <= 0) & ~just_ended[touches[:, 0]]
    candidates = touches[alive_prey & free]
    rows, first = np.unique(candidates[:, 0], return_index=True)     # one target per Myxo
    k = predation_clock(s)
    starts = world.rng.random(len(rows)) < 1.0 - np.exp(-s.pause_rate * k * s.dt)
    rows, targets = rows[starts], e.uid[candidates[first[starts], 1]]
    m.pause_left[rows] = s.kill_delay / k
    m.pause_target[rows] = targets
    return rows, targets


def rows_of(ecoli, uids):
    """Row of each E. coli ID, or -1 if that cell no longer exists (IDs are kept sorted)."""
    if len(ecoli.uid) == 0:
        return np.full(len(uids), -1, dtype=np.int64)
    pos = np.clip(np.searchsorted(ecoli.uid, uids), 0, len(ecoli.uid) - 1)
    return np.where(ecoli.uid[pos] == uids, pos, -1)


def finish_kills(world, ended):
    """At the end of each pause, burst the target with chance kill_success if it is still alive.

    Returns:
        (killer Myxo uids, killed E. coli uids) for this tick.
    """
    m, e, s = world.myxo, world.ecoli, world.settings
    killers = np.nonzero(ended)[0]
    rows = rows_of(e, m.pause_target[killers])
    m.pause_target[killers] = -1
    ok = (rows >= 0) & (world.rng.random(len(rows)) < s.kill_success)
    ok[ok] &= e.lysis_timer[rows[ok]] < 0
    victims, first = np.unique(rows[ok], return_index=True)       # one killer per victim
    eaters = killers[ok][first]
    dead = np.zeros(state.count(e), dtype=bool)
    dead[victims] = True
    killed_uids = e.uid[victims].copy()
    spill = np.ones(state.count(e))
    spill[victims] = killer_eats(world, eaters, victims)
    lyse_ecoli(world, dead, spill)
    return m.uid[eaters], killed_uids


def killer_eats(world, eaters, victims):
    """Each killer absorbs killer_share of its victim's contents at once (lysis happens at the
    killer's contact site, Seef 2021; B65). Returns the share of each victim's food left to spill."""
    m, e, s = world.myxo, world.ecoli, world.settings
    contents = s.ecoli_content * (e.length[victims] / 3.0) * ecoli_life.content_fraction(e, s)[victims]
    offered = s.killer_share * contents
    m.energy[eaters], leftover = myxo_energy.absorb(m.energy[eaters], offered, s)
    eaten = offered - leftover
    return np.where(contents > 0, 1.0 - eaten / np.maximum(contents, 1e-12), 1.0)


def spread_over_points(amount_per_rod, n_rods, k):
    """Share each rod's amount equally among its k points: (n_rods·k,)."""
    return np.repeat(np.broadcast_to(amount_per_rod, n_rods) / k, k)


def lysis_deposits(world, dead, spill):
    """Food, attractant and cell-wall matrix released by each bursting rod, per rod point.

    Args:
        spill: (M,) share of each rod's food that ends up on the ground (1 unless a killer ate some).
    Returns:
        points (D·k, 2) and the amounts of food, attractant and matrix per point (D·k,), plus
        the doubled-angle direction terms cos 2θ and sin 2θ of each point's colony.
    """
    e, s = world.ecoli, world.settings
    k, n_dead = s.ecoli_points, int(dead.sum())
    pts = ecoli_body.contact_points(e, s).reshape(-1, k, 2)[dead].reshape(-1, 2)
    food = (s.ecoli_content * (e.length[dead] / 3.0) * ecoli_life.content_fraction(e, s)[dead]
            * spill[dead])
    theta = np.asarray(world.colony_axis)[e.colony[dead]]
    return (pts, spread_over_points(food, n_dead, k),
            spread_over_points(s.attractant_per_lysis, n_dead, k),
            spread_over_points(s.matrix_per_ghost, n_dead, k),
            np.repeat(np.cos(2 * theta), k), np.repeat(np.sin(2 * theta), k))


def lyse_ecoli(world, dead, spill=None):
    """Burst the rods marked `dead`: spill their food (minus any the killer ate) and attractant,
    leave their wall as matrix tagged with their colony's ripple direction, and remove them
    (B17, B38, B45, B65)."""
    dead = np.asarray(dead, dtype=bool)
    if not dead.any():
        return
    spill = np.ones(len(dead)) if spill is None else spill
    f, box = world.fields, world.settings.box
    pts, food, attract, matrix, cos2, sin2 = lysis_deposits(world, dead, spill)
    grids.deposit(f.food, pts, food, box)
    grids.deposit(f.attractant, pts, attract, box)
    grids.deposit(f.matrix, pts, matrix, box)
    grids.deposit(f.axis_c, pts, matrix * cos2, box)
    grids.deposit(f.axis_s, pts, matrix * sin2, box)
    state.keep_rows(world.ecoli, ~dead)
