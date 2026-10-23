"""
myxo_modes.py — how a cell reacts to the prey food around it (B70, B71, B83). Real cells start
the stringent response when food runs out outside, not when their reserves run low (Manoil &
Kaiser 1980; Harris 1998), so these rules read the prey food within reach, never the store:

  starvation clock  starts when the prey food within reach falls below living_food (too little
                    to cover running costs), and resets only when a real meal is back: prey food
                    above scout_food (30% of top-speed food). Scraps from dead Myxo never count
                    (Hoang & Kroos 2018: a small dose of food doesn't stop starvation).
  stringent mode    once the clock passes stringent_delay (30 bio-min), the fast effects: running
                    costs cut to 30% on the core (in myxo_energy.upkeep), no division, takes up
                    scarce food 15% more readily (B72, B84).
  starving behaviour once the clock passes behaviour_delay (2 bio-h): follows the prey smell more
                    keenly (B80) and speeds up, to 1.5× over 15 bio-h of starving (Jelsbak 2002)
                    (B75, B84).
  scout mode        a lucky draw: the chance starts when prey food within reach drops below
                    scout_food and is at its top at zero food, where 10% of cells scout at once.
                    Off-trail A-motility, stronger slime, keener smell, steering toward the smell,
                    no division. Since B95 a spell ends when the scout finds prey food or has starved
                    for behaviour_delay (B97; stringent_delay before), random ends optional; a cell
                    rests before scouting again, and at most 10% of cells scout at once. Cells starving
                    that long scout only if stringent_scouts is on.

The clock runs on the biology clock; switching scout mode on and off runs on the real clock,
like movement.
"""
import numpy as np

import counters
import grids


def food_around(world):
    """Prey food within absorb_radius of each cell's head: (N,). Scraps don't count."""
    s, f, m = world.settings, world.fields, world.myxo
    if len(m.uid) == 0:
        return np.zeros(0)
    _, vals = grids.disc_squares(f.food, m.nodes[:, 0], s.box, s.absorb_radius, f.spacing)
    return vals.sum(axis=1)


def stringent(world):
    """True for cells in stringent mode: starving for at least stringent_delay (B83)."""
    return world.myxo.starve_time >= world.settings.stringent_delay


def starving_behaviour(world):
    """True for cells starving long enough for the starving behaviours (keener smell, speed
    change): at least behaviour_delay (B84)."""
    return world.myxo.starve_time >= world.settings.behaviour_delay


def update_starve_clock(world, dt_bio):
    """The starvation clock: it starts when prey food within reach falls below living_food, keeps
    running through crumbs and scraps, and goes back to 0 once prey food within reach is above
    scout_food, a real meal (B83)."""
    s, m = world.settings, world.myxo
    food = food_around(world)
    running = (m.starve_time > 0) | (food < s.living_food)
    counters.add(world, "clock_resets", int(((m.starve_time > 0) & (food >= s.scout_food)).sum()))
    m.starve_time = np.where(food >= s.scout_food, 0.0, np.where(running, m.starve_time + dt_bio, 0.0))


def scout_chance(world, food):
    """Chance per real minute of starting to scout: 0 with prey food at scout_food or more, rising
    in a straight line to scout_start_rate at zero food (B83)."""
    s = world.settings
    return s.scout_start_rate * np.clip(1.0 - food / s.scout_food, 0.0, 1.0)


def resting(world):
    """True for cells that scouted recently and must wait scout_rest_time before scouting again (B95)."""
    w = world
    if not hasattr(w, "scout_rest_uids"):          # worlds pickled before B95 (e.g. web scenes)
        w.scout_rest_uids, w.scout_rest_until = np.zeros(0, dtype=np.int64), np.zeros(0)
    if len(w.scout_rest_uids) == 0:
        return np.zeros(len(w.myxo.uid), dtype=bool)
    live = w.scout_rest_until > w.t
    w.scout_rest_uids, w.scout_rest_until = w.scout_rest_uids[live], w.scout_rest_until[live]
    return np.isin(w.myxo.uid, w.scout_rest_uids)


def start_rest(world, uids):
    """Cells whose spell just ended rest for scout_rest_time real minutes (B95)."""
    w = world
    if len(uids) == 0 or w.settings.scout_rest_time <= 0:
        return
    w.scout_rest_uids = np.concatenate([w.scout_rest_uids, uids])
    w.scout_rest_until = np.concatenate([w.scout_rest_until, np.full(len(uids), w.t + w.settings.scout_rest_time)])


def cap_starts(world, begin, keep):
    """At most scout_max_share of all cells scout at once: extra would-be scouts are dropped at random (B95)."""
    room = max(int(world.settings.scout_max_share * len(begin)) - int(keep.sum()), 0)
    idx = np.nonzero(begin)[0]
    if len(idx) > room:
        begin = begin.copy()
        begin[world.rng.choice(idx, len(idx) - room, replace=False)] = False
    return begin


def update_scouts(world):
    """Start and stop scouting for this tick (B71, B83, B95, B97). A spell ends when the scout finds
    prey food, when it has starved for behaviour_delay (unless stringent_scouts), or, with
    scout_random_end, at random. The block used to start at stringent_delay (30 bio-min, 3 real min at
    10×), which switched scouting practically off (review of 23 Oct 2026, C3).
    After a spell a cell rests scout_rest_time before it may scout again, and at most
    scout_max_share of cells scout at once. No random numbers are used when scouting is off."""
    s, m = world.settings, world.myxo
    if s.scout_start_rate <= 0 or len(m.uid) == 0:
        m.scout[:] = False
        return
    food = food_around(world)
    roll = world.rng.random(len(m.uid))
    ends = food >= s.scout_food
    if s.scout_random_end:
        ends = ends | (roll < s.dt / s.scout_episode)
    allowed = ~resting(world)
    if not s.stringent_scouts:
        starving = starving_behaviour(world)
        ends, allowed = ends | starving, allowed & ~starving
    keep = m.scout & ~ends
    begin = cap_starts(world, ~m.scout & allowed & (roll < scout_chance(world, food) * s.dt), keep)
    start_rest(world, m.uid[m.scout & ends])
    m.scout = keep | begin
    counters.add(world, "scout_starts", int(begin.sum()))
    counters.add(world, "scout_minutes", int(m.scout.sum()) * s.dt)


def mode_factors(world, scout_value, starving_value, starving):
    """A per-cell multiplier: 1 for ordinary cells, scout_value for scouts, starving_value for the
    `starving` cells, which wins for a starving scout (B72, B83)."""
    m = world.myxo
    factor = np.ones(len(m.uid))
    factor[m.scout] = scout_value
    factor[starving] = starving_value
    return factor


def starving_speed(world):
    """Speed of each cell were it showing starving behaviour: it speeds up to stringent_loner_speed
    over stringent_speedup_time of starving (Jelsbak 2002, timed from when food ran out) (B75, B83,
    B84). There's no slow-down when packed any more: in a flat world it can't tell aggregates
    from swarm streams (B84)."""
    s, m = world.settings, world.myxo
    ramp = np.minimum(m.starve_time / s.stringent_speedup_time, 1.0)
    return 1.0 + (s.stringent_loner_speed - 1.0) * ramp


def speed_factors(world):
    """Each cell's speed relative to normal: scouts ×1.1 (B71, B80); cells showing starving
    behaviour speed up with time starving (B75, B84); a starving scout takes whichever is faster,
    so scouting never slows a cell (B83)."""
    s, m = world.settings, world.myxo
    factor = np.ones(len(m.uid))
    factor[m.scout] = s.scout_speed
    starving = starving_behaviour(world)
    if starving.any():
        starved = starving_speed(world)
        factor[starving] = np.where(m.scout[starving], np.maximum(s.scout_speed, starved[starving]),
                                    starved[starving])
    return factor


def affinity_factors(world):
    """Food affinity relative to normal: stringent cells ×1.15, scouts unchanged (B72, B84)."""
    return mode_factors(world, 1.0, world.settings.stringent_affinity, stringent(world))


def smell_factors(world):
    """How strongly each cell follows the prey smell, relative to normal: scouts, and cells showing
    starving behaviour, ×1.5 (B72, B80, B84)."""
    s = world.settings
    return mode_factors(world, s.scout_smell, s.stringent_smell, starving_behaviour(world))
