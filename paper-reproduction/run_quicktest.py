"""
run_quicktest.py — step 1 of the plan: rippling-only and swarming-only runs at
the authors' quick-test size, saved for validation.

Usage:
    python run_quicktest.py rippling            # 1,000 cells, 65 µm box, 150 min
    python run_quicktest.py swarming            # 370 cells, same box
    python run_quicktest.py rippling --T 60 --seed 2

Each run writes results/<mode>_seed<seed>.npz; make_figures.py turns those into plots.
"""
import argparse
import os
import numpy as np

from datatypes import Params
from engine import Simulation

QUICK_TEST = {               # authors' own test settings [code]; same densities as the paper
    "rippling": dict(n_cells=1000, box=65.0),
    "swarming": dict(n_cells=370, box=65.0),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=list(QUICK_TEST))
    ap.add_argument("--T", type=float, default=150.0, help="simulated minutes")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    params = Params(mode=args.mode, T=args.T, **QUICK_TEST[args.mode])
    sim = Simulation(params, seed=args.seed)
    sim.run()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"{args.mode}_seed{args.seed}.npz")
    np.savez_compressed(path, **sim.results())
    print("saved", path)


if __name__ == "__main__":
    main()
