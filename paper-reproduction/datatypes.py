"""
datatypes.py — what the simulation is made of: parameters and state containers.

Nothing in here does any physics. The physics lives in functions.py and the
order of events lives in engine.py. Section numbers (§3.5 etc.) refer to the
"model foundations" draft in the Motility Sim project.

Source tags used in comments:
  [paper] stated in Saulnier et al. 2026 (Methods, "Fitting procedure of the 2D model")
  [code]  from the authors' released code, where the PDF defers to the Supplement
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Params:
    # ---- 1. From the literature [paper] -----------------------------------
    R_star: float = 5.0            # min   maximum refractory period
    node_spacing: float = 0.5      # µm    ε, distance between discs
    n_nodes: int = 10              #       N_D, discs per cell -> 5 µm long cell
    sense_radius: float = 5.0      # µm    H, how far ahead pili "feel" EPS
    eps_c_min: float = 0.1         #       minimum detectable EPS (code: EPS_max / 100)

    # ---- 2. Measured in the paper [paper] ---------------------------------
    disc_diam: float = 0.7         # µm    D, cell width
    speed: float = 4.0             # µm/min v
    R_min: float = 1.0 / 3.0       # min   minimum refractory period (20 s)

    # ---- 3. Ad hoc [paper] -------------------------------------------------
    k_spring: float = 50.0         # 1/min k_s
    k_rep: float = 450.0           # 1/(µm·min) k_r (only caps the push at deep overlap)
    view_angle: float = np.pi      # 2α, a semicircle in front of the head
    eps_deposit: float = 2.0       # 1/min a
    eps_max: float = 10.0          #       EPS_max (code uses it only to set c_min)
    gamma_ripple: float = 11.0     # 1/min γ' (printed µm/min; acts as a turning rate)
    gamma_eps: float = 11.0        # 1/min γ  (same remark)
    F_star: float = 3.0            # 1/min maximum reversal rate. Paper prints 30; the code
                                   #       default is 3. With the code-form probability the two
                                   #       behave almost identically (see §3.5 note).
    memory: float = 1.0 / 3.0      # min   d, frustration memory window (20 s)
    beta: float = 2.0              # 1/min β, memory decay rate (printed "2 min")

    # ---- 4. Fitted to TBR distributions [paper] ---------------------------
    f_T: float = 0.08              #       threshold, applied to the rescaled signal s (0-1)
    alpha_F: float = 75.0          #       steepness of the reversal-rate curve
    alpha_R: float = 100.0         #       steepness of the refractory-period curve

    # ---- run settings [code] ----------------------------------------------
    dt: float = 0.005              # min   time step (0.3 s)
    traction_scale: int = 10       #       head is pulled at speed × N_D (see functions.traction)
    spring_passes_per_node: int = 5  #     springs relaxed 5·N_D = 50 times per step
    eps_grid: float = 0.3          # µm    EPS grid spacing
    n_sectors: int = 5             #       wedges in the view semicircle
    eps_choice_tolerance: float = 0.8  #   wedges within 80% of the best count as "good"
    ripple_axis: float = 0.0       # rad   θ0, the prescribed rippling direction (horizontal)

    # ---- what to simulate ---------------------------------------------------
    box: float = 65.0              # µm    side of the periodic square box
    n_cells: int = 1000
    mode: str = "rippling"         # "rippling", "swarming", or "split" (left half ripples)
    T: float = 150.0               # min   total simulated time

    @property
    def cell_length(self) -> float:
        return self.node_spacing * self.n_nodes

    @property
    def n_steps(self) -> int:
        return int(round(self.T / self.dt))


@dataclass
class Population:
    """
    All cells, stored as arrays (one row per cell) rather than one Python object
    per cell. Each array is one *property* of every cell at once, which lets
    numpy update a thousand cells in a single operation.
    """
    nodes: np.ndarray        # (N, n_nodes, 2) disc positions, NOT wrapped into the box;
                             #   disc 0 is the head (leading pole)
    age: np.ndarray          # (N,) min since last reversal (the reversal clock r)
    memory: np.ndarray       # (N, K) recent frustration values (ring buffer)
    signal: np.ndarray       # (N,) smoothed, rescaled frustration s in [0, 1]
    can_reverse: np.ndarray  # (N,) bool; False mimics the frzE mutant
    ripples: np.ndarray      # (N,) bool; True = in the prey-matrix (rippling) zone
    last_reversal: np.ndarray  # (N,) time of last reversal, NaN if none yet

    @property
    def n(self) -> int:
        return self.nodes.shape[0]


@dataclass
class EPSField:
    """Slime laid by swarming cells, on a periodic grid (§3.5, alignment rule)."""
    grid: np.ndarray         # (n, n) EPS amount per grid square
    spacing: float           # µm per square (box / n, ≈ 0.3 µm)

    @classmethod
    def empty(cls, box: float, target_spacing: float) -> "EPSField":
        n = int(round(box / target_spacing))
        return cls(grid=np.zeros((n, n)), spacing=box / n)


@dataclass
class RunLog:
    """Everything recorded for validation (§3.6)."""
    tbr_time: list = field(default_factory=list)     # when each TBR ended (min)
    tbr: list = field(default_factory=list)          # time between reversals (min)
    rev_cell: list = field(default_factory=list)     # which cell reversed
    rev_time: list = field(default_factory=list)
    rev_signal: list = field(default_factory=list)   # its s at that moment
    signal_samples: list = field(default_factory=list)  # (time, s for all cells), every 2 s
    kymo: list = field(default_factory=list)         # density along x, every 0.1 min
    snapshots: list = field(default_factory=list)    # (time, wrapped node positions)
