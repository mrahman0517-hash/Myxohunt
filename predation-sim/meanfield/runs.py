"""
meanfield/runs.py — the finished full-simulation runs the average-world model learns from, with
the settings that differ between them, and a loader for their statistics.

Every run uses the live world (150 µm) and the defaults of its time except for the settings
listed. "rich" multiplies every patch's maximum (richness), "regrow" multiplies the ground's
refill speed.
"""
import os
from dataclasses import dataclass

import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "checks", "output")


@dataclass
class Run:
    """One finished run and the settings that set it apart."""
    name: str
    efficiency: float
    starving_cost: float
    rich: float = 1.0
    regrow: float = 1.0
    label: str = ""
    wake: float = 0.01          # food that wakes a dormant E. coli (0.2 since B87)
    grace: float = 24.0         # bio-h dormant before E. coli can starve to death (0 since B87)
    fit: bool = True            # False: drawn by compare.py but left out of fit.py


RUNS = [
    Run("b84_full_120h", 0.5, 0.1, label="B84: 50%, 10%"),
    Run("b85_full_120h_s1", 0.3, 0.3, label="B85: 30%, 30%, seed 1"),
    Run("b85_full_120h_s2", 0.3, 0.3, label="B85: 30%, 30%, seed 2"),
    Run("b85_full_48h_r50", 0.3, 0.3, rich=0.5, label="ground ×0.5, 30%, 30%"),
    Run("b85_full_48h_r35", 0.3, 0.3, rich=0.35, label="ground ×0.35, 30%, 30%"),
    Run("b85_diag_r50_eff50", 0.5, 0.3, rich=0.5, label="ground ×0.5, 50%, 30%"),
    Run("b85_diag_r50_oldhunters", 0.5, 0.1, rich=0.5, label="ground ×0.5, 50%, 10%"),
    Run("b85_refill6_eff50_s1", 0.5, 0.3, regrow=1 / 6, label="refill ÷6, 50%, 30%"),
    Run("cand_B_150h", 0.6, 0.3, rich=0.7, regrow=1 / 20, wake=0.03, label="B: ÷20, ×0.7, 60%, wake 0.03"),
    Run("cand_F_150h", 0.6, 0.3, rich=0.7, regrow=1 / 40, label="F: ÷40, ×0.7, 60%"),
    # Not for fitting: from 85 bio-h on about half its prey were one colony of inherited persisters
    # (B87 result), while the model assumes 5% persisters in every colony.
    Run("cand_B87_150h", 0.6, 0.3, rich=0.7, regrow=1 / 20, wake=0.2, grace=0.0,
        label="B with B87 E. coli rules", fit=False),
    Run("cand_B88_r6_150h", 0.6, 0.3, rich=0.7, regrow=1 / 6, wake=0.2, grace=0.0,
        label="B88: ÷6, ×0.7, 60%"),
    Run("cand_B88_r10_150h", 0.6, 0.3, rich=0.7, regrow=1 / 10, wake=0.2, grace=0.0,
        label="B88: ÷10, ×0.7, 60%"),
    # Not for fitting: 20% famine lysis instead of 70% (B89); the model has one fitted hunter loss rate.
    Run("cand_B89_r8_150h", 0.6, 0.3, rich=0.7, regrow=1 / 8, wake=0.2, grace=0.0,
        label="B89: ÷8, lysis 20% (not in model)", fit=False),
    Run("cand_B89_r10_150h", 0.6, 0.3, rich=0.7, regrow=1 / 10, wake=0.2, grace=0.0,
        label="B89: ÷10, lysis 20% (not in model)", fit=False),
]


def load(run):
    """The run's statistics as arrays: bio-hours, living E. coli, dormant E. coli, Myxo, mean
    ground nutrient, prey remains (matrix)."""
    d = np.genfromtxt(os.path.join(OUT, run.name + "_stats.csv"), delimiter=",", names=True)
    return dict(h=d["bio_t"] / 60.0, E=d["ecoli"], D=d["ecoli_dormant"], H=d["myxo"],
                n=d["nutrients"], M=d["matrix"])


def available(runs=RUNS):
    """The runs whose statistics exist on disk."""
    return [r for r in runs if os.path.exists(os.path.join(OUT, r.name + "_stats.csv"))]
