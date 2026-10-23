"""Checks for the review fixes of 23 Oct 2026 (B97): direct event counters with a closed food and
store ledger, the run tool's settings parsing and restart guard, and the founder switch."""
import os
import sys

import numpy as np
import pytest

import counters
import seeding
import state
from engine import Simulation
from settings import Settings, make_settings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "checks")))
import check_populations as cp                                       # noqa: E402


def _busy_world():
    """A 40 µm world where everything happens within a few real minutes: 150 E. coli on bare ground
    (they go dormant, starve and burst quickly), 120 hungry Myxo among them (some ready to divide, some about to
    reach their famine), and food and scraps on the ground."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, myxo_arrival_window=0.0,
                 ecoli_seed_interval=0.0, starvation_death_rate=0.02, starved_lysis_delay=5.0,
                 famine_time=40.0, seed=3)
    sim = Simulation(s, seed_cells=False)
    w, rng = sim.world, np.random.default_rng(3)
    for p in rng.uniform(0, 40, size=(150, 2)):
        state.append_rows(w.ecoli, seeding.ecoli_seed(w, p))
    w.fields.nutrients[:] = 0.0                                      # bare ground: the E. coli go dormant and starve
    w.fields.richness[:] = 0.0
    n = 120
    state.append_rows(w.myxo, seeding.make_myxo(w, rng.uniform(0, 40, size=(n, 2)), rng.uniform(0, 2 * np.pi, n)))
    w.myxo.energy[:] = rng.uniform(5, 200, n)
    w.myxo.energy[:10] = 205.0                                       # ready to divide
    w.myxo.starve_time[10:40] = 39.0                                 # famine due in a moment
    w.fields.food[:] = rng.uniform(0, 2, w.fields.food.shape)
    w.fields.scraps[:] = rng.uniform(0, 1, w.fields.scraps.shape)
    return sim


def test_counters_close_the_food_scraps_and_store_ledgers():
    """Every unit of prey food, scraps and Myxo store is accounted for: what's on the ground or in
    the cells now = what was there + what came in − what went out, to rounding (B97)."""
    sim = _busy_world()
    w = sim.world
    food0, scraps0, store0 = w.fields.food.sum(), w.fields.scraps.sum(), w.myxo.energy.sum()
    sim.run_for(real_minutes=8.0)
    c = counters.totals(w)
    for name in ("ecoli_killed", "ecoli_starved", "ecoli_burst", "myxo_divisions", "famine_lysed",
                 "famine_spores", "food_eaten", "scraps_eaten", "touch_ticks"):
        assert c[name] > 0, name                                     # the test world exercises every flow
    food_in = c["food_spilled_kill"] + c["food_spilled_starved"]
    assert w.fields.food.sum() == pytest.approx(food0 + food_in - c["food_eaten"] - c["food_lost"], rel=1e-9)
    assert w.fields.scraps.sum() == pytest.approx(
        scraps0 + c["scraps_spilled"] - c["scraps_eaten"] - c["scraps_lost"], rel=1e-9)
    store_in = c["store_from_kills"] + c["store_from_food"] + c["store_from_scraps"] + c["store_arrived"]
    store_out = c["store_upkeep"] + c["store_lysed"] + c["store_spored"] + c["store_dead"]
    assert w.myxo.energy.sum() == pytest.approx(store0 + store_in - store_out, rel=1e-9)
    assert c["food_eaten_killer"] + c["food_spilled_kill"] == pytest.approx(c["kill_content"], rel=1e-9)
    gained = c["store_from_kills"] + c["store_from_food"]
    assert gained <= w.settings.efficiency * (c["food_eaten_killer"] + c["food_eaten"]) + 1e-9


def test_the_stats_rows_carry_the_counters_and_old_rows_get_blanks():
    """Each stats row ends with the running totals; a CSV mixing rows from before a new column
    still writes (old checkpoints resumed after B97)."""
    sim = _busy_world()
    sim.run_for(real_minutes=1.0)
    row = sim.stats.rows[-1]
    assert "ecoli_killed" in row and "ecoli_persisters" in row and "myxo_store" in row
    sim.stats.rows.insert(0, {"t": 0.0, "ecoli": 1})                 # a row from an older run
    path = os.path.join(os.path.dirname(__file__), "_tmp_stats.csv")
    try:
        sim.stats.to_csv(path)
        assert open(path, encoding="utf8").readline().startswith("t,ecoli,")
    finally:
        os.remove(path)


def test_true_false_settings_parse_from_text():
    """'False' and '0' switch a rule off; bool('False') would have been True (B97)."""
    got = cp.parse_overrides(["stringent_scouts=False", "invade_on_contact=0", "famine_exit=on", "seed=3"])
    assert got == {"stringent_scouts": False, "invade_on_contact": False, "famine_exit": True, "seed": 3}
    with pytest.raises(ValueError):
        cp.parse_overrides(["famine_exit=maybe"])


def test_a_restart_with_other_settings_is_caught():
    """A checkpoint made with one seed or setting is not silently reused for another, including a
    restart that leaves out an override the run was made with (B97)."""
    s = make_settings("live", seed=1, efficiency=0.6)
    assert cp.mismatches(s, 1, {"efficiency": 0.6}) == []
    assert sorted(k for k, *_ in cp.mismatches(s, 2, {"efficiency": 0.5})) == ["efficiency", "seed"]
    assert [k for k, *_ in cp.mismatches(s, 1, {})] == ["efficiency"]


def test_switching_founders_off_on_a_running_world_stops_them():
    """The app's founder switch sets the interval to 0 on a running world: no founder lands, not
    one at every ground update (B97 fix)."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, ecoli_seed_interval=10.0)
    sim = Simulation(s, seed_cells=False)
    w = sim.world
    w.settings.ecoli_seed_interval = 0.0
    w.bio_t = 1000.0
    for _ in range(5):
        seeding.add_due_founder(w)
    assert state.count(w.ecoli) == 0
    w.settings.ecoli_seed_interval = 10.0                            # back on: the next one comes an interval later
    seeding.add_due_founder(w)
    assert state.count(w.ecoli) == 0 and w.next_ecoli_seed == 1010.0
    w.bio_t = 1010.0
    seeding.add_due_founder(w)
    assert state.count(w.ecoli) == 1


def test_myxo_dropped_in_directly_are_counted_as_arrivals():
    """Every way Myxo come in goes through seeding.add_myxo, so the ledger counts their stores (B97)."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0)
    w = Simulation(s, seed_cells=False).world
    seeding.uniform_myxo(w, 30)
    seeding.add_myxo(w, seeding.myxo_group(w, np.array([20.0, 20.0]), 10))
    c = counters.totals(w)
    assert c["myxo_arrived"] == 40 and c["store_arrived"] == pytest.approx(w.myxo.energy.sum())
