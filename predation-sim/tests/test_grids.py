"""Checks for grids.py: reading and writing squares, spreading, fading, regrowing, smoothing."""
import numpy as np

import grids


def test_make_grid_fits_the_box_exactly():
    """500 µm at about 0.3 µm per square gives 1,667 squares of 0.29994 µm."""
    grid, spacing = grids.make_grid(500.0, 0.3)
    assert grid.shape == (1667, 1667)
    assert np.isclose(spacing * 1667, 500.0)


def test_deposit_adds_repeats_and_sample_reads_them_back():
    """Two deposits on the same square add up; sampling returns the total."""
    grid, _ = grids.make_grid(10.0, 1.0)
    pts = np.array([[2.5, 3.5], [2.2, 3.9], [7.0, 1.0]])
    grids.deposit(grid, pts, np.array([1.0, 2.0, 5.0]), 10.0)
    assert np.allclose(grids.sample(grid, pts, 10.0), [3.0, 3.0, 5.0])
    assert np.isclose(grid.sum(), 8.0)


def test_cell_index_wraps_outside_points():
    """A point just left of the box lands in the last column."""
    ix, iy = grids.cell_index(np.array([[-0.5, 10.5]]), 10.0, 10)
    assert (ix[0], iy[0]) == (9, 0)


def test_diffuse_conserves_total_and_spreads_like_a_gaussian():
    """A spike keeps its total and spreads with variance 2·D·t along each axis."""
    grid, spacing = grids.make_grid(100.0, 1.0)
    grid[50, 50] = 1.0
    out = grids.diffuse(grid, D=2.0, dt=5.0, spacing=spacing)
    assert np.isclose(out.sum(), 1.0)
    x = np.arange(100) - 50
    var_x = (out.sum(axis=1) * x ** 2).sum()
    assert np.isclose(var_x, 2 * 2.0 * 5.0, rtol=0.05)


def test_spreading_never_makes_negative_amounts():
    """Raw FFT spreading of one spike leaves ±1e-17 errors in ~40% of squares; the map we keep
    must be 0 or above everywhere, with the total unchanged (B73)."""
    g = np.zeros((150, 150))
    g[40, 40] = 25.0
    out = grids.diffuse(g, 5.0, 1.0, 1.0)
    assert out.min() >= 0.0
    assert np.isclose(out.sum(), 25.0)


def test_diffuse_with_zero_time_changes_nothing():
    """No time, no spreading."""
    grid = np.random.default_rng(0).random((20, 20))
    assert np.allclose(grids.diffuse(grid, 5.0, 0.0, 1.0), grid)


def test_fade_and_regrow():
    """Fading halves after one half-life; regrowth approaches each square's own maximum."""
    g = np.ones((4, 4))
    grids.fade(g, fade_time=10.0 / np.log(2), dt=10.0)
    assert np.allclose(g, 0.5)
    ceiling = np.full((4, 4), 0.7)
    n = np.zeros((4, 4))
    grids.regrow(n, ceiling, rate=1.0, dt=50.0)
    assert np.allclose(n, 0.7)
    n[:] = 0.0
    grids.regrow(n, ceiling, rate=1.0, dt=np.log(2))
    assert np.allclose(n, 0.35)        # half way after one 'half-life' of regrowth


def test_disc_average_keeps_uniform_maps_and_totals():
    """Averaging a flat map changes nothing; averaging a spike spreads it over the disc."""
    flat = np.full((50, 50), 0.4)
    assert np.allclose(grids.disc_average(flat, 3.0, 1.0), 0.4)
    spike = np.zeros((50, 50))
    spike[10, 10] = 1.0
    out = grids.disc_average(spike, 3.0, 1.0)
    assert np.isclose(out.sum(), 1.0)
    assert out[10, 10] > 0 and np.isclose(out[10, 14], 0.0, atol=1e-12)


def test_random_patches_stay_in_range_and_are_smooth():
    """Patches span exactly [lo, hi], and neighbouring squares differ only a little."""
    rng = np.random.default_rng(1)
    p = grids.random_patches(150, 1.0, 30.0, 0.3, 1.0, rng)
    assert np.isclose(p.min(), 0.3) and np.isclose(p.max(), 1.0)
    jump = np.abs(np.diff(p, axis=0)).mean()
    assert jump < 0.05 * (1.0 - 0.3)


def test_gradient_of_a_wave():
    """The slope of sin(2πx/L) matches its derivative (2π/L)·cos(2πx/L)."""
    L, n = 100.0, 100
    x = (np.arange(n) + 0.5) * (L / n)
    grid = np.repeat(np.sin(2 * np.pi * x / L)[:, None], n, axis=1)
    pts = np.array([[x[10], 5.0], [x[60], 5.0]])
    g = grids.gradient(grid, pts, L, L / n)
    expected = (2 * np.pi / L) * np.cos(2 * np.pi * pts[:, 0] / L)
    assert np.allclose(g[:, 0], expected, rtol=0.01)
    assert np.allclose(g[:, 1], 0.0)
