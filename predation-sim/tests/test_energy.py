"""Checks for the Myxo food store (milestone 6): upkeep, eating, sharing, division, death."""
import numpy as np

import myxo_energy as en
import seeding
import state
from engine import Simulation
from settings import Settings


def _world(n_cells=1, energy=60.0, **overrides):
    """An empty 40 µm world with n horizontal Myxo cells side by side, all at `energy`."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, **overrides)
    sim = Simulation(s, seed_cells=False)
    starts = np.array([[15.0, 20.0 + 0.0 * i] for i in range(n_cells)])
    state.append_rows(sim.world.myxo, seeding.make_myxo(sim.world, starts, np.zeros(n_cells)))
    sim.world.myxo.energy[:] = energy
    return sim.world


def test_a_full_store_lasts_the_preset_time():
    """With no food, a newborn's store (100) runs out in exactly the preset's time (B23, B75)."""
    w = _world(energy=100.0)
    en.upkeep(w, w.settings.survive_time)
    assert np.isclose(w.myxo.energy[0], 0.0)


def test_starvation_mode_cuts_running_costs():
    """In stringent mode upkeep on the core drops to 30%: in the time 20 units last at full cost,
    a stringent cell uses only 6 (B70, B83, B85)."""
    w = _world(energy=20.0)
    w.myxo.starve_time[:] = w.settings.stringent_delay
    t_normal = w.settings.survive_time * 20.0 / 100.0         # how long 20 units would last at full cost
    en.upkeep(w, t_normal)
    assert np.isclose(w.myxo.energy[0], 20.0 - 20.0 * w.settings.starvation_upkeep, atol=1e-6)


def test_one_ecoli_gives_30_below_200_and_a_third_of_that_in_the_reserve():
    """One E. coli's material (100) gives 30 below 200 (efficiency 30%); 30 units into the reserve
    above 200 give 3 (a third of 30%) (B21, B22, B75, B85)."""
    s = Settings()
    e, left = en.absorb(np.array([40.0, 200.0]), np.array([100.0, 30.0]), s)
    assert np.allclose(e, [40.0 + 100.0 * s.efficiency, 200.0 + 30.0 * s.efficiency / 3])
    assert np.allclose(e, [70.0, 203.0]) and np.allclose(left, 0.0)


def test_a_full_cell_leaves_extra_food_on_the_ground():
    """Food beyond the 210 cap is not absorbed; it stays for others."""
    s = Settings()
    e, left = en.absorb(np.array([208.0]), np.array([50.0]), s)
    assert np.isclose(e[0], 210.0) and np.isclose(left[0], 50.0 - 2.0 / s.reserve_efficiency)


def test_hungry_cells_get_the_larger_share_of_a_small_puddle():
    """Two cells on one square with too little food: the emptier one takes more (B26)."""
    w = _world(n_cells=2)
    w.myxo.energy[:] = [10.0, 100.0]
    w.myxo.nodes[1] = w.myxo.nodes[0]                     # same square under both heads
    sq = tuple(np.floor(w.myxo.nodes[0, 0] / w.fields.spacing).astype(int))
    w.fields.food[sq] = 0.5
    before = w.myxo.energy.copy()
    en.uptake(w, dt_bio=1000.0)                            # ask for far more than is there
    gained = w.myxo.energy - before
    assert gained[0] > gained[1] > 0
    assert w.fields.food[sq] < 1e-12


def test_cells_eat_from_the_ground_within_2_um_of_their_head_only():
    """Food 1.5 µm from the head is eaten; food 4 µm away is left alone (B71)."""
    w = _world(energy=50.0)
    head = w.myxo.nodes[0, 0]
    near = tuple(np.floor((head + [0.0, 1.5]) / w.fields.spacing).astype(int))
    far = tuple(np.floor((head + [0.0, 4.0]) / w.fields.spacing).astype(int))
    w.fields.food[near] = w.fields.food[far] = 1.0
    en.uptake(w, dt_bio=1000.0)
    assert w.fields.food[near] < 1.0 and w.fields.food[far] == 1.0


def test_eating_never_creates_energy_from_rounding_noise():
    """Next to squares holding ±1e-17 rounding errors, cells gain at most 30% of the food they
    actually remove: no free fill-up (B73; this bug gave every run a free meal at the first kills)."""
    w = _world(n_cells=200, energy=40.0)
    rng = np.random.default_rng(0)
    w.myxo.nodes += rng.uniform(-10.0, 10.0, size=(200, 1, 2))       # scatter the cells
    w.fields.food[:] = rng.normal(0.0, 1e-17, w.fields.food.shape)    # noise of both signs
    w.fields.food[20, 20] += 1.0                                      # one real crumb of food
    e0, food0 = w.myxo.energy.sum(), np.maximum(w.fields.food, 0.0).sum()
    en.uptake(w, dt_bio=0.05)
    used = food0 - w.fields.food.sum()
    assert w.myxo.energy.sum() - e0 <= w.settings.efficiency * used + 1e-9
    assert w.fields.food.min() >= 0.0


def test_scouts_do_not_divide():
    """A scouting cell is busy exploring: no division even with a full store (B71)."""
    w = _world(energy=210.0, division_rate_max=1e9)
    w.myxo.scout[:] = True
    en.divide_myxo(w, 1.0)
    assert state.count(w.myxo) == 1


def test_division_needs_a_doubled_store_and_makes_two_normal_newborns():
    """No division below 190; a mother at 200 becomes two daughters of 100, normal newborns, and
    the total store is unchanged: division creates nothing (B24, B75)."""
    w = _world(energy=189.0, division_rate_max=1e9)
    en.divide_myxo(w, 1.0)
    assert state.count(w.myxo) == 1
    w.myxo.energy[:] = 200.0
    en.divide_myxo(w, 1.0)
    assert state.count(w.myxo) == 2
    assert np.allclose(w.myxo.energy, 100.0)
    assert np.isclose(w.myxo.energy.sum(), 200.0)
    assert len(set(w.myxo.uid.tolist())) == 2


def test_an_empty_cell_dies_and_leaves_nothing():
    """The store is the whole cell, so a Myxo that starved to zero has used itself up: it is
    removed and leaves no scraps, no food and no matrix (B84, replaces B39 and B82)."""
    w = _world(energy=0.0)
    en.starvation_deaths_myxo(w)
    assert state.count(w.myxo) == 0
    assert w.fields.scraps.sum() == 0.0 and w.fields.food.sum() == 0.0 and w.fields.matrix.sum() == 0.0


def test_scraps_keep_a_cell_alive_but_only_up_to_30():
    """On plenty of scraps a cell at 10 fills to 30 and no further, the rest stays on the ground;
    a cell already at 50 takes none (B83)."""
    w = _world(n_cells=2)
    w.myxo.nodes[1] += [0.0, 10.0]                           # a second cell, well apart
    w.myxo.energy[:] = [10.0, 50.0]
    w.fields.scraps[:] = 10.0
    before = w.fields.scraps.sum()
    for _ in range(200):
        en.uptake(w, dt_bio=1.0)
    assert np.isclose(w.myxo.energy[0], 30.0) and w.myxo.energy[1] == 50.0
    assert np.isclose(before - w.fields.scraps.sum(), 20.0 / w.settings.efficiency)


def test_prey_food_fills_a_cell_past_the_scrap_cap():
    """Prey food has no such cap: the 130 units within reach take a cell from 10 to 75 (B75, B83)."""
    w = _world(energy=10.0)
    w.fields.food[:] = 10.0                                  # 13 squares within reach
    for _ in range(400):
        en.uptake(w, dt_bio=1.0)
    assert np.isclose(w.myxo.energy[0], 10.0 + 130.0 * w.settings.efficiency, rtol=0.01)


def test_stringent_cells_do_not_divide_even_when_full():
    """The stringent response stops growth: a full cell that has run out of prey food doesn't
    divide (B25, B83)."""
    w = _world(energy=210.0, division_rate_max=1e9)
    w.myxo.starve_time[:] = w.settings.stringent_delay
    en.divide_myxo(w, 1.0)
    assert state.count(w.myxo) == 1


def test_a_starving_cell_burns_its_surplus_first_then_its_costs_drop():
    """A stringent cell at 160 pays full costs on the 60 above a newborn's 100 (about 14 bio-h), then
    30% of them on its core (100 → 82 in the same time again); one long step gives the same result
    as two (B84, B85)."""
    full = Settings().energy_newborn / Settings().survive_time
    w = _world(energy=160.0)
    w.myxo.starve_time[:] = w.settings.stringent_delay
    core_left = 100.0 - 60.0 * w.settings.starvation_upkeep
    en.upkeep(w, 60.0 / full)                                 # time to burn the surplus at full cost
    assert np.isclose(w.myxo.energy[0], 100.0)
    en.upkeep(w, 60.0 / full)                                 # the same time again, now at 30%
    assert np.isclose(w.myxo.energy[0], core_left) and np.isclose(core_left, 82.0)
    w2 = _world(energy=160.0)
    w2.myxo.starve_time[:] = w2.settings.stringent_delay
    en.upkeep(w2, 120.0 / full)
    assert np.isclose(w2.myxo.energy[0], core_left)


def test_lower_efficiency_uses_more_food_for_the_same_growth():
    """With uptake divided by efficiency (B85), a cell at 30% gains its store exactly as fast as one
    at 50% with the old uptake numbers (so the 5.4 bio-h generation holds), on thin food and on rich
    food alike, but takes 5/3 as much food off the ground: each prey feeds fewer hunters."""
    for food in (0.2, 10.0):
        new = _world(energy=60.0)
        old = _world(energy=60.0, efficiency=0.5, uptake_rate=0.5, uptake_max=5.0)
        for w in (new, old):
            w.fields.food[:] = food
        before = new.fields.food.sum()
        en.uptake(new, dt_bio=1.0)
        en.uptake(old, dt_bio=1.0)
        assert np.isclose(new.myxo.energy[0], old.myxo.energy[0])
        assert np.isclose(before - new.fields.food.sum(), (before - old.fields.food.sum()) * 0.5 / 0.3)
