"""
myxo_reversals.py — the paper's reversal rule (H1 + H2): frustration → 20 s memory → signal s
→ refractory period and reversal rate → reversal. Copied from paper-reproduction/functions.py
(validated against the authors' code, A10–A11), with two additions:
  - paused (killing) cells freeze their memory and clock (B16), so memory slots are per cell;
  - the post-refractory rate is multiplied by the pull-toward-prey factor (B10, B32).
"""
import numpy as np

import grids
import myxo_body


# copied from paper-reproduction/functions.py:frustration
def frustration(v_target, v_real):
    """f = 1 − (v_t · v_r) / max(|v_t|², |v_r|²). 0 = moved as intended, 2 = pushed backwards."""
    dot = np.einsum("ij,ij->i", v_target, v_real)
    denom = np.maximum(np.einsum("ij,ij->i", v_target, v_target), np.einsum("ij,ij->i", v_real, v_real))
    return 1.0 - dot / np.maximum(denom, 1e-12)


# copied from paper-reproduction/functions.py:memory_weights
def memory_weights(s):
    """Weights e^(−β(k+1)Δt) for lags k = 0…K−1, and the rescaling 2·Σw (so s lands in 0–1)."""
    K = s.memory_length
    w = np.exp(-s.beta * (np.arange(K) + 1) * s.dt)
    return w, 2.0 * w.sum()


def write_memory(memory, mem_slot, f, active):
    """For active cells only: move to the next memory slot and store this tick's frustration."""
    K = memory.shape[1]
    rows = np.nonzero(active)[0]
    mem_slot[rows] = (mem_slot[rows] + 1) % K
    memory[rows, mem_slot[rows]] = f[rows]


# adapted from paper-reproduction/functions.py:smoothed_signal (one newest slot per cell)
def smoothed_signal(memory, mem_slot, weights, norm):
    """Weighted average of each cell's last K frustration values, newest weighted most."""
    K = memory.shape[1]
    lag = (mem_slot[:, None] - np.arange(K)[None, :]) % K
    return np.sum(memory * weights[lag], axis=1) / norm


# copied from paper-reproduction/functions.py:refractory_period
def refractory_period(sig, s):
    """T_RP(s) = R* − (R* − R_min) / (1 + exp[−α_R (s − f_T)]): 5 min when calm, 20 s when jammed."""
    return s.R_star - (s.R_star - s.R_min) / (1.0 + np.exp(-s.alpha_R * (sig - s.f_T)))


# copied from paper-reproduction/functions.py:reversal_rate
def reversal_rate(sig, s):
    """T_REV⁻¹(s) = F* / (1 + exp[−α_F (s − f_T)]): rises steeply around f_T."""
    return s.F_star / (1.0 + np.exp(-s.alpha_F * (sig - s.f_T)))


def chemotaxis_factor(world, heads, heading, boost=None):
    """Pull toward prey through reversals (B32): heading up the attractant gradient → reverse
    less; heading down it → reverse more. Equals 1 everywhere when chemo_strength is 0.
    boost (N,) multiplies each cell's strength (scouts follow the smell more keenly; B72)."""
    s, f = world.settings, world.fields
    if s.chemo_strength == 0 or len(heads) == 0:
        return np.ones(len(heads))
    up = np.einsum("ij,ij->i", heading, grids.gradient(f.attractant, heads, s.box, f.spacing))
    strength = s.chemo_strength if boost is None else s.chemo_strength * boost
    lo, hi = s.chemo_factor_range
    return np.clip(np.exp(-strength * up), lo, hi)


# adapted from paper-reproduction/functions.py:reversal_probability (chemotaxis factor added)
def reversal_probability(age, sig, factor, s):
    """Chance of reversing this tick: 0 inside the refractory period, else (1 − e^(−rate·factor))·Δt."""
    past_rp = age > refractory_period(sig, s)
    return np.where(past_rp, (1.0 - np.exp(-reversal_rate(sig, s) * factor)) * s.dt, 0.0)


def decide_reversals(world, active, factor):
    """Age the active cells' clocks, roll the dice, flip the reversing cells and reset their clock.

    Returns:
        (N,) bool, the cells that reversed this tick.
    """
    m, s = world.myxo, world.settings
    m.age[active] += s.dt
    prob = reversal_probability(m.age, m.signal, factor, s) * active
    flip = world.rng.random(len(m.age)) < prob
    myxo_body.reverse(m.nodes, flip)
    m.age[flip] = 0.0
    return flip
