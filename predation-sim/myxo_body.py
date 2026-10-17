"""
myxo_body.py — Myxo mechanics: the pull at the leading pole, the springs that hold the 10-disc
body together, turning the head, reversing, keeping cells in the box, and the daughter body
at division. Physics copied from paper-reproduction/functions.py (validated, decision-log A11).
"""
import numpy as np

import geometry as geo


# copied from paper-reproduction/functions.py:head_direction
def head_direction(nodes):
    """Direction each cell is heading: from disc 1 towards disc 0 (the head). (N, 2)"""
    return geo.unit(nodes[:, 0] - nodes[:, 1])


# copied from paper-reproduction/functions.py:traction, plus the `moving` mask and per-cell speed
def traction(nodes, heading, moving, s, speed_factor=None):
    """Pull the head disc of every moving cell forward.

    The pull is speed × 10 per tick, but the springs then share that displacement among all
    10 discs, so the cell as a whole moves at exactly its speed. Paused cells (killing) are not
    pulled: their A-motility adhesions come apart during the kill (Seef 2021, B16).
    speed_factor (N,) scales each cell's speed (scouts faster, starving cells slower; B71).
    """
    factor = np.ones(len(nodes)) if speed_factor is None else speed_factor
    pull = s.speed * s.traction_scale * factor[moving]       # same order of sums as the paper code,
    nodes[moving, 0] += pull[:, None] * heading[moving] * s.dt  # so factor 1 gives identical numbers


# copied from paper-reproduction/functions.py:relax_springs
def relax_springs(nodes, s):
    """Pull neighbouring discs back towards 0.5 µm apart, 50 times per tick.

    Returns the heading after relaxation (what the frustration signal uses).
    """
    x = np.ascontiguousarray(nodes[..., 0])
    y = np.ascontiguousarray(nodes[..., 1])
    for _ in range(s.spring_passes_per_node * s.n_nodes):
        bx, by = x[:, :-1] - x[:, 1:], y[:, :-1] - y[:, 1:]
        length = np.maximum(np.sqrt(bx * bx + by * by), 1e-12)
        c = -s.k_spring * s.dt * (length - s.node_spacing) / length
        x[:, :-1] += c * bx
        x[:, 1:] -= c * bx
        y[:, :-1] += c * by
        y[:, 1:] -= c * by
    nodes[..., 0], nodes[..., 1] = x, y
    return head_direction(nodes) if len(nodes) else np.zeros((0, 2))


# copied from paper-reproduction/functions.py:rotate_heads
def rotate_heads(nodes, angle, which):
    """Turn the head disc about disc 1 by `angle` (radians), for the cells in `which`."""
    if not np.any(which):
        return
    v = nodes[which, 0] - nodes[which, 1]
    c, s = np.cos(angle[which]), np.sin(angle[which])
    nodes[which, 0] = nodes[which, 1] + np.stack([c * v[:, 0] - s * v[:, 1],
                                                  s * v[:, 0] + c * v[:, 1]], axis=1)


def reverse(nodes, flip):
    """Swap head and tail of the reversing cells: the old tail becomes the leading pole."""
    nodes[flip] = nodes[flip, ::-1]


# copied from paper-reproduction/engine.py (step 5)
def wrap_cells(nodes, box):
    """Shift each whole cell so its head is inside the box (discs are never split up)."""
    nodes -= np.floor(nodes[:, :1] / box) * box


def split_cell(nodes_one, s):
    """Body of a newborn daughter: a copy of the mother shifted 0.8 µm sideways.

    Repulsion then pushes the two apart. Used at division (milestone 6).
    """
    axis = geo.unit(nodes_one[0] - nodes_one[-1])
    side = np.array([-axis[1], axis[0]])
    return nodes_one + 0.8 * side
