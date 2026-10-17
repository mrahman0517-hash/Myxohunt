# Motility Sim: *Myxococcus xanthus* hunting *E. coli*

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

Colours: magenta = E. coli (dark = dormant), green = M. xanthus (bright = well fed, yellow = scout,
white rim = killing a prey), grey = slime trails, mauve = prey remains, brown = ground nutrients.

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

## The live app

The world runs as you watch, from real time (×1) up to as fast as the computer can. Cell counts
against hours of biology are plotted below the world. The right panel holds the main settings:
some change the running world at once, the rest apply to the next world. The Settings button (top
right of the world) opens the advanced settings, switches that turn a rule off, the rules where
studies disagree (the recommended option starred), and the fixed values, which are measured or
from the paper and can't be changed. "Recommended" restores the starting settings.

## Layout

- `predation-sim/`: the simulation (one small file per job; `engine.py` sets the order of events),
  the app (`app_live.py`, `drawing.py`, `ui_widgets.py`), the recorder (`run_record.py`), check
  scripts (`checks/`) and an average-world model learned from the runs (`meanfield/`).
- `paper-reproduction/`: the validated rebuild of the paper's 2D model.
- `docs/`: every decision with its reason and source (`decision-log.md`), the sources
  (`sources.md`), every setting and its backing (`parameters.md`), and the build manual.
