"""Checks for killing on contact (milestone 4): pauses, kill success, bursting, ID bookkeeping."""
import numpy as np

import predation
import seeding
import state
from engine import Simulation
from settings import Settings


def _myxo_next_to_prey(**overrides):
    """One horizontal E. coli with one Myxo lying right alongside it (touching)."""
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, **overrides)
    sim = Simulation(s, seed_cells=False)
    w = sim.world
    w.fields.richness[:] = 1.0
    w.fields.nutrients[:] = 1.0
    state.append_rows(w.ecoli, seeding.ecoli_seed(w, [20.0, 20.0]))
    w.ecoli.angle[:] = 0.0
    state.append_rows(w.myxo, seeding.make_myxo(w, np.array([[18.0, 20.85]]), np.array([0.0])))
    return sim


def test_rows_of_finds_cells_by_id_even_after_deaths():
    """IDs stay findable after earlier rows are removed; missing IDs give -1."""
    sim = _myxo_next_to_prey()
    w = sim.world
    for x in (5.0, 10.0, 30.0):
        state.append_rows(w.ecoli, seeding.ecoli_seed(w, [x, 5.0]))
    uids = w.ecoli.uid.copy()
    state.keep_rows(w.ecoli, np.array([True, False, True, True]))
    assert list(predation.rows_of(w.ecoli, uids)) == [0, -1, 1, 2]


def test_predation_runs_on_the_biology_clock_when_scaled():
    """With scaling on, pauses start speed-up times sooner and last speed-up times shorter (B66)."""
    sim = _myxo_next_to_prey(speedup=10.0, scale_predation=True)
    w = sim.world
    for _ in range(200):
        rows, _ = predation.start_pauses(w, np.array([[0, 0]]), np.zeros(1, dtype=bool))
        if len(rows):
            break
    assert np.isclose(w.myxo.pause_left[0], w.settings.kill_delay / 10.0)
    assert predation.predation_clock(Settings(scale_predation=False)) == 1.0


def test_touching_prey_starts_pauses_at_the_tuned_rate():
    """Unscaled (real-time) predation: over 0.5 min of touching, about 30% pause (B15)."""
    sim = _myxo_next_to_prey(scale_predation=False)
    w, s = sim.world, sim.world.settings
    touches = np.array([[0, 0]])
    ticks = int(0.5 / s.dt)
    paused = 0
    for _ in range(2000):
        w.myxo.pause_left[:] = 0.0
        for _ in range(ticks):
            rows, _ = predation.start_pauses(w, touches, np.zeros(1, dtype=bool))
            if len(rows):
                paused += 1
                break
    assert np.isclose(paused / 2000, 1 - np.exp(-s.pause_rate * 0.5), atol=0.03)


def test_a_pause_kills_the_target_about_80_percent_of_the_time():
    """A finished pause bursts its (still living) target in ~80% of 1,000 trials (B14)."""
    sim = _myxo_next_to_prey()
    w = sim.world
    kills = 0
    for _ in range(1000):
        if state.count(w.ecoli) == 0:                      # replace the prey after a kill
            state.append_rows(w.ecoli, seeding.ecoli_seed(w, [20.0, 20.0]))
        w.myxo.pause_left[:] = 1e-6
        w.myxo.pause_target[:] = w.ecoli.uid[0]
        _, killed = predation.finish_kills(w, predation.count_down_pauses(w))
        kills += len(killed)
    assert np.isclose(kills / 1000, 0.8, atol=0.04)


def test_a_kill_feeds_the_killer_and_spills_the_rest():
    """The killer eats its share (a quarter) of the contents at once; the rest spills as food
    for the pack, with smell and wall left on the ground (B17, B65, B76)."""
    sim = _myxo_next_to_prey(kill_success=1.0)
    w = sim.world
    share = w.settings.killer_share
    contents = w.settings.ecoli_content * w.ecoli.length[0] / 3.0
    before = w.myxo.energy[0]
    w.myxo.pause_left[:] = 1e-6
    w.myxo.pause_target[:] = w.ecoli.uid[0]
    killers, killed = predation.finish_kills(w, predation.count_down_pauses(w))
    assert state.count(w.ecoli) == 0 and len(killed) == 1 and killers[0] == w.myxo.uid[0]
    assert np.isclose(w.myxo.energy[0] - before, share * contents * w.settings.efficiency)
    assert np.isclose(w.fields.food.sum(), (1.0 - share) * contents)
    assert w.fields.attractant.sum() > 0 and w.fields.matrix.sum() > 0
    assert w.myxo.pause_target[0] == -1


def test_absorption_never_exceeds_the_growth_anchored_ceiling():
    """On a huge pile of food a hungry cell still absorbs at most uptake_max per bio minute (B65)."""
    sim = _myxo_next_to_prey()
    w = sim.world
    w.myxo.energy[:] = 0.0
    w.fields.food[:] = 1e6
    import myxo_energy
    myxo_energy.uptake(w, dt_bio=1.0)
    assert np.isclose(w.myxo.energy[0], w.settings.uptake_max * w.settings.efficiency)


def test_full_simulation_myxo_beside_prey_eventually_kills_it():
    """In the running engine, a Myxo lying against an E. coli pauses, stands still, and kills it."""
    sim = _myxo_next_to_prey(kill_success=1.0, pause_rate=50.0, ecoli_doubling=1e9, F_star=0.0)
    w = sim.world
    saw_pause = False
    for _ in range(int(3.0 / w.settings.dt)):
        sim.step()
        saw_pause |= bool((w.myxo.pause_left > 0).any())
        if state.count(w.ecoli) == 0:
            break
    assert saw_pause
    assert state.count(w.ecoli) == 0


def test_ghosts_keep_giving_off_smell_while_they_last():
    """An eaten spot keeps smelling of prey: ghosts (matrix) give off attractant at every ground
    update, and once they are gone the smell dies away within hours (B74)."""
    import fields_update
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0)
    w = Simulation(s, seed_cells=False).world
    w.fields.matrix[20, 20] = 1.0                            # one ghost
    fields_update.update_fields(w, 60.0)
    smell = w.fields.attractant.sum()
    assert smell > 0.0
    w.fields.matrix[:] = 0.0                                 # the ghost has faded away
    fields_update.update_fields(w, 600.0)
    assert w.fields.attractant.sum() < 0.01 * smell


def test_myxo_crawl_over_prey_but_still_touch_it():
    """With crawling over prey on (B76), a Myxo lying on an E. coli neither shoves nor is shoved,
    yet the touch still counts for killing; with it off, the two push apart."""
    import contacts
    for crawl in (True, False):
        w = _myxo_next_to_prey(myxo_crawl_over_prey=crawl).world
        w.myxo.nodes[0] += w.ecoli.centre[0] - w.myxo.nodes[0].mean(axis=0)   # right on top of the prey
        nodes, centre = w.myxo.nodes.copy(), w.ecoli.centre.copy()
        touches = contacts.resolve_contacts(w)
        assert len(touches) == 1
        moved = np.abs(w.myxo.nodes - nodes).max() + np.abs(w.ecoli.centre - centre).max()
        assert moved == 0.0 if crawl else moved > 0.0


def test_living_prey_start_rippling_along_their_colonys_direction():
    """Inside a packed living colony, with no ghosts at all, cells ripple, lined up with that
    colony's direction (contact with prey triggers rippling, Berleman 2006; B76). With the
    living-prey weight at 0, only ghosts count (B11)."""
    import fields_update
    import myxo_alignment as align
    for weight in (1.0, 0.0):
        s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, ripple_live_prey_weight=weight)
        w = Simulation(s, seed_cells=False).world
        xs, ys = np.meshgrid(np.arange(10.0, 30.0, 2.1), np.arange(10.0, 30.0, 1.0))
        for p in np.stack([xs.ravel(), ys.ravel()], axis=1):     # a block of 2 µm rods, packed
            state.append_rows(w.ecoli, seeding.ecoli_seed(w, p))
        w.ecoli.angle[:], w.ecoli.colony[:] = 0.0, 0
        w.colony_axis[0] = np.pi / 6                              # this colony ripples at 30°
        fields_update.refresh_sensed_maps(w)
        head = np.array([[20.0, 20.0]])
        if weight > 0:
            assert align.ripple_mask(w, head)[0]
            assert np.isclose(align.local_axis(w, head)[0] % np.pi, np.pi / 6)
        else:
            assert not align.ripple_mask(w, head)[0]
