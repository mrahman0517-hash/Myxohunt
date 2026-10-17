"""Checks for state.py (adding and removing cells) and settings.py (presets, saving)."""
import numpy as np
import pytest

import state
from settings import Settings, make_settings, STARVATION_PRESETS


def _three_ecoli(world):
    """Three E. coli rows with recognisable lengths 2, 3 and 4 µm."""
    cells = state.empty_ecoli()
    new = state.EColiCells(centre=np.zeros((3, 2)), angle=np.zeros(3), length=np.array([2.0, 3.0, 4.0]),
                           colony=np.zeros(3, dtype=np.int64), dormant=np.zeros(3, dtype=bool),
                           starve_time=np.zeros(3), persister=np.zeros(3, dtype=bool),
                           lysis_timer=np.full(3, -1.0), divide_at=np.full(3, 4.0),
                           speed_factor=np.ones(3), uid=state.new_uids(world, 3))
    state.append_rows(cells, new)
    return cells


def _world():
    """A small empty World for bookkeeping tests."""
    return state.new_world(Settings(box=20.0))


def test_append_and_keep_rows_keep_columns_in_step():
    """Removing the middle cell removes its length and its ID together."""
    world = _world()
    cells = _three_ecoli(world)
    state.keep_rows(cells, np.array([True, False, True]))
    assert state.count(cells) == 2
    assert np.allclose(cells.length, [2.0, 4.0])
    assert list(cells.uid) == [0, 2]


def test_uids_are_never_reused():
    """IDs keep counting up, even after cells die."""
    world = _world()
    cells = _three_ecoli(world)
    state.keep_rows(cells, np.array([False, True, True]))
    assert list(state.new_uids(world, 2)) == [3, 4]


def test_keep_rows_rejects_a_wrong_sized_mask():
    """A mask that doesn't match the population is a bug, so it raises an error."""
    world = _world()
    cells = _three_ecoli(world)
    with pytest.raises(ValueError):
        state.keep_rows(cells, np.array([True, False]))


def test_empty_myxo_has_the_right_shapes():
    """An empty population already has 10 discs and a 66-value memory per (future) cell."""
    m = state.empty_myxo(Settings().memory_length)
    assert m.nodes.shape == (0, 10, 2) and m.memory.shape == (0, 66)


def test_settings_modes_and_presets():
    """Live and record worlds differ in size and colony count; the preset sets survival time."""
    assert make_settings("live").box == 150.0 and make_settings("live").start_colonies == 2
    assert make_settings("record").box == 500.0 and make_settings("record").start_colonies == 4
    assert make_settings("live").seed_min_dist_ecoli == 75.0
    assert make_settings("record").seed_min_dist_ecoli == 150.0
    assert make_settings("live", starvation_preset="slow").survive_time == STARVATION_PRESETS["slow"]
    with pytest.raises(AttributeError):
        make_settings("live", no_such_setting=1)


def test_settings_survive_a_save_and_load(tmp_path):
    """Saving to JSON and loading back gives identical settings."""
    s = make_settings("record", speedup=12.0, chemo_strength=0.0)
    path = tmp_path / "settings.json"
    s.to_json(path)
    assert Settings.from_json(path) == s
