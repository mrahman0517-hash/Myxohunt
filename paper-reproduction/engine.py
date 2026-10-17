"""
engine.py — the Simulation class: sets up the cells and runs the time loop.

One call to step() is one time step (0.3 s). The order follows the authors'
main loop (foundations §4.3); frustration must be computed after ALL of this
step's motion, because it compares where the cell meant to go with where it
actually got to.
"""
import time
import numpy as np

import functions as fn
from datatypes import Params, Population, EPSField, RunLog


class Simulation:
    def __init__(self, params: Params, seed: int = 0, record_from: float | None = None):
        self.p = params
        self.rng = np.random.default_rng(seed)
        self.t = 0.0
        self.step_count = 0
        # validation statistics use the last 50 min, as in the authors' TBR plots
        self.record_from = params.T - 50.0 if record_from is None else record_from

        self.weights, self.norm = fn.memory_weights(params)
        self.pop = self._place_cells()
        self.eps = EPSField.empty(params.box, params.eps_grid)
        self.offsets = fn.sensing_offsets(self.eps, params)
        self.log = RunLog()

    # ------------------------------------------------------------ set-up
    def _place_cells(self) -> Population:
        """Random positions; aligned start for rippling, random headings otherwise [code]."""
        p, rng, N = self.p, self.rng, self.p.n_cells
        start = rng.uniform(0, p.box, size=(N, 2))
        if p.mode == "rippling":
            direction = p.ripple_axis + np.pi * rng.integers(0, 2, size=N)   # half each way
        else:
            direction = rng.uniform(0, 2 * np.pi, size=N)
        k = np.arange(p.n_nodes) * p.node_spacing
        unitvec = np.stack([np.cos(direction), np.sin(direction)], axis=1)
        nodes = start[:, None, :] + k[None, :, None] * unitvec[:, None, :]

        K = int(p.memory / p.dt)
        pop = Population(
            nodes=nodes,
            age=rng.integers(0, int(p.R_star / p.dt), size=N) * p.dt,   # staggered clocks
            memory=np.zeros((N, K)),
            signal=np.zeros(N),
            can_reverse=np.ones(N, dtype=bool),
            ripples=np.zeros(N, dtype=bool),
            last_reversal=np.full(N, np.nan),
        )
        self._update_zones(pop)
        return pop

    def _update_zones(self, pop):
        """Which alignment rule applies to each cell (the only rippling/swarming difference)."""
        if self.p.mode == "rippling":
            pop.ripples[:] = True
        elif self.p.mode == "swarming":
            pop.ripples[:] = False
        else:  # "split": prey matrix on the left half of the box
            pop.ripples[:] = np.mod(pop.nodes[:, 0, 0], self.p.box) < self.p.box / 2

    # ------------------------------------------------------------ one time step
    def step(self):
        p, pop = self.p, self.pop
        nodes = pop.nodes
        self._update_zones(pop)
        head_before = nodes[:, 0].copy()

        # 1. motion and mechanics
        fn.traction(nodes, fn.head_direction(nodes), p)
        fn.repulsion(nodes, p.box, p)
        heading = fn.relax_springs(nodes, p)
        theta = fn.angle_of(heading)

        # 2. alignment: the ONLY rule that differs between the two fields
        turn = np.zeros(pop.n)
        rip, swarm = pop.ripples, ~pop.ripples
        if rip.any():
            turn[rip] = fn.ripple_turn(theta[rip], p)
        if swarm.any():
            fn.eps_lay(self.eps, nodes[swarm, -1], p)
            turn[swarm] = fn.eps_turn(self.eps, nodes[swarm, 0], theta[swarm], self.offsets, p, self.rng)
        fn.rotate_heads(nodes, turn, turn != 0)

        # 3. frustration: intended vs realised head velocity, then the 20 s memory
        v_real = (nodes[:, 0] - head_before) / p.dt
        f = fn.frustration(p.speed * heading, v_real)
        slot = self.step_count % pop.memory.shape[1]
        pop.memory[:, slot] = f
        pop.signal = fn.smoothed_signal(pop.memory, slot, self.weights, self.norm)

        # 4. reversal clock and decision
        pop.age += p.dt
        prob = fn.reversal_probability(pop.age, pop.signal, p) * pop.can_reverse
        flip = self.rng.random(pop.n) < prob
        if flip.any():
            self._record_reversals(np.nonzero(flip)[0])
            nodes[flip] = nodes[flip, ::-1]          # head becomes tail
            pop.age[flip] = 0.0

        # 5. keep every cell's head inside the box (shift the whole cell, not single discs)
        nodes -= (np.floor(nodes[:, :1] / p.box) * p.box)

        self.t += p.dt
        self.step_count += 1
        self._record_periodic()

    # ------------------------------------------------------------ recording
    def _record_reversals(self, idx):
        pop, log = self.pop, self.log
        if self.t >= self.record_from:
            prev = pop.last_reversal[idx]
            ok = ~np.isnan(prev)
            log.tbr.extend((self.t - prev[ok]).tolist())
            log.tbr_time.extend([self.t] * int(ok.sum()))
            log.rev_cell.extend(idx.tolist())
            log.rev_time.extend([self.t] * len(idx))
            log.rev_signal.extend(pop.signal[idx].tolist())
        pop.last_reversal[idx] = self.t

    def _record_periodic(self):
        p, k = self.p, self.step_count
        if self.t < self.record_from:
            return
        if k % 7 == 0:                                   # ≈ every 2 s, like the videos
            self.log.signal_samples.append(self.pop.signal.astype(np.float32))
        if k % 20 == 0:                                  # every 0.1 min: density along x
            x = np.mod(self.pop.nodes[:, :, 0], p.box).ravel()
            self.log.kymo.append(np.histogram(x, bins=int(p.box), range=(0, p.box))[0].astype(np.float32))
        if k % int(round(5.0 / p.dt)) == 0:              # every 5 min: positions
            self.log.snapshots.append((self.t, self.pop.nodes.astype(np.float32)))

    # ------------------------------------------------------------ driver
    def run(self, progress_every: float = 10.0):
        p = self.p
        t0 = time.time()
        every = int(round(progress_every / p.dt))
        for _ in range(p.n_steps):
            self.step()
            if self.step_count % every == 0:
                rate = self.step_count / (time.time() - t0)
                left = (p.n_steps - self.step_count) / rate / 60
                print(f"[{p.mode}] t = {self.t:6.1f} min | {rate:5.1f} steps/s | ~{left:4.1f} min left",
                      flush=True)
        self.log.snapshots.append((self.t, self.pop.nodes.astype(np.float32)))

    def results(self) -> dict:
        """Everything needed for the validation plots, as plain arrays."""
        log, p = self.log, self.p
        snaps = [s.astype(float) for t, s in log.snapshots]
        edges = np.arange(1.25, p.box / 2, 2.5)            # distance rings 2.5 µm wide
        orders = []
        for nodes in snaps:
            axis, centre = fn.cell_axis_and_centre(nodes, p.box)
            orders.append(fn.nematic_order(centre, axis, p.box, edges))
        samples = np.array(log.signal_samples)
        return dict(
            mode=p.mode, box=p.box, n_cells=p.n_cells, T=p.T,
            tbr=np.array(log.tbr), tbr_time=np.array(log.tbr_time),
            rev_cell=np.array(log.rev_cell, dtype=int), rev_signal=np.array(log.rev_signal),
            quartiles=fn.quartile_fractions(samples, log.rev_cell, log.rev_signal),
            signal_samples=samples,
            order_r=0.5 * (edges[1:] + edges[:-1]), order=np.nanmean(orders, axis=0),
            kymo=np.array(log.kymo), final_nodes=snaps[-1],
        )
