"""
ecoli_body.py — E. coli as rigid rods: where their contact points are, how pushes move them,
how they lengthen and how they divide (B5, B52). E. coli don't glide; they only get pushed.
"""
import numpy as np

import geometry as geo
import seeding
import state


def contact_points(ecoli, s):
    """All rod points for the contact search, wrapped into the box: (M·k, 2)."""
    pts = geo.rod_points(ecoli.centre, ecoli.angle, ecoli.length, s.ecoli_points, s.ecoli_width)
    return geo.wrap_points(pts.reshape(-1, 2), s.box)


def point_offsets(ecoli, s):
    """Each rod point's position relative to its rod centre: (M, k, 2)."""
    zero = np.zeros_like(ecoli.centre)
    return geo.rod_points(zero, ecoli.angle, ecoli.length, s.ecoli_points, s.ecoli_width)


def apply_pushes(ecoli, disp, s):
    """Move each rod as one rigid body from the pushes on its points.

    The rod slides by the average push and turns by the average twisting push (torque),
    then its centre is wrapped back into the box.

    Args:
        ecoli: the E. coli population (changed in place).
        disp: (M·k, 2) push on every rod point (µm this tick).
        s: settings.
    """
    M, k = state.count(ecoli), s.ecoli_points
    if M == 0:
        return
    d = disp.reshape(M, k, 2)
    r = point_offsets(ecoli, s)
    torque = np.sum(r[..., 0] * d[..., 1] - r[..., 1] * d[..., 0], axis=1)
    inertia = np.sum(r[..., 0] ** 2 + r[..., 1] ** 2, axis=1)
    ecoli.centre += s.ecoli_mobility * d.mean(axis=1)
    ecoli.angle += s.ecoli_mobility * np.where(inertia > 0, torque / np.maximum(inertia, 1e-12), 0.0)
    ecoli.centre[:] = geo.wrap_points(ecoli.centre, s.box)


def grow(ecoli, rate, dt_bio):
    """Lengthen each rod exponentially: length × exp(rate·dt). Returns the µm added per rod."""
    new_length = ecoli.length * np.exp(rate * dt_bio)
    grown = new_length - ecoli.length
    ecoli.length = new_length
    return grown


def daughters(world, idx):
    """Second daughters of the dividing rods `idx`: half length, centred on the far half."""
    e, s = world.ecoli, world.settings
    half = 0.5 * e.length[idx]
    direction = np.stack([np.cos(e.angle[idx]), np.sin(e.angle[idx])], axis=1)
    k = len(idx)
    return state.EColiCells(
        centre=geo.wrap_points(e.centre[idx] + 0.5 * half[:, None] * direction, s.box),
        angle=e.angle[idx] + 0.05 * world.rng.standard_normal(k), length=half.copy(),
        colony=e.colony[idx].copy(), dormant=np.zeros(k, dtype=bool), starve_time=np.zeros(k),
        persister=seeding.persister_flags(world, k), lysis_timer=np.full(k, -1.0),
        divide_at=seeding.divide_lengths(world, k), speed_factor=seeding.speed_factors(world, k),
        uid=state.new_uids(world, k))


def divide(world):
    """Split every living rod that has reached its own division length into two halves (B5).

    The mother's row becomes the first daughter (near half, keeps its ID); the second
    daughter is added at the bottom with a new ID. Total length is unchanged. Both daughters
    draw their own division length, growth speed and persister flag (B53, B55, B88).
    """
    e, s = world.ecoli, world.settings
    idx = np.nonzero((e.lysis_timer < 0) & (e.length >= e.divide_at))[0]
    if idx.size == 0:
        return
    second = daughters(world, idx)
    half = 0.5 * e.length[idx]
    direction = np.stack([np.cos(e.angle[idx]), np.sin(e.angle[idx])], axis=1)
    e.centre[idx] = geo.wrap_points(e.centre[idx] - 0.5 * half[:, None] * direction, s.box)
    e.length[idx] = half
    e.angle[idx] += 0.05 * world.rng.standard_normal(idx.size)
    e.divide_at[idx] = seeding.divide_lengths(world, idx.size)
    e.speed_factor[idx] = seeding.speed_factors(world, idx.size)
    e.persister[idx] = seeding.persister_flags(world, idx.size)
    state.append_rows(e, second)
