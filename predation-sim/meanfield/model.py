"""
meanfield/model.py — the average-world model: the live world boiled down to three numbers that
change smoothly in time (no single cells, no space). Time is in bio-hours.

It stands in for the full simulation when exploring settings: one run takes milliseconds instead
of hours. Its fitted numbers are learned from the full simulation's own runs (fit.py), so it only
approximates what the full simulation does; the settings it picks must be checked there.

The three numbers:
  n   mean ground nutrient (units per µm²)
  E   living E. coli (growing and dormant together)
  H   Myxo

The processes, each read off the full simulation:
  prey births   B = c1 × regrow × rich × E  +  c2 × (n/rich)^kappa × rich^omega × E^theta
                    a trickle: each cell lives on the food regrowing in the few µm² around it
                    (dormant cells wake whenever a trace of food regrows under them, so they almost
                    never starve to death; only hunters remove them), plus growth at colony edges
                    into fresh ground (rising slower than E: only the edge grows)
  ground        dn/dt = regrow × (rich − n) − B / area   (each birth eats one unit)
  kills         K = a × E^alpha × H^eta × (n/rich)^lam
                    hunters mostly catch growing cells at colony edges; on empty ground most prey
                    are dormant clumps that the packs rarely reach, so kills fall with the ground's fullness
  starving prey S = (1 − persister) × dormant share × E × death rate per dormant cell
                    worked out from the sim's own rules, not fitted: a dormant cell wakes (and its
                    starvation clock restarts) as soon as the food regrowing under it reaches the wake
                    level; it can only die if that takes longer than its day of dormancy
                    (dormant_days), and then dies at the measured starvation_death rate. With today's
                    settings regrowth always wins, so E. coli practically never starve (the runs agree)
  hunters       dH/dt = chi × efficiency × (K + cs × S) − mu × H + arrivals
                    each kill turns into chi × efficiency new Myxo once the fed cells' costs are paid;
                    mu covers famine exits and starving to death
"""
from dataclasses import dataclass, asdict

import numpy as np
from scipy.integrate import solve_ivp

REGROW_REF = 0.02          # 1/bio-h: the default refill speed (1/3000 per bio-min)


@dataclass
class World:
    """The settings of one live world, in the model's units (bio-hours, cells, µm²)."""
    regrow: float = REGROW_REF        # 1/bio-h, nutrient_regrow_rate × 60
    rich: float = 0.65                # mean patch maximum: (richness_min + richness_max) / 2
    start_fill: float = 0.61          # mean starting nutrient as a share of rich (read from the runs at t = 0)
    efficiency: float = 0.5           # Myxo's share of eaten food kept
    area: float = 150.0 ** 2          # µm², the live world
    founder_every: float = 6.0        # bio-h between new E. coli founders
    start_prey: float = 2.0           # E. coli at the start (two starting colonies)
    arrivals: float = 110.0           # Myxo coming in (5 × 20 + 10)
    arrival_window: float = 10.0      # bio-h over which they come in
    wake_level: float = 0.2           # nutrient under a cell that ends its dormancy (wake_threshold since B87;
                                      #   0.01, the dormant_threshold, before)
    dormant_days: float = 0.0         # bio-h dormant before the death phase (dormancy_before_death: 0 since B87,
                                      #   24 before)
    starvation_death: float = np.log(1000.0) / (10 * 24.0)  # 1/bio-h, 0.69 per day (Schink et al.; measured)
    persister: float = 0.05           # share of E. coli that never starve to death (measured)
    rich_lo: float = 0.3 / 0.65       # poorest and richest patch as shares of the mean richness
    rich_hi: float = 1.0 / 0.65


@dataclass
class Fitted:
    """Numbers learned from the full simulation (values from fit.py; these defaults are the
    process fits of 16 Oct 2026)."""
    c1: float = 5.15       # µm² of regrowing ground each prey cell lives on (the trickle)
    c2: float = 25.9       # edge growth into fresh ground ...
    kappa: float = 0.86    # ... rising with the ground's fullness ...
    omega: float = 1.39    # ... with its richness ...
    theta: float = 0.41    # ... and with the number of prey, less than in proportion
    a: float = 0.000306    # kills scale
    alpha: float = 1.11    # kills rise with prey ...
    eta: float = 0.97      # ... with hunters ...
    lam: float = 1.03      # ... and with the ground's fullness (growing, exposed prey)
    chi: float = 0.42      # share of a kill's content that ends up as new Myxo
    mu: float = 0.015      # Myxo lost per bio-h (famine exits, starving to death)
    g0: float = 0.58       # share of E. coli growing (not dormant) ...
    g1: float = 0.47       # ... = g0 × (n/rich)^g1, at most 1 (a loose fit, R² 0.23)
    cs: float = 0.25       # food from a prey that starved, relative to a killed one (starved_content_min)

    def to_dict(self):
        """The numbers as a plain dict (for saving)."""
        return asdict(self)


def arrivals(t, w):
    """Myxo arriving per bio-h at time t: evenly over the arrival window."""
    return w.arrivals / w.arrival_window if t < w.arrival_window else 0.0


def rates(n, E, H, w, f):
    """Prey births (trickle, edge growth) and kills per bio-h at this state."""
    rel = max(n, 1e-9) / w.rich
    trickle = f.c1 * w.regrow * w.rich * E
    edge = f.c2 * rel ** f.kappa * w.rich ** f.omega * E ** f.theta if E > 0 else 0.0
    kills = f.a * E ** f.alpha * H ** f.eta * rel ** f.lam if E > 0 and H > 0 else 0.0
    return trickle, edge, kills


def dormant_death_rate(w):
    """Average starvation deaths per dormant cell per bio-h, over the rich and poor patches.

    On a patch whose maximum is R the food under a dormant cell regrows from 0 to the wake level
    in tau = −ln(1 − wake/R) / regrow hours (never, if wake ≥ R). If tau is shorter than the day of
    dormancy the cell never dies. Otherwise each sleep ends in death with chance
    p = 1 − exp(−death × (tau − day)), and a sleep lasts day + p / death hours on average (it ends
    at death or at waking, whichever comes first), so the cell dies at p / (day + p / death) per
    hour. A cell that never wakes (p = 1) dies about day + 1/death ≈ 59 bio-h after going dormant.
    """
    total = 0.0
    patches = w.rich * np.linspace(w.rich_lo, w.rich_hi, 21)
    for R in patches:
        if w.wake_level >= R:
            risk = 1.0
        else:
            tau = -np.log(1.0 - w.wake_level / R) / w.regrow
            risk = 1.0 - np.exp(-w.starvation_death * max(tau - w.dormant_days, 0.0))
        total += risk / (w.dormant_days + risk / w.starvation_death)
    return total / len(patches)


def rhs(t, y, w, f, death_rate=None):
    """How fast each tracked number changes at time t."""
    n, E, H = max(y[0], 0.0), max(y[1], 0.0), max(y[2], 0.0)
    trickle, edge, kills = rates(n, E, H, w, f)
    births = trickle + edge
    rate = dormant_death_rate(w) if death_rate is None else death_rate
    dormant = 1.0 - min(f.g0 * (max(n, 1e-9) / w.rich) ** f.g1, 1.0)
    starved = (1.0 - w.persister) * dormant * E * rate
    dn = w.regrow * (w.rich - n) - births / w.area
    dE = births + 1.0 / w.founder_every - kills - starved
    dH = f.chi * w.efficiency * (kills + f.cs * starved) - f.mu * H + arrivals(t, w)
    return [dn, dE, dH]


def simulate(w, f, hours=120.0, step=0.25):
    """Run the model from the empty start (prey only, ground part-filled) for `hours`.

    Returns:
        dict of arrays: h, n, E, H, and ok (whether the solver succeeded).
    """
    y0 = [w.start_fill * w.rich, w.start_prey, 0.0]
    t = np.arange(0.0, hours + 1e-9, step)
    sol = solve_ivp(rhs, (0.0, hours), y0, t_eval=t, args=(w, f, dormant_death_rate(w)), method="LSODA",
                    rtol=1e-6, atol=1e-8, max_step=0.5)
    n, E, H = np.maximum(sol.y, 0.0)
    return dict(h=sol.t, n=n, E=E, H=H, ok=sol.success)


def world_for(run):
    """The model World matching a full-simulation run (meanfield.runs.Run), with the E. coli
    starvation rules of the run's time."""
    return World(regrow=REGROW_REF * run.regrow, rich=0.65 * run.rich, efficiency=run.efficiency,
                 wake_level=run.wake, dormant_days=run.grace)
