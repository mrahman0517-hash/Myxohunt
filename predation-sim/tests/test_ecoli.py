"""Checks for E. coli growth, division, pushing, starvation and bursting (milestone 2)."""
import numpy as np

import ecoli_body
import ecoli_life
import predation
import seeding
import state
from engine import Simulation
from settings import Settings


def _world_with_one_seed(nutrient=1.0, **overrides):
    """A small world, uniform ground at `nutrient`, one E. coli in the middle."""
    s = Settings(box=40.0, start_colonies=1, **overrides)
    w = state.new_world(s)
    w.fields.richness[:] = nutrient
    w.fields.nutrients[:] = nutrient
    state.append_rows(w.ecoli, seeding.ecoli_seed(w, [20.0, 20.0]))
    return w


def test_monod_is_one_on_the_richest_ground_and_zero_without_food():
    """Top speed on richness 1.0; half speed near n = K/(1 + 2K); nothing at zero."""
    assert np.isclose(ecoli_life.monod_factor(np.array([1.0]), 0.2)[0], 1.0)
    assert np.isclose(ecoli_life.monod_factor(np.array([0.2 / 1.4]), 0.2)[0], 0.5)
    assert ecoli_life.monod_factor(np.array([0.0]), 0.2)[0] == 0.0


def test_one_seed_doubles_in_about_20_bio_minutes():
    """With plenty of food (none used up) and average-speed cells, length doubles in 20 bio min."""
    w = _world_with_one_seed(nutrient=1.0, nutrient_per_um=0.0, ecoli_speed_noise=0.0)
    start = w.ecoli.length.sum()
    for _ in range(int(20.0 / (w.settings.dt * w.settings.speedup))):
        grown = ecoli_body.grow(w.ecoli, ecoli_life.growth_rates(w), w.settings.dt * w.settings.speedup)
        ecoli_life.consume(w, grown)
        ecoli_body.divide(w)
    assert np.isclose(w.ecoli.length.sum() / start, 2.0, rtol=0.05)


def test_division_conserves_length_and_keeps_the_colony():
    """A rod past its division length splits into two halves, end to end, same colony."""
    w = _world_with_one_seed()
    w.ecoli.length[:] = 4.4
    w.ecoli.divide_at[:] = 4.0
    ecoli_body.divide(w)
    assert state.count(w.ecoli) == 2
    assert np.allclose(w.ecoli.length, 2.2)
    assert np.isclose(np.linalg.norm(w.ecoli.centre[0] - w.ecoli.centre[1]), 2.2, atol=0.01)
    assert w.ecoli.colony[0] == w.ecoli.colony[1]
    assert list(w.ecoli.uid) == sorted(w.ecoli.uid)


def test_newborn_cells_differ_in_size_and_speed():
    """Division lengths spread about ±10% around 4 µm and growth speeds about ±20% around 1 (B53, B55)."""
    w = _world_with_one_seed()
    lengths, speeds = seeding.divide_lengths(w, 5000), seeding.speed_factors(w, 5000)
    assert np.isclose(lengths.mean(), 4.0, atol=0.05) and np.isclose(lengths.std(), 0.4, atol=0.05)
    assert np.isclose(speeds.mean(), 1.0, atol=0.02) and np.isclose(speeds.std(), 0.2, atol=0.02)
    assert speeds.min() >= 0.4 and lengths.min() >= 3.0


def test_no_growth_without_food_and_dormancy_starts():
    """On empty ground a cell doesn't grow and is marked dormant, counting its hungry time."""
    w = _world_with_one_seed(nutrient=0.0)
    assert ecoli_life.growth_rates(w)[0] == 0.0
    ecoli_life.update_dormancy(w, 5.0)
    assert w.ecoli.dormant[0] and np.isclose(w.ecoli.starve_time[0], 5.0)


def test_starved_cell_dies_then_bursts_later_with_less_food():
    """A long-starved cell dies, stays intact for the delay (2 bio-h, Schink et al.), then bursts
    with 25% of its food, its contents having shrunk over a day of starving (B45, B80, B87)."""
    w = _world_with_one_seed(nutrient=0.0, starvation_death_rate=1e9)
    w.ecoli.persister[:] = False
    w.ecoli.dormant[:] = True
    w.ecoli.starve_time[:] = w.settings.starved_shrink_time + 1.0
    ecoli_life.starvation_deaths(w, 1.0)
    delay = w.settings.starved_lysis_delay
    assert np.isclose(delay, 120.0) and np.isclose(w.ecoli.lysis_timer[0], delay)
    assert not ecoli_life.count_down_lysis(w, 0.9 * delay).any()   # still intact
    bursting = ecoli_life.count_down_lysis(w, 0.2 * delay)
    predation.lyse_ecoli(w, bursting)
    expected_food = w.settings.ecoli_content * (2.0 / 3.0) * w.settings.starved_content_min
    assert state.count(w.ecoli) == 0
    assert np.isclose(w.fields.food.sum(), expected_food)
    assert np.isclose(w.fields.matrix.sum(), w.settings.matrix_per_ghost)


def test_lysis_writes_the_colony_direction_into_the_ground():
    """The wall material carries its colony's ripple direction (doubled-angle sums)."""
    w = _world_with_one_seed()
    w.colony_axis[0] = np.radians(30.0)
    predation.lyse_ecoli(w, np.array([True]))
    c, s = w.fields.axis_c.sum(), w.fields.axis_s.sum()
    assert np.isclose(np.degrees(0.5 * np.arctan2(s, c)), 30.0)


def test_growing_colony_keeps_cells_from_overlapping():
    """After a few divisions in a full simulation, rods are pushed apart (no deep overlaps)."""
    sim = Simulation(Settings(box=40.0, start_colonies=1, seed=3, myxo_groups=0, myxo_singles=0))
    sim.world.fields.richness[:] = sim.world.fields.nutrients[:] = 1.0   # rich ground: growth isn't the point
    sim.run_for(real_minutes=12.0)                        # 120 bio min at speed-up 10: a small colony
    e, s = sim.world.ecoli, sim.world.settings
    assert state.count(e) >= 8
    pts = ecoli_body.contact_points(e, s).reshape(-1, s.ecoli_points, 2)
    centres = pts.reshape(-1, 2)
    owner = np.repeat(np.arange(state.count(e)), s.ecoli_points)
    d = np.linalg.norm(centres[:, None] - centres[None], axis=-1)
    other = owner[:, None] != owner[None]
    assert d[other].min() > 0.6 * s.ecoli_width


def test_a_new_founder_lands_every_6_bio_hours_anywhere():
    """When a founder is due, a single new E. coli lands at a random spot, with no placement
    rules, even on bare ground; the next one is due 6 bio-h later (B75, B78)."""
    s = Settings(box=150.0, start_colonies=0, myxo_groups=0, myxo_singles=0)
    w = Simulation(s, seed_cells=False).world
    assert np.isclose(w.next_ecoli_seed, 360.0)
    w.bio_t = 300.0
    seeding.add_due_founder(w)                                # not due yet
    assert state.count(w.ecoli) == 0
    w.bio_t = 400.0
    w.fields.nutrients[:] = 0.0                               # bare ground doesn't stop it
    seeding.add_due_founder(w)
    assert state.count(w.ecoli) == 1
    assert np.isclose(w.next_ecoli_seed, 400.0 + 360.0)
    seeding.add_due_founder(w)                                # the next one isn't due yet
    assert state.count(w.ecoli) == 1


def test_a_dormant_cell_needs_a_real_meal_to_wake():
    """A trace of food (below wake_threshold) keeps a dormant cell dormant with its clock running;
    a real meal (wake_threshold) wakes it and restarts the clock. A growing cell on the same thin
    food keeps growing: only below dormant_threshold does it stop (B87)."""
    w = _world_with_one_seed(nutrient=0.1)
    w.ecoli.dormant[:] = True
    w.ecoli.starve_time[:] = 5.0
    ecoli_life.update_dormancy(w, 1.0)
    assert w.ecoli.dormant[0] and np.isclose(w.ecoli.starve_time[0], 6.0)
    w.fields.nutrients[:] = w.settings.wake_threshold + 0.01
    ecoli_life.update_dormancy(w, 1.0)
    assert not w.ecoli.dormant[0] and w.ecoli.starve_time[0] == 0.0
    w.fields.nutrients[:] = 0.1
    ecoli_life.update_dormancy(w, 1.0)
    assert not w.ecoli.dormant[0] and ecoli_life.growth_rates(w)[0] > 0.0


def test_starving_cells_start_dying_as_soon_as_they_go_dormant():
    """With no day of grace, freshly dormant cells (not persisters) die at the measured rate,
    about 2.8% per bio-hour (0.69 per day, Schink et al.); persisters never do (B87)."""
    s = Settings(box=200.0, start_colonies=0)
    w = state.new_world(s)
    w.fields.richness[:] = 0.0
    w.fields.nutrients[:] = 0.0
    k = 4000
    starts = np.random.default_rng(1).uniform(5.0, 195.0, size=(k, 2))
    state.append_rows(w.ecoli, state.EColiCells(
        centre=starts, angle=np.zeros(k), length=np.full(k, s.ecoli_birth_length),
        colony=np.zeros(k, dtype=np.int64), dormant=np.zeros(k, dtype=bool), starve_time=np.zeros(k),
        persister=np.zeros(k, dtype=bool), lysis_timer=np.full(k, -1.0), divide_at=seeding.divide_lengths(w, k),
        speed_factor=seeding.speed_factors(w, k), uid=state.new_uids(w, k)))
    w.ecoli.persister[:200] = True
    ecoli_life.update_dormancy(w, 1.0)                      # just gone dormant
    ecoli_life.starvation_deaths(w, 60.0)                   # one bio-hour
    died = w.ecoli.lysis_timer >= 0
    expected = 1.0 - np.exp(-s.starvation_death_rate * 60.0)
    assert not died[:200].any()
    assert abs(died[200:].mean() - expected) < 0.008


def test_persisters_are_drawn_for_each_newborn_not_inherited():
    """Surviving starvation is each cell's own 5% chance (B88): when 4,000 persister mothers
    divide, about 5% of the 8,000 daughters are persisters, not all of them."""
    s = Settings(box=200.0, start_colonies=0)
    w = state.new_world(s)
    k = 4000
    starts = np.random.default_rng(1).uniform(5.0, 195.0, size=(k, 2))
    state.append_rows(w.ecoli, state.EColiCells(
        centre=starts, angle=np.zeros(k), length=np.full(k, 2 * s.ecoli_divide_length),
        colony=np.zeros(k, dtype=np.int64), dormant=np.zeros(k, dtype=bool), starve_time=np.zeros(k),
        persister=np.ones(k, dtype=bool), lysis_timer=np.full(k, -1.0), divide_at=seeding.divide_lengths(w, k),
        speed_factor=seeding.speed_factors(w, k), uid=state.new_uids(w, k)))
    ecoli_body.divide(w)
    assert len(w.ecoli.uid) == 2 * k
    assert abs(w.ecoli.persister.mean() - s.persister_fraction) < 0.012
