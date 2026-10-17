"""
web_controller.py — the simulation behind the web app (B94). It runs in the visitor's browser with
Pyodide (Python compiled for the browser, with numpy and scipy): it builds worlds from the same
settings catalogue as the desktop app (app_params.py), applies the page's controls, steps the world
for a slice of computing time, and packs each frame into plain bytes for the page to draw.
No pygame here.
"""
import json
import time

import numpy as np

import app_params as P
import geometry as geo
import myxo_modes
from engine import Simulation
from settings import make_settings

REVERSAL_FLASH = 0.25            # real min: drawn orange this long after a reversal (B92)
GROUND_EMPTY = np.array([255, 250, 232])
GROUND_RICH = np.array([226, 168, 92])
MATRIX_TINT = np.array([196, 150, 214])
MYXO_DIM = np.array([25, 95, 40])
MYXO_BRIGHT = np.array([70, 225, 95])
SCOUT = (200, 235, 60)
REVERSED = (255, 150, 40)


def fmt_parts(fmt):
    """Split a format such as '÷{:g}', '{:.0%}' or '{:g} bio-min' into what the page needs to show
    a value the same way: a prefix, a suffix, and whether it is a percentage."""
    prefix, rest = fmt.split("{", 1)
    spec, suffix = rest.split("}", 1)
    return dict(prefix=prefix, suffix=suffix, percent=spec.endswith("%"))


ATTACK_GROW = 50.0       # real min the colony grows alone before the hunters arrive (attack scene)
ATTACK_DROPS, ATTACK_SIZE = 4, 60
PAPER_BOX = dict(box=65.0, start_colonies=0, myxo_groups=0, myxo_singles=0, eps_fade_time=float("inf"),
                 matrix_half_life=float("inf"), chemo_strength=0.0, speedup=1.0, scout_start_rate=0.0)
SCENES = {   # B95: what each scene changes on top of the chosen settings
    "world": {},
    "swarm": PAPER_BOX,
    "ripple": PAPER_BOX,
    "attack": dict(start_colonies=1, myxo_groups=0, myxo_singles=0, ecoli_seed_interval=0.0,
                   richness_min=0.3, richness_max=1.0),
}
WARM = {"swarm": 30.0, "ripple": 30.0, "attack": ATTACK_GROW}   # real min pre-run by web/make_scenes.py
SCENE_DIR = "/sim/scenes"


def colony_centre_and_radius(world):
    """Centre (circular mean, safe across the edges) and outer radius of the E. coli."""
    box, c = world.settings.box, world.ecoli.centre
    ang = c / box * 2 * np.pi
    centre = (np.arctan2(np.sin(ang).mean(0), np.cos(ang).mean(0)) % (2 * np.pi)) / (2 * np.pi) * box
    d = geo.min_image(c - centre, box)
    return centre, float(np.linalg.norm(d, axis=1).max())


class Controller:
    """One running world and the settings the page has chosen."""

    def __init__(self):
        self.values, self.saved_on, self.scene = dict(P.RECOMMENDED), {}, "world"
        self.reset()

    # ------------------------------------------------------------ settings
    def desired(self):
        """The chosen settings (those applied 'on reset' take effect in the next world), with the
        scene's own changes on top."""
        return make_settings("live", **{**self.values, **SCENES[self.scene]})

    def reset(self):
        """A new world from the chosen settings and scene; the paper's boxes and the attack start
        from a state pre-run on a PC (web/make_scenes.py) when one ships with the page."""
        if self.load_warm():
            return
        self.build()

    def load_warm(self):
        """Start from a pre-run state, if there is one for this scene."""
        import gzip
        import os
        import pickle
        path = os.path.join(SCENE_DIR, self.scene + ".pkl.gz")
        if self.scene == "world" or not os.path.exists(path):
            return False
        with gzip.open(path, "rb") as fh:
            self.sim, self.focus = pickle.load(fh)
        for key, value in {**self.values, **SCENES[self.scene]}.items():   # the page's live choices
            if key not in ("box", "start_colonies", "myxo_groups", "myxo_singles", "richness_min", "richness_max"):
                setattr(self.sim.world.settings, key, value)
        self.attacked = True
        self.rows_sent = 0
        self.world_id = getattr(self, "world_id", 0) + 1
        return True

    def build(self):
        """A brand-new world for the scene."""
        self.sim = Simulation(self.desired(), seed_cells=self.scene in ("world", "attack"))
        w = self.sim.world
        if self.scene in ("swarm", "ripple"):
            import seeding
            if self.scene == "ripple":
                f = w.fields
                f.matrix[:], f.matrix_smooth[:], f.axis_c[:], f.axis_s[:] = 1.0, 1.0, 1.0, 0.0
                seeding.uniform_myxo(w, 1000, aligned_axis=0.0)
            else:
                seeding.uniform_myxo(w, 370)
        self.attacked = self.scene != "attack"
        self.focus = None
        if self.scene == "attack" and len(w.ecoli.uid):
            c = w.ecoli.centre[0]
            self.focus = [float(c[0]), float(c[1]), 80.0]
        self.rows_sent = 0
        self.world_id = getattr(self, "world_id", 0) + 1

    def set_scene(self, name):
        """Switch scene: a new world."""
        self.scene = name
        self.reset()

    def maybe_attack(self):
        """Attack scene: once the colony has grown, drops of hunters arrive at its edge."""
        w = self.sim.world
        if self.attacked or w.t < ATTACK_GROW:
            return
        import seeding
        import state
        centre, radius = colony_centre_and_radius(w)
        for k in range(ATTACK_DROPS):
            a = 2 * np.pi * k / ATTACK_DROPS
            spot = centre + (radius + 4.0) * np.array([np.cos(a), np.sin(a)])
            state.append_rows(w.myxo, seeding.myxo_group(w, spot, ATTACK_SIZE))
        self.focus = [float(centre[0]), float(centre[1]), 2 * radius + 24]
        self.attacked = True

    def recommended(self):
        """Back to the recommended settings, in a new world."""
        self.values, self.saved_on = dict(P.RECOMMENDED), {}
        self.reset()

    def apply(self, changes, live):
        """Record setting changes; write them into the running world too if they are live."""
        self.values.update(changes)
        if live:
            for key, value in changes.items():
                setattr(self.sim.world.settings, key, value)

    def set_param(self, key, value):
        """A slider moved."""
        param = next(p for p in P.MAIN + P.ADVANCED if p.key == key)
        value = int(round(value)) if float(param.step).is_integer() else float(value)
        self.apply(param.settings_for(value, self.desired()), param.when == "live")

    def set_switch(self, index, on):
        """A rule switched off or back on (restoring what it replaced)."""
        switch = P.EFFECTS[index]
        if on:
            self.apply(self.saved_on.pop(switch.label, {}), True)
        else:
            d = self.desired()
            self.saved_on[switch.label] = {k: getattr(d, k) for k in switch.off}
            self.apply(dict(switch.off), True)

    def set_evidence(self, index, option):
        """One of the options where studies disagree."""
        self.apply(dict(P.EVIDENCE[index].options[option][1]), True)

    # ------------------------------------------------------------ what the page shows
    def state_json(self):
        """Every control's current value, as JSON."""
        d = self.desired()
        evidence = []
        for rule in P.EVIDENCE:
            match = [i for i, (_, ch) in enumerate(rule.options) if all(getattr(d, k) == v for k, v in ch.items())]
            evidence.append(match[0] if match else -1)
        return json.dumps(dict(
            params={p.key: p.value_from(d) for p in P.MAIN + P.ADVANCED},
            switches=[not all(getattr(d, k) == v for k, v in s.off.items()) for s in P.EFFECTS],
            evidence=evidence))

    def catalog_json(self):
        """Everything the page needs to build its controls, as JSON."""
        def param(p):
            return dict(key=p.key, label=p.label, lo=p.lo, hi=p.hi, step=p.step, when=p.when,
                        backing=p.backing, **fmt_parts(p.fmt))
        return json.dumps(dict(
            main=[param(p) for p in P.MAIN], advanced=[param(p) for p in P.ADVANCED],
            switches=[dict(label=s.label, note=s.note) for s in P.EFFECTS],
            evidence=[dict(label=r.label, options=[o[0] for o in r.options], best=r.best) for r in P.EVIDENCE],
            fixed=[dict(name=n, value=v, source=src) for n, v, src in P.FIXED]))

    # ------------------------------------------------------------ running
    def run(self, budget_ms, max_minutes):
        """Step until budget_ms of computing is used or max_minutes of simulated real time have
        passed (0 = no limit); returns the simulated minutes."""
        w = self.sim.world
        start, t0 = w.t, time.perf_counter()
        n_max = int(max_minutes / w.settings.dt) if max_minutes > 0 else 10 ** 9
        n = 0
        while n < n_max and (time.perf_counter() - t0) * 1000.0 < budget_ms:
            self.sim.step()
            if not self.attacked:
                self.maybe_attack()
            n += 1
        if n:
            self.ms_per_step = (time.perf_counter() - t0) * 1000.0 / n
        return w.t - start

    # ------------------------------------------------------------ one frame for the page
    def ground_image(self):
        """Nutrients (cream to brown) with prey remains tinted mauve: RGBA rows from the top."""
        s, f = self.sim.world.settings, self.sim.world.fields
        rich = np.clip(f.nutrients, 0.0, 1.0)[..., None]
        rgb = GROUND_EMPTY + (GROUND_RICH - GROUND_EMPTY) * rich
        tint = np.clip(f.matrix / s.matrix_ripple_threshold, 0.0, 1.0)[..., None] * 0.55
        rgb = rgb + (MATRIX_TINT - rgb) * tint
        img = np.empty(rgb.shape[:2] + (4,), dtype=np.uint8)
        img[..., :3], img[..., 3] = rgb, 255
        return np.ascontiguousarray(img.transpose(1, 0, 2)[::-1])

    def slime_image(self):
        """Slime trails as grey with see-through strength, at half the slime grid's resolution."""
        f = self.sim.world.fields
        slime = f.eps + f.eps_scout
        n = slime.shape[0] // 2 * 2
        slime = slime[:n, :n].reshape(n // 2, 2, n // 2, 2).max(axis=(1, 3))
        img = np.zeros(slime.shape + (4,), dtype=np.uint8)
        img[..., :3] = 95
        img[..., 3] = (150 * np.clip(slime / 0.5, 0.0, 1.0)).astype(np.uint8)
        return np.ascontiguousarray(img.transpose(1, 0, 2)[::-1])

    def ecoli_arrays(self):
        """Rod end points (x0, y0, x1, y1 in µm, wrapped) and state (0 growing, 1 dormant, 2 dead)."""
        s, e = self.sim.world.settings, self.sim.world.ecoli
        ends = np.mod(geo.rod_points(e.centre, e.angle, e.length, 2, s.ecoli_width), s.box)
        kind = np.where(e.lysis_timer >= 0, 2, np.where(e.dormant, 1, 0)).astype(np.uint8)
        return ends.reshape(-1, 4).astype(np.float32), kind

    def myxo_arrays(self):
        """Disc positions (wrapped, µm), colours (green by store, scouts yellow, orange after a
        reversal) and whether each cell is killing."""
        s, m = self.sim.world.settings, self.sim.world.myxo
        full = np.clip(m.energy / 200.0, 0.0, 1.0)[:, None]
        colours = (MYXO_DIM + (MYXO_BRIGHT - MYXO_DIM) * full).astype(np.uint8)
        colours[m.scout] = SCOUT
        colours[m.age < REVERSAL_FLASH] = REVERSED
        nodes = np.mod(m.nodes, s.box).astype(np.float32)
        return nodes, colours, (m.pause_left > 0).astype(np.uint8)

    def frame(self):
        """Everything to draw, as bytes, plus a JSON line of numbers (time, counts, new graph rows)."""
        w = self.sim.world
        e, m = w.ecoli, w.myxo
        alive = e.lysis_timer < 0
        ground, slime = self.ground_image(), self.slime_image()
        rods, kind = self.ecoli_arrays()
        nodes, colours, killing = self.myxo_arrays()
        rows = self.sim.stats.rows[self.rows_sent:]
        self.rows_sent = len(self.sim.stats.rows)
        meta = dict(world=self.world_id, scene=self.scene, focus=self.focus, t=w.t, bio_h=w.bio_t / 60.0, box=w.settings.box, ground_n=ground.shape[0],
                    slime_n=slime.shape[0], n_ecoli=int(alive.sum()), dormant=int((alive & e.dormant).sum()),
                    n_myxo=len(m.uid), starving=int(myxo_modes.stringent(w).sum()) if len(m.uid) else 0,
                    killing=int(killing.sum()), n_spores=len(w.spores), ms_per_step=getattr(self, "ms_per_step", 0.0),
                    rows=[[r["bio_t"] / 60.0, r["ecoli"], r["ecoli_dormant"], r["myxo"], r["myxo_stringent"]]
                          for r in rows])
        return dict(meta=json.dumps(meta), ground=ground.tobytes(), slime=slime.tobytes(), rods=rods.tobytes(),
                    kind=kind.tobytes(), nodes=nodes.tobytes(), colours=colours.tobytes(),
                    killing=killing.tobytes(), spores=np.asarray(w.spores, dtype=np.float32).tobytes())
