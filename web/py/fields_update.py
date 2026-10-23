"""
fields_update.py — the slow changes to the ground maps, run every `grid_every` ticks (B51):
nutrients regrow and spread; food and attractant spread and fade; matrix and slime fade; the
prey material (ghosts and living prey) and its ripple direction are re-averaged for the ripple
check.
"""
import numpy as np

import counters
import ecoli_body
import grids


def update_nutrients(world, dt_bio):
    """Nutrients regrow toward each spot's own richness, then spread (B33, B48)."""
    s, f = world.settings, world.fields
    grids.regrow(f.nutrients, f.richness, s.nutrient_regrow_rate, dt_bio)
    f.nutrients = grids.diffuse(f.nutrients, s.nutrient_diffusion, dt_bio, f.spacing)


def update_spills(world, dt_bio):
    """Spilled prey food, scraps and attractant spread out and slowly disappear (B17, B32).
    Scraps from dead Myxo spread and fade exactly like prey food (B83). Ghosts (the matrix) keep
    giving off attractant for as long as they last, so eaten spots go on smelling of prey while
    their food is still there (B74)."""
    s, f = world.settings, world.fields
    food_before, scraps_before = f.food.sum(), f.scraps.sum()
    f.food = grids.diffuse(f.food, s.food_diffusion, dt_bio, f.spacing)
    grids.fade(f.food, s.food_decay_time, dt_bio)
    f.scraps = grids.diffuse(f.scraps, s.food_diffusion, dt_bio, f.spacing)
    grids.fade(f.scraps, s.food_decay_time, dt_bio)
    counters.add(world, "food_lost", food_before - f.food.sum())          # fading (and rounding at 0)
    counters.add(world, "scraps_lost", scraps_before - f.scraps.sum())
    f.attractant += s.ghost_attractant_rate * f.matrix * dt_bio
    f.attractant = grids.diffuse(f.attractant, s.attractant_diffusion, dt_bio, f.spacing)
    grids.fade(f.attractant, s.attractant_decay_time, dt_bio)


def update_matrix_and_slime(world, dt_bio):
    """Matrix (with its direction) and slime fade."""
    s, f = world.settings, world.fields
    matrix_fade_time = s.matrix_half_life / np.log(2)
    for grid in (f.matrix, f.axis_c, f.axis_s):
        grids.fade(grid, matrix_fade_time, dt_bio)
    grids.fade(f.eps, s.eps_fade_time, dt_bio)
    grids.fade(f.eps_scout, s.eps_fade_time * s.scout_slime_fade, dt_bio)      # scout slime lasts longer (B71)


def live_prey_maps(world):
    """Living E. coli as maps: cells per µm², and the doubled-angle terms of their colonies'
    ripple directions (B13, B38), so that contact with living prey can start rippling (B76).

    Returns:
        (amount, cos 2θ sum, sin 2θ sum), each a coarse grid.
    """
    s, f, e = world.settings, world.fields, world.ecoli
    maps = [np.zeros_like(f.matrix) for _ in range(3)]
    alive = e.lysis_timer < 0
    if s.ripple_live_prey_weight <= 0 or not alive.any():
        return maps
    k = s.ecoli_points
    pts = ecoli_body.contact_points(e, s).reshape(-1, k, 2)[alive].reshape(-1, 2)
    theta = np.repeat(np.asarray(world.colony_axis)[e.colony[alive]], k)
    share = 1.0 / (k * f.spacing ** 2)                      # one cell spread over its k points
    grids.deposit(maps[0], pts, share, s.box)
    grids.deposit(maps[1], pts, share * np.cos(2.0 * theta), s.box)
    grids.deposit(maps[2], pts, share * np.sin(2.0 * theta), s.box)
    return maps


def smooth_prey_material(world):
    """Prey material around each square for the ripple check, averaged over matrix_sense_radius:
    ghosts plus living prey (B43, B76). The ripple direction is averaged over the same circle,
    so a cell between ghosts still knows its colony's direction."""
    s, f = world.settings, world.fields
    live, live_c, live_s = live_prey_maps(world)
    w = s.ripple_live_prey_weight
    f.matrix_smooth = grids.disc_average(f.matrix + w * live, s.matrix_sense_radius, f.spacing)
    f.axis_c_smooth = grids.disc_average(f.axis_c + w * live_c, s.matrix_sense_radius, f.spacing)
    f.axis_s_smooth = grids.disc_average(f.axis_s + w * live_s, s.matrix_sense_radius, f.spacing)


def refresh_sensed_maps(world):
    """The maps cells read directly (ripple trigger and direction), rebuilt from the current cells;
    also used once when the world is built. (The crowding map was removed in B84.)"""
    smooth_prey_material(world)


def update_fields(world, dt_bio):
    """All slow ground changes, in order."""
    update_nutrients(world, dt_bio)
    update_spills(world, dt_bio)
    update_matrix_and_slime(world, dt_bio)
    refresh_sensed_maps(world)
