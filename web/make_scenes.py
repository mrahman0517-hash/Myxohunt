"""
web/make_scenes.py — pre-run the web app's slow-starting scenes on a PC and save them for the page
(B95): the paper's swarming and rippling boxes after 30 real min (streams and ripples formed), and
the attack scene's colony grown for 50 real min with its four drops of 60 Myxo just arrived.

    python web/make_scenes.py [scene ...]

Writes web/scenes/<scene>.pkl.gz (the whole simulation, pickled and compressed).
"""
import gzip
import os
import pickle
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "predation-sim"))
import web_controller as W                                  # noqa: E402


def main():
    """Build each scene fresh, run it to its warm-up time, and save it."""
    os.makedirs(os.path.join(HERE, "scenes"), exist_ok=True)
    for scene in sys.argv[1:] or ["swarm", "ripple", "attack"]:
        c = W.Controller()
        c.scene = scene
        c.build()
        dt = c.sim.world.settings.dt
        while c.sim.world.t < W.WARM[scene] - dt / 2:
            c.run(10_000, W.WARM[scene] - c.sim.world.t + dt / 2)       # at least one step each time
            print(f"{scene}: {c.sim.world.t:.1f} real min", flush=True)
        c.maybe_attack()
        path = os.path.join(HERE, "scenes", scene + ".pkl.gz")
        with gzip.open(path, "wb", compresslevel=6) as fh:
            pickle.dump((c.sim, c.focus), fh)
        print(f"saved {path} ({os.path.getsize(path) / 1e6:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
