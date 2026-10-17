"""
ecoli_life.py — how E. coli lives on the ground's nutrients: growth speed (Monod curve), eating
the nutrients, going dormant when food runs out, and starving to death (B33, B34, B45).
"""
import numpy as np

import ecoli_body
import grids


def monod_factor(nutrient, half_saturation):
    """Growth speed from the food under a cell: 0 with no food, 1 on the richest ground (1.0).

    The Monod curve n/(K + n), scaled so that n = 1 gives exactly 1: on the richest patch a
    cell doubles at its rich-medium rate (20 min). The curve keeps its Monod shape; half
    speed comes at n = K/(1 + 2K), about 0.14 for K = 0.2.

    Args:
        nutrient: (M,) nutrient level under each cell, 0..1.
        half_saturation: the Monod constant K.
    Returns:
        (M,) growth factor between 0 and 1.
    """
    n = np.clip(nutrient, 0.0, None)
    return n * (1.0 + half_saturation) / (half_saturation + n)


def alive(ecoli):
    """True for living cells (not dead-and-waiting-to-burst)."""
    return ecoli.lysis_timer < 0


def body_points(world):
    """Points along each rod's body (its contact points), rod by rod: (M·k, 2)."""
    return ecoli_body.contact_points(world.ecoli, world.settings)


def nutrient_under(world):
    """Mean nutrient level along each rod's body: a rod takes up food over its whole surface,
    not at one point (B78). (M,)"""
    k = world.settings.ecoli_points
    levels = grids.sample(world.fields.nutrients, body_points(world), world.settings.box)
    return levels.reshape(-1, k).mean(axis=1)


def growth_rates(world):
    """Growth rate of each rod (1/bio min): ln2/doubling × Monod × its own speed; 0 if dormant or dead."""
    e, s = world.ecoli, world.settings
    rate = (np.log(2) / s.ecoli_doubling * e.speed_factor
            * monod_factor(nutrient_under(world), s.monod_half_saturation))
    return np.where(alive(e) & ~e.dormant, rate, 0.0)


def consume(world, grown):
    """Take the nutrients a rod used to grow from the squares along its body, an equal share at
    each of its points (never below zero) (B78)."""
    s, f = world.settings, world.fields
    if grown.size == 0:
        return
    k = s.ecoli_points
    used = np.repeat(grown * s.nutrient_per_um / k, k)
    grids.deposit(f.nutrients, body_points(world), -used, s.box)
    np.clip(f.nutrients, 0.0, None, out=f.nutrients)


def update_dormancy(world, dt_bio):
    """No food → stop growing and count the time; a real meal back → wake up and reset (B34, B87).

    A growing cell goes dormant when the food under it falls below dormant_threshold. A dormant
    cell stays dormant, its starvation clock running, until the food under it is back to
    wake_threshold: a trace of regrowing food no longer resets it (B87).
    """
    e, s = world.ecoli, world.settings
    level = nutrient_under(world)
    hungry = alive(e) & ((level < s.dormant_threshold) | (e.dormant & (level < s.wake_threshold)))
    e.starve_time = np.where(hungry, e.starve_time + dt_bio, np.where(alive(e), 0.0, e.starve_time))
    e.dormant = np.where(alive(e), hungry, e.dormant)


def starvation_deaths(world, dt_bio):
    """Dormant cells (not persisters) may die once dormancy_before_death has passed (none since B87:
    viability falls from the start of starvation, Schink et al.); the body stays intact until it
    bursts (B45)."""
    e, s = world.ecoli, world.settings
    at_risk = alive(e) & e.dormant & ~e.persister & (e.starve_time > s.dormancy_before_death)
    dies = at_risk & (world.rng.random(len(e.uid)) < 1.0 - np.exp(-s.starvation_death_rate * dt_bio))
    e.lysis_timer[dies] = s.starved_lysis_delay


def leak_attractant(world, dt_bio):
    """Living E. coli leak a faint attractant (outer-membrane vesicles rich in PE), which
    spreads and fades like the attractant from burst prey (B63; off when the rate is 0)."""
    e, s = world.ecoli, world.settings
    if s.ecoli_attractant_rate <= 0 or len(e.uid) == 0:
        return
    living = alive(e)
    grids.deposit(world.fields.attractant, e.centre[living], s.ecoli_attractant_rate * dt_bio, s.box)


def content_fraction(ecoli, s):
    """Share of a cell's food still inside it: 1 if it never starved, shrinking to 25% over
    starved_shrink_time of starving (B45, B87)."""
    starved = np.minimum(ecoli.starve_time / s.starved_shrink_time, 1.0)
    return 1.0 - (1.0 - s.starved_content_min) * starved


def count_down_lysis(world, dt_bio):
    """Count down dead-intact cells; return the ones whose time to burst has come."""
    e = world.ecoli
    dead = ~alive(e)
    e.lysis_timer[dead] = e.lysis_timer[dead] - dt_bio
    return dead & (e.lysis_timer <= 0)
