"""
functions.py — the model's rules as plain functions.

Each function takes arrays in and gives arrays (or a number) back. None of them
knows about the time loop; engine.py decides the order. Shapes:
  N = number of cells, n = discs per cell (10), nodes has shape (N, n, 2).
"""
import numpy as np
from scipy.spatial import cKDTree


# ---------------------------------------------------------------- geometry
def unit(v):
    """Scale vectors (…, 2) to length 1."""
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def head_direction(nodes):
    """Direction the cell is heading: from disc 1 towards disc 0 (the head)."""
    return unit(nodes[:, 0] - nodes[:, 1])


def angle_of(vec):
    return np.arctan2(vec[..., 1], vec[..., 0])


def wrap_angle(a):
    """Bring angles into (-π, π]."""
    return (a + np.pi) % (2 * np.pi) - np.pi


def min_image(d, box):
    """Shortest separation across the periodic box edges."""
    return d - box * np.round(d / box)


# ---------------------------------------------------------------- body & motion (§3.5)
def traction(nodes, heading, p):
    """
    Pull the head disc forward. The pull is speed × N_D, but the springs then
    share that displacement with all 10 discs (spring pushes are equal and
    opposite), so the cell's centre moves at exactly `speed`.
    """
    nodes[:, 0] += p.speed * p.traction_scale * heading * p.dt


def repulsion(nodes, box, p):
    """
    Push apart discs of different cells (and non-neighbouring discs of the same
    cell) that are closer than one disc diameter D. Push size:
        (D − r)² / max(r − 0.9 D, 2 / k_r)       [code]
    """
    N, n, _ = nodes.shape
    flat = nodes.reshape(-1, 2)
    wrapped = np.mod(flat, box)
    wrapped[wrapped >= box] = 0.0                      # guard float edge case
    pairs = cKDTree(wrapped, boxsize=box).query_pairs(p.disc_diam, output_type="ndarray")
    if len(pairs) == 0:
        return
    a, b = pairs[:, 0], pairs[:, 1]
    same_neighbour = (a // n == b // n) & (np.abs(a - b) == 1)   # bonded discs: springs handle them
    a, b = a[~same_neighbour], b[~same_neighbour]
    d = min_image(wrapped[a] - wrapped[b], box)
    r = np.maximum(np.linalg.norm(d, axis=1), 1e-9)
    D = p.disc_diam
    push = (D - r) ** 2 / np.maximum(r - 0.9 * D, 2.0 / p.k_rep) * p.dt
    step = d / r[:, None] * push[:, None]              # direction a <- b
    disp = np.zeros_like(flat)
    for k in range(2):
        disp[:, k] += np.bincount(a, weights=step[:, k], minlength=len(flat))
        disp[:, k] -= np.bincount(b, weights=step[:, k], minlength=len(flat))
    nodes += disp.reshape(N, n, 2)


def relax_springs(nodes, p):
    """
    Pull each pair of neighbouring discs back towards spacing ε. Repeated
    5·N_D times per step so the chain is nearly at rest length afterwards.
    Returns the heading after relaxation (what the frustration signal uses).
    """
    x = np.ascontiguousarray(nodes[..., 0])            # separate x and y arrays are faster
    y = np.ascontiguousarray(nodes[..., 1])
    for _ in range(p.spring_passes_per_node * p.n_nodes):
        bx, by = x[:, :-1] - x[:, 1:], y[:, :-1] - y[:, 1:]   # bonds point towards the head
        length = np.sqrt(bx * bx + by * by)
        c = -p.k_spring * p.dt * (length - p.node_spacing) / length
        x[:, :-1] += c * bx
        x[:, 1:] -= c * bx
        y[:, :-1] += c * by
        y[:, 1:] -= c * by
    nodes[..., 0], nodes[..., 1] = x, y
    return head_direction(nodes)


def rotate_heads(nodes, angle, which):
    """Turn the head disc about disc 1 by `angle` (radians), for cells in `which`."""
    if not np.any(which):
        return
    v = nodes[which, 0] - nodes[which, 1]
    c, s = np.cos(angle[which]), np.sin(angle[which])
    nodes[which, 0] = nodes[which, 1] + np.stack([c * v[:, 0] - s * v[:, 1],
                                                  s * v[:, 0] + c * v[:, 1]], axis=1)


# ---------------------------------------------------------------- alignment (§3.5, H3)
def ripple_turn(theta, p):
    """Δθ = γ' · sin 2(θ0 − θ) · Δt. The 2 makes θ0 and θ0+π equally good."""
    return p.gamma_ripple * np.sin(2.0 * (p.ripple_axis - theta)) * p.dt


def eps_lay(field, tails, p):
    """Every swarming cell adds a·v·Δt of EPS under its rear disc."""
    n = field.grid.shape[0]
    ix = np.floor(np.mod(tails[:, 0], n * field.spacing) / field.spacing).astype(int) % n
    iy = np.floor(np.mod(tails[:, 1], n * field.spacing) / field.spacing).astype(int) % n
    np.add.at(field.grid, (ix, iy), p.eps_deposit * p.speed * p.dt)


HEADING_BINS = 1440   # headings rounded to 0.25° when looking up wedges (pure speed-up)


def sensing_offsets(field, p):
    """
    Computed once: the grid squares inside the sensing disc (radius H) and, for
    every possible heading, which of the 5 wedges each square falls in
    (-1 = behind the cell, outside the semicircle).
    """
    r = int(p.sense_radius / field.spacing)
    ox, oy = np.meshgrid(np.arange(-r, r + 1), np.arange(-r, r + 1), indexing="ij")
    ox, oy = ox.ravel(), oy.ravel()
    keep = (ox ** 2 + oy ** 2 <= r * r) & ((ox != 0) | (oy != 0))
    ox, oy = ox[keep], oy[keep]
    phi = np.arctan2(oy, ox)
    headings = np.arange(HEADING_BINS) * 2 * np.pi / HEADING_BINS
    rel = wrap_angle(phi[None, :] - headings[:, None])              # square's angle vs heading
    width = p.view_angle / p.n_sectors                               # π/5
    table = (np.rint(rel / width) + p.n_sectors // 2).astype(np.int8)
    table[np.abs(rel) > p.view_angle / 2] = -1
    return ox, oy, table


def eps_turn(field, heads, theta, offsets, p, rng):
    """
    Trail following (code mechanics):
      1. split the semicircle ahead of the head into 5 wedges and sum the EPS in each;
      2. if no square anywhere in the semicircle exceeds c_min, don't turn;
      3. among wedges holding ≥ 80% of the best wedge, pick the one nearest the heading;
      4. turn by Δθ = γ · sin 2(θ_wedge − θ) · Δt.
    """
    ox, oy, table = offsets
    N, n = len(theta), field.grid.shape[0]
    hx = np.floor(np.mod(heads[:, 0], n * field.spacing) / field.spacing).astype(int)
    hy = np.floor(np.mod(heads[:, 1], n * field.spacing) / field.spacing).astype(int)
    vals = field.grid[(hx[:, None] + ox[None]) % n, (hy[:, None] + oy[None]) % n]   # (N, squares)

    hbin = np.rint(np.mod(theta, 2 * np.pi) / (2 * np.pi) * HEADING_BINS).astype(int) % HEADING_BINS
    sector = table[hbin]                                             # (N, squares), -1 = behind
    ahead = sector >= 0
    rows = np.broadcast_to(np.arange(N)[:, None], sector.shape)
    sums = np.bincount((rows * p.n_sectors + sector)[ahead], weights=vals[ahead],
                       minlength=N * p.n_sectors).reshape(N, p.n_sectors)
    peak = np.where(ahead, vals, 0.0).max(axis=1)

    width = p.view_angle / p.n_sectors
    offsets_k = (np.arange(p.n_sectors) - p.n_sectors // 2) * width  # wedge centres vs heading
    good = sums >= p.eps_choice_tolerance * sums.max(axis=1, keepdims=True)
    closeness = np.abs(offsets_k)[None, :] * (1 + rng.uniform(-1e-3, 1e-3, size=sums.shape))
    chosen = offsets_k[np.argmin(np.where(good, closeness, np.inf), axis=1)]
    sees_trail = peak >= p.eps_c_min                                 # code: max < EPS_max/100 -> no turn
    return np.where(sees_trail, p.gamma_eps * np.sin(2.0 * chosen) * p.dt, 0.0)


# ---------------------------------------------------------------- reversal signal (§3.4)
def frustration(v_target, v_real):
    """f = 1 − (v_t · v_r) / max(|v_t|², |v_r|²). 0 = moving as intended, 2 = pushed backwards."""
    dot = np.einsum("ij,ij->i", v_target, v_real)
    denom = np.maximum(np.einsum("ij,ij->i", v_target, v_target),
                       np.einsum("ij,ij->i", v_real, v_real))
    return 1.0 - dot / np.maximum(denom, 1e-12)


def memory_weights(p):
    """Weights e^(−β(k+1)Δt) for lags k = 0…K−1, and the rescaling 2·Σw (so s lands in 0–1)."""
    K = int(p.memory / p.dt)
    w = np.exp(-p.beta * (np.arange(K) + 1) * p.dt)
    return w, 2.0 * w.sum()


def smoothed_signal(memory, slot, weights, norm):
    """Weighted average of the last K frustration values; the newest sits in `slot`."""
    K = memory.shape[1]
    lag_of_slot = (slot - np.arange(K)) % K          # how many steps ago each slot was written
    return memory @ weights[lag_of_slot] / norm


# ---------------------------------------------------------------- reversal rule (§3.5, H1+H2)
def refractory_period(s, p):
    """T_RP(s) = R* − (R* − R_min) / (1 + exp[−α_R (s − f_T)])"""
    return p.R_star - (p.R_star - p.R_min) / (1.0 + np.exp(-p.alpha_R * (s - p.f_T)))


def reversal_rate(s, p):
    """T_REV⁻¹(s) = F* / (1 + exp[−α_F (s − f_T)])"""
    return p.F_star / (1.0 + np.exp(-p.alpha_F * (s - p.f_T)))


def reversal_probability(age, s, p):
    """
    Chance of reversing during this step. Zero inside the refractory period;
    after it, the code form (1 − exp[−rate]) · Δt  (decision 2: reproduce their figures).
    """
    past_rp = age > refractory_period(s, p)
    return np.where(past_rp, (1.0 - np.exp(-reversal_rate(s, p))) * p.dt, 0.0)


# ---------------------------------------------------------------- measurements (§3.6)
def cell_axis_and_centre(nodes, box):
    """Orientation (head minus tail) and centre of each cell, centre wrapped into the box."""
    axis = angle_of(nodes[:, 0] - nodes[:, -1])
    centre = np.mod(nodes.mean(axis=1), box)
    return axis, centre


def nematic_order(centre, axis, box, edges):
    """
    O(r) = ⟨ (1/N_i(r)) Σ_j [2 cos²(θ_i − θ_j) − 1] ⟩_i over neighbours in each distance ring.
    1 = parallel or antiparallel, 0 = random.
    """
    d = min_image(centre[:, None, :] - centre[None, :, :], box)
    dist = np.linalg.norm(d, axis=-1)
    np.fill_diagonal(dist, np.inf)
    align = 2.0 * np.cos(axis[:, None] - axis[None, :]) ** 2 - 1.0
    out = np.full(len(edges) - 1, np.nan)
    for k in range(len(edges) - 1):
        ring = (dist >= edges[k]) & (dist < edges[k + 1])
        counts = ring.sum(axis=1)
        has = counts > 0
        if has.any():
            out[k] = (np.where(ring, align, 0.0).sum(axis=1)[has] / counts[has]).mean()
    return out


def quartile_fractions(samples, rev_cell, rev_signal):
    """
    For each cell, split its own signal history into quartiles, then count which
    quartile each of its reversals fell in (§3.4). Returns 4 fractions, low → high.
    """
    q = np.percentile(samples, [25, 50, 75], axis=0)   # samples: (n_times, N)
    counts = np.zeros(4)
    for c, s in zip(rev_cell, rev_signal):
        counts[np.searchsorted(q[:, c], s)] += 1
    return counts / max(counts.sum(), 1)
