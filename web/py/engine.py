"""
engine.py — the only place that decides the order of events (build manual §2).

Every tick (0.3 s, real speed): Myxo movement, contacts, alignment, frustration and reversals
(killing arrives in milestone 4), then cell biology sped up by `speedup`. Every `grid_every`
ticks: the ground maps (B51).
"""
import numpy as np

import contacts
import ecoli_body
import ecoli_life
import fields_update
import geometry as geo
import myxo_alignment as align
import myxo_body
import myxo_energy
import myxo_famine
import myxo_modes
import myxo_reversals as rev
import predation
import seeding
import state
from stats import StatsLog


class Simulation:
    """One simulated world and the clock that drives it."""

    def __init__(self, settings, seed_cells=True):
        """Build the world: patchy ground, then the E. coli seeds, then the Myxo seeds.

        seed_cells=False leaves both populations empty (for validation runs that place
        their own cells).
        """
        self.world = state.new_world(settings)
        seeding.initial_ground(self.world)
        if seed_cells:
            seeding.initial_ecoli(self.world)
            seeding.initial_myxo(self.world)
        self.world.eps_offsets = align.sensing_offsets(self.world.fields.eps_spacing, settings)
        fields_update.refresh_sensed_maps(self.world)
        self.weights, self.norm = rev.memory_weights(settings)
        self.touches = None    # Myxo–E. coli touches found in the latest tick
        self.flipped = None    # Myxo that reversed in the latest tick
        self.new_pauses = None  # (myxo rows, prey uids) of killing pauses started in the latest tick
        self.kills = None      # (killer uids, prey uids) of kills in the latest tick
        self.stats = StatsLog()
        self.stats.add(self.world)

    # ------------------------------------------------------------ fast: every tick, real speed
    def turn(self, active, heading):
        """Step 6, alignment: rippling cells turn to their spot's axis; moving swarming cells lay
        slime under their tail; trail followers turn toward trails ahead (paper H3), while scouts
        wander off-trail with small random turns (A-motility, B67). Scouts lay their own, stronger
        slime layer, which followers sense on top of the ordinary one (B71)."""
        w, s, m, f = self.world, self.world.settings, self.world.myxo, self.world.fields
        theta = geo.angle_of(heading)
        ripples = align.ripple_mask(w, m.nodes[:, 0])
        off_matrix = ~ripples & active
        invaders = off_matrix & ~m.scout & self.touching_live_prey()      # B95
        followers, scouts = off_matrix & ~m.scout & ~invaders, off_matrix & m.scout
        turn = np.zeros(state.count(m))
        turn[ripples] = align.ripple_turn(theta[ripples], align.local_axis(w, m.nodes[ripples, 0]), s)
        if (followers | invaders).any():
            align.eps_lay(f.eps, f.eps_spacing, m.nodes[followers | invaders, -1], s)
        if scouts.any():
            align.eps_lay(f.eps_scout, f.eps_spacing, m.nodes[scouts, -1], s, s.scout_slime)
        if followers.any():
            turn[followers], on_trail = align.eps_turn(f.eps, f.eps_spacing, m.nodes[followers, 0], theta[followers],
                                                       w.eps_offsets, s, w.rng, extra=f.eps_scout, with_trail=True)
            leaders = np.nonzero(followers)[0][~on_trail]                  # no slime ahead: front of a stream
            turn[leaders] = align.smell_turn(w, m.nodes[leaders, 0], theta[leaders])
        if scouts.any():
            turn[scouts] = (align.scout_turn(int(scouts.sum()), s, w.rng)
                            + align.smell_turn(w, m.nodes[scouts, 0], theta[scouts]))
        if invaders.any():
            turn[invaders] = align.smell_turn(w, m.nodes[invaders, 0], theta[invaders])
        myxo_body.rotate_heads(m.nodes, turn, active & (turn != 0))

    def touching_live_prey(self):
        """True for Myxo touching a living E. coli this tick, when invasion on contact is on (B95)."""
        w, n = self.world, state.count(self.world.myxo)
        mask = np.zeros(n, dtype=bool)
        if not w.settings.invade_on_contact or self.touches is None or len(self.touches) == 0:
            return mask
        live = w.ecoli.lysis_timer[self.touches[:, 1]] < 0
        mask[self.touches[live, 0]] = True
        return mask

    def update_signal(self, active, heading, head_before, speed_factor):
        """Step 7: frustration from intended vs real head movement, into each active cell's memory.
        The intended speed is the cell's own (scouts faster, starving cells slower; B71)."""
        s, m = self.world.settings, self.world.myxo
        v_real = (m.nodes[:, 0] - head_before) / s.dt
        f = rev.frustration(s.speed * speed_factor[:, None] * heading, v_real)
        rev.write_memory(m.memory, m.mem_slot, f, active)
        m.signal = np.where(active, rev.smoothed_signal(m.memory, m.mem_slot, self.weights, self.norm),
                            m.signal)
        self.prey_contact(active)

    def prey_contact(self, active):
        """Touching living prey raises the Frz signal to at least prey_contact_signal, so the cell
        reverses rapidly on the spot instead of leaving (B62, off when the setting is 0)."""
        w, s = self.world, self.world.settings
        if s.prey_contact_signal <= 0 or self.touches is None or len(self.touches) == 0:
            return
        live = w.ecoli.lysis_timer[self.touches[:, 1]] < 0
        rows = np.unique(self.touches[live, 0])
        rows = rows[active[rows]]
        w.myxo.signal[rows] = np.maximum(w.myxo.signal[rows], s.prey_contact_signal)

    def predate(self):
        """Step 9: count down killing pauses, start new ones on touched prey, finish kills.

        New pauses are started before kills are finished, because bursting prey removes rows
        and the touch list refers to this tick's rows (B14, B15).
        """
        w = self.world
        ended = predation.count_down_pauses(w)
        self.new_pauses = predation.start_pauses(w, self.touches, ended)
        self.kills = predation.finish_kills(w, ended)

    def step_fast(self):
        """Movement, contacts, alignment, frustration and reversals, in the paper's order (§4.3)."""
        w, s, m = self.world, self.world.settings, self.world.myxo
        active = m.pause_left <= 0                                   # not paused to kill (B16)
        speed = myxo_modes.speed_factors(w)                          # scouts faster, starving slower (B71)
        head_before = m.nodes[:, 0].copy()
        myxo_body.traction(m.nodes, myxo_body.head_direction(m.nodes), active, s, speed)
        self.touches = contacts.resolve_contacts(w)
        heading = myxo_body.relax_springs(m.nodes, s)
        self.turn(active, heading)
        self.update_signal(active, heading, head_before, speed)
        factor = rev.chemotaxis_factor(w, m.nodes[:, 0], heading, myxo_modes.smell_factors(w))
        self.flipped = rev.decide_reversals(w, active, factor)
        myxo_modes.update_scouts(w)
        self.predate()
        myxo_body.wrap_cells(m.nodes, s.box)
        w.ecoli.centre[:] = geo.wrap_points(w.ecoli.centre, s.box)

    # ------------------------------------------------------------ cells: every tick, sped up
    def step_ecoli(self, dt_bio):
        """E. coli: grow on the nutrients under them, divide, go dormant, starve, burst."""
        w = self.world
        grown = ecoli_body.grow(w.ecoli, ecoli_life.growth_rates(w), dt_bio)
        ecoli_life.consume(w, grown)
        ecoli_body.divide(w)
        ecoli_life.update_dormancy(w, dt_bio)
        ecoli_life.starvation_deaths(w, dt_bio)
        predation.lyse_ecoli(w, ecoli_life.count_down_lysis(w, dt_bio))
        ecoli_life.leak_attractant(w, dt_bio)

    def step_myxo(self, dt_bio):
        """Myxo: a day into starvation take a fate (B80), pay upkeep, eat spilled food, divide if
        well fed, die if empty (B20–B28)."""
        w = self.world
        myxo_modes.update_starve_clock(w, dt_bio)
        myxo_famine.famine_exit(w, dt_bio)
        myxo_energy.upkeep(w, dt_bio)
        myxo_energy.uptake(w, dt_bio)
        myxo_energy.divide_myxo(w, dt_bio)
        myxo_energy.starvation_deaths_myxo(w)

    def step_cells(self):
        """All per-cell biology for one tick, at the sped-up biological rate."""
        w = self.world
        dt_bio = w.settings.dt * w.settings.speedup
        self.step_ecoli(dt_bio)
        self.step_myxo(dt_bio)
        w.bio_t += dt_bio

    # ------------------------------------------------------------ grids: every grid_every ticks
    def step_grids(self):
        """The ground maps catch up on the biological time since their last update."""
        w = self.world
        dt_bio = w.settings.grid_every * w.settings.dt * w.settings.speedup
        fields_update.update_fields(w, dt_bio)
        seeding.add_due_founder(w)                                   # a new E. coli founder now and then (B75)
        seeding.add_due_myxo(w)                                      # Myxo seeds coming in from outside (B78)
        self.stats.add(w)

    # ------------------------------------------------------------ driver
    def step(self):
        """One tick: fast steps, cell biology, and the ground maps when their turn comes."""
        w = self.world
        self.step_fast()
        self.step_cells()
        w.t += w.settings.dt
        w.step_count += 1
        if w.step_count % w.settings.grid_every == 0:
            self.step_grids()

    def run_for(self, real_minutes, callback=None, every_minutes=None):
        """Run for a stretch of real time, optionally calling `callback(world)` at intervals."""
        dt = self.world.settings.dt
        n_steps = int(round(real_minutes / dt))
        every = int(round(every_minutes / dt)) if every_minutes else None
        for i in range(n_steps):
            self.step()
            if callback and every and (i + 1) % every == 0:
                callback(self.world)
