"""
Branch a stopped population run: carry on from its checkpoint for a while with some settings
changed, saving under a new name (B99). The original checkpoint is left as it was, so a treatment
and a control can start from the very same state and the same random numbers; any difference
between them comes from the change.

Usage (from predation-sim/):
    python checks/branch_test.py new_name from_name bio_hours [setting=value ...]
Writes checks/output/<new_name>_stats.csv (the original run's rows, then the branch's) and saves a
checkpoint every 30 real min, kept at the end; starting the same command again carries on from it,
and with more bio_hours it extends a finished branch.
"""
import os
import pickle
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import check_populations as cp                              # noqa: E402

OUT = cp.OUT


def load(name):
    """A checkpoint's (simulation, snapshots)."""
    with open(os.path.join(OUT, name + ".ckpt"), "rb") as fh:
        return pickle.load(fh)


def main():
    """Branch, run for the given biological hours, and save."""
    new, old, hours = sys.argv[1], sys.argv[2], float(sys.argv[3])
    changes = cp.parse_overrides(sys.argv[4:])
    base = os.path.join(OUT, new)
    if os.path.exists(base + ".ckpt"):
        sim, snaps = load(new)
        wrong = [k for k, v in changes.items() if not cp.same_value(getattr(sim.world.settings, k), v)]
        if wrong:
            sys.exit(f"{new}.ckpt was made with other values for {wrong}; use a new name")
        print(f"carrying on from the branch checkpoint at {sim.world.bio_t / 60:.1f} bio-h", flush=True)
    else:
        sim, snaps = load(old)
        sim.world.branch_start = sim.world.bio_t                  # where the branch began, in bio min
        for key, value in changes.items():
            setattr(sim.world.settings, key, value)
        print(f"branching {old} at {sim.world.bio_t / 60:.1f} bio-h with {changes}", flush=True)
    s = sim.world.settings
    end_t = sim.world.t + (sim.world.branch_start + hours * 60.0 - sim.world.bio_t) / s.speedup
    t0 = time.time()
    while sim.world.t < end_t - s.dt / 2:
        chunk = min(cp.SAVE_EVERY, end_t - sim.world.t)
        sim.run_for(real_minutes=chunk, callback=lambda w: cp.status(w, t0), every_minutes=10.0)
        cp.save_progress(base, sim, snaps)
    cp.save_progress(base, sim, snaps)
    sim.stats.to_csv(base + "_stats.csv")
    print("done", base + "_stats.csv", flush=True)


if __name__ == "__main__":
    main()
