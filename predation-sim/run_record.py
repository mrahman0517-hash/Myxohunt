"""
run_record.py — a headless video of one world (milestone 8, B1).

Runs the simulation without a window and draws a frame every few real minutes with drawing.py.
Each frame is saved as a picture, and at the end they are joined into an MP4. A checkpoint is
saved regularly, so a stopped recording carries on from where it was when started again with the
same name. --encode-only makes the MP4 from the frames saved so far (e.g. if time runs out).

Two scenes:
- world (default): the live world from the start (E. coli founders, Myxo arriving over 10 bio-h).
- closeup: one colony grown alone, then four drops of 20 Myxo at its edge (the B76 invasion test),
  drawn zoomed in on the colony, to show single kills, invasion and rippling.

Usage (from predation-sim/):
  python run_record.py NAME [--scene world|closeup] [--minutes 600] [--frame-every 0.25] [--seed 1]
                       [--mode live] [--size 1024] [--fps 30] [--encode-only] [setting=value ...]
--minutes counts from the start of the recording (after the colony has grown, for the close-up).
Writes ../videos/NAME/frames/*.jpg, ../videos/NAME/stats.csv and ../videos/NAME.mp4.
"""
import argparse
import glob
import os
import pickle
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")            # no window: must come before pygame
import numpy as np                                           # noqa: E402
import pygame                                                # noqa: E402

import drawing                                               # noqa: E402
from engine import Simulation                                # noqa: E402
from settings import make_settings                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEOS = os.path.join(HERE, "..", "videos")


def parse_overrides(args, mode):
    """Turn 'name=value' arguments into settings changes, each converted to that setting's own type."""
    defaults = make_settings(mode)
    out = {}
    for arg in args:
        name, value = arg.split("=", 1)
        kind = type(getattr(defaults, name))
        if kind is bool:
            out[name] = value.strip().lower() in ("1", "true", "yes", "on")
        else:
            out[name] = kind(float(value)) if kind in (int, float) else kind(value)
    return out


def read_args():
    """The command line."""
    p = argparse.ArgumentParser(description="Record a video of the predation simulation.")
    p.add_argument("name")
    p.add_argument("--scene", default="world", choices=["world", "closeup"])
    p.add_argument("--grow", type=float, default=40.0, help="closeup: real minutes the colony grows first")
    p.add_argument("--group-size", type=int, default=20, help="closeup: Myxo in each of the four drops")
    p.add_argument("--minutes", type=float, default=600.0, help="real minutes to record")
    p.add_argument("--frame-every", type=float, default=0.25, help="real minutes between frames")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--mode", default="live", choices=["live", "record"])
    p.add_argument("--size", type=int, default=1024, help="frame width and height in pixels")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--quality", type=float, default=8, help="video quality 0–10 (lower = smaller file)")
    p.add_argument("--save-every", type=float, default=30.0, help="real minutes between checkpoints")
    p.add_argument("--encode-only", action="store_true")
    p.add_argument("overrides", nargs="*", help="setting=value")
    return p.parse_args()


def save_frame(sim, surf, font, folder, k, scene):
    """Draw the world and save it as frame number k."""
    drawing.draw_world(surf, sim.world, font, view=scene["view"], title=scene["title"])
    pygame.image.save(surf, os.path.join(folder, f"frame_{k:05d}.jpg"))


def save_checkpoint(path, sim, k, scene):
    """The whole simulation, the next frame number and the scene, so a stopped recording can
    carry on."""
    with open(path + ".tmp", "wb") as fh:
        pickle.dump((sim, k, scene), fh)
    os.replace(path + ".tmp", path)


def new_scene(args):
    """A fresh simulation for the chosen scene, with its view, title and start time."""
    if args.scene == "world":
        settings = make_settings(args.mode, seed=args.seed, **parse_overrides(args.overrides, args.mode))
        return Simulation(settings), dict(view=None, title="", start=0.0)
    sys.path.insert(0, os.path.join(HERE, "checks"))
    from check_predation import add_attackers, colony_centre_and_radius   # the B76 invasion test's scene
    settings = make_settings("live", seed=args.seed, start_colonies=1, myxo_groups=0, myxo_singles=0,
                             ecoli_seed_interval=0.0, **parse_overrides(args.overrides, "live"))
    sim = Simulation(settings)
    sim.run_for(real_minutes=args.grow)
    centre, radius = colony_centre_and_radius(sim.world)
    add_attackers(sim.world, groups=4, size=args.group_size)
    view = drawing.View(sim.world.settings.box, args.size, tuple(centre), 2 * radius + 24)
    title = f"Close-up: {len(sim.world.myxo.uid)} M. xanthus arrive at one E. coli colony"
    return sim, dict(view=view, title=title, start=sim.world.t)


def encode(folder, out, fps, quality=8):
    """Join the saved frames into an MP4."""
    import imageio.v2 as imageio
    frames = sorted(glob.glob(os.path.join(folder, "frame_*.jpg")))
    with imageio.get_writer(out, fps=fps, codec="libx264", quality=quality, macro_block_size=16) as writer:
        for path in frames:
            writer.append_data(imageio.imread(path))
    print(f"saved {out} ({len(frames)} frames, {len(frames) / fps:.0f} s)", flush=True)


def progress(sim, t0, k, n):
    """One progress line."""
    w = sim.world
    print(f"t {w.t:5.1f} real min ({w.bio_t / 60:5.1f} bio h) | frame {k}/{n} | "
          f"E. coli {int((w.ecoli.lysis_timer < 0).sum())} | Myxo {len(w.myxo.uid)} | {time.time() - t0:5.0f} s",
          flush=True)


def record(args, folder, ckpt):
    """Run the world, saving a frame every --frame-every real minutes and a checkpoint every
    --save-every real minutes."""
    if os.path.exists(ckpt):
        with open(ckpt, "rb") as fh:
            saved = pickle.load(fh)
        sim, k = saved[:2]
        scene = saved[2] if len(saved) > 2 else dict(view=None, title="", start=0.0)   # older checkpoints
        print(f"carrying on from the checkpoint at {sim.world.t:.1f} real min (frame {k})", flush=True)
    else:
        (sim, scene), k = new_scene(args), 0
    pygame.init()
    surf = pygame.Surface((args.size, args.size))
    font = pygame.font.Font(None, max(16, args.size // 42))
    times = scene["start"] + np.arange(0.0, args.minutes + 1e-9, args.frame_every)
    dt, t0, last_save, last_print = sim.world.settings.dt, time.time(), sim.world.t, -1e9
    while k < len(times):
        steps = int(round((times[k] - sim.world.t) / dt))
        for _ in range(max(steps, 0)):
            sim.step()
        save_frame(sim, surf, font, folder, k, scene)
        k += 1
        if sim.world.t - last_print >= 10.0 - 1e-9:
            progress(sim, t0, k, len(times))
            last_print = sim.world.t
        if sim.world.t - last_save >= args.save_every - 1e-9:
            sim.stats.to_csv(os.path.join(folder, "..", "stats.csv"))
            save_checkpoint(ckpt, sim, k, scene)
            last_save = sim.world.t
    sim.stats.to_csv(os.path.join(folder, "..", "stats.csv"))
    save_checkpoint(ckpt, sim, k, scene)


def main():
    """Record (or carry on recording), then encode the MP4."""
    args = read_args()
    base = os.path.join(VIDEOS, args.name)
    folder = os.path.join(base, "frames")
    os.makedirs(folder, exist_ok=True)
    if not args.encode_only:
        record(args, folder, os.path.join(base, args.name + ".ckpt"))
    encode(folder, os.path.join(VIDEOS, args.name + ".mp4"), args.fps, args.quality)


if __name__ == "__main__":
    sys.exit(main())
