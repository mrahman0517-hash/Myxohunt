"""
seeding.py — the starting world and newcomers: patchy ground filled to random levels, the first
E. coli seeds, a new E. coli founder every ecoli_seed_interval at a random spot (B75, B78), and
Myxo seeds coming in from outside at random times within myxo_arrival_window (B78).
"""
import numpy as np

import counters
import geometry as geo
import grids
import state


# ---------------------------------------------------------------- ground
def initial_ground(world):
    """Lay down rich and poor patches (each square's own maximum, B48) and fill each patch to a
    random share of its maximum, so the ground starts uneven and refills over time (B78)."""
    s, f = world.settings, world.fields
    n = f.richness.shape[0]
    f.richness = grids.random_patches(n, f.spacing, s.patch_size, s.richness_min, s.richness_max, world.rng)
    fill = grids.random_patches(n, f.spacing, s.patch_size, s.nutrient_start_min, s.nutrient_start_max,
                                world.rng)
    f.nutrients = f.richness * fill


# ---------------------------------------------------------------- E. coli
def divide_lengths(world, k):
    """Length at which each of k newborn E. coli will divide: 4 µm ± 10%, never below 1.5× birth size (B5, B53)."""
    s = world.settings
    lengths = s.ecoli_divide_length + s.ecoli_divide_noise * world.rng.standard_normal(k)
    return np.maximum(lengths, 1.5 * s.ecoli_birth_length)


def speed_factors(world, k):
    """Each of k newborn E. coli's own growth speed: about 1 ± 20%, kept within 0.4–1.6 (B55).

    Drawn fresh at every birth: real cells don't inherit their mother's growth speed.
    """
    s = world.settings
    return np.clip(1.0 + s.ecoli_speed_noise * world.rng.standard_normal(k), 0.4, 1.6)


def persister_flags(world, k):
    """Whether each of k newborn E. coli is a long-term survivor that never starves (5%, B40, B88).

    Drawn fresh at every birth: surviving starvation is chance for each cell, not inherited, so
    every colony keeps about 5% survivors.
    """
    return world.rng.random(k) < world.settings.persister_fraction


def new_colony(world):
    """Start a new colony: give it an ID and its own random ripple direction (B13)."""
    world.colony_axis.append(world.rng.uniform(0.0, np.pi))
    return len(world.colony_axis) - 1


def ecoli_seed(world, position):
    """One newborn E. coli at `position`, founding a new colony, pointing in a random direction."""
    s, rng = world.settings, world.rng
    return state.EColiCells(
        centre=np.asarray(position, dtype=float).reshape(1, 2), angle=rng.uniform(0, 2 * np.pi, 1),
        length=np.array([s.ecoli_birth_length]), colony=np.array([new_colony(world)], dtype=np.int64),
        dormant=np.zeros(1, dtype=bool), starve_time=np.zeros(1),
        persister=persister_flags(world, 1), lysis_timer=np.full(1, -1.0),
        divide_at=divide_lengths(world, 1), speed_factor=speed_factors(world, 1),
        uid=state.new_uids(world, 1))


def far_enough(point, others, min_dist, box):
    """True if `point` is at least `min_dist` µm from every point in `others` (wrap-around)."""
    if len(others) == 0:
        return True
    d = np.linalg.norm(geo.min_image(np.asarray(others) - point, box), axis=1)
    return bool(d.min() >= min_dist)


def initial_ecoli(world, tries=200):
    """Place the starting E. coli seeds at random, at least seed_min_dist_ecoli apart (B44)."""
    _place_ecoli(world, tries)


def add_due_founder(world):
    """Every ecoli_seed_interval bio min a single new E. coli lands at a random spot, founding a
    new colony; there are no placement rules (B75, B78). An interval of 0 means none: the app's
    switch can set it on a running world, so nothing lands then, and when it's switched back on the
    next founder comes one interval later (B97 fix)."""
    interval = world.settings.ecoli_seed_interval
    if interval <= 0:
        world.next_ecoli_seed = float("inf")
        return
    if world.next_ecoli_seed == float("inf"):
        world.next_ecoli_seed = world.bio_t + interval
    if world.bio_t < world.next_ecoli_seed:
        return
    point = world.rng.uniform(0, world.settings.box, 2)
    state.append_rows(world.ecoli, ecoli_seed(world, point))
    world.next_ecoli_seed = world.bio_t + world.settings.ecoli_seed_interval
    counters.add(world, "ecoli_founders")


# ---------------------------------------------------------------- Myxo
def make_myxo(world, starts, headings):
    """Straight 10-disc Myxo cells starting at `starts` and lying along `headings` (k cells).

    Clocks start at random between 0 and R* (staggered, as in the authors' code); food store
    at energy_start (B20); empty frustration memory; not paused.
    """
    s, rng, k = world.settings, world.rng, len(starts)
    steps = np.arange(s.n_nodes) * s.node_spacing
    direction = np.stack([np.cos(headings), np.sin(headings)], axis=1)
    nodes = starts[:, None, :] + steps[None, :, None] * direction[:, None, :]
    return state.MyxoCells(
        nodes=nodes, age=rng.integers(0, int(s.R_star / s.dt), size=k) * s.dt,
        memory=np.zeros((k, s.memory_length)), mem_slot=np.zeros(k, dtype=np.int64),
        signal=np.zeros(k), energy=np.full(k, s.energy_start), pause_left=np.zeros(k),
        pause_target=np.full(k, -1, dtype=np.int64), scout=np.zeros(k, dtype=bool),
        starve_time=np.zeros(k), uid=state.new_uids(world, k))


def myxo_group(world, centre, size):
    """A drop of `size` Myxo cells within myxo_group_radius of `centre`, roughly aligned (B8).

    They share a random direction ±20°, and each points either way along it.
    """
    s, rng = world.settings, world.rng
    r = s.myxo_group_radius * np.sqrt(rng.random(size))
    phi = rng.uniform(0, 2 * np.pi, size)
    starts = centre + np.stack([r * np.cos(phi), r * np.sin(phi)], axis=1)
    headings = (rng.uniform(0, np.pi) + np.radians(20) * rng.uniform(-1, 1, size)
                + np.pi * rng.integers(0, 2, size))
    return make_myxo(world, starts, headings)


def seed_clearance(s):
    """How far a seed's centre must stay from every E. coli so that every disc of every cell in
    the group starts at least myxo_min_dist_colony away: that gap, plus the group's radius, plus
    one body length (B47, B72)."""
    return s.myxo_min_dist_colony + s.myxo_group_radius + (s.n_nodes - 1) * s.node_spacing


def myxo_spot(world, tries=200):
    """A random spot far enough from every E. coli that no cell of the seed starts within
    myxo_min_dist_colony of one (B47); if none is found within `tries`, the farthest spot tried."""
    s, centres = world.settings, world.ecoli.centre
    best, best_d = None, -1.0
    for _ in range(tries):
        point = world.rng.uniform(0, s.box, 2)
        if len(centres) == 0:
            return point
        d = np.linalg.norm(geo.min_image(centres - point, s.box), axis=1).min()
        if d >= seed_clearance(s):
            return point
        if d > best_d:
            best, best_d = point, d
    return best


def initial_myxo(world):
    """Schedule the Myxo seeds (B8, B50, B78): each group and single cell comes in from outside
    at a random time within myxo_arrival_window. Seeds due at time 0 are placed at once."""
    s = world.settings
    sizes = [s.myxo_group_size] * s.myxo_groups + [1] * s.myxo_singles
    times = world.rng.uniform(0.0, s.myxo_arrival_window, len(sizes)) if s.myxo_arrival_window > 0         else np.zeros(len(sizes))
    world.myxo_arrivals = sorted(zip(times.tolist(), sizes))
    add_due_myxo(world)


def add_due_myxo(world):
    """Place every Myxo seed whose arrival time has come, at a random spot that keeps every one of
    its cells at least myxo_min_dist_colony from the E. coli (B47, B72, B78)."""
    while world.myxo_arrivals and world.myxo_arrivals[0][0] <= world.bio_t:
        _, size = world.myxo_arrivals.pop(0)
        add_myxo(world, myxo_group(world, myxo_spot(world), size))


def add_myxo(world, cells):
    """Put newcomer Myxo into the world, counting them and their stores (B97). Every way Myxo come
    in (arrivals, the test boxes, the attack drops) goes through here."""
    state.append_rows(world.myxo, cells)
    counters.add(world, "myxo_arrived", state.count(cells))
    counters.add(world, "store_arrived", cells.energy.sum())


def uniform_myxo(world, n, aligned_axis=None):
    """For validation runs: n cells at random positions, random headings or along one axis
    (half each way), like the paper-reproduction quick tests."""
    s, rng = world.settings, world.rng
    starts = rng.uniform(0, s.box, size=(n, 2))
    if aligned_axis is None:
        headings = rng.uniform(0, 2 * np.pi, n)
    else:
        headings = aligned_axis + np.pi * rng.integers(0, 2, n)
    add_myxo(world, make_myxo(world, starts, headings))


def _place_ecoli(world, tries):
    """Pick start_colonies random spots at least seed_min_dist_ecoli apart and seed one E. coli on each."""
    s, chosen = world.settings, []
    for _ in range(s.start_colonies):
        for _ in range(tries):
            point = world.rng.uniform(0, s.box, 2)
            if far_enough(point, chosen, s.seed_min_dist_ecoli, s.box):
                chosen.append(point)
                break
    for point in chosen:
        state.append_rows(world.ecoli, ecoli_seed(world, point))
