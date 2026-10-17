"""
myxo_famine.py — what starving Myxo do after a day (B80).

About 24 h after starvation starts, Myxo begin development: cell lysis and aggregation start
together (Lee 2012). Each starving cell then ends up in one of three fates:
  lysis   about 70% (classic counts 60–80%): the cell dies and what's left of it feeds its
          neighbours, as scraps (B83, B84);
  spore   about 10%: the cell rounds up and waits, costing nothing;
  rod     the rest, about 20% (10–20% measured, O'Connor & Zusman 1991): a persister-like
          "peripheral rod" that stays active in stringent mode and can regrow when food returns.

We don't model fruiting bodies. Spores are taken out of the moving population and kept as
points on the ground; they don't germinate yet.
"""
import numpy as np

import grids
import state

LYSE, SPORE, ROD = 0, 1, 2


def starting_development(world, dt_bio):
    """Cells whose starvation clock passed famine_time in this tick: (N,) bool. A cell crosses
    once per famine, because only a real meal of prey food resets its clock (B83)."""
    s, t = world.settings, world.myxo.starve_time
    return (t >= s.famine_time) & (t - dt_bio < s.famine_time)


def draw_fates(world, n):
    """A fate for each of n cells starting development: LYSE, SPORE or ROD."""
    s = world.settings
    roll = world.rng.random(n)
    return np.where(roll < s.famine_lysis_share, LYSE,
                    np.where(roll < s.famine_lysis_share + s.famine_spore_share, SPORE, ROD))


def lyse(world, rows):
    """Developmental lysis: whatever is left in the store spills as scraps for the others. The
    store is the whole cell, so there's no separate body to add (B84, replaces B82); no prey
    matrix."""
    m, s = world.myxo, world.settings
    centres = np.mod(m.nodes[rows].mean(axis=1), s.box)
    grids.deposit(world.fields.scraps, centres, np.maximum(m.energy[rows], 0.0), s.box)
    world.myxo_lysed += len(rows)


def sporulate(world, rows):
    """The cells become spores: kept as points on the ground, out of the moving population."""
    m, s = world.myxo, world.settings
    world.spores = np.concatenate([world.spores, np.mod(m.nodes[rows].mean(axis=1), s.box)])


def famine_exit(world, dt_bio):
    """Cells that have been starving for famine_time take their fate. No random numbers
    are drawn unless a cell is due, so runs without long famines are unchanged."""
    s, m = world.settings, world.myxo
    if not s.famine_exit or state.count(m) == 0:
        return
    due = np.nonzero(starting_development(world, dt_bio))[0]
    if due.size == 0:
        return
    fate = draw_fates(world, due.size)
    lyse(world, due[fate == LYSE])
    sporulate(world, due[fate == SPORE])
    state.keep_rows(m, ~np.isin(np.arange(state.count(m)), due[fate != ROD]))
