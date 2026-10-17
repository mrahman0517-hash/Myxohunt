"""
myxo_energy.py — each Myxo's food store (B20–B28, B39, B75): upkeep, eating spilled food (hungry
cells first), division when the store has doubled, and death when it runs out.

Two kinds of food lie on the ground (B83): prey food (from killed or burst E. coli) feeds a cell
fully; scraps (from dead or lysed Myxo) only keep it alive, filling its store up to scrap_cap.

The store counts the cell's material: 100 is a normal newborn. A fed cell builds up to 200 (a
second cell's worth) and splits into two daughters of about 100 each, as a real cell doubles its
contents before dividing (B75). Food converts at `efficiency` (30%, B85); the reserve between 200
and 210 fills at a third of that and is used first when food runs short (it's simply the part above 200).
"""
import numpy as np

import grids
import myxo_body
import myxo_modes
import state


# ---------------------------------------------------------------- upkeep
def starving_cost(energy, dt_bio, full, cut, core):
    """What a stringent cell spends in dt_bio: the surplus above `core` at the full rate first, as
    stored fuel is used first when food runs out, then the core at the cut rate (B84)."""
    on_surplus = np.minimum(np.maximum(energy - core, 0.0) / full, dt_bio)   # bio min spent on surplus
    return full * on_surplus + cut * (dt_bio - on_surplus)


def upkeep(world, dt_bio):
    """Living costs: the store runs down so a newborn's store (100) lasts the preset time (B23, B75).

    In stringent mode (myxo_modes.stringent) the stringent response shuts down growth and cuts
    running costs to starvation_upkeep, so the cell survives days, as starving Myxo do (B70, B83).
    The cut protects only the core, a newborn's 100: a starving cell burns anything above that at
    the full rate first (B84; Hoiczyk 2009, B22).
    """
    s, m = world.settings, world.myxo
    full = s.energy_newborn / s.survive_time
    starving = starving_cost(m.energy, dt_bio, full, full * s.starvation_upkeep, s.energy_newborn)
    m.energy -= np.where(myxo_modes.stringent(world), starving, full * dt_bio)


# ---------------------------------------------------------------- eating
def hunger(energy, s):
    """How hungry each cell is: 1 when empty, 0 when completely full (210) (B26)."""
    return np.clip((s.energy_cap - energy) / s.energy_cap, 0.0, 1.0)


def food_demand(world, grid, dt_bio):
    """How much food each cell would take from each square of `grid` within absorb_radius of its
    head (B71).

    The cell's rate is uptake_rate × affinity × the food around it, never above uptake_max (B65);
    hunger scales it (B26), and it takes from each nearby square in proportion to what's there.

    Returns:
        demand (N, K) and the flat square indices (N, K).
    """
    s, f, m = world.settings, world.fields, world.myxo
    flat, vals = grids.disc_squares(grid, m.nodes[:, 0], s.box, s.absorb_radius, f.spacing)
    vals = np.maximum(vals, 0.0)                           # no "negative food" (B73)
    around = vals.sum(axis=1)
    per_min = np.minimum(s.uptake_rate * myxo_modes.affinity_factors(world) * around, s.uptake_max)
    total = np.minimum(per_min * dt_bio, around) * hunger(m.energy, s)
    share = np.where(around[:, None] > 0, vals / np.maximum(around[:, None], 1e-300), 0.0)
    return total[:, None] * share, flat


def share_food(grid, demand, flat):
    """Share each square's food in `grid` among the cells reaching it in proportion to their
    demand (hungry cells ask for more, so they get more). Returns what each cell takes from each
    square.

    Food and demand are both kept at 0 or above, so the scale-down factor always lies between
    0 and 1: no one can take more than a square holds (B73).
    """
    food = np.maximum(grid.ravel(), 0.0)
    asked = np.bincount(flat.ravel().astype(np.intp), weights=demand.ravel(), minlength=food.size)   # intp: browsers
    scale = np.where(asked > food, food / np.maximum(asked, 1e-300), 1.0)
    return demand * scale[flat]


def absorb(energy, taken, s):
    """Turn food taken into stored energy: `efficiency` (30%) up to 200, a third of that in the
    reserve up to 210 (B21, B22, B75, B85).

    Returns:
        (new energy, food left over because the cell is full).
    """
    to_full = np.maximum(s.energy_full - energy, 0.0) / s.efficiency
    low = np.minimum(taken, to_full)
    energy = energy + low * s.efficiency
    to_cap = np.maximum(s.energy_cap - energy, 0.0) / s.reserve_efficiency
    high = np.minimum(taken - low, to_cap)
    return energy + high * s.reserve_efficiency, taken - low - high


def absorb_scraps(energy, taken, s):
    """Turn scraps into stored energy at `efficiency`, but only up to scrap_cap: they keep a cell alive,
    never content (B83).

    Returns:
        (new energy, scraps left over because the cell is at the cap).
    """
    room = np.maximum(s.scrap_cap - energy, 0.0) / s.efficiency
    used = np.minimum(taken, room)
    return energy + used * s.efficiency, taken - used


def eat_from(world, grid, dt_bio, absorb_fn, eaters):
    """The cells in `eaters` eat from one food map; anything they can't store goes back to the
    squares it came from (B26)."""
    m = world.myxo
    demand, flat = food_demand(world, grid, dt_bio)
    demand *= eaters[:, None]
    taken = share_food(grid, demand, flat)                 # (N, K)
    total = taken.sum(axis=1)
    m.energy, leftover = absorb_fn(m.energy, total, world.settings)
    back = taken * np.where(total > 0, leftover / np.maximum(total, 1e-300), 0.0)[:, None]
    food = grid.ravel()                                    # a view: changes write into the map
    np.add.at(food, flat.ravel(), (back - taken).ravel())
    np.clip(grid, 0.0, None, out=grid)


def uptake(world, dt_bio):
    """Each Myxo eats prey food within reach of its head; cells below scrap_cap then also eat
    scraps, up to that cap (B26, B83)."""
    m, f, s = world.myxo, world.fields, world.settings
    if state.count(m) == 0:
        return
    eat_from(world, f.food, dt_bio, absorb, np.ones(state.count(m), dtype=bool))
    eat_from(world, f.scraps, dt_bio, absorb_scraps, m.energy < s.scrap_cap)


# ---------------------------------------------------------------- division
def division_chance(energy, dt_bio, s):
    """Chance of dividing now: 0 below 190, rising to division_rate_max at 210 (B24, B75)."""
    ready = np.clip((energy - s.division_threshold) / (s.energy_cap - s.division_threshold), 0.0, 1.0)
    return np.where(energy >= s.division_threshold, 1.0 - np.exp(-s.division_rate_max * ready * dt_bio), 0.0)


def daughters_of(world, idx):
    """New daughter cells for the dividing mothers `idx`: a body beside the mother, the same
    clocks (reversal and starvation) and memory, and half of the mother's store (B75, B83)."""
    m, s = world.myxo, world.settings
    k = len(idx)
    return state.MyxoCells(
        nodes=np.stack([myxo_body.split_cell(m.nodes[i], s) for i in idx]) if k else m.nodes[:0].copy(),
        age=m.age[idx].copy(), memory=m.memory[idx].copy(), mem_slot=m.mem_slot[idx].copy(),
        signal=m.signal[idx].copy(), energy=m.energy[idx] / 2.0,
        pause_left=np.zeros(k), pause_target=np.full(k, -1, dtype=np.int64),
        scout=np.zeros(k, dtype=bool), starve_time=m.starve_time[idx].copy(), uid=state.new_uids(world, k))


def divide_myxo(world, dt_bio):
    """Moving cells whose store has about doubled may divide into two equal halves of ~100: two
    normal newborns, nothing created or lost (B24, B75). Scouts don't divide (B71), nor do
    stringent cells (B25), which can now hold a full store (B83)."""
    m, s = world.myxo, world.settings
    free = (m.pause_left <= 0) & ~m.scout & ~myxo_modes.stringent(world)
    ready = np.nonzero(free & (m.energy >= s.division_threshold))[0]
    if ready.size == 0:                                   # no dice rolled unless someone could divide
        return
    idx = ready[world.rng.random(ready.size) < division_chance(m.energy[ready], dt_bio, s)]
    if idx.size == 0:
        return
    born = daughters_of(world, idx)
    m.energy[idx] = m.energy[idx] / 2.0
    state.append_rows(m, born)


# ---------------------------------------------------------------- death
def starvation_deaths_myxo(world):
    """Cells whose store has run out die. The store is the whole cell, so a cell that starved to
    zero has used itself up and leaves nothing (B84, replaces B39 and B82)."""
    m = world.myxo
    dead = m.energy <= 0
    if dead.any():
        state.keep_rows(m, ~dead)
