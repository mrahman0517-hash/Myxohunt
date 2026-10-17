"""Checks for the famine exit (B80): a day into stringent mode, starving Myxo lyse, become spores
or stay on as rods."""
import numpy as np

import myxo_famine
import myxo_modes
import seeding
import state
from engine import Simulation
from settings import Settings


def _starving_sim(n=2000, energy=10.0, **overrides):
    """A simulation of n Myxo scattered over an empty 40 µm world, all at `energy` (10 = stringent),
    no food anywhere."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, **overrides)
    sim = Simulation(s, seed_cells=False)
    starts = np.random.default_rng(0).uniform(0, 40, size=(n, 2))
    state.append_rows(sim.world.myxo, seeding.make_myxo(sim.world, starts, np.zeros(n)))
    sim.world.myxo.energy[:] = energy
    return sim


def _starving(n=2000, energy=10.0, **overrides):
    """The world of `_starving_sim`."""
    return _starving_sim(n, energy, **overrides).world


def _one_tick(w, dt_bio=0.05):
    """The starvation clock, then the famine exit, as in engine.step_myxo."""
    myxo_modes.update_starve_clock(w, dt_bio)
    myxo_famine.famine_exit(w, dt_bio)


def test_a_day_into_starvation_70_percent_lyse_10_percent_sporulate_and_20_percent_stay_as_rods():
    """Cells crossing 24 h in stringent mode take one fate each, in the measured shares (Lee 2012;
    O'Connor & Zusman 1991); the rods are not drawn again while they stay starved (B80)."""
    w = _starving()
    n = state.count(w.myxo)
    w.myxo.starve_time[:] = w.settings.famine_time - 0.01           # all cross in the next tick
    _one_tick(w)
    lysed, spores, rods = w.myxo_lysed, len(w.spores), state.count(w.myxo)
    assert lysed + spores + rods == n
    assert np.isclose(lysed / n, 0.7, atol=0.03)
    assert np.isclose(spores / n, 0.1, atol=0.02)
    assert np.isclose(rods / n, 0.2, atol=0.03)
    for _ in range(100):
        _one_tick(w)
    assert state.count(w.myxo) == rods and w.myxo_lysed == lysed     # rods stay rods


def test_lysing_cells_spill_only_their_store_as_scraps_and_spores_keep_theirs():
    """Each lysed cell leaves what's left of its store (10) as scraps: the store is the whole cell
    (B83, B84); no prey food and no prey matrix. Spores lie where the cells were (B80)."""
    w = _starving(n=500, energy=10.0)
    w.myxo.starve_time[:] = w.settings.famine_time - 0.01
    _one_tick(w)
    expected = w.myxo_lysed * 10.0
    assert np.isclose(w.fields.scraps.sum(), expected)
    assert w.fields.food.sum() == 0.0 and w.fields.matrix.sum() == 0.0
    assert w.spores.shape == (len(w.spores), 2) and (w.spores >= 0).all() and (w.spores < 40).all()


def test_nothing_happens_before_a_day_after_feeding_or_when_switched_off():
    """No fates (and no random numbers drawn) before 24 h of starving, for cells that found a real
    meal of prey food (their clock is back at 0), or with famine_exit off (B80, B83)."""
    for prey_food, clock, on in ((0.0, 600.0, True), (1.0, 2000.0, True), (0.0, 1439.99, False)):
        w = _starving(n=200, famine_exit=on)
        w.fields.food[:] = prey_food
        w.myxo.starve_time[:] = clock
        before = w.rng.bit_generator.state
        _one_tick(w)
        assert state.count(w.myxo) == 200 and len(w.spores) == 0 and w.myxo_lysed == 0
        assert w.rng.bit_generator.state == before


def test_a_crumb_does_not_postpone_the_famine():
    """Scraps and thin prey food don't end starvation, so the famine still comes a day after the
    prey food ran out (B81, B83; before B81, a crumb restarted the 24 h)."""
    w = _starving(n=500)
    w.myxo.starve_time[:] = w.settings.famine_time - 1.0
    w.fields.scraps[:] = 5.0
    w.fields.food[:] = 0.1                                           # 1.3 units within reach
    for _ in range(40):                                              # 2 bio-min
        _one_tick(w)
    assert w.myxo_lysed + len(w.spores) > 0.7 * 500


def test_the_famine_exit_runs_in_the_engine():
    """In the running engine, starving cells reach the famine and the stats count the fates."""
    sim = _starving_sim(n=300)
    w = sim.world
    w.myxo.starve_time[:] = w.settings.famine_time - 0.2
    sim.run_for(real_minutes=0.1)
    row = sim.stats.rows[-1]
    assert row["myxo_lysed"] > 0 and row["myxo_spores"] > 0
    assert row["myxo_rods"] == row["myxo"] == state.count(w.myxo)
