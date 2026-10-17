# Motility Sim

A 2D agent-based simulation of *Myxococcus xanthus* predation, grounded in
Saulnier et al. 2026, *Nature Physics*, doi:10.1038/s41567-026-03416-y (PDF in `Resources/`).
End goal: *E. coli* prey colonies appear at random; *M. xanthus* swarms to them, feeds, and
ripples on digested prey. The two movement modes are the focus; the video comes last.

## Layout

- `paper-reproduction/`: the faithful rebuild of the paper's 2D model (plan step 1, done and
  validated). It has its own `CLAUDE.md` with the code layout, run commands and model
  details. It is a validation exercise, not the main project.
- `predation-sim/`: the main project, built milestone by milestone from
  `docs/build-manual.md`. Run from inside it: `..\.venv\Scripts\python.exe -m pytest tests`.
- `docs/`: background and decisions shared by the whole project.
- `.venv/` and `requirements.txt` at the root are shared by all code.

## Decisions and results

@docs/decision-log.md

Append every new decision to `docs/decision-log.md` (decision, why, source, date) as soon as
it is made.

## Working with me

- I'm a microbiologist and new to programming and to the maths. Explain code in plain
  language, derive any maths step by step, and connect it to the biology.
- Keep answers concise and dense, with few bullet points. Give honest critique; flag
  uncertainty and your own mistakes plainly.
- Cite the paper section or figure (or "authors' code") for every model rule you add or change.
- Ask before long or expensive runs; quick tests first.
- When a choice comes up, give me 2–4 options with plain trade-offs (and mark the one you
  recommend), rather than a single suggestion. Don't settle open choices on my behalf.

## Reference docs (read when relevant; not loaded automatically)

- `docs/model-foundations.md` (and `.docx`): every rule, equation, parameter and validation metric.
- `docs/swarming-rippling-pathways.md`: cause-to-effect summary of the two patterns.
- `docs/sim-plan.md`: the original project plan and open design questions (prey, feeding, 3D).
- `Resources/`: the article PDF.
- `docs/build-manual.md`: the full coding spec for `predation-sim/` (files, functions,
  parameters, build milestones). Follow it when building.
- `docs/sources.md`: every outside fact we use, with a link and a one-to-two-sentence note.
  Add an entry whenever a new fact enters the model.
- `docs/parameters.md`: every setting with its backing (paper, measured, tuned, assumed, the
  user's choice) and the levers that set the predator–prey balance. Update it when settings change.
