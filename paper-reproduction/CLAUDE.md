# Paper reproduction (step 1 of the plan)

A rebuild of the 2D agent-based model in Saulnier et al. 2026, *Nature Physics*,
doi:10.1038/s41567-026-03416-y (PDF in `../Resources/`), used to validate the core before
the predation project is built on it. Project-wide brief and decisions: `../CLAUDE.md`.

## Where things stand (9 October 2026)

- Step 1 is done: rippling-only and swarming-only runs at quick-test size reproduce the
  paper's simulated signatures (two-peaked vs one-peaked time between reversals, swarming
  alignment decaying within ~20 µm, reversals concentrated in each cell's top frustration
  quartile). Numbers are in `../docs/decision-log.md` (Part A).
- Same-settings comparison with the authors' own code (github.com/MignotLab/SpatialPatternsCollectives,
  commit b31a499) done 10 Oct 2026: close match (decision-log A10, A11). Their results are in
  `results/authors/`, overlay figure in `figures/vs_authors/`.
- Not done: more seeds, a bigger box.
- Next is step 2: the split-box coexistence run (paper Fig. 6b, c). Suggested size:
  a 130 µm box at the paper's densities (~2,700 cells, about an hour per run on one core).
  Agree the box size and starting ratios with me before running.

## Code layout — keep this split

| File | Role |
|---|---|
| `datatypes.py` | `Params` (every parameter with a source tag: [paper], [code] or assumed), `Population`, `EPSField`, `RunLog`. Containers only. |
| `functions.py` | The model's rules as pure functions (arrays in, arrays out). All physics lives here. |
| `engine.py` | `Simulation`: set-up, the time-step order, recording. Only place that decides the order of events. |
| `visualization.py` | Drawing only; never changes simulation state. |
| `run_quicktest.py`, `make_figures.py` | Entry points. |

Cells are stored as arrays (one row per cell), not one Python object per cell, for speed.
New rules go into `functions.py` as functions and get called from `engine.py`.

## Run

The venv lives at the project root (`../.venv`, built from `../requirements.txt`).
Run from inside this folder, since `results/` and `figures/` are relative paths:

```
cd paper-reproduction
..\.venv\Scripts\activate         (Windows; on macOS/Linux: source ../.venv/bin/activate)
python run_quicktest.py rippling  (or swarming; --T minutes, --seed n)
python make_figures.py
```

A 150-minute quick test takes about 15–20 minutes on one core. Use `--T 30` to smoke-test.

## Model details that are easy to get wrong

- The threshold f_T = 0.08 applies to the smoothed signal s = weighted mean of the last 20 s
  of frustration, divided by 2 (a 0–1 scale), not to raw frustration f (0–2).
- β = 2 is a decay rate (per minute) inside the 20 s window, although the paper prints "2 min".
- Reversal chance per step uses the authors' code form, (1 − exp[−rate]) · Δt, so the effective
  maximum rate is about 1 per minute whether F* is 3 (code) or 30 (paper text).
- The head disc is pulled at speed × 10; the springs share that out, so the cell's centre moves
  at 4 µm/min.
- Rippling cells neither lay nor follow EPS. EPS is laid under the rear disc.
- Rippling alignment is imposed (one horizontal axis); its biological origin is unknown.
