"""
geometry.py — small maths helpers for directions, angles and the wrap-around box.
No biology here.
"""
import numpy as np


# copied from paper-reproduction/functions.py:unit
def unit(v):
    """Scale vectors (…, 2) to length 1."""
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


# copied from paper-reproduction/functions.py:angle_of
def angle_of(vec):
    """Direction of each vector (…, 2), in radians."""
    return np.arctan2(vec[..., 1], vec[..., 0])


# copied from paper-reproduction/functions.py:wrap_angle
def wrap_angle(a):
    """Bring angles into (−π, π]."""
    return (a + np.pi) % (2 * np.pi) - np.pi


# copied from paper-reproduction/functions.py:min_image
def min_image(d, box):
    """Shortest separation across the wrap-around edges of the box."""
    return d - box * np.round(d / box)


def wrap_points(p, box):
    """Fold positions back into [0, box), so a cell leaving one side re-enters the other.

    Args:
        p: (…, 2) positions in µm.
        box: side of the square world in µm.
    Returns:
        (…, 2) positions inside [0, box). A value that rounds to exactly `box` becomes 0.
    """
    folded = np.mod(p, box)
    return np.where(folded >= box, 0.0, folded)


def rod_points(centre, angle, length, k, width):
    """k evenly spaced points along each E. coli rod, used to find contacts.

    Each point is the centre of a disc as wide as the rod, so the end points sit half a
    width in from the tips: the rod then spans exactly `length` from tip to tip.

    Args:
        centre: (M, 2) rod centres (µm).
        angle: (M,) rod directions (rad).
        length: (M,) tip-to-tip lengths (µm).
        k: number of points per rod.
        width: rod width (µm).
    Returns:
        (M, k, 2) point positions (not wrapped).
    """
    direction = np.stack([np.cos(angle), np.sin(angle)], axis=1)        # (M, 2)
    half_span = 0.5 * np.maximum(length - width, 0.0)                    # (M,)
    steps = np.linspace(-1.0, 1.0, k)                                    # (k,)
    offsets = (half_span[:, None] * steps[None, :])[:, :, None] * direction[:, None, :]
    return centre[:, None, :] + offsets


def axis_from_fields(c, s):
    """Ripple axis (a line, not an arrow) from the doubled-angle sums: ½·atan2(s, c) (B38).

    Args:
        c, s: arrays of matrix-weighted sums of cos 2θ and sin 2θ.
    Returns:
        Axis angles in (−π/2, π/2]; a line at θ and at θ + π is the same line.
    """
    return 0.5 * np.arctan2(s, c)
