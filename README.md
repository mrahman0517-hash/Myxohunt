# MyxoHunt: swarming, hunting and rippling of *Myxococcus xanthus*

A 2D agent-based simulation of a bacterial predator and its prey, built on the swarming and
rippling model of Saulnier et al. 2026, *Nature Physics* (doi:10.1038/s41567-026-03416-y).

*E. coli* colonies grow on patchy ground. *M. xanthus* cells arrive, swarm along slime trails,
find colonies, kill prey on contact and eat what spills out, ripple on prey remains, and starve
into a famine when prey run out. Both species are individual cells at real size (Myxo: the paper's
10-disc chains; E. coli: 1 µm-wide rods); slow biology runs 10× faster than movement.

## Videos

- `videos/world250_60h.mp4`: a 250 µm world with 10 colonies over 60 h of biology.
- `videos/predation_100h.mp4`: the 150 µm live world over 100 h of biology.
- `videos/closeup_240.mp4`: a close-up of 240 Myxo eating one E. coli colony (7.5 h).
- `videos/closeup_invasion.mp4`: the same with 80 Myxo, too few to outpace the colony's growth.
- `videos/swarm_reversals.mp4`, `videos/ripple_reversals.mp4`: the paper's 65 µm test box, swarming
  (370 cells) and rippling (1,000 cells), 20 real minutes each, to see the reversals.

Colours: magenta = E. coli (dark = dormant), green = M. xanthus (bright = well fed, yellow = scout,
white rim = killing a prey), white dot = a Myxo's leading pole, orange = reversed in the last 15 s,
grey = slime trails, mauve = prey remains, brown = ground nutrients.

## Run it

```
python -m venv .venv
.venv\Scripts\activate            (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cd predation-sim
python app_live.py                # the live window (see below)
python run_record.py myvideo --minutes 360          # a 60 bio-h video of the live world
python run_record.py close --scene closeup --grow 60 --group-size 60 --minutes 45 --frame-every 0.05 --quality 5
python -m pytest tests            # 86 tests
```

## In the browser

`web/` runs the same simulation live in the browser (Pyodide: Python with numpy and scipy compiled
for the web), with the same sliders, switches, evidence options and graph. It's a static site: on
Vercel, import this repository with **Root Directory `web`** (framework "Other", no build
command). After changing the simulation, run `python web/build.py` to refresh `web/py/`. To try
it locally: `python -m http.server 8765 --directory web`, then open http://localhost:8765. The
first visit downloads about 25 MB; it runs at up to about ×10 real time. Biology runs 10× faster
than gliding; that speed-up is locked, because changing it would change the balance (B97).

## The live app

The world runs as you watch, from real time (×1) up to as fast as the computer can. Cell counts
against hours of biology are plotted below the world. The right panel holds the main settings:
some change the running world at once, the rest apply to the next world. The Settings button (top
right of the world) opens the advanced settings, switches that turn a rule off, the rules where
studies disagree (the recommended option starred), and the fixed values, which are measured or
from the paper and can't be changed. "Recommended" restores the starting settings.

## Known limitation: in the band, but not steady enough to pass

The aim was a balanced cycle, after the first wave, of about 700–1,000 E. coli and about 150 Myxo,
judged over 150–300 bio-h on four seeds (`checks/judge_band.py`, 3 of 4 must pass).

- **The Recommended settings** (famine lysis 70%, ground refill ÷5; `docs/decision-log.md`, B103–B104)
  put the means inside both bands in all four seeds: prey 707–828, hunters 171–201.
- **Why they still fail the rule (0 of 4 pass):** on drift. The rule allows at most 20% change per
  100 bio-h. The prey take until about 190 bio-h to climb back from the first-wave crash, and both
  populations swing slowly within the band.
- **Earlier presets:** refill ÷6 (B101–B102) held steadier but left the prey just under the band (1 of
  4 passed). The original preset (famine lysis 20%, refill ÷8; B98) crashed the prey to about 100–350.
- **Rippling** almost never forms in the predation world: the hunters are too sparse.

## Layout

- `predation-sim/`: the simulation (one small file per job; `engine.py` sets the order of events),
  the app (`app_live.py`, `drawing.py`, `ui_widgets.py`), the recorder (`run_record.py`), check
  scripts (`checks/`) and an average-world model learned from the runs (`meanfield/`).
- `paper-reproduction/`: the validated rebuild of the paper's 2D model.
- `docs/`: every decision with its reason and source (`decision-log.md`), the sources
  (`sources.md`), every setting and its backing (`parameters.md`), and the build manual.
