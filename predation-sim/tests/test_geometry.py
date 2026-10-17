"""Checks for geometry.py: wrap-around distances, rod points and the ripple-axis encoding."""
import numpy as np

import geometry as geo


def test_min_image_takes_the_short_way_round():
    """Two points near opposite edges of a 100 µm box are 2 µm apart, not 98."""
    d = geo.min_image(np.array([[98.0, -99.0]]), 100.0)
    assert np.allclose(d, [[-2.0, 1.0]])


def test_wrap_points_folds_into_the_box():
    """Positions outside [0, box) come back in from the other side; box itself becomes 0."""
    p = np.array([[-1.0, 101.0], [100.0, 50.0]])
    assert np.allclose(geo.wrap_points(p, 100.0), [[99.0, 1.0], [0.0, 50.0]])


def test_rod_points_span_the_rod_exactly():
    """End points sit half a width in from the tips, evenly spaced, centred on the rod."""
    pts = geo.rod_points(np.array([[10.0, 10.0]]), np.array([0.0]), np.array([3.0]), 5, 1.0)
    xs = pts[0, :, 0]
    assert np.allclose(xs, [9.0, 9.5, 10.0, 10.5, 11.0])   # ±(3 − 1)/2 around the centre
    assert np.allclose(pts[0, :, 1], 10.0)


def test_rod_points_follow_the_angle():
    """A rod pointing straight up has its points stacked vertically."""
    pts = geo.rod_points(np.zeros((1, 2)), np.array([np.pi / 2]), np.array([2.0]), 3, 1.0)
    assert np.allclose(pts[0, :, 0], 0.0, atol=1e-12)
    assert np.allclose(pts[0, :, 1], [-0.5, 0.0, 0.5])


def test_axis_encoding_treats_opposite_directions_as_one_line():
    """10° and 190° are the same line: their doubled angles add up instead of cancelling."""
    thetas = np.radians([10.0, 190.0])
    c, s = np.cos(2 * thetas).sum(), np.sin(2 * thetas).sum()
    assert np.isclose(np.degrees(geo.axis_from_fields(c, s)), 10.0)


def test_axis_encoding_blends_two_colonies():
    """Equal matrix from colonies at 0° and 60° blends to a 30° line (the figure in the chat)."""
    thetas = np.radians([0.0, 60.0])
    c, s = np.cos(2 * thetas).sum(), np.sin(2 * thetas).sum()
    assert np.isclose(np.degrees(geo.axis_from_fields(c, s)), 30.0)
