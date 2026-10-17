"""
state.py — what the simulation remembers: the two cell "spreadsheets", the ground maps,
and the World that holds them. No biology happens here.

Cells are stored as arrays with one row per cell (build manual §3). Rows are added and
removed only through append_rows and keep_rows, so every column stays in step.
"""
from dataclasses import dataclass, field, fields

import numpy as np

import grids
from settings import Settings


@dataclass
class MyxoCells:
    """All Myxo cells. N rows; disc 0 of `nodes` is the leading pole (head)."""
    nodes: np.ndarray         # (N, 10, 2) disc positions, not wrapped
    age: np.ndarray           # (N,) real min since the last reversal
    memory: np.ndarray        # (N, K) recent frustration values (ring buffer)
    mem_slot: np.ndarray      # (N,) int, newest slot in each cell's memory
    signal: np.ndarray        # (N,) smoothed frustration s, 0..1
    energy: np.ndarray        # (N,) food store, 0..210; 100 = a normal newborn (B75)
    pause_left: np.ndarray    # (N,) real min left in a killing pause, 0 = moving
    pause_target: np.ndarray  # (N,) int, uid of the E. coli being killed, -1 = none
    scout: np.ndarray         # (N,) bool, explores off-trail with A-motility (B67)
    starve_time: np.ndarray   # (N,) bio min since the cell's prey food ran out, 0 when fed (B75, B83)
    uid: np.ndarray           # (N,) int, permanent ID


@dataclass
class EColiCells:
    """All E. coli rods. M rows."""
    centre: np.ndarray        # (M, 2) rod centre, wrapped into the box
    angle: np.ndarray         # (M,) rod direction (rad)
    length: np.ndarray        # (M,) tip-to-tip length (µm)
    colony: np.ndarray        # (M,) int, colony ID
    dormant: np.ndarray       # (M,) bool, stopped growing for lack of food
    starve_time: np.ndarray   # (M,) bio min spent dormant
    persister: np.ndarray     # (M,) bool, never dies of starvation
    lysis_timer: np.ndarray   # (M,) -1 = alive, >= 0 = dead and intact, bio min until it bursts
    divide_at: np.ndarray     # (M,) length (µm) at which this cell divides, drawn at birth
    speed_factor: np.ndarray  # (M,) this cell's own growth speed (about 1 ± 0.1), drawn at birth
    uid: np.ndarray           # (M,) int, permanent ID, increasing


@dataclass
class Fields:
    """The ground maps. Indexing is grid[ix, iy], x first."""
    eps: np.ndarray           # fine grid: slime
    eps_scout: np.ndarray     # fine grid: slime laid by scouts (stronger, fades more slowly; B71)
    eps_spacing: float        # µm per fine square
    richness: np.ndarray      # coarse grid: fixed maximum nutrient level per spot
    nutrients: np.ndarray     # what E. coli eats now
    food: np.ndarray          # prey food: contents spilled by killed or burst E. coli
    scraps: np.ndarray        # what dead or lysed Myxo spill: keeps cells alive, never content (B83)
    attractant: np.ndarray    # lipid "smell" from lysis
    matrix: np.ndarray        # dead-prey cell wall
    matrix_smooth: np.ndarray  # prey material (ghosts + living prey) averaged around each square (ripple check, B76)
    axis_c: np.ndarray        # matrix-weighted sum of cos 2θ (ripple direction)
    axis_s: np.ndarray        # matrix-weighted sum of sin 2θ
    axis_c_smooth: np.ndarray  # cos 2θ sum of ghosts and living prey, averaged like matrix_smooth (B76)
    axis_s_smooth: np.ndarray  # sin 2θ sum, the same (B76)
    spacing: float            # µm per coarse square


@dataclass
class World:
    """Everything one simulation needs, in one place."""
    settings: Settings
    rng: np.random.Generator
    myxo: MyxoCells
    ecoli: EColiCells
    fields: Fields
    t: float = 0.0            # real minutes since the start
    bio_t: float = 0.0        # biological minutes since the start
    step_count: int = 0
    next_uid: int = 0
    colony_axis: list = field(default_factory=list)  # ripple direction per colony ID (rad)
    eps_offsets: tuple = None  # slime-sensing table, built once by myxo_alignment
    next_ecoli_seed: float = float("inf")  # bio min when the next new E. coli founder is due (B75)
    myxo_arrivals: list = field(default_factory=list)  # (bio min, cells) of Myxo seeds still to come in (B78)
    spores: np.ndarray = field(default_factory=lambda: np.zeros((0, 2)))  # where Myxo spores wait (B80)
    myxo_lysed: int = 0       # Myxo that have lysed in development so far (B80)


# ---------------------------------------------------------------- empty containers
def empty_myxo(K, n_nodes=10):
    """A Myxo population with no cells yet, but with every column in the right shape."""
    return MyxoCells(nodes=np.zeros((0, n_nodes, 2)), age=np.zeros(0), memory=np.zeros((0, K)),
                     mem_slot=np.zeros(0, dtype=np.int64), signal=np.zeros(0), energy=np.zeros(0),
                     pause_left=np.zeros(0), pause_target=np.zeros(0, dtype=np.int64),
                     scout=np.zeros(0, dtype=bool), starve_time=np.zeros(0),
                     uid=np.zeros(0, dtype=np.int64))


def empty_ecoli():
    """An E. coli population with no cells yet, but with every column in the right shape."""
    return EColiCells(centre=np.zeros((0, 2)), angle=np.zeros(0), length=np.zeros(0),
                      colony=np.zeros(0, dtype=np.int64), dormant=np.zeros(0, dtype=bool),
                      starve_time=np.zeros(0), persister=np.zeros(0, dtype=bool),
                      lysis_timer=np.zeros(0), divide_at=np.zeros(0), speed_factor=np.zeros(0),
                      uid=np.zeros(0, dtype=np.int64))


def empty_fields(settings):
    """All ground maps for a new world, empty (zeros). Richness and nutrients are filled by seeding."""
    eps, eps_spacing = grids.make_grid(settings.box, settings.eps_grid)
    coarse, spacing = grids.make_grid(settings.box, settings.coarse_grid)
    return Fields(eps=eps, eps_scout=eps.copy(), eps_spacing=eps_spacing, richness=coarse.copy(), nutrients=coarse.copy(),
                  food=coarse.copy(), scraps=coarse.copy(), attractant=coarse.copy(), matrix=coarse.copy(),
                  matrix_smooth=coarse.copy(), axis_c=coarse.copy(), axis_s=coarse.copy(),
                  axis_c_smooth=coarse.copy(), axis_s_smooth=coarse.copy(),
                  spacing=spacing)


def new_world(settings):
    """A world with empty populations and empty maps; seeding.py fills it in."""
    first_seed = settings.ecoli_seed_interval if settings.ecoli_seed_interval > 0 else float("inf")
    return World(settings=settings, rng=np.random.default_rng(settings.seed),
                 myxo=empty_myxo(settings.memory_length, settings.n_nodes),
                 ecoli=empty_ecoli(), fields=empty_fields(settings), next_ecoli_seed=first_seed)


# ---------------------------------------------------------------- adding and removing rows
def append_rows(cells, new):
    """Add the rows of `new` (newborn or seeded cells) to the bottom of `cells`, column by column."""
    if type(cells) is not type(new):
        raise TypeError("append_rows needs two populations of the same kind")
    for f in fields(cells):
        joined = np.concatenate([getattr(cells, f.name), getattr(new, f.name)], axis=0)
        setattr(cells, f.name, joined)


def keep_rows(cells, mask):
    """Keep only the rows where `mask` is True (used when cells die), column by column."""
    mask = np.asarray(mask, dtype=bool)
    if mask.shape != (count(cells),):
        raise ValueError("mask must have one entry per cell")
    for f in fields(cells):
        setattr(cells, f.name, getattr(cells, f.name)[mask])


def count(cells):
    """Number of cells (rows)."""
    return len(cells.uid)


def new_uids(world, n):
    """Hand out the next n permanent IDs; they are never reused."""
    ids = np.arange(world.next_uid, world.next_uid + n, dtype=np.int64)
    world.next_uid += n
    return ids
