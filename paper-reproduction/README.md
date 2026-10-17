# Motility Sim — step 1: the 2D core

A rebuild of the 2D agent-based model in Saulnier et al. 2026 (*Nature Physics*),
written to reproduce their rippling and swarming results before we add prey.

## Set up

The venv lives at the project root and is shared. From the root folder:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

From inside `paper-reproduction/` (results and figures are written relative to it):

```bash
cd paper-reproduction
python run_quicktest.py rippling   # 1,000 cells, 65 µm box, 150 simulated min (~15–20 min on one core)
python run_quicktest.py swarming   # 370 cells, same box
python make_figures.py             # prints a summary table, writes figures/validation.png
```

Try a shorter run first with `--T 30`. Statistics always use the last 50 minutes
of a run, so use at least `--T 60`.

## How the code is organised

| File | What it holds | Changes the simulation? |
|---|---|---|
| `datatypes.py` | `Params` (every parameter, with its source), `Population` (all cells as arrays), `EPSField`, `RunLog` | No, only containers |
| `functions.py` | The model's rules as plain functions: traction, repulsion, springs, alignment, EPS trails, frustration, reversal curves, measurements | Each function does one rule |
| `engine.py` | `Simulation`: places cells, runs the time loop in the authors' order, records statistics | Yes, it calls the rules in order |
| `visualization.py` | Drawing only | No |
| `run_quicktest.py`, `make_figures.py` | Entry points | No |

One time step (0.3 s), as in `Simulation.step()`:

1. Pull each head disc forward, push overlapping discs apart, relax the springs.
2. Turn the head: towards the rippling axis, or towards EPS trails (swarming cells also lay EPS).
3. Compare intended and real head velocity → frustration f → 20 s weighted memory → signal s.
4. Age the reversal clock; past the refractory period, reverse at random at the frustration-dependent rate.
5. Keep every cell inside the periodic box.

## Where this differs from the authors' code (all intended to be equivalent)

- Repulsion looks at every disc within one disc diameter; theirs looks at the 13 nearest discs.
  These match unless more than 12 discs overlap one disc.
- The EPS grid wraps around the box edges directly; theirs copies the edges. The heading is
  rounded to 0.25° when deciding which wedge a grid square falls in (a speed-up).
- Times between reversals are recorded only for real intervals (from one reversal to the next);
  their first interval per cell starts from a random clock value. Both use the last 50 minutes.

`../docs/model-foundations.md` explains every rule and parameter; `CLAUDE.md` (here and at the project root) holds the brief for Claude Code.
