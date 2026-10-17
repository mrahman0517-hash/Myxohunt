"""
contacts.py — one shared contact search per tick: push apart overlapping cells (Myxo with
Myxo, E. coli with E. coli; Myxo crawl over prey, B76), and list which Myxo touch which E. coli.
"""
import numpy as np
from scipy.spatial import cKDTree

import ecoli_body
import geometry as geo
import state

MYXO, ECOLI = 0, 1


def all_points(world):
    """Every contact point in the world, wrapped into the box.

    Returns:
        points (P, 2), diameter (P,), owner (P,) row of the cell it belongs to,
        kind (P,) MYXO or ECOLI, local (P,) disc/point number within its cell.
    """
    s, m, e = world.settings, world.myxo, world.ecoli
    N, M, n, k = state.count(m), state.count(e), s.n_nodes, s.ecoli_points
    pts = np.concatenate([geo.wrap_points(m.nodes.reshape(-1, 2), s.box),
                          ecoli_body.contact_points(e, s)]) if (N + M) else np.zeros((0, 2))
    diam = np.concatenate([np.full(N * n, s.disc_diam), np.full(M * k, s.ecoli_width)])
    owner = np.concatenate([np.repeat(np.arange(N), n), np.repeat(np.arange(M), k)])
    kind = np.concatenate([np.full(N * n, MYXO), np.full(M * k, ECOLI)])
    local = np.concatenate([np.tile(np.arange(n), N), np.tile(np.arange(k), M)])
    return pts, diam, owner.astype(np.int64), kind, local


def find_pairs(points, box, rmax):
    """All pairs of points closer than rmax, across the wrap-around edges: (Q, 2)."""
    if len(points) < 2:
        return np.zeros((0, 2), dtype=np.int64)
    return cKDTree(points, boxsize=box).query_pairs(rmax, output_type="ndarray")


def drop_bonded(pairs, kind, owner, local):
    """Remove pairs inside one cell: neighbouring discs of a Myxo (its springs handle them)
    and any two points of the same E. coli rod (it's rigid)."""
    a, b = pairs[:, 0], pairs[:, 1]
    same_cell = (kind[a] == kind[b]) & (owner[a] == owner[b])
    bonded = same_cell & ((kind[a] == ECOLI) | (np.abs(local[a] - local[b]) == 1))
    return pairs[~bonded]


def push_shares(kind, a, b, s):
    """How each pair's shove is split between its two points (each 1.0 when equal).

    In a Myxo–E. coli pair the E. coli takes 2·ecoli_push_share of the shove and the Myxo
    the rest, so above 0.5 Myxo plough into colonies (B62). The total separation is unchanged.
    """
    wa, wb = np.ones(len(a)), np.ones(len(a))
    if s.ecoli_push_share != 0.5:
        q = 2.0 * s.ecoli_push_share
        a_ecoli = (kind[a] == ECOLI) & (kind[b] == MYXO)
        b_ecoli = (kind[a] == MYXO) & (kind[b] == ECOLI)
        wa[a_ecoli], wb[a_ecoli] = q, 2.0 - q
        wa[b_ecoli], wb[b_ecoli] = 2.0 - q, q
    return wa, wb


def push_amounts(points, pairs, diam, kind, box, s):
    """How far each point is pushed this tick by overlapping neighbours: (P, 2).

    Adapted from paper-reproduction/functions.py:repulsion, with D = the pair's mean diameter:
    push = (D − r)² / max(r − 0.9 D, 2/k_r) · dt along the line between centres.
    """
    disp = np.zeros_like(points)
    if len(pairs) == 0:
        return disp
    a, b = pairs[:, 0], pairs[:, 1]
    d = geo.min_image(points[a] - points[b], box)
    r = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
    D = 0.5 * (diam[a] + diam[b])
    push = np.where(r < D, (D - r) ** 2 / np.maximum(r - 0.9 * D, 2.0 / s.k_rep) * s.dt, 0.0)
    step = d / r[:, None] * push[:, None]
    wa, wb = push_shares(kind, a, b, s)
    a, b = a.astype(np.intp), b.astype(np.intp)       # bincount needs the platform's index type (32-bit in browsers)
    for axis in range(2):
        disp[:, axis] += np.bincount(a, weights=step[:, axis] * wa, minlength=len(points))
        disp[:, axis] -= np.bincount(b, weights=step[:, axis] * wb, minlength=len(points))
    return disp


def myxo_ecoli_touches(points, pairs, kind, owner, box, s):
    """Which Myxo (row) touches which E. coli (row): (T, 2) unique [myxo, ecoli] pairs."""
    a, b = pairs[:, 0], pairs[:, 1]
    mixed = kind[a] != kind[b]
    a, b = a[mixed], b[mixed]
    close = np.linalg.norm(geo.min_image(points[a] - points[b], box), axis=1) < s.touch_distance
    a, b = a[close], b[close]
    myxo_pt = np.where(kind[a] == MYXO, a, b)
    ecoli_pt = np.where(kind[a] == MYXO, b, a)
    found = np.stack([owner[myxo_pt], owner[ecoli_pt]], axis=1)
    return np.unique(found, axis=0) if len(found) else np.zeros((0, 2), dtype=np.int64)


def shoving_pairs(pairs, kind, s):
    """The pairs that push each other apart. With myxo_crawl_over_prey, Myxo and E. coli never
    shove: Myxo glide over and between prey, standing in for the 3D colony that A-motile cells
    penetrate (Seef 2021; B76). Their touches still count for killing."""
    if not s.myxo_crawl_over_prey or len(pairs) == 0:
        return pairs
    return pairs[kind[pairs[:, 0]] == kind[pairs[:, 1]]]


def resolve_contacts(world):
    """Push all overlapping cells apart and return the Myxo–E. coli touches for predation."""
    s = world.settings
    points, diam, owner, kind, local = all_points(world)
    rmax = max(s.ecoli_width, s.disc_diam, s.touch_distance)
    pairs = drop_bonded(find_pairs(points, s.box, rmax), kind, owner, local)
    disp = push_amounts(points, shoving_pairs(pairs, kind, s), diam, kind, s.box, s)
    n_myxo_pts = state.count(world.myxo) * s.n_nodes
    world.myxo.nodes += disp[:n_myxo_pts].reshape(world.myxo.nodes.shape)
    ecoli_body.apply_pushes(world.ecoli, disp[n_myxo_pts:], s)
    return myxo_ecoli_touches(points, pairs, kind, owner, s.box, s)
