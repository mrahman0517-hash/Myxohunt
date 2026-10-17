"""
grids.py — everything about the ground maps: finding squares, adding to them, reading them,
spreading, fading, regrowing and smoothing. No biology here.

Every grid is square and wraps around at the edges, like the world. Indexing is grid[ix, iy]
with x first. Spreading and smoothing use the fast Fourier transform (FFT): it treats the map
as wrap-around automatically and stays stable for any time step (B37).
"""
from functools import lru_cache

import numpy as np


# ---------------------------------------------------------------- squares
def make_grid(box, spacing):
    """An empty square grid whose squares fit the box exactly.

    Args:
        box: side of the world (µm).
        spacing: wanted square size (µm); adjusted slightly so n squares fill the box.
    Returns:
        (grid of zeros (n, n), true spacing in µm).
    """
    n = int(round(box / spacing))
    return np.zeros((n, n)), box / n


def cell_index(points, box, n):
    """Which square each point falls in, wrapping points that lie outside the box.

    Args:
        points: (P, 2) positions (µm).
        box: side of the world (µm).
        n: squares per side.
    Returns:
        ix, iy: (P,) integer square indices.
    """
    size = box / n
    ix = np.floor(np.mod(points[:, 0], box) / size).astype(np.int64) % n
    iy = np.floor(np.mod(points[:, 1], box) / size).astype(np.int64) % n
    return ix, iy


def sample(grid, points, box):
    """Value of the square under each point (P,)."""
    ix, iy = cell_index(points, box, grid.shape[0])
    return grid[ix, iy]


def deposit(grid, points, amounts, box):
    """Add `amounts` (one number, or one per point) to the squares under the points.

    Uses np.add.at, so two points on the same square both count.
    """
    ix, iy = cell_index(points, box, grid.shape[0])
    np.add.at(grid, (ix, iy), amounts)


@lru_cache(maxsize=16)
def disc_offsets(radius, spacing):
    """Square offsets (dx, dy) covering a disc of `radius` µm on a grid of `spacing` (cached)."""
    r = max(int(np.floor(radius / spacing)), 0)
    dx, dy = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1), indexing="ij")
    keep = (dx ** 2 + dy ** 2) * spacing ** 2 <= radius ** 2
    return dx[keep], dy[keep]


def disc_squares(grid, points, box, radius, spacing):
    """The squares within `radius` µm of each point and their values.

    Returns:
        flat (P, K) flat square indices (ix·n + iy) and values (P, K).
    """
    n = grid.shape[0]
    dx, dy = disc_offsets(float(radius), float(spacing))
    ix, iy = cell_index(points, box, n)
    sx, sy = (ix[:, None] + dx[None]) % n, (iy[:, None] + dy[None]) % n
    return sx * n + sy, grid[sx, sy]


# ---------------------------------------------------------------- slow changes
def fade(grid, fade_time, dt):
    """Shrink every square by the same factor, exp(−dt/fade_time), in place."""
    grid *= np.exp(-dt / fade_time)


def regrow(grid, ceiling, rate, dt):
    """Move each square toward its own maximum: fast when far below it, levelling off at it.

    Exact solution of dN/dt = rate·(ceiling − N) over dt (B33, B48). In place.
    """
    grid[...] = ceiling - (ceiling - grid) * np.exp(-rate * dt)


# ---------------------------------------------------------------- spreading (diffusion)
@lru_cache(maxsize=32)
def _diffusion_kernel(n, spacing, d_times_t):
    """Fourier-space factor exp(−D·k²·t) for an n×n wrap-around grid (cached)."""
    k = 2 * np.pi * np.fft.fftfreq(n, d=spacing)
    k_half = 2 * np.pi * np.fft.rfftfreq(n, d=spacing)
    k2 = k[:, None] ** 2 + k_half[None, :] ** 2
    return np.exp(-d_times_t * k2)


def diffuse(grid, D, dt, spacing):
    """Spread a map the way a dissolved substance spreads, for time dt.

    Exact for wrap-around maps and stable for any dt; the total amount is unchanged.
    The FFT leaves rounding errors of about ±1e-17 in every square. Amounts can never be
    negative, so the negative errors are set to 0 (B73: they once let cells eat "negative food").

    Args:
        grid: (n, n) map.
        D: diffusion coefficient (µm²/min).
        dt: time (min).
        spacing: square size (µm).
    Returns:
        A new (n, n) map, never negative.
    """
    if D * dt <= 0:
        return grid.copy()
    kernel = _diffusion_kernel(grid.shape[0], float(spacing), float(D * dt))
    return np.maximum(np.fft.irfft2(np.fft.rfft2(grid) * kernel, s=grid.shape), 0.0)


# ---------------------------------------------------------------- smoothing over a disc
@lru_cache(maxsize=32)
def _disc_kernel_fft(n, spacing, radius):
    """Fourier transform of a disc of the given radius, normalised to sum 1 (cached)."""
    offsets = np.fft.fftfreq(n, d=1.0 / n) * spacing          # signed distances, wrap-around
    dist2 = offsets[:, None] ** 2 + offsets[None, :] ** 2
    disc = (dist2 <= radius ** 2).astype(float)
    return np.fft.rfft2(disc / disc.sum())


def disc_average(grid, radius, spacing):
    """Average of each square's surroundings within `radius` µm (wrap-around) (B43).

    Args:
        grid: (n, n) map.
        radius: averaging radius (µm).
        spacing: square size (µm).
    Returns:
        A new (n, n) map; a uniform map stays unchanged and the total is preserved.
    """
    kernel = _disc_kernel_fft(grid.shape[0], float(spacing), float(radius))
    return np.fft.irfft2(np.fft.rfft2(grid) * kernel, s=grid.shape)


def random_patches(n, spacing, patch_size, lo, hi, rng):
    """A smooth random map of rich and poor patches, scaled to [lo, hi] (B48).

    White noise is averaged over discs of diameter `patch_size`, then stretched so the
    poorest square is `lo` and the richest is `hi`.
    """
    smooth = disc_average(rng.random((n, n)), 0.5 * patch_size, spacing)
    span = smooth.max() - smooth.min()
    if span == 0:
        return np.full((n, n), 0.5 * (lo + hi))
    return lo + (smooth - smooth.min()) / span * (hi - lo)


# ---------------------------------------------------------------- slopes
def gradient(grid, points, box, spacing):
    """Slope of the map at each point's square, by central differences (wrap-around).

    Args:
        grid: (n, n) map.
        points: (P, 2) positions (µm).
        box: side of the world (µm).
        spacing: square size (µm).
    Returns:
        (P, 2) slope (map units per µm) in x and y.
    """
    n = grid.shape[0]
    ix, iy = cell_index(points, box, n)
    gx = (grid[(ix + 1) % n, iy] - grid[(ix - 1) % n, iy]) / (2 * spacing)
    gy = (grid[ix, (iy + 1) % n] - grid[ix, (iy - 1) % n]) / (2 * spacing)
    return np.stack([gx, gy], axis=1)
