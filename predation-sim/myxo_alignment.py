"""
myxo_alignment.py — how a Myxo picks its heading (paper H3): on prey-matrix ground it turns
toward that spot's ripple axis; elsewhere it lays slime under its tail and turns toward slime
trails ahead. Trail-following copied from paper-reproduction/functions.py (validated, A11).
"""
import numpy as np

import geometry as geo
import grids

HEADING_BINS = 1440   # headings rounded to 0.25° when looking up wedges (pure speed-up)


# ---------------------------------------------------------------- where cells ripple
def ripple_mask(world, heads):
    """True where the prey material averaged around the head (ghosts and living prey) reaches the
    threshold (B11, B43, B46, B76)."""
    s = world.settings
    return grids.sample(world.fields.matrix_smooth, heads, s.box) >= s.matrix_ripple_threshold


def local_axis(world, heads):
    """Ripple axis under each head (rad), from the averaged doubled-angle maps of ghosts and
    living prey (B13, B38, B76)."""
    f, box = world.fields, world.settings.box
    return geo.axis_from_fields(grids.sample(f.axis_c_smooth, heads, box),
                                grids.sample(f.axis_s_smooth, heads, box))


# adapted from paper-reproduction/functions.py:ripple_turn (axis per cell instead of one global axis)
def ripple_turn(theta, axis, s):
    """Δθ = γ′ · sin 2(axis − θ) · Δt. The 2 makes both ways along the axis equally good."""
    return s.gamma_ripple * np.sin(2.0 * (axis - theta)) * s.dt


# ---------------------------------------------------------------- scouts
def scout_turn(k, s, rng):
    """Small random turns for k scouts gliding off-trail (A-motility; B67).

    A random walk in heading with rotational diffusion D: Δθ = √(2·D·Δt)·(normal random number),
    so a scout's path stays roughly straight for speed/D ≈ 20 µm before bending away.
    """
    return np.sqrt(2.0 * s.scout_turn_noise * s.dt) * rng.standard_normal(k)


# ---------------------------------------------------------------- slime trails
# adapted from paper-reproduction/functions.py:eps_lay (grid passed directly)
def eps_lay(eps, spacing, tails, s, amount=1.0):
    """Every moving swarming cell adds a·v·Δt (× amount) of slime under its rear disc."""
    n = eps.shape[0]
    ix = np.floor(np.mod(tails[:, 0], n * spacing) / spacing).astype(int) % n
    iy = np.floor(np.mod(tails[:, 1], n * spacing) / spacing).astype(int) % n
    np.add.at(eps, (ix, iy), s.eps_deposit * s.speed * s.dt * amount)


# adapted from paper-reproduction/functions.py:sensing_offsets
def sensing_offsets(spacing, s):
    """Built once: the grid squares within reach of the pili and, for every possible heading,
    which of the 5 wedges each square falls in (-1 = behind the cell)."""
    r = int(s.sense_radius / spacing)
    ox, oy = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1), indexing="ij")
    ox, oy = ox.ravel(), oy.ravel()
    keep = (ox ** 2 + oy ** 2 <= r * r) & ((ox != 0) | (oy != 0))
    ox, oy = ox[keep], oy[keep]
    headings = np.arange(HEADING_BINS) * 2 * np.pi / HEADING_BINS
    rel = geo.wrap_angle(np.arctan2(oy, ox)[None, :] - headings[:, None])
    width = s.view_angle / s.n_sectors
    table = (np.rint(rel / width) + s.n_sectors // 2).astype(np.int8)
    table[np.abs(rel) > s.view_angle / 2] = -1
    return ox, oy, table


def wedge_sums(eps, spacing, heads, theta, offsets, s, extra=None):
    """Slime summed in each of the 5 wedges ahead of each head, and the strongest square seen.
    `extra` is a second slime layer (scout slime, B71) sensed together with the first."""
    ox, oy, table = offsets
    N, n = len(theta), eps.shape[0]
    hx = np.floor(np.mod(heads[:, 0], n * spacing) / spacing).astype(int)
    hy = np.floor(np.mod(heads[:, 1], n * spacing) / spacing).astype(int)
    sx, sy = (hx[:, None] + ox[None]) % n, (hy[:, None] + oy[None]) % n
    vals = eps[sx, sy] if extra is None else eps[sx, sy] + extra[sx, sy]
    hbin = np.rint(np.mod(theta, 2 * np.pi) / (2 * np.pi) * HEADING_BINS).astype(int) % HEADING_BINS
    sector = table[hbin]
    ahead = sector >= 0
    rows = np.broadcast_to(np.arange(N)[:, None], sector.shape)
    sums = np.bincount((rows * s.n_sectors + sector)[ahead], weights=vals[ahead],
                       minlength=N * s.n_sectors).reshape(N, s.n_sectors)
    return sums, np.where(ahead, vals, 0.0).max(axis=1)


# adapted from paper-reproduction/functions.py:eps_turn (split into wedge_sums + choice)
def eps_turn(eps, spacing, heads, theta, offsets, s, rng, extra=None):
    """Turn toward slime: among wedges with ≥ 80% of the best, pick the one nearest straight
    ahead; Δθ = γ · sin 2(θ_wedge − θ) · Δt. No turn if no square reaches c_min.
    `extra`: scout slime, sensed on top of ordinary slime (B71)."""
    if len(theta) == 0:
        return np.zeros(0)
    sums, peak = wedge_sums(eps, spacing, heads, theta, offsets, s, extra)
    width = s.view_angle / s.n_sectors
    centres = (np.arange(s.n_sectors) - s.n_sectors // 2) * width
    good = sums >= s.eps_choice_tolerance * sums.max(axis=1, keepdims=True)
    closeness = np.abs(centres)[None, :] * (1 + rng.uniform(-1e-3, 1e-3, size=sums.shape))
    chosen = centres[np.argmin(np.where(good, closeness, np.inf), axis=1)]
    return np.where(peak >= s.eps_c_min, s.gamma_eps * np.sin(2.0 * chosen) * s.dt, 0.0)
