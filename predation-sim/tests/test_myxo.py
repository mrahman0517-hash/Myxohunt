"""Checks for Myxo movement, frustration, memory and reversals (milestone 3)."""
import os
import sys

import numpy as np

import myxo_alignment as align
import myxo_body
import myxo_modes
import myxo_reversals as rev
import seeding
import state
from engine import Simulation
from settings import Settings

REPRO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "paper-reproduction"))


def _reproduction():
    """The validated paper-reproduction functions and parameters, for side-by-side checks."""
    sys.path.insert(0, REPRO)
    import functions as old_fn                     # noqa: E402
    from datatypes import Params                   # noqa: E402
    sys.path.remove(REPRO)
    return old_fn, Params()


def _one_cell_world(**overrides):
    """An empty 40 µm world with one horizontal Myxo cell (a trail follower unless asked) and no E. coli."""
    options = dict(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, scout_start_rate=0.0)
    s = Settings(**{**options, **overrides})
    sim = Simulation(s, seed_cells=False)
    state.append_rows(sim.world.myxo, seeding.make_myxo(sim.world, np.array([[20.0, 20.0]]), np.array([0.0])))
    sim.world.myxo.age[:] = 0.0
    return sim


def test_frustration_worked_cases():
    """The table from model-foundations §3.4: as intended 0, half speed 0.5, stopped 1, backwards 2."""
    vt = np.array([[4.0, 0.0]] * 4)
    vr = np.array([[4.0, 0.0], [2.0, 0.0], [0.0, 0.0], [-4.0, 0.0]])
    assert np.allclose(rev.frustration(vt, vr), [0.0, 0.5, 1.0, 2.0])


def test_reversal_curves_match_the_reproduction():
    """Refractory period and reversal rate are identical to the validated code."""
    old_fn, p = _reproduction()
    s = Settings()
    sig = np.linspace(0, 0.3, 31)
    assert np.allclose(rev.refractory_period(sig, s), old_fn.refractory_period(sig, p))
    assert np.allclose(rev.reversal_rate(sig, s), old_fn.reversal_rate(sig, p))


def test_per_cell_memory_matches_the_reproduction_when_nobody_pauses():
    """With all cells active, per-cell memory gives exactly the old global-slot signal."""
    old_fn, p = _reproduction()
    s = Settings()
    w, norm = rev.memory_weights(s)
    K, rng = s.memory_length, np.random.default_rng(0)
    mem_new, slots = np.zeros((3, K)), np.zeros(3, dtype=np.int64)
    mem_old = np.zeros((3, K))
    for step in range(100):
        f = rng.random(3) * 2
        rev.write_memory(mem_new, slots, f, np.ones(3, dtype=bool))
        mem_old[:, step % K] = f
        old = old_fn.smoothed_signal(mem_old, step % K, w, norm)
    assert np.allclose(rev.smoothed_signal(mem_new, slots, w, norm), old)


def test_a_free_cell_moves_at_4_um_per_min():
    """A lone cell's body centre advances at the paper's 4 µm/min."""
    sim = _one_cell_world(F_star=0.0)               # no reversals, so it keeps going one way
    start = sim.world.myxo.nodes.mean(axis=1).copy()
    sim.run_for(real_minutes=1.0)
    moved = np.linalg.norm(sim.world.myxo.nodes.mean(axis=1) - start)
    assert np.isclose(moved, 4.0, rtol=0.03)


def test_a_paused_cell_stands_still_and_freezes_its_clock_and_memory():
    """During a killing pause: no pull, no ageing, no new memory (B16)."""
    sim = _one_cell_world()
    m = sim.world.myxo
    m.pause_left[:] = 1.0
    nodes, age, slot = m.nodes.copy(), m.age.copy(), m.mem_slot.copy()
    for _ in range(50):
        sim.step_fast()
    assert np.allclose(m.nodes, nodes, atol=1e-9)
    assert np.allclose(m.age, age) and np.array_equal(m.mem_slot, slot)


def test_reversal_swaps_head_and_tail_and_resets_the_clock():
    """A forced reversal makes the old tail the new head and restarts the clock."""
    sim = _one_cell_world()
    m = sim.world.myxo
    head, tail = m.nodes[0, 0].copy(), m.nodes[0, -1].copy()
    m.age[:] = 10.0
    m.signal[:] = 0.5                                   # very jammed: past the refractory period
    flips = [rev.decide_reversals(sim.world, np.ones(1, dtype=bool), np.ones(1))[0] for _ in range(3000)]
    assert any(flips)
    assert np.allclose(sim.world.myxo.nodes[0, 0], tail) or np.allclose(sim.world.myxo.nodes[0, 0], head)
    assert sim.world.myxo.age[0] < 10.0


def test_pull_toward_prey_changes_reversals_only_when_switched_on():
    """Factor 1 at strength 0; heading up an attractant slope lowers the reversal factor."""
    sim = _one_cell_world(chemo_strength=0.0)
    heads, uphill = sim.world.myxo.nodes[:, 0], np.array([[1.0, 0.0]])
    assert np.allclose(rev.chemotaxis_factor(sim.world, heads, uphill), 1.0)
    sim.world.settings.chemo_strength = 2.0
    x = np.arange(sim.world.fields.attractant.shape[0])
    sim.world.fields.attractant[:] = 0.05 * x[:, None]       # attractant rises toward +x
    up = rev.chemotaxis_factor(sim.world, heads, uphill)
    down = rev.chemotaxis_factor(sim.world, heads, -uphill)
    assert up[0] < 1.0 < down[0]


def test_scouts_ignore_slime_and_wander_while_followers_take_the_trail():
    """On a slime trail at 30° off its heading, a follower turns toward it; a scout doesn't care,
    and its path bends only by small random turns (B67)."""
    for scout in (False, True):
        sim = _one_cell_world(F_star=0.0, scout_turn_noise=0.0,
                              scout_start_rate=1e-9, scout_episode=1e9)   # nobody switches mid-test
        w = sim.world
        w.myxo.scout[:] = scout
        head = w.myxo.nodes[0, 0]
        heading = myxo_body.head_direction(w.myxo.nodes)[0]
        angle = np.arctan2(heading[1], heading[0]) + np.radians(30)
        trail = np.array([np.cos(angle), np.sin(angle)])        # 30° off the cell's heading
        pts = head + np.outer(np.linspace(0.5, 5, 40), trail)
        import grids
        grids.deposit(w.fields.eps, pts, 5.0, w.settings.box)
        before = myxo_body.head_direction(w.myxo.nodes)[0].copy()
        for _ in range(60):
            sim.step_fast()
        after = myxo_body.head_direction(w.myxo.nodes)[0]
        cross = before[0] * after[1] - before[1] * after[0]
        turned = np.degrees(np.arctan2(cross, before @ after))
        if scout:
            assert abs(turned) < 1.0       # ignores the trail entirely (random turns off here)
        else:
            assert abs(turned) > 10        # pulled toward the trail


def test_scouts_and_starving_loners_glide_at_their_own_speed_without_feeling_jammed():
    """A free scout moves 10% faster (4.4 µm/min, as lone cells do; Spormann & Kaiser 1999); a lone
    cell 15 bio-h into starvation moves 1.5× (6 µm/min). Each judges its progress against its own
    speed, so neither builds up false frustration (B71, B75, B80)."""
    for is_scout, energy, starved, expected in ((True, 60.0, 0.0, 4.4), (False, 10.0, 900.0, 6.0)):
        sim = _one_cell_world(F_star=0.0, scout_start_rate=1e-9, scout_episode=1e9, scout_turn_noise=0.0)
        m = sim.world.myxo
        m.energy[:], m.scout[:], m.starve_time[:] = energy, is_scout, starved
        start = m.nodes.mean(axis=1).copy()
        sim.run_for(real_minutes=1.0)
        moved = np.linalg.norm(m.nodes.mean(axis=1) - start)
        assert np.isclose(moved, expected, rtol=0.03)
        assert m.signal[0] < 0.02                             # far below the 0.08 threshold


def test_scouts_follow_the_prey_smell_more_strongly():
    """On the same attractant slope, a scout's reversal factor moves further from 1 than a
    follower's: fewer reversals heading uphill, more heading downhill (B72)."""
    sim = _one_cell_world(chemo_strength=2.0, scout_start_rate=1e-9, scout_episode=1e9)
    w = sim.world
    x = np.arange(w.fields.attractant.shape[0])
    w.fields.attractant[:] = 0.05 * x[:, None]                # attractant rises toward +x
    heads, uphill = w.myxo.nodes[:, 0], np.array([[1.0, 0.0]])
    factors = {}
    for is_scout in (False, True):
        w.myxo.scout[:] = is_scout
        boost = myxo_modes.smell_factors(w)
        factors[is_scout] = (rev.chemotaxis_factor(w, heads, uphill, boost)[0],
                             rev.chemotaxis_factor(w, heads, -uphill, boost)[0])
    assert factors[True][0] < factors[False][0] < 1.0 < factors[False][1] < factors[True][1]


def _three_cells(**overrides):
    """Three cells in an empty world: an ordinary cell, a scout and a stringent (starving) cell."""
    w = _one_cell_world(scout_start_rate=1e-9, scout_episode=1e9, **overrides).world
    state.append_rows(w.myxo, seeding.make_myxo(w, np.array([[10.0, 10.0], [30.0, 30.0]]), np.zeros(2)))
    w.myxo.scout[:] = [False, True, False]
    w.myxo.starve_time[:] = [0.0, 0.0, w.settings.behaviour_delay]
    return w


def test_starving_cells_follow_the_prey_smell_as_strongly_as_scouts():
    """The lipid attractant works in starving cells (Kearns 2001): stringent cells get the same ×1.5
    smell boost as scouts, ordinary cells none (B72, B80)."""
    assert np.allclose(myxo_modes.smell_factors(_three_cells()), [1.0, 1.5, 1.5])


def test_only_stringent_cells_take_up_food_more_readily():
    """Food affinity: ordinary cells and scouts 1, stringent cells 1.15 (B72)."""
    assert np.allclose(myxo_modes.affinity_factors(_three_cells()), [1.0, 1.0, 1.15])


def test_starving_cells_speed_up_over_15_hours_once_their_behaviour_changes():
    """Speed, timed from when the prey food ran out: unchanged before behaviour_delay (2 bio-h),
    then 1 + 0.5 × (time/15 h), ×1.5 from 15 bio-h on (Jelsbak 2002). There's no slow-down when
    packed any more (B75, B83, B84)."""
    w = _one_cell_world().world
    m, s = w.myxo, w.settings
    m.starve_time[:] = s.behaviour_delay - 1.0
    assert myxo_modes.speed_factors(w)[0] == 1.0
    m.starve_time[:] = s.behaviour_delay
    expected = 1.0 + (s.stringent_loner_speed - 1.0) * s.behaviour_delay / s.stringent_speedup_time
    assert np.isclose(myxo_modes.speed_factors(w)[0], expected)
    m.starve_time[:] = 900.0
    assert np.isclose(myxo_modes.speed_factors(w)[0], 1.5)


def test_fast_stringent_effects_at_30_minutes_starving_behaviours_at_2_hours():
    """After 30 bio-min of starving a cell is stringent (better uptake now, cost cut and no
    division in myxo_energy) but has no keener smell or speed change yet; after 2 bio-h it has
    both (B84)."""
    w = _one_cell_world().world
    w.myxo.starve_time[:] = 60.0
    assert myxo_modes.stringent(w)[0] and not myxo_modes.starving_behaviour(w)[0]
    assert np.isclose(myxo_modes.affinity_factors(w)[0], 1.15)
    assert myxo_modes.smell_factors(w)[0] == 1.0 and myxo_modes.speed_factors(w)[0] == 1.0
    w.myxo.starve_time[:] = 120.0
    assert np.isclose(myxo_modes.smell_factors(w)[0], 1.5) and myxo_modes.speed_factors(w)[0] > 1.0


def test_a_starving_scout_is_never_slower_than_a_starving_cell():
    """A starving scout keeps every starving perk and moves at whichever is faster, its scout speed
    or its starving speed, so scouting never puts a cell at a disadvantage (B83)."""
    w = _three_cells()
    w.myxo.scout[:] = [False, True, True]
    w.myxo.starve_time[:] = [0.0, 0.0, 900.0]                 # the third: a starving scout, 15 h in
    speeds = myxo_modes.speed_factors(w)
    assert np.isclose(speeds[1], 1.1) and np.isclose(speeds[2], 1.5)
    assert np.isclose(myxo_modes.affinity_factors(w)[2], 1.15)


def test_the_starvation_clock_follows_prey_food_not_the_store():
    """The clock starts when prey food within reach falls below 1 unit, keeps running through
    crumbs (thin prey food) and scraps, and resets only when prey food is back above 3 units, a
    real meal. The store plays no part (B83)."""
    w = _one_cell_world().world
    m, f = w.myxo, w.fields
    m.energy[:] = 200.0                                       # well stocked, but no food outside
    myxo_modes.update_starve_clock(w, 20.0)
    myxo_modes.update_starve_clock(w, 20.0)
    assert np.isclose(m.starve_time[0], 40.0) and myxo_modes.stringent(w)[0]
    f.scraps[:] = 10.0                                        # scraps never end starvation
    f.food[:] = 0.2                                           # thin prey food: a crumb (0.2 × 13 squares)
    myxo_modes.update_starve_clock(w, 20.0)
    assert np.isclose(m.starve_time[0], 60.0)
    f.food[:] = 1.0                                           # a real meal within reach (13 units)
    myxo_modes.update_starve_clock(w, 20.0)
    assert m.starve_time[0] == 0.0 and not myxo_modes.stringent(w)[0]
    m.energy[:] = 5.0                                         # nearly empty, but fed outside
    myxo_modes.update_starve_clock(w, 20.0)
    assert m.starve_time[0] == 0.0


def _crowd(n=1000, **overrides):
    """n + 1 cells scattered over an empty 40 µm world (default scouting), none scouting, no food."""
    w = _one_cell_world(scout_start_rate=Settings().scout_start_rate, **overrides).world
    starts = np.random.default_rng(0).uniform(0, 40, size=(n, 2))
    state.append_rows(w.myxo, seeding.make_myxo(w, starts, np.zeros(n)))
    assert not w.myxo.scout.any()                             # new cells never start as scouts
    return w


def test_with_no_prey_food_10_percent_scout_at_once_and_about_half_get_a_turn_in_10_bio_hours():
    """At zero prey food the start rate is 0.011 per real min and spells last 10 min, so about 10% of
    cells scout at any moment and 1 − e^(−0.011 × 60) ≈ 49% get a turn within an hour of real time
    (10 bio-h). The store doesn't matter (B83). B83's rotating scouts are an option since B95
    (random ends, no rest, no cap)."""
    w = _crowd(scout_random_end=True, scout_rest_time=0.0, scout_max_share=1.0)
    w.myxo.energy[:] = np.linspace(5.0, 205.0, state.count(w.myxo))
    ever = np.zeros(state.count(w.myxo), dtype=bool)
    shares = []
    for i in range(int(60.0 / w.settings.dt)):               # 60 real minutes
        myxo_modes.update_scouts(w)
        ever |= w.myxo.scout
        if i * w.settings.dt > 40.0:
            shares.append(w.myxo.scout.mean())
    assert np.isclose(np.mean(shares), 0.10, atol=0.02)
    assert np.isclose(ever.mean(), 0.49, atol=0.05)


def test_scouting_needs_scarce_prey_food_and_stops_when_it_is_back():
    """No scouting starts with prey food at 3 units or more within reach; the chance at 1.5 units
    is half its top; a scout stops at once when prey food is back above 3 units. Scraps don't count
    as food here either (B83)."""
    w = _crowd(n=200)
    s = w.settings
    food = np.array([0.0, 1.5, 3.0, 13.0])
    assert np.allclose(myxo_modes.scout_chance(w, food) / s.scout_start_rate, [1.0, 0.5, 0.0, 0.0])
    w.fields.food[:] = 1.0                                    # 13 units within reach
    w.fields.scraps[:] = 0.0
    for _ in range(1000):
        myxo_modes.update_scouts(w)
    assert not w.myxo.scout.any()
    w.myxo.scout[:] = True
    w.fields.food[:] = 0.0
    w.fields.scraps[:] = 5.0                                  # scraps don't stop the search
    myxo_modes.update_scouts(w)
    assert w.myxo.scout.mean() > 0.95
    w.fields.food[:] = 1.0                                    # real prey food: stop and eat
    myxo_modes.update_scouts(w)
    assert not w.myxo.scout.any()


def test_seeds_start_away_from_colonies():
    """No disc of any Myxo starts within 30 µm of an E. coli, for small and big groups (B47, B72)."""
    from geometry import min_image
    for groups, size, radius in ((5, 30, 8.0), (3, 300, 25.0)):
        sim = Simulation(Settings(box=150.0, seed=4, myxo_groups=groups, myxo_group_size=size,
                                  myxo_group_radius=radius, myxo_arrival_window=0.0))
        w = sim.world
        assert state.count(w.myxo) == groups * size + 10
        discs = w.myxo.nodes.reshape(-1, 2)
        d = np.linalg.norm(min_image(discs[:, None] - w.ecoli.centre[None], 150.0), axis=-1)
        assert d.min() >= 30.0


def test_myxo_seeds_come_in_from_outside_over_the_first_10_bio_hours():
    """No Myxo at the start; each of the 15 seeds (5 groups of 20, 10 single cells) comes in at a
    random time within the first 600 bio min (B78)."""
    w = Simulation(Settings(box=150.0, seed=4)).world
    assert state.count(w.myxo) == 0
    times = [t for t, _ in w.myxo_arrivals]
    assert len(times) == 15 and 0.0 < min(times) and max(times) <= 600.0
    w.bio_t = 300.0
    seeding.add_due_myxo(w)
    early = state.count(w.myxo)
    w.bio_t = 600.0
    seeding.add_due_myxo(w)
    assert 0 < early < 5 * 20 + 10
    assert state.count(w.myxo) == 5 * 20 + 10 and not w.myxo_arrivals


def test_scouts_stay_scouts_until_prey_rest_afterwards_and_never_exceed_the_cap():
    """B95: with no prey food, spells don't end at random, so scouts stay scouts; at most 10% of
    cells scout; a spell ends when prey food turns up, and that cell rests before scouting again."""
    w = _crowd()
    for _ in range(int(60.0 / w.settings.dt)):                # 60 real minutes, no food anywhere
        myxo_modes.update_scouts(w)
        assert w.myxo.scout.mean() <= w.settings.scout_max_share + 1e-9
    first = w.myxo.scout.copy()
    assert first.mean() > 0.09                                # the cap fills up
    for _ in range(200):
        myxo_modes.update_scouts(w)
    assert (w.myxo.scout[first]).all()                        # nobody gave up without prey
    w.fields.food[:] = 50.0                                   # prey food everywhere: every spell ends
    myxo_modes.update_scouts(w)
    assert not w.myxo.scout.any()
    assert myxo_modes.resting(w)[first].all()                 # and those cells must rest now


def test_a_starving_scout_stops_scouting_unless_starving_cells_may_scout():
    """B95, B97: a scout keeps scouting through the first starving hours (stringent from 30 bio-min);
    with stringent_scouts off it stops once it has starved for behaviour_delay (2 bio-h); with it on
    (the default since B97) it carries on."""
    for allowed in (False, True):
        w = _crowd(n=200, stringent_scouts=allowed)
        w.myxo.scout[:] = True
        w.myxo.starve_time[:] = w.settings.stringent_delay + 1.0
        myxo_modes.update_scouts(w)
        assert w.myxo.scout.all()                             # stringent, but not yet starving 2 bio-h
        w.myxo.starve_time[:] = w.settings.behaviour_delay + 1.0
        myxo_modes.update_scouts(w)
        assert w.myxo.scout.all() == allowed


def test_cells_in_their_first_starving_hours_may_start_scouting():
    """B97: a cell that has starved past stringent_delay but not yet behaviour_delay may still start
    a spell; one starved longer may not, when stringent_scouts is off."""
    for starved, expect_some in ((30.0 + 1.0, True), (120.0 + 1.0, False)):
        w = _crowd(n=400, stringent_scouts=False)
        w.settings.scout_start_rate = 5.0                     # high, so starts are near certain if allowed
        w.myxo.starve_time[:] = starved
        for _ in range(20):
            myxo_modes.update_scouts(w)
        assert w.myxo.scout.any() == expect_some


def test_leading_cells_scouts_and_invaders_turn_toward_the_prey_smell():
    """B95: a cell heading across a smell rising to its left turns left; with no smell nothing turns."""
    w = _one_cell_world().world
    heads = np.array([[20.0, 20.0]])
    assert align.smell_turn(w, heads, np.array([0.0]))[0] == 0.0          # flat smell: no turn
    w.fields.attractant[:] = np.arange(w.fields.attractant.shape[1])[None, :] * 1.0   # rises with y
    turn = align.smell_turn(w, heads, np.array([0.0]))[0]                 # heading +x, smell up +y
    assert turn > 0
