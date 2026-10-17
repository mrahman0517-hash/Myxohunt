"""The new engine must move Myxo exactly like the validated paper reproduction (decision-log A13).

Both engines start from identical cells with the same random sequence, no E. coli, no slime
fading and no pull toward prey; disc positions and signals must then match tick for tick.
"""
import os
import sys

import numpy as np

import state
from settings import Settings

REPRO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "paper-reproduction"))


def _old_engine():
    """Import the reproduction's engine without clashing with predation-sim's own engine.py."""
    saved = {k: sys.modules.pop(k) for k in ("engine", "functions", "datatypes") if k in sys.modules}
    sys.path.insert(0, REPRO)
    try:
        import engine as old_engine                  # noqa: E402
        from datatypes import Params                 # noqa: E402
    finally:
        sys.path.remove(REPRO)
        for k in ("engine", "functions", "datatypes"):
            sys.modules.pop(k, None)
        sys.modules.update(saved)
    return old_engine, Params


def _copy_cells(old_pop):
    """The reproduction's cells, as predation-sim Myxo (trail followers, not paused)."""
    n = old_pop.n
    return state.MyxoCells(
        nodes=old_pop.nodes.copy(), age=old_pop.age.copy(), memory=np.zeros_like(old_pop.memory),
        mem_slot=np.zeros(n, dtype=np.int64), signal=np.zeros(n), energy=np.full(n, 60.0),
        pause_left=np.zeros(n), pause_target=np.full(n, -1), scout=np.zeros(n, dtype=bool),
        starve_time=np.zeros(n),
        uid=np.arange(n))


def test_rippling_on_matrix_matches_the_reproduction_tick_for_tick():
    """Cells on full matrix with ripple axis 0 move exactly like the reproduction's rippling mode
    (milestone 5): positions and signals match for 400 ticks (A13 extended to rippling)."""
    old_engine, Params = _old_engine()
    from engine import Simulation
    old = old_engine.Simulation(Params(mode="rippling", n_cells=300, box=40.0, T=5.0), seed=3)
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0, eps_fade_time=float("inf"),
                 matrix_half_life=float("inf"), chemo_strength=0.0, speedup=1.0, scout_start_rate=0.0)
    new = Simulation(s, seed_cells=False)
    f = new.world.fields
    f.matrix[:], f.matrix_smooth[:], f.axis_c[:], f.axis_s[:] = 1.0, 1.0, 1.0, 0.0   # axis 0, everywhere
    new.world.myxo = _copy_cells(old.pop)
    old.rng, new.world.rng = np.random.default_rng(11), np.random.default_rng(11)
    for _ in range(400):
        old.step()
        new.step()
    assert np.abs(old.pop.nodes - new.world.myxo.nodes).max() < 1e-9
    assert np.abs(old.pop.signal - new.world.myxo.signal).max() < 1e-12


def test_new_engine_matches_reproduction_tick_for_tick():
    """150 swarming cells in a 40 µm box: identical positions and signals for 400 ticks (2 min)."""
    old_engine, Params = _old_engine()
    from engine import Simulation
    old = old_engine.Simulation(Params(mode="swarming", n_cells=150, box=40.0, T=5.0), seed=2)
    s = Settings(box=40.0, start_colonies=0, myxo_groups=0, myxo_singles=0,
                 eps_fade_time=float("inf"), chemo_strength=0.0, speedup=1.0, scout_start_rate=0.0)
    new = Simulation(s, seed_cells=False)
    n = old.pop.n
    new.world.myxo = state.MyxoCells(
        nodes=old.pop.nodes.copy(), age=old.pop.age.copy(), memory=np.zeros_like(old.pop.memory),
        mem_slot=np.zeros(n, dtype=np.int64), signal=np.zeros(n), energy=np.full(n, 60.0),
        pause_left=np.zeros(n), pause_target=np.full(n, -1), scout=np.zeros(n, dtype=bool),
        starve_time=np.zeros(n),
        uid=np.arange(n))
    old.rng, new.world.rng = np.random.default_rng(7), np.random.default_rng(7)
    reversals = 0
    for _ in range(400):
        old.step()
        new.step()
        reversals += int(new.flipped.sum())
    assert reversals > 0                                       # the reversal rule was exercised
    assert np.abs(old.pop.nodes - new.world.myxo.nodes).max() < 1e-9
    assert np.abs(old.pop.signal - new.world.myxo.signal).max() < 1e-12
