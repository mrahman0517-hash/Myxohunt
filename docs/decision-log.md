# Decision log

Every decision in the project, with the reason in plain words and where it comes from. Add new
decisions at the end of the right part as soon as they're made, and never delete an old one:
mark it **Replaced by #…** instead.

Each entry gives the decision in bold, then why, then the source: a paper (details in
`sources.md`), "authors' code", or "our assumption" when no measurement exists.

---

## Part A: Paper reproduction (swarming and rippling)

The faithful rebuild of Saulnier et al. 2026, in `paper-reproduction/`. Its job is to prove the
swarming and rippling core works before the predation project builds on it.

**A1. Cell body: the authors' 10-disc chain (0.5 µm apart, 5 µm long, 0.7 µm wide, bends freely).** *9 Oct 2026*
Needed to reproduce their figures. Literature sizes (5–7 µm × 0.5 µm) are kept as a later
sensitivity test. Source: Saulnier 2026, Methods.

**A2. Reversal chance per step uses the code form, p = (1 − exp[−rate]) · Δt.** *9 Oct 2026*
This reproduces the published figures. It caps the effective rate near once a minute, so F* =
3 (code) and F* = 30 (paper text) behave almost the same. The literal form can be tested
later. Source: authors' code.

**A3. Test size: 1,000 rippling cells or 370 swarming cells in a 65 × 65 µm wrap-around box.** *9 Oct 2026*
These are the authors' own test settings, at the paper's densities (about 0.24 and 0.09
cells/µm²). We scale up only after validating. Source: authors' code.

**A4. Prey as a biomass field on a grid.** *9 Oct 2026* — **Replaced by B5** (E. coli as real rods).

**A5. Rippling axis: decide once prey exists.** *9 Oct 2026* — **Replaced by B13.**

**A6. No M. xanthus growth until the core is validated.** *9 Oct 2026* — **Replaced by B23–B28** (energy rules).
The paper keeps cell number fixed.

**A7. Model details that are easy to get wrong.** *9 Oct 2026*
- **Threshold:** f_T = 0.08 applies to the smoothed signal s (the 20-s weighted mean of f,
  divided by 2), not to raw f.
- **β = 2 is a decay rate per minute**, though the paper prints "2 min".
- **Traction:** the head is pulled at speed × 10; the springs share that out, so the cell
  moves at 4 µm/min.
- **Rippling cells** neither lay nor follow EPS. EPS is laid under the rear disc.

Source: authors' code; see `model-foundations.md`.

**A8. Small differences from the authors' code, all meant to give the same result.** *9 Oct 2026*
- **Repulsion** checks every disc within one diameter; theirs checks the 13 nearest.
- **The EPS grid** wraps directly at the edges; theirs copies the edges. Heading is rounded to
  0.25° for speed.
- **Time between reversals** is counted only from one real reversal to the next.

Source: `paper-reproduction/README.md`.

**A9. Run the comparison with the authors' code once. Skip the split-box test (Fig. 6).** *10 Oct 2026*
- **Code comparison:** checks our rebuild against theirs, including the turning caveat below.
- **Split-box:** skipped, because the predation sim tests the same thing naturally, wherever
  a rippling spot borders swarming ground.

Source: our choice.

**A12. Results differ by about 10% between runs from chance alone.** *10 Oct 2026*
- **The runs:** at the swarming quick-test size (370 cells, 65 µm, one 150-min run each),
  the mean time between reversals was 3.37 min (predation-sim), 3.76 min (reproduction) and
  3.57 min (authors' code).
- **Why it's chance:** A13 shows the first two engines are identical, so their gap is
  entirely random (different random sequences, and the swarm is chaotic).
- **Consequence:** differences of this size, including ours vs the authors' (A11), are within
  run-to-run noise. Several seeds are needed for firmer numbers.

Source: our runs.

**A13. predation-sim's Myxo engine is exactly equivalent to the reproduction.** *10 Oct 2026*
- **How tested:** both started from identical cells with the same random sequence, no slime
  fading and no pull toward prey.
- **Result:** disc positions, signals and slime match exactly for 2,000 ticks (10 min)
  with reversals on.
- **Kept as a regression test:** `predation-sim/tests/test_equivalence.py`.
- **The only divergence found:** slime fading set to "practically never" (1e12) still
  changes slime at rounding level, which tips ties in trail choice. It isn't a modelling
  difference.

Source: our tests.

### Step 1 result (9 October 2026)
One seed, 150 simulated minutes, with statistics from the last 50 minutes
(`paper-reproduction/results/`, `paper-reproduction/figures/validation.png`).

| Signature | This model | Paper's simulation | Paper's experiment |
|---|---|---|---|
| Rippling TBR | Bimodal, peaks ≈0.8 and ≈5.5 min, mean 5.42 min (n = 9,297) | Bimodal, mean 5.02 min | Bimodal, mean 3.21 min |
| Swarming TBR | Unimodal, mean 3.76 min (n = 4,875) | Unimodal, mean 3.27 min | Unimodal, mean 3.73 min |
| Reversals in top own-frustration quartile, rippling | 80% | ≈75% (read off Fig. 5d) | 50.5% |
| Same, swarming | 67% | ≈57% (read off Fig. 5h) | 43.6% |
| Swarming nematic order | 0.85 at 2.5 µm, ≈0.05 by 20 µm | ≈0.8 at 5 µm, ≈0 by ~35 µm | ≈0.55 at 5 µm, ≈0.05 by 25 µm |
| Frustration (smoothed, 0–2 scale) | Median 0.08 rippling vs 0.12 swarming | Suppl. only | Means 0.48 vs 0.68 (tracked, noisier) |

**Status:** the shape signatures are reproduced, and the same-settings comparison with the
authors' code matches closely (A11). Not yet done: more seeds and a larger box.

**Turning caveat, resolved 10 Oct 2026:** frustration is measured after the alignment turn,
so turning to line up counts as frustration. One realignment from 45° off-axis raises s to
about 0.07 on its own. Reading the authors' code confirms they do the same, so this is
faithful, not a bug.

**A10. Code check against the authors' repository (commit b31a499, read 10 Oct 2026).** *10 Oct 2026*
These all match ours:
- **Step order** (`main.py`): move, push, springs, then turn; the head is measured after the
  turn.
- **Turning:** the head disc is rotated about disc 1 (`alignment.py`).
- **Frustration:** same formula, with the target direction taken before the turn
  (`reversal_signal.py`).
- **Reversal chance:** (1 − e^(−rate))·dt (`reversals.py`).
- **Defaults** (`parameters.py`): F* = 3, f_T = 0.08, α_F = 75, α_R = 100, RP 5 min → 20 s,
  20 s memory with β = 2, `new_romr` off.
- **Paper runs** (`scripts/simu_2d`) change only cell number, box size and alignment type.

One small difference: their EPS fades with a 100 h lifetime, about 2.5% over a 150-min run,
so it's negligible. Source: authors' code.

**A11. Numerical comparison with the authors' code: our rebuild matches.** *10 Oct 2026*
Their model ran at our exact quick-test settings (seed 1, 150 min, statistics from the last
50 min). Files: `paper-reproduction/results/authors/` and
`paper-reproduction/figures/vs_authors/validation.png`.

| Signature | Ours | Authors' code |
|---|---|---|
| Rippling TBR mean / median | 5.42 / 4.73 min | 5.08 / 4.57 min |
| Rippling TBR peaks | 0.8 and 5.5 min | 0.8 and 5.2 min |
| Rippling top-quartile reversals | 80.0% | 78.7% |
| Swarming TBR mean / median | 3.76 / 3.14 min | 3.57 / 2.83 min |
| Swarming top-quartile reversals | 66.8% | 62.9% |
| Swarming alignment at 2.5 / 10 / 20 µm | 0.85 / 0.39 / 0.07 | 0.85 / 0.49 / 0.03 |
| Frustration median, rippling / swarming | 0.076 / 0.116 | 0.080 / 0.127 |

- **Match:** the whole time-between-reversals distributions differ by at most 3% (rippling)
  and 5% (swarming) at any point (KS distance). They're statistically distinguishable only
  because there are about 10,000 reversals each.
- **Small consistent difference:** ours has slightly fewer very short reversal intervals and
  about 5–8% lower frustration. A likely cause is the repulsion neighbour search (all discs
  within one diameter vs their 13 nearest; A8). It's too small to matter for the predation
  project.
- **Long-range alignment:** their swarming alignment beyond 20 µm turns negative. That's one
  run's stream geometry in a small box, not a model difference.
- **Caveat:** one seed each. Seed-to-seed spread isn't measured yet, so differences of this
  size may be partly chance.

Source: our runs of both codes.

### Cell biology reference (M. xanthus)
- **Cell:** Gram-negative rod, no flagella, flexible.
- **Size:** about 5–7 µm × 0.5 µm. The paper uses 5 µm and measured 0.7 µm width.
- **Motility:**
  - S-motility: type IV pili at the leading pole, which bind EPS.
  - A-motility: Agl–Glt focal adhesions along the body, driven by the proton motive force.
  - Both relocate to the other pole when the cell reverses.
- **Polarity:** MglA-GTP at the leading pole, MglB at the lagging pole; RomR and Frz switch them.
- **Genome (DK1622):** one circular chromosome, 9,139,763 bp.
- **Speed:** 2–4 µm/min (paper: 4).
- **Doubling time:** 4–6 h; about 5.5 h on prey (Seef 2021).

---

## Part B: Predation project

The main goal is a video, seen from a microbiologist's point of view:
- E. coli seeds grow into colonies.
- Myxo swarms to a colony, kills and eats it.
- Myxo ripples on the digested spot.
- As the leftovers fade, Myxo swarms off to the next colony.

Decided in discussion, 9–10 October 2026.

### World and app

**B1. App: pygame, with a Live mode and a Record mode.** *9 Oct 2026*
- **Live:** a small world you can watch and adjust with sliders.
- **Record:** a bigger world that runs in the background and saves a video.

Cell movement is costly (about 30 steps/s for 1,000 cells), so a big world can't run live.
Source: our choice.

**B2. Record world: 500 × 500 µm. Live world: small (about 150 µm).** *9 Oct 2026*
- **Size:** fits about 3–5 colonies, and a video takes roughly 1–3 h to compute.
- **Why not bigger:** cost grows with the number of cells, not the area, and at 1 mm a Myxo
  cell would only be about 5 pixels long.

Source: our choice.

**B3. Edges wrap around (a cell leaving one side comes back on the other).** *9 Oct 2026*
Avoids cells piling up against walls; the paper does the same. Source: Saulnier 2026.

**B4. Time scaling: slow biology is sped up by one shared factor (a slider, starting at 10×). Movement stays at real speed.** *9 Oct 2026*
- **Scaled:** growth, division, digestion and fading.
- **Not scaled:** swarming and rippling, which only work at real speeds (4 µm/min, 0.3-s
  steps).
- **Why:** at real speed, 48 h of predation would take days to compute. One shared factor
  keeps biology's ratios. Fast events such as killing (minutes) run in real time.

Source: our assumption.

### E. coli

**B5. E. coli are individual rigid rods at real size: born about 2 µm long and 1 µm wide, dividing at about 4 µm.** *9 Oct 2026*
- **Behaviour:** they grow, divide and push neighbours aside. They don't glide, so they need
  no spring chain.
- **Why:** the user wants true form and size, and rigid rods keep it cheap.

Source: BioNumbers.

**B6 → replaced by B33** (wording and regrowth rule). Original: **E. coli food: a food layer in the agar that slowly refills. Growth speed follows local food, stopping at zero (the Monod curve).** *9 Oct 2026*
Unlimited food would make colonies grow without end. With limited food, colony centres
stall while edges keep spreading, as on a real plate. Note: the paper's assay uses starvation
agar, so this rule is ours. Source: Monod growth (standard microbiology); our assumption for
the numbers.

**B33. Ground nutrients regrow evenly everywhere, fast when low and levelling off at a maximum (like grass in a predator–prey model). The simulation runs endlessly.** *10 Oct 2026*
E. coli growth follows local nutrients (the Monod curve). This replaces the "agar" wording;
nothing is meant to run out for good. Patchy "nutrient rain" (closer to soil) was considered
and kept as a possible later option. Source: our assumption (logistic regrowth); Monod growth.

**B34. Starving E. coli follow real phases: no food → stop growing (dormant) → after a while (scaled), most die off gradually → a few survive long.** *10 Oct 2026* — **Death rate measured since B80** (0.69 per bio-day, Schink et al.).
- **Burst on death:** a starved E. coli that dies bursts like a killed one, leaving spreading
  food and a cell-wall ghost (prey matrix).
- **Consequence:** Myxo may ripple even on a colony that starved by itself.

Source: Finkel 2006 (stationary, death and long-term stationary phases; 90–99% die).

**B7 → replaced by B44** (no new seeding). Original: **New colonies: keep N colonies alive (an app slider with set choices, e.g. 1, 2, 4, 8).** *9 Oct 2026*
When a colony is eaten, a new seed lands somewhere with food and away from Myxo. This gives
a steady prey supply without flooding the screen. Source: our choice.

### Myxo seeds and movement

**B8. Myxo seeds: 10 seeds, 3 groups of 20 cells and 7 single cells.** *9 Oct 2026*
Groups can swarm together and lay trails; single cells show lone scouting. Source: the user's
choice.

**B9. Myxo body and movement rules: unchanged from Part A.** *9 Oct 2026*
Swarming and rippling are already validated there. Source: Saulnier 2026; `paper-reproduction/`.

**B10. Weak pull toward prey (predataxis), with a strength slider. At 0 it's the pure paper model.** *9 Oct 2026*
Directed movement toward prey has been seen experimentally. Without a pull, seeds may starve
before finding small, distant colonies. Source: Berleman 2008.

**B32. The pull toward prey (B10) senses only material released by burst or dying prey (lipids, food), and works by changing reversals.** *10 Oct 2026*
- **Mechanism:** a cell heading up the gradient reverses less often, and one heading down
  reverses more. That's how gliding Myxo follows a chemical, and it plugs straight into the
  existing reversal rule.
- **No pull from living colonies:** E. coli makes no AHL signals, and long-range attraction to
  intact prey is unproven.

Source: Kearns & Shimkets 1998; Lloyd & Whitworth 2017.

**B31. Slime (EPS) trails fade slowly (over hours, scaled).** *10 Oct 2026*
In the paper, trails effectively never fade. That's fine for short runs, but over a long video
the ground would end up covered in slime and trail-following would stop meaning anything.
Source: our assumption (differs from Saulnier 2026).

### Rippling

**B11. Ripple trigger: prey matrix on the ground, and nothing else.** *9 Oct 2026* — **Extended in B76:** contact with living prey triggers rippling too.
- **What triggers:** cell-wall material from dead prey makes cells line up and ripple; on
  bare ground they swarm.
- **What doesn't:** frustration only sets the timing of reversals, in both patterns.
  Starvation plays no part.
- **Consequence:** ripples can start inside a colony that's still being eaten, matching
  "rippling is a predatory behaviour".

Source: Shimkets & Kaiser 1982; Saulnier 2026; Berleman 2006.

**B12. The prey matrix fades slowly, so rippling spots shrink and cells drift back to swarming.** *9 Oct 2026*
This is what sends Myxo hunting again. Neither the paper nor the biology gives a rule for
leaving a rippling spot (in nature, fruiting bodies follow instead). Source: our assumption.

**B13. Each eaten colony gets its own random ripple direction.** *9 Oct 2026*
The paper imposes one horizontal axis and says nobody knows what sets it in nature. A random
direction per colony is the honest choice. Source: our assumption.

### Predation

**B14. Killing happens on contact, using measured numbers.** *9 Oct 2026*
- **Pause rate:** about 30% of touches make the Myxo stop and assemble its killing machine.
- **Kill rate:** more than 80% of pauses end with the prey bursting, within about 2 min, so
  about 26% of touches kill.
- **After the kill:** the Myxo then moves on.

Source: Seef 2021 (Figs. 2–4).

**B15. Touch rule: while touching prey, a Myxo has a chance per minute to start a pause, tuned so about 30% of typical touches pause.** *9 Oct 2026*
Simpler than tracking each touch separately, and it reuses the contact check we already do.
Source: our simplification of Seef 2021.

**B16. During a killing pause, the cell's reversal clock and frustration memory are frozen.** *9 Oct 2026*
Otherwise standing still to kill would read as a total jam and trigger a reversal right after.
Biology doesn't tell us what happens here. Source: our assumption.

**B17. A killed prey releases its contents as food that spreads over the ground grid. Its empty cell wall (the "ghost") becomes prey matrix.** *9 Oct 2026*
- **Food:** spreads like a stain, using a cellular-automaton averaging step. Myxo absorbs
  from the square it stands on.
- **Why:** contents are digested outside the cell by secreted enzymes and shared with nearby
  cells (wolf-pack feeding). Ghosts and debris stay behind.

Source: Seef 2021; Berleman & Kirby 2009.

**B18. Kill and digestion speeds are tuned, not measured. Target: a colony eaten over a sensible scaled time (about 48 h of biology).** *9 Oct 2026*
Source: Saulnier 2026, Fig. 1a; our tuning.

**B19. Watch-out: prey growth is sped up, but killing is not.** *9 Oct 2026*
Colonies could outgrow the hunters. The agar food limit (B6) caps colony size; tune this if it
happens. Source: our note.

### Energy (Myxo)

**B20. Each Myxo has a food store on a 0–100 scale, plus a reserve from 100 to 110. Cells start at 60.** *9 Oct 2026* — **Scale replaced by B75** (100 = a normal newborn; the store doubles to 200 before division). Cells still start at 60.
A simple stand-in for the cell's material and reserves. The numbers are ours; the rules below
follow biology. Source: our assumption.

**B21. One eaten E. coli gives 15 units: about 50 units of content, of which Myxo keeps 30%.** *9 Oct 2026* — **Replaced by B75:** an E. coli holds 100 units (about one Myxo cell's worth), and Myxo keep 50%.
- **Efficiency:** bacterial growth efficiency is measured at under 5% to about 60%, near 50%
  where food is rich. We use 30%.
- **Why not the 10% rule:** that's an ecosystem-level average across whole food-chain levels,
  not one bacterium eating another.

Source: del Giorgio & Cole 1998; Lindeman 1942.

**B22. The reserve (100–110) fills at a third of the normal rate (5 units per E. coli) and is used first when food runs out.** *9 Oct 2026* — **Range moved by B75** to 200–210; still a third of the normal rate.
- **Biology:** surplus food is turned into storage granules (glycogen or PHB; lipid bodies in
  Myxo). That costs extra, and stores are spent first when food runs out.
- **The cap:** no measured maximum exists, so the 110 cap is ours.

Source: Hoiczyk 2009; storage-polymer reviews.

**B23. Upkeep: the store runs down over time, and the cell dies at 0. The speed is a preset: very fast, fast, medium or slow (a full store lasts about 3, 6, 12 or 24 h of biology).** *9 Oct 2026*
Moving costs energy (proton motive force and ATP). Rippling and swarming cost the same,
since cells move at the same speed. The death numbers in the literature are disputed. Source:
our assumption; Wireman & Dworkin 1977 vs O'Connor & Zusman 1988.

**B24. Division: a cell needs 90 or more. It pays 50 and splits the rest equally, so each daughter gets 20 or more. The chance of dividing rises with energy above 90, and is 0 below.** *9 Oct 2026* — **Replaced by B75:** division from 190, the store split in half, so daughters start at ~100.
- **Grow, then split equally:** bacteria build first, then split at mid-cell (PomXYZ in
  Myxo).
- **The "adder":** cells add a roughly fixed amount between births. The 50 is that fixed
  amount.
- **Floor:** the floor of 20 keeps daughters from starting near death.

Source: Taheri-Araghi 2015; Schumacher 2017.

**B25. No division while starving.** *9 Oct 2026*
Starvation triggers the stringent response ((p)ppGpp), which stops growth and starts
development. Source: Singer & Kaiser 1995.

**B26. Hungry cells absorb food faster, so on a shared puddle the hungry neighbours get most of it.** *10 Oct 2026*
Gets the user's "feed the neighbours first" idea with one rule per cell and no neighbour
checks. Nutrient-limited bacteria raise their high-affinity uptake. Source: Ferenci and
colleagues (verified 10 Oct 2026). It's an analogy: shown in E. coli taking up sugar, not
measured in Myxo.

**B27. A dead Myxo's remaining food becomes a small spreading puddle for others.** *10 Oct 2026*
The idea that dying cells feed survivors is an old, unproven hypothesis, but it's cheap to add
and sensible. Source: our assumption (developmental-lysis hypothesis).

**B28. Food sharing between touching cells (via outer membrane exchange): not included.** *10 Oct 2026*
Myxo cells do swap outer-membrane material with relatives, but that's membrane, not food, so
using it for energy would be a stretch. Source: Ducret 2013; Wall lab reviews.

### Working rules

**B29. Code style.** *9 Oct 2026*
- Many small Python files, each with one tiny job, and one engine that runs them.
- A plain-language `"""docstring"""` on every function.
- Short functions, split into sub-functions.
- Fast numpy arrays, with no per-cell Python loops.

Source: the user.

**B30. Every outside fact goes into `sources.md` with a link and a 1–2 sentence note. Every decision goes here.** *9 Oct 2026*
Source: the user.

### Set while writing the build manual (10 Oct 2026; confirmed by the user the same day; all still adjustable)

**B35. Grids: slime on a 0.3 µm grid (the paper's), everything else on a 1 µm grid.** *10 Oct 2026*
The fine grid is needed for trail sensing. The coarser grid keeps nutrients, food, attractant
and matrix fast to update. Source: our assumption.

**B36 → replaced by B51.** Original: **Slow biology updates every 20 steps (0.1 real min), not every step.** *10 Oct 2026*
Growth and fading change too little in 0.3 s to be worth computing each step. Source: our
assumption.

**B37. Spreading (diffusion) is computed with an exact wrap-around method (FFT).** *10 Oct 2026*
The simple method becomes unstable at our step sizes once the speed-up is applied; the FFT
method is stable at any step size. Source: standard numerical method.

**B38. Overlapping rippling areas blend their axes.** *10 Oct 2026*
- **How:** matrix is stored together with its colony's axis, using doubled angles.
- **Why:** where two eaten colonies merge, the local direction blends smoothly instead of
  jumping. This settles the "merged colonies" question.

Source: our assumption (standard nematic averaging).

**B39. A dead Myxo releases its body (50 units) as food, but leaves no prey matrix.** *10 Oct 2026* — **Body now 100 units (B75). Replaced by B84:** a dead Myxo leaves only what's left of its store.
- **Refines B27:** death happens at energy 0, so it's the body itself that feeds others.
- **No matrix:** stops Myxo deaths from triggering rippling on their own.

Source: our assumption.

**B40. New colonies start from a single E. coli. About 5% of E. coli are long-term survivors that never starve to death.** *10 Oct 2026*
Source: our assumption; Finkel 2006 (90–99% die).

**B41. Provisional colours: E. coli magenta, Myxo green, as in the paper's Fig. 1a (mCherry/GFP). Myxo brightness shows energy.** *10 Oct 2026*
The final look is still open. Source: Saulnier 2026, Fig. 1a.

**B42. The build follows `docs/build-manual.md`: eight milestones, each checked and shown to the user before the next.** *10 Oct 2026*
Source: the user's request for a manual any coding agent can follow.

### From the user's review of the build manual (10 Oct 2026)

**B43. Ripple check uses the matrix averaged over about 3 µm around the head, not a single square. The threshold stays 0.3 (about one dead cell's wall per square, [tuned]).** *10 Oct 2026*
- **Why:** a real cell's pole feels more than one point. Averaging also gives smooth,
  non-flickering edges to rippling areas.
- **Refines B11:** the trigger is still local; only how it's measured changes.

Source: our assumption.

**B44. No new seeding. E. coli colonies come only from the starting seeds and regrow only from survivors. Replaces B7.** *10 Oct 2026* — **Replaced by B75:** a new E. coli founder every 6 bio-h.
- **Choice:** chosen by the user as the most natural option. The app's colony setting
  becomes "starting colonies".
- **Risk, stated plainly:** if Myxo wipes out every E. coli, prey is gone for good, and the
  Myxo will eventually starve. The 5% starvation survivors (B40) don't protect against
  predation. Revisit if runs end too early; for example, a rare random seed could be added
  later.

Source: the user's choice.

**B45. A starved E. coli goes dormant, then dies, then bursts about 30 bio-min later (a short delay, [tuned]). The food it releases shrinks the longer it starved: from 100% at the start of dormancy to 25% at death.** *10 Oct 2026* — **Delay replaced by B80:** 120 bio-min, measured (Schink et al.).
- **Biology:** time-lapse of starving E. coli shows a long alive-but-dormant phase, in which
  the cell shrinks inside its wall and burns its own contents. Its membrane voltage then
  collapses (death), and swelling and lysis follow soon after.
- **Lysis is regulated:** it's an active process (σE) that feeds survivors (cryptic growth).
- **Content numbers:** the 25% floor and the linear decline are our assumptions.
- **Dead intact cells:** they still take up space and can be pushed, but they don't grow and
  Myxo doesn't target them for killing.
- **Refines B34.**

Source: Schink et al. (Basan lab); Nitta et al. 2000.

**B46. The matrix amount only switches rippling on or off. Alignment strength stays fixed at the paper's γ′ = 11 above the threshold.** *10 Oct 2026*
- **The matrix amount also:** weights a spot's say in the ripple direction (B38) and is drawn
  on screen.
- **Alternatives considered:** strength rising with the amount; a soft edge below the
  threshold.

Source: Saulnier 2026 (fixed γ′); the user's choice.

**B47. Myxo seeds start at least 30 µm from any E. coli colony.** *10 Oct 2026*
Every seed has to search first, so the video shows swarming before feeding. Placement is
otherwise random. Source: the user's choice.

**B48. Ground nutrients start in random patches: smooth rich and poor areas, not uniform.** *10 Oct 2026*
More natural, like soil. Colony growth then depends on where seeds land.
- **Patches last:** each spot has a fixed "richness" between 0.3 and 1.0, and nutrients
  regrow toward that spot's own richness. Rich ground stays rich.
- **Patch size:** about 30 µm across ([tuned]).
- **Replaces part of B33:** nutrients no longer regrow toward 1 everywhere.

Source: the user's choice; our assumption for the numbers.

**B49. Killing as one "pause → burst" step stays (B14), now with two systems behind it.** *10 Oct 2026*
- **Biology:** a Tad-like system triggers prey death, then a type-3-like system lyses the
  prey.
- **Model:** we don't simulate them separately; the measured pause and kill numbers already
  cover both.

Source: Thiery 2022; Seef 2021.

**B50. Both E. coli and Myxo are seeded once, at the start only. No reseeding of either during a run, for now.** *10 Oct 2026* — **E. coli part replaced by B75** (new founders); **Myxo part replaced by B78** (they come in over the first 10 bio-h).
Confirms B44 for E. coli and states the same for Myxo. Populations change only through
growth, division and death. Revisit after the first long runs show what happens (for example,
whether prey or predators die out). Source: the user's choice.

**B51. Split timing: cell biology every tick, ground grids every N ticks (N is a setting, default 20, can be 1). Replaces B36.** *10 Oct 2026*
- **Cell biology:** E. coli growth, division, dormancy and death, plus Myxo upkeep, uptake,
  division and death. It's cheap per-cell work, so it runs every 0.3 s and cells grow
  smoothly.
- **Ground grids:** nutrient regrowth and spreading, food and attractant spreading, fading,
  and matrix smoothing. These process whole maps (500 × 500 squares in the record world), so
  they run every N ticks.
- **Deposits** onto the grids still happen every tick.
- **Why N = 20 is fine:** per tick a rod grows only about 0.17% at a 10× speed-up, so
  batching the grids is invisible.
- **Measured cost (10 Oct 2026, milestone 1):** a full grid update on the 500 µm world takes
  about 45 ms (one spreading about 11 ms, the smoothing about 9 ms, fades about 2 ms). Every
  tick, that would roughly double the run time; every 20 ticks it adds about 2 ms per tick.
- **Comparing:** N can be dropped to 1 in the app.

Source: discussion with the user (a side-chat explanation brought into the main session);
our estimate.

**B52. E. coli contact points sit at ±(length − width)/2 along the rod, not ±length/2.** *10 Oct 2026*
- **Why:** each contact point is the centre of a disc as wide as the rod. With the ends at
  ±length/2, a 2 µm cell would act 3 µm long. With this fix it spans exactly its true
  length, as B5 intends.
- **Manual:** corrected during milestone 1.

Source: geometry.

**B53 (speed part replaced by B55). E. coli cells differ from each other: division length 4 µm ± 10% (SD 0.4 µm) and each cell's own growth speed ± 10% (0.7–1.3), both drawn at birth.** *10 Oct 2026*
- **Why:** with identical cells, the whole colony divided in lock-step (a staircase growth
  curve, a pulsing colony). Real E. coli lose synchrony within a few generations because
  size at division and generation time vary.
- **Numbers:** 10% is a typical single-cell value. It's our assumption, not a measured
  figure from our sources.

Source: the user's choice; first colony run (milestone 2).

**B54. Nutrients spread slowly (10 µm²/bio-min), and E. coli uses 3 nutrient units per µm of growth.** *10 Oct 2026* — **Numbers replaced by B78** (local ground: 0.1 µm²/bio-min, 0.5 units per µm); the colony-size target stays.
- **Target (chosen by the user):** in the live world a colony grows freely, reaches about 700
  cells (~50 µm) by about 500 bio-min, then keeps creeping outward slowly at its edge while
  its centre starves and goes dormant. That's how real colonies on agar behave.
- **Alternative rejected:** fast spreading (100 µm²/bio-min, 5 units/µm) stopped colonies
  sharply but emptied the whole world evenly, so the rich and poor patches stopped
  mattering. That's more like a shaken flask.
- **Replaces** the first guesses (0.1 units/µm, 100 µm²/bio-min), with which colonies never
  ran short and filled the world.
- **Monod curve:** scaled so the richest ground (1.0) gives exactly the 20-min doubling (half
  speed at nutrient ≈ 0.14).
- **Note:** without Myxo, colonies never fully stop growing.
- **Honest scale note:** the ~700-cell, ~50 µm size is not biological. It's chosen to fit our
  150 µm world and the computer's limits. Real E. coli colonies on agar reach millimetres
  across and hundreds of millions of cells overnight, as multilayer domes.
  - **What's realistic:** the pattern, with nutrient-limited growth concentrated in a rim at
    the edge while the centre goes stationary.
  - **What's not:** the slow nutrient spreading (10 µm²/bio-min) is an artificial
    shrink-to-fit. Real small molecules such as glucose spread thousands of times faster;
    real colonies become nutrient-limited because they're so large and dense.

Source: tuning runs, 10 Oct 2026; general colony biology.

**B55. E. coli growth speed now varies ±20% (SD 0.2, kept within 0.4–1.6) and is redrawn at every birth. Division length stays ±10%. Replaces the speed part of B53.** *10 Oct 2026*
- **Biology:**
  - In mother-machine tracking, a cell's growth speed fluctuates every cycle and isn't
    inherited (cells "forget" their mother's speed), so redrawing at birth matches that.
  - Growth-speed differences drive much of the spread in generation time and size.
  - One review gives a generation-time spread of about 29% (original source not traced).
- **Why the change:** with ±10% for both, our cells probably varied too little (about 15%).

Source: Wang 2010; Wallden 2016; Grilli 2018; the user's choice.

**B56. Starting colonies are random but far apart: at least 75 µm in the live world and 150 µm in the record world.** *10 Oct 2026*
- **Why:** with 40 µm, two ~50 µm colonies could nearly touch (as in the first picture),
  leaving little bare ground for Myxo to swarm across.
- **Geometric limit:** in the 150 µm wrap-around world, two seeds can be at most about
  106 µm apart.

Source: the user's choice.

**B57. No safety brake on E. coli growth.** *10 Oct 2026*
If Myxo fail (for example, all seeds starve), E. coli slowly spread over the whole world and
the simulation slows down as cell numbers climb. This is accepted, because real runs have
Myxo controlling the prey. Alternatives considered: a clearly labelled computing limit, much
slower regrowth, crowding-stops-growth. Revisit if it becomes a problem. Source: the user's
choice.

**B58. Known flaw in the single speed-up (B4): sped-up prey outgrows real-time killing. Kept for now (10×); re-check at milestone 6.** *10 Oct 2026*
- **The flaw:** B4 assumed all biology is slow (hours) compared with movement (minutes).
  That holds for Myxo (5.5 h doubling → 33 min at 10×), but not for E. coli: its 20-min
  doubling becomes 2 min, as fast as one killing pause.
- **Measured (milestone 4 check, live world, 80 Myxo at the colony edge):**
  - A young colony grew 396 → 1,227 in 30 min.
  - A mature colony (700 bio-min) grew 1,794 → 2,796 in 40 min, while the Myxo killed 148.
- **Real assays differ:** the prey isn't growing at all (starvation agar; Saulnier 2026;
  Seef 2021).
- **The user's choice:** keep 10× and see whether fed, multiplying Myxo (milestone 6) turn
  the balance.
- **Fallbacks if they don't:**
  - a separate, slower speed-up for E. coli (e.g. 2×);
  - no speed-up for E. coli;
  - mature colonies that stop growing.

Source: our runs; Saulnier 2026; Seef 2021.

**B59. Myxo currently touch a colony and then wander off along their trails. No new "stay" rule for now.** *10 Oct 2026*
- **Why they leave:** nothing yet makes prey worth staying for. There's no hunger, and the
  pull toward prey only comes from spilled contents.
- **Re-check at milestone 6:** feeding plus the existing pull toward spilled food (B32)
  should keep them near kills.
- **Alternatives kept in reserve:**
  - prey contact suppressing escape (a Frz-based "stay" rule; one review describes rapid
    reversals on prey contact);
  - a stronger pull toward spilled food.

Source: the user's choice.

**B60. Several Myxo may pause on the same prey; whoever finishes first kills it, and the others' pauses are wasted.** *10 Oct 2026*
- **Measured:** about 25% of new pauses at a colony rim target prey already under attack.
  Of 119 finished pauses, 71 killed, 23 failed by chance (the 20% from Seef 2021) and 25
  found their target already gone.
- **Why kept:** plausible, since each Myxo builds its own killing machine at its own
  contact.

Source: the user's choice; our runs.

**B61. Touches last longer in the model than B15 assumed, and the per-touch numbers aren't directly comparable with Seef 2021.** *10 Oct 2026*
- **Measured at a colony rim:**
  - Touches last a median of 54–67 s (mean 87–108 s), against the assumed 30 s.
  - About 19–20% of touches lead to a pause, and kills per touch are about 11–12% (Seef:
    about 30% and 26%).
- **Why not comparable:** at a crowded rim, one Myxo touches several prey at once but can
  only pause on one. Seef measured single encounters.
- **Not retuned yet.** A proper recalibration would measure isolated single-cell encounters
  in the model.

Source: our runs (`checks/check_predation.py`).

**B62 (under test). Two rules to keep Myxo at their prey, as settings that are off by default.** *10 Oct 2026* — **Rule 1 (contact reversals) off again since B76; rule 2 (pushing) unused since Myxo crawl over prey (B76).**
- **Why:** the first full-world run (milestone 6) confirmed B58 and B59. Myxo fed once,
  divided (67 → 95), then mostly drifted off along trails and starved (9 left by 8 bio-h),
  while the colonies reached about 2,800 cells.
- **Rule 1, `prey_contact_signal`:** while touching living prey, a cell's Frz signal is
  raised to at least this level. Above f_T, the lock-out shrinks toward 20 s and reversals
  become rapid, so the cell jiggles on the spot instead of leaving. This uses the paper's own
  reversal machinery and fits "rapid reversals on prey contact" (Berleman 2008; Frz review).
- **Rule 2, `ecoli_push_share`:** the share of a Myxo–E. coli shove taken by the E. coli.
  Above 0.5, Myxo push into colonies (A-motility needed to invade prey colonies; Seef 2021).
- **Being tested together with the user's balance idea** (E. coli uses food less
  efficiently; the ground replenishes slowly):
  - A: 6 nutrient/µm, regrowth 5× slower.
  - B: A plus both rules (contact signal 0.15, push share 0.8).
  - C: 9 nutrient/µm, regrowth 10× slower, plus both rules.

Source: the user's ideas; Seef 2021; Berleman 2008.

**Results of A–C (10 Oct 2026, live world, 90 real min = 15 bio-h, seed 1):**

| Run | E. coli at 15 h | Myxo peak → at 15 h |
|---|---|---|
| Original settings | ~2,800 | 95 → 9 |
| A: feeding change | ~870 | 88 → 15 |
| B: A + staying rules | ~870 | 94 → 8 |
| C: stronger feeding change + staying rules | ~500 | 92 → 10 |

- **What worked:** the feeding change makes colonies 3–6× smaller and stall.
- **What didn't:** Myxo starve on the same schedule (crashing at 6–8 h). The staying rules
  can't help, because contact is rare.
- **Diagnosis:** a search problem. Myxo follow their own slime into a closed network of loops
  that runs past the colonies. Nothing guides them to living prey (B32 allowed only burst
  prey to give off a smell).

**B63 (under test). Search and survival, tested together on top of A and both staying rules.** *10 Oct 2026*
- **Colony smell, `ecoli_attractant_rate` (rate 2 in the test):** living E. coli leak a faint
  attractant that spreads and fades like the attractant from burst prey. Myxo reverse less when
  heading toward it (the B32 mechanism).
  - **Basis:** Gram-negative bacteria release outer-membrane vesicles (Kulp & Kuehn 2010), the
    E. coli outer membrane is PE-enriched, and Myxo moves up PE gradients (Kearns & Shimkets
    1998).
  - **Caveat:** that Myxo find prey this way is unproven, so this is plausible but our
    assumption. It revises B32's "no pull from living colonies".
- **Starvation survival:** the "slow" preset (a full store lasts 24 bio-h). Starving Myxo
  really survive days (development takes 1–3 days), so this is within real biology.
- **Trails fade faster, `eps_fade_time` 60 bio-min instead of 360:** this breaks the circling
  loops. It has no biological backing (trail decay hasn't been measured; the authors' code uses
  about 100 h), so it's a model convenience. One variant keeps 360 to see whether it's needed.
- **Variants:**
  - D: everything.
  - E: D with trails at 360.
  - F: D without ploughing (`ecoli_push_share` 0.5), answering the user's "why do Myxo push into
    E. coli rather than stick?".
- **On sticking:** the model has no adhesion, only shoving. "Sticking" exists only as the
  killing pause, which starts in about 30% of contacts per Seef 2021; other contacts glide
  past or in. Real Myxo both grip (pause) and invade (Seef 2021).

Source: the user's choices; the sources named above.

**Results of D–F (10 Oct 2026, same world and seed):**

| Run | E. coli at 15 h | Myxo peak → at 15 h |
|---|---|---|
| D: everything | ~820 | 101 → 34 |
| E: D with trails at 360 | ~810 | 99 → 36 |
| F: D without ploughing | ~750 | 105 → 34 |

- **Better:** with 24 h survival, about 3× more Myxo are alive at 15 h than in A–C, and one
  colony shows a bite eaten out of its edge.
- **Not solved:** there's still only one real feeding event (about 4 h). Myxo keep circling
  their own trails.
- **No effect:** faster trail fading (D vs E) and ploughing (D vs F) made no difference,
  because contact is rare.
- **Why the smell is weak:** it only changes reversals, while slime steers every tick. On a
  trail, the trail wins. The smell rate (2) also wasn't calibrated.
- **Stickiness (`prey_contact_signal`) didn't help:** B vs A gave 8 vs 15 Myxo. It only acts
  on contact, and contact was rare.

**B64 (under test). The user takes D as the base and enlarges the Myxo seeds to 5 groups of 30 plus 10 single cells (160 Myxo).** *10 Oct 2026*
D and E (trails at 360, better backed) are being run side by side with the bigger seeds, so the
trail-fading choice can be made with evidence. Source: the user's choice.
- **Result:** with 160 Myxo the trail network looks like the paper's swarming (thick streams),
  and a stream cut through one colony. D and E ended with 72 and 85 Myxo at 15 h (from about
  250), so trail fading made no difference.
- **The user chose 6 h (B31) for trails.** `eps_fade_time` stays 360.
- **Diagnosis:** Myxo kill but don't eat. About 7,200 food units, roughly 140 E. coli's worth,
  lay spread thinly on the ground while Myxo starved. The killer moves on at once, food thins
  out by spreading and decay, and passing cells absorb less than their upkeep.

**B65. Eating from kills: the killer eats first, and absorption has a ceiling anchored to real growth.** *10 Oct 2026* — **Ceiling re-anchored in B75** (5 units/bio-min on the new scale). **Killer share 25% since B76.**
- **Killer share, `killer_share` 0.5 [assumed]:** the killer absorbs half its victim's
  contents at the moment of lysis; the rest spills for neighbours. Lysis happens at the
  killer's contact site (Seef 2021); the 50% is ours.
- **Absorption ceiling, `uptake_max` 3 food units/bio-min [biology-anchored]:**
  - Cells absorb in proportion to the food under them, but never faster than this.
  - **Why 3:** working back through our energy rules (24 h upkeep preset, hunger factor,
    division cost 50), it lets a cell on plentiful food reach division in about 5.5 bio-h,
    the measured generation time of Myxo on prey (Seef 2021).
- **Not added:** a "stop where there's food" rule. No evidence was found: PE lowers reversals
  rather than stopping cells (Kearns & Shimkets 1998), and a 2011 study questioned nutrient
  chemotaxis as a driver of swarming (PMC3194913).
- **Food spreading** (5 µm²/bio-min) stays as it is, and it's tuned, not biological. Real
  dissolved small molecules spread thousands of times faster (~600 µm²/s). In nature food stays
  local because packed predators digest and absorb it at once, which is what B65 models.

Source: Seef 2021; our derivation; the user's choices.

**Result of E3 (B65 added, 160 Myxo):** almost no change, with 91 Myxo left at 15 h. Kills were
too rare for eating rules to matter: about 100–130 kills in 15 bio-h from 160–250 Myxo, while a
Myxo needs about 0.6 kills per bio-hour just for upkeep.

**B66. Predation runs on the biology clock: the pause rate is multiplied and the kill delay divided by the speed-up (`scale_predation`, on). Fixes the root cause of B58 and the starvation in E–E3.** *11 Oct 2026*
- **The root cause:** the single speed-up (B4) sped up the slow biology (growth, upkeep)
  but not killing, which depends on contact and ran at real speed. Wherever the two trade,
  the balance was off by the speed-up factor:
  - Prey outbred the hunters (E. coli doubling in 2 real min against ~3 min per kill; B58).
  - Hunters starved. A real Myxo eats about one prey per 1.5 h and spends about 3% of its time
    killing. At 10× it would have to kill about 40% of the time.
- **The principle:** a process can only be sped up honestly if everything it trades with is
  sped up equally.
- **The user's priority (asked 11 Oct 2026):** a realistic balance at the population level,
  keeping 10× for watchability.
- **What scaling gives:** kills per Myxo generation and per prey doubling match real biology.
  Seef's measured values stay in the settings as the base.
- **Honest costs:**
  - Single encounters look too fast on screen: nearly every touch leads to a kill (Seef
    measured about 30%), and a kill takes 12 s instead of 2 min.
  - Movement can't be sped up, so per biological hour a Myxo covers 10× less ground than a
    real one, and searching remains harder than in nature.
- **Alternatives considered:**
  - a lower speed-up (3×: honest in detail, about 3× more computing);
  - separate speed-ups for each process.

Source: our analysis; the user's choice; Seef 2021.

**Result of E4 (B66 on):** only a small gain. At 15 h there were ~630 E. coli (E3: ~750) and
103 Myxo (E3: 91), with roughly 150–200 kills. Single contacts now kill fast, but only 0–4 of
200+ Myxo are ever pausing. The bottleneck is meeting prey at all.
- **How movement works:** on a trail, slime steers a cell every tick, and reversals only send
  it back along the same trail. The colony smell acts through reversal timing (a biased random
  walk), so it can only choose which way along a trail a cell goes.
- **Why loops form:** the first random paths become self-reinforcing highways, and whether
  one passes a colony is luck.

**B67 (under test). Scouts: a share of Myxo explore off-trail with A-motility.** *11 Oct 2026* — **Who scouts and when: replaced by B70, then B71.** The off-trail movement stays.
- **Biology:** the paper's own introduction says A-motility lets individual cells detach from
  groups and explore the prey environment as scouts (ref. 7, Rombouts et al. 2023). Groups
  glide on slime trails with pili (S-motility).
- **Model:**
  - Scouts don't follow slime, but they still lay it, so their path to a prey can recruit
    groups.
  - They wander with small random turns: rotational diffusion `scout_turn_noise` 0.2 rad²/min,
    so a path stays roughly straight for about 20 µm [assumed].
  - Otherwise they follow the same rules as other cells: reversals, rippling on matrix,
    eating, dividing.
  - Daughters become scouts with the same probability, since scouting is a behaviour, not a
    strain.
- **Being tested:** `scout_fraction` 5% and 10% on top of E4.

- **Rombouts 2023 also reports** that cells switch often between lone foraging and swarms. Our
  scout flag is fixed for a cell's life; switching over time is a possible refinement.

Source: Saulnier 2026 introduction; Rombouts 2023 (doi:10.1038/s41467-023-41193-x); our
assumptions for the numbers.

**Results with scouts (11 Oct 2026, on top of E4):**

| | E4 | 5% scouts | 10% scouts |
|---|---|---|---|
| E. coli at 15 h | ~630, rising | ~400, flat from 10 h | ~400, flat from 12 h |
| Kills (from matrix) | ~150–200 | ~310 | ~290 |
| Myxo at 15 h | 103 | 121 | 123 |

- **In the pictures:** colonies are eaten into (one split in two, one with a U-shaped bite).
  Scout tracks lead into the colonies. In an eaten patch, Myxo line up in parallel on the prey
  matrix: rippling appeared on its own.
- **Myxo numbers fall toward about 90–120,** which matches the prey production the ground
  allows. With scarce, slowly regrowing nutrients, the ground makes about 25 E. coli per
  bio-hour, enough to feed about 90–120 Myxo. This now behaves like normal predator–prey
  ecology rather than a modelling flaw.

**B68. Locked in as the new defaults (the user's choice, 11 Oct 2026).** *11 Oct 2026*

| Setting | New default | Replaces |
|---|---|---|
| `nutrient_per_um` (**back to 3 in B75**) | 6 | 3 (B54) |
| `nutrient_regrow_rate` | 1/3000 per bio-min | 1/600 |
| `prey_contact_signal` (B62; **off again in B76**) | 0.15 | off |
| `ecoli_push_share` (B62) | 0.8 | 0.5 |
| `ecoli_attractant_rate` (B63) | 2 | off |
| `starvation_preset` | slow (24 h) | medium |
| Myxo seeds (B64; **5 × 50 + 10 in B74**) | 5 × 30 + 10 singles | 3 × 20 + 7 |
| `scout_fraction` (B67; **replaced by B71**) | 10% | off |
| `scale_predation` (B66) | on | — |
| `eps_fade_time` | 360 (B31) | unchanged |

- **Tests:** one test was adjusted to the slower colony growth.
- **Next:** a 30 bio-h "full story" run to see whether colonies get eaten up, ripple, and the
  Myxo move on.

Source: the user's choice; the runs above.

**B69. Known limitation, tuning paused: the "eat everything, ripple, move on" cycle doesn't complete yet.** *11 Oct 2026*
- **The full-story run (defaults of B68, live world, 30 bio-h, seed 1):**
  - **0–13 h works:** colonies grow, are attacked, one splits, and a rippling patch appears.
  - **After about 13 h:** no Myxo is ever in a killing pause again. The colonies sit as
    ~300–355 dormant cells (the whole ground is depleted), and the Myxo starve slowly from
    about 145 to 37.
- **Likely causes:**
  - The trail highways settle away from the dormant clumps.
  - Few scouts remain (10% of a shrinking population).
  - About 4,000 food units lie spread too thinly to cover upkeep (ground food meets about 40% of
    it).
- **The user's choice:** pause tuning and build on (rippling check, live app), so smell, scout
  and food settings can be tried interactively.
- **Candidate fixes when we return:**
  - a stronger smell (×5–×20);
  - smell steering cells near prey (our assumption);
  - richer ground.

Source: our run; the user's choice.

**B70. Four corrections after B69 (the user chose all four): starvation mode, food that stays, scouting as a switch, and a test at higher Myxo density.** *11 Oct 2026* — **Stringent trigger replaced by B83** (prey food ran out, not a low store).
- **Starvation mode:** below a store of 20 (`starvation_level`), running costs drop to 10%
  (`starvation_upkeep`), so the last 20 units last about 2 bio-days instead of about 5 h.
  Division was already impossible below 90. Biology: the stringent response shuts down
  growth, and starving Myxo survive for days. The direction is backed (Singer & Kaiser 1995);
  the 20 and the 10% are ours. Renamed "stringent mode" and extended in B71.
- **Spilled food no longer fades (`food_decay_time` = ∞):** with only two species nothing else
  eats it, so it stays (and keeps spreading) until a Myxo absorbs it. The prey smell still
  fades. Our assumption.
- **Scouting as a switch:** cells take turns scouting (spells of `scout_episode` 10 min) rather
  than a fixed 10% for life, as Rombouts 2023 reports. **Replaced the same day by B71's
  hunger trigger.**
- **Density test:** our Myxo were 10–50× below the paper's density. The user asked for two
  live-world runs: 3 groups of 300 (900 Myxo, about half the paper's swarming density) and
  their preferred 5 groups of 50 plus 10 single cells (260).

Source: Singer & Kaiser 1995; Rombouts 2023; our assumptions for the numbers; the user's
choices.

**B71. The user's explore-or-conserve design: scout mode and stringent mode, plus eating within 2 µm.** *11 Oct 2026* — **Food affinity of both modes and the stringent speed: replaced by B72. Scout speed 1.1× since B80** (measured). **Who scouts and when stringent mode starts: replaced by B83.**
Two separate states, set every tick from each cell's own store and surroundings
(`myxo_modes.py`).
- **Scout mode:**
  - **Trigger:** a hungry cell (store below 90) with no food within 2 µm may start scouting.
    The chance rises as its store falls, from 0 at 90 to `scout_start_rate` 0.1/min just above
    20. A spell lasts 10 min on average and ends at once if food turns up or the store falls
    into stringent mode. So at most about half of the hungriest cells scout at any moment, and
    cells take turns.
  - **Perks:** ignores other cells' slime (A-motility, small random turns); glides 20% faster
    (4.8 µm/min); lays slime that counts double for followers and fades half as fast; takes
    up food 50% more readily; never divides.
- **Stringent mode (store below 20):** no scouting, no division, running costs cut by 90%
  (B70), glides 10% slower (3.6 µm/min), takes up food 50% more readily. It keeps following
  slime with its group: starving Myxo don't march toward food, and their natural next step
  would be fruiting bodies (out of scope).
- **Eating within 2 µm (`absorb_radius`):** a cell takes food from every square within 2 µm of
  its head, not only the one under it, standing in for digestion by secreted enzymes. Reason:
  with time compressed, a cell sweeping a 1 µm path collected only about a fifth of its
  upkeep from thin food (B69).
- **Built in, not a new rule:** each cell judges its frustration against its own speed, so
  fast scouts and slow starving cells don't feel falsely jammed.
- **Tests:** 59 pass; both tick-for-tick equivalence tests are still exact with scouting off.

| Rule | Backing |
|---|---|
| Scouts ignore slime | **Backed:** A-motility lets single cells explore (Rombouts 2023; Saulnier 2026 introduction) |
| Scouting triggered by hunger with no food nearby, ending at food | **Plausible** (foraging theory), not shown in Myxo; cells do switch individually (Rombouts 2023) |
| Scouts faster, stronger slime, higher affinity | **Our assumptions** (no measurements found) |
| No division when starving | **Backed:** stringent response (Singer & Kaiser 1995) |
| Costs cut when starving | **Direction backed,** the 90% is ours |
| Starving cells 10% slower | **Plausible** (falling proton motive force), not measured |
| Starving cells keep following slime | **The natural behaviour** |
| Eating within 2 µm | **Plausible** (extracellular digestion, Berleman & Kirby 2009); the 2 µm is ours |

Source: the user's design; the sources in the table; our assumptions for the numbers.

**B72. The user's corrections to B71 (from a side discussion), plus B47 applied to every cell.** *11 Oct 2026* — **Stringent cells get the smell boost too since B80.**
- **Scouts follow the prey smell more strongly, and no longer absorb food better.** The user
  meant smell-following, not uptake. In the reversal rule (B32), the smell's strength is ×1.5
  for scouts (`scout_smell`). It's kept modest because the reversal multiplier is clipped to
  0.2–5. Backing: Myxo follow the lipid smell only when starving (Kearns 2001); no study singles
  out scouts. The number is ours.
- **Stringent cells take up scarce food 15% more readily** (`stringent_affinity` 1.15, the
  user's number; B71 had 1.5 for both modes).
  - **Backing:** hungry bacteria switch on high-affinity uptake (Ferenci, B26). It's an
    analogy from E. coli, and truly starving cells shut much of their metabolism down, so a
    modest boost fits.
  - **Where it acts:** only on thin food, since `uptake_max` caps rich puddles.
- **Stringent cells glide 25% slower** (`starvation_speed` 0.75, was 0.9). **Replaced by B75:** speed
  now depends on crowding; 0.75 applies to packed cells. The user's choice,
  to go with the 90% cost cut.
  - **Correction:** the B71 note ("plausible, not measured") was wrong. It has been measured,
    and the other way: free-moving starving cells get 1.5× faster over 15 h (Jelsbak &
    Søgaard-Andersen 2002). Only cells inside aggregates slow down (Sliusarenko 2007).
  - **Status:** our assumption, against the data for cells outside aggregates. The user was
    asked whether to keep it.
- **B47 now holds for every cell:** a seed's centre keeps 30 µm + the group's radius + one
  body length from every E. coli, so no disc starts within 30 µm. Before, only the centre was
  checked, so a 300-cell group's edge could start about 5 µm from prey.
- **Tests:** 61 pass; both equivalence tests are still exact.

Source: the user's choices; Kearns 2001; Ferenci (B26); Jelsbak & Søgaard-Andersen 2002;
Sliusarenko 2007.

**B73. Bug fixed: in every run since milestone 6, Myxo got a free meal right after the first kills.** *11 Oct 2026*
- **What happened:** spreading food with the FFT leaves rounding errors of about ±1e-17 in
  every square. Where a square's food and a cell's demand were both tiny negatives, the
  sharing step divided by a guard value of 1e-300. That handed out about 10²⁶⁵ food units and
  filled the cell to 110 for free. It fired at the first spreading step after the first kill.
- **Size:** in every predator–prey run (B62–B71), the mean store jumped by 20–32 units in one
  step. In the B71 5 × 50 + 10 run that was about 900 E. coli's worth of food from nothing, and
  it drove the rise from 260 to 455 Myxo.
- **What it changes in earlier results:**
  - **Artifacts:** the early "fed once, then divided" burst in every run since B62 (for
    example "67 → 95" in B62, "one real feeding event at about 4 h" in B63) was mostly this
    bug. Myxo numbers in B62–B71 are inflated.
  - **B62–B69 (no stringent mode):** the bug made the Myxo look better fed, not worse, so
    the direction of the findings (Myxo rarely meet prey, trail loops) probably stands.
  - **B71 (stringent mode on):** here the bug made the hunt look *worse*. The free meal set
    off a division wave, the daughters started at 20–30 and turned stringent at once, and
    scouting stopped. Without the bug the Myxo ate far more (see the result below).
  - **The B71 "stringent wave":** the mass divisions behind it came from the free meal. The
    rule clash itself is real: daughters start at 20–30 (B24), right at the stringent line.
- **Fix:** spreading never returns negative amounts (rounding errors below 0 become 0). The
  sharing step treats negative food or demand as 0, so its scale-down factor always lies
  between 0 and 1.
- **Cause:** a coding error in the first uptake code (milestone 6). B71's 2 µm reach made it
  fire more widely. An energy-balance test would have caught it; one now exists.
- **Tests:** two new ones: spreading stays at 0 or above, and eating next to rounding noise
  gains at most 30% of the food removed (the old code filled 98 of 200 test cells to 110).
  63 pass.

Source: our tests and runs.

**Results of the first clean runs (B72 rules + fix, live world, 30 bio-h, seed 1;
`checks/output/b73_5x50p10.png`, `b73_3x300.png`):**

| | B71 5 × 50 + 10 (with the bug) | Clean 5 × 50 + 10 | Clean 3 × 300 |
|---|---|---|---|
| E. coli peak → at 30 h | 853, still rising | ~408 at 10 h → ~280 at 16 h → 352 (all dormant) | 752, still rising |
| Kills (matrix peak) | ~157 | ~400 | ~215 |
| Myxo start → at 30 h | 260 → 455 | 260 → 297 | 900 → 918 |
| Stringent at 30 h | 428 of 455 | 270 of 297 | 907 of 918 |

- **More Myxo did worse:** the three 300-cell groups started far from the colonies (B47
  measured from every cell pushes big groups further out). They stayed as dense rafts at the
  world's edges, and only thin streams reached the prey.
- **Everyone turned stringent together:** all seeds start at a store of 60 and burn it at the
  same rate, so at about 9.6 bio-h all 900 cells crossed 20 within minutes, and scouting
  stopped.
- **The "eat" step works:** one colony was broken into small clumps, and the other was bitten
  and cut through by a Myxo stream.
- **Why the Myxo barely grew:** the prey in our world is small.
  - At its peak the world held about 408 E. coli, about 6,100 store units at 30%.
  - 260 Myxo at full running cost spend about 1,100 units per bio-hour, so the whole prey
    stock feeds them for only about 5–6 bio-hours.
  - This follows from the scaled-down colonies (B54 note). It's a prey-supply limit, not a
    search failure.
- **Stringent wave:** scouting stopped once most cells turned stringent at about 9.5 bio-h,
  when the starting store of 60 had run down to 20.

**B74. From the user's review of the clean runs: ghosts keep smelling, spilled food fades slowly, 5 × 50 + 10 seeds.** *11 Oct 2026*
- **Ghosts keep giving off the prey smell while they last** (`ghost_attractant_rate`, 2 units
  per bio-min per ghost, the same as a living E. coli).
  - **Why:** before, a kill gave one puff that faded within about a bio-hour, while its food
    stayed. So spilled food piled up unfound (about 15% of all food released by 11 h).
  - **Basis:** the attractant is the PE-rich envelope (Kearns & Shimkets 1998; E. coli outer
    membrane rich in PE), and a ghost is the leftover envelope. It fades with the matrix
    (half-life 12 bio-h). The lasting smell and its rate are our assumptions.
- **Spilled food fades again, with a 12 bio-h half-life** (`food_decay_time` 1,039 bio-min).
  That's the same as the ghosts, so an eaten spot smells of prey as long as its food lasts.
  Replaces B70's "never fades" (the user: food can go, but slowly). Our assumption.
- **Seeds: 5 groups of 50 plus 10 single cells (260 Myxo) by default** (group radius 10 µm,
  the same packing as before). The user's choice; it also beat 3 × 300 in the clean runs.
- **Confirmed:** B47's 30 µm is measured from every Myxo cell, i.e. from the group's edge
  (B72).
- **Not added:** extra food affinity for daughters. There's no evidence, and B26 already
  favours hungry cells.
- **Not changed:** the food a kill releases. The spill is the uneaten half of the prey, and
  about 85% of it was eaten in the clean run; the pile-up came from hunters not smelling it.
- **Tests:** 64 pass.

Source: the user's choices; Kearns & Shimkets 1998; the E. coli outer-membrane study in
`sources.md`; our assumptions for the numbers.

**B75. The user's choices: daughters are normal newborns (the store doubles before division), 50% efficiency, bigger colonies, a new E. coli founder every 6 bio-h, and starving cells' speed set by crowding.** *11 Oct 2026*
- **The store counts a cell's material; 100 = a normal newborn.** A fed cell builds up to 200
  (a second cell's worth), then splits into two daughters of about 100 each. Division is
  possible from 190, with the chance rising to the cap of 210. Nothing is created or lost.
  - **Why:** daughters started at 20–30, right on the stringent line, because one number did
    two jobs (growth toward division and reserves). Real cells double their contents first,
    and each daughter gets half of everything, so it's as well fed as its mother was. Cells add
    about one newborn's worth per cycle (the adder; Taheri-Araghi 2015).
  - **Not "daughters at 100 for free":** that would create 100–150 units at every division,
    the same kind of free energy as the B73 bug.
  - **Prey in the same units:** an average E. coli holds about one Myxo cell's worth (100), as
    the two are similar in size (E. coli about 1 × 3 µm; Myxo 0.7 × 5 µm in the model). A dead
    Myxo's body is also 100.
  - **Re-scaled with it:**
    - Upkeep is counted per newborn (a newborn's 100 lasts the preset time).
    - The reserve sits at 200–210.
    - The urge to scout is 0 at a newborn's 100 or above.
    - The uptake ceiling is re-anchored: 5 food units per bio-min gives a mean generation of
      5.4 bio-h on plentiful food (measured: 5.5 h, Seef 2021).
- **Myxo keep 50% of eaten food** (was 30%). Bacterial growth efficiency is near 50% where food
  is rich (del Giorgio & Cole 1998, B21), and prey contents are rich food. One E. coli gives 50
  store units (was 15), so about 2 kills build a new cell.
- **Bigger colonies:** E. coli use 3 nutrient units per µm of growth again (B54's value; B68
  doubled it while predation was broken), so colonies reach about 700 cells.
- **A new E. coli founder every 6 bio-h** (replaces B44's "no new seeds"; **landing rules dropped in B78**):
  - **Where:** a single cell lands where the ground holds at least 0.3 nutrient units, at
    least 75 µm from other E. coli and 30 µm from any Myxo.
  - **If no spot qualifies,** it tries again at each ground update.
  - The interval and the rules are our assumptions.
- **Starving cells' speed depends on crowding** (replaces B72's flat 0.75×). **Crowding part dropped
  in B84.** Each cell keeps a starvation clock.
  - **Alone:** a stringent cell speeds up to 1.5× over 15 bio-h of starvation (Jelsbak 2002).
  - **Packed among other Myxo** (as dense as rippling, 0.24 cells/µm², counted within one body
    length): it glides at 0.75×, since cells slow inside aggregates (Sliusarenko 2007). The 0.75
    is the user's number.
  - **In between:** a mix.
- **Tests:** 67 pass; both equivalence tests are still exact.
- **Quick check (30 real min):** no impossible energy jumps. A cell that fed early reached 198
  and split into two at about 100.

Source: the user's choices; Taheri-Araghi 2015; del Giorgio & Cole 1998; Seef 2021; Jelsbak &
Søgaard-Andersen 2002; Sliusarenko 2007; our assumptions for the numbers.

**B76. Myxo get inside colonies and ripple while they eat: contact reversals off, Myxo crawl over prey, living prey trigger rippling, and the killer keeps 25%.** *11 Oct 2026* — **Living-prey trigger kept in B79.**
- **Why (the user):** Myxo were eating colonies from the surface, and only a few were ever
  killing. Real Myxo penetrate the colony and the whole pack feeds.
- **Biology (checked 11 Oct 2026):**
  - **Invasion:** single A-motile cells penetrate "the tightly-knitted E. coli colony", killing
    prey as they advance, and groups follow. After each kill the cell "resumes movement".
    Without A-motility cells "remain stuck at the border" (Seef 2021, Figs. 1–2).
  - **Rippling:** it occurs when cells "make direct contact with either prey or large
    macromolecules", so living prey count too (Berleman 2006).
- **Contact reversals off** (`prey_contact_signal` 0; was 0.15). B62's rule made a cell reverse
  rapidly whenever it touched prey, so after each kill it bounced back out. It was our
  assumption.
- **Myxo crawl over prey** (`myxo_crawl_over_prey`). Myxo and E. coli no longer shove each
  other; touches still kill. This stands in for the 3D colony that real cells slip into and
  over. On screen, Myxo can lie on top of prey. Our assumption.
- **Living prey trigger rippling too** (`ripple_live_prey_weight` 1: a living E. coli counts
  like one ghost).
  - Inside a packed colony (about 0.33 cells/µm²) cells ripple along that colony's own
    direction (B13). At the edge, less than half the circle is prey, so cells still swarm in.
  - **Fixed along the way:** the ripple direction is now averaged over the same 3 µm circle as
    the trigger. Before, a cell sitting between ghosts read "no direction" and defaulted to
    horizontal.
- **The killer keeps 25% of each kill** (`killer_share`; was 50%), so 75% spills for the pack
  (wolf-pack feeding, Berleman & Kirby 2009). The user's number, first raised in a side chat
  whose notes were lost.
- **Test** (`checks/check_penetration.py`: one grown colony of 686 E. coli, 80 Myxo at its
  edge, 2.5 bio-h, seed 1):

  | | Kills | Killing at a time | Deep inside | Rippling |
  |---|---|---|---|---|
  | Before (B75 rules) | 406 | 7.5 | 6 | 17 |
  | Reversals off + crawl over | 565 | 10.8 | 8 | 30 |
  | + rippling on living prey (B76) | 527 | 9.9 | 15 | 32 |

  - With all of B76 the colony is hollowed out from the inside: a ring with Myxo feeding in
    the middle.
  - The kills differ by about 7% between the last two rows, which is within run-to-run noise
    (A12).
  - **Still seen:** many Myxo leave along the slime highways.
- **Tests:** 69 pass; both equivalence tests are still exact.

Source: the user's choices; Seef 2021; Berleman 2006; Berleman & Kirby 2009; our runs.

**B77. No extra rule to hold the pack at a colony, after testing; check again in the full run.** *11 Oct 2026*
- **The question (the user):** in B76's test many Myxo leave along slime highways. How do we
  stop that?
- **Fixes tried** (`checks/check_staying.py`: same colony and 80 Myxo, 2.5 bio-h; "with the
  pack" = ending within 10 µm of the colony):

  | Change | With the pack | Kills |
  |---|---|---|
  | None (B76) | 56% | 527 |
  | Prey smell 5× stronger | 62% | 547 |
  | Ripple threshold halved | 56% | 629 |
  | Trails fade within 1 bio-h | 61% | 580 |
  | Smell 5× + threshold halved | 57% | 612 |
  | Prey shorten the lock-out (Frz signal ≥ 0.10 on prey) | 52% | 455 |
  | The same at ≥ 0.15 | 49% | 502 |

  - None held the pack; all differences are within run-to-run chance (about 10%, A12).
  - **The lock-out idea:** it came from Zhang 2012 (prey stimulate reversals, and rippling keeps
    cells on prey longer). It made things worse: the cells inside spread out singly instead of
    hollowing the colony together. The option was removed from the code.
- **Why it doesn't matter as much as it looked:**
  - **Most leavers never fed:** 40 of 95 cells never touched prey (26 of them left). They
    started facing away from the colony and glided off in the first minutes, laying the
    highways seen in the pictures.
  - **Feeders mostly stay:** of the cells that touched prey, 71% stayed. 12 of the 16 that
    left had only brushed the edge at the very start, so about 9 in 10 cells that actually got
    in stayed with the pack.
- **The paper's lock-out as the limit:** a calm cell can't reverse for up to about 5 minutes
  after its last reversal (the refractory period), and it glides about 20 µm in that time,
  nearly a colony's radius. A stronger smell can't override it.
- **Decision:** no new rule. The full run will measure whether cells that reach a colony stay.
- **Source corrected:** our note on Berleman 2008 said "ripples shorten with more prey". The
  abstract only says the wavelength depends on prey, so the note was fixed.

Source: our tests; Zhang 2012; Berleman 2008.

**Result of the full run with B74–B76 (live world, 5 × 50 + 10, 30 bio-h, seed 1;
`checks/output/b76_full_30h.png`):** the best so far.
- **Myxo well fed and growing:** 260 → 384 (+48%). The mean store sat at 100–107 (a healthy
  newborn's level) from 13 h on; only 23–56 cells (about 10–15%) were stringent, against about
  90% in the B73 runs.
- **The pack stays with prey:** Myxo within 10 µm of living E. coli rose from 0 to about 90 by
  15 h, then held at 90–117, about a quarter of all Myxo. Kills reached about 717 or more by
  17.5 h (matrix peak).
- **Colonies eaten:** E. coli peaked at 1,105 (10 h; bigger colonies, B75), then fell to
  860–900. The upper colony was broken into fragments; the lower one was cut into bands by Myxo
  streams running through it.
- **No new colony ever appeared:** the founder rule (B75) can't be met in the live world.
  - By 12 h the whole ground was bare (mean nutrients 0.03 vs the 0.3 required).
  - A spot 75 µm from every E. coli and 30 µm from every Myxo barely exists in a 150 µm world
    with two big colonies and highways everywhere.
- **Rippling faded:** about 33 rippling cells at 15 h, about 2 by 30 h. The Myxo mostly stream
  along channels they cut through the colonies and eat the channel walls slowly.
- **Spilled food:** it peaked at about 16,900 units (about 170 E. coli's worth) at 12.5 h,
  with the killer now keeping only 25%, and fell to about 3,100 by 30 h (eaten or faded).
- **No impossible energy jumps.** The largest rise of the mean store between ground updates
  was 0.32.

**B78. Local ground and newcomers: nutrients barely spread, patches start at random levels, E. coli feed along their whole body, new founders land anywhere, and Myxo (5 × 20 + 10) come in from outside over the first 10 bio-h.** *11 Oct 2026*
- **Why (the user):**
  - Two colonies were never meant to drain the whole world.
  - Myxo should be newcomers, not natives.
  - The world was too crowded with Myxo.
- **Why two colonies drained the world:** nutrients spread at 10 µm²/bio-min (B54), and a colony
  acts as a sink. The spreading reached about 50 µm in 1 bio-h and the whole 150 µm world by
  about 10 h. Bare ground takes about 35 bio-h to refill halfway, so it stayed bare (mean
  nutrients 0.63 → 0.03 by 16 h). In proportion this is like a real plate, where a colony
  drains a zone a few colony-widths wide; but our world is only three colony-widths across.
- **The user's design:** each square has its own maximum (B48's patches), refills toward it
  (B33), and doesn't share with distant squares. Patches start at random levels.
- **Local ground** (`nutrient_diffusion` 0.1 µm²/bio-min, 100× slower): a colony drains its own
  patch plus about 25 µm over 30 bio-h.
- **Random start:** each patch starts at 30–100% of its maximum (a second smooth random map).
- **E. coli feed along their whole body:** the growth rate uses the mean nutrient at the rod's
  contact points, and an equal share is eaten at each. A rod takes up food over its whole
  surface. With the old one-square feeding, a cell stalled once the square under its centre
  emptied.
- **Growth cost 3 → 0.5 nutrient units per µm**, tuned so the colony size chosen in B54/B75
  still holds on local ground (E. coli only, live world, two founders):

  | Ground | Cost | Cells at 500 bio-min | Ground left |
  |---|---|---|---|
  | Local | 3 | 43 | 106% |
  | Local | 1 | 215 | 104% |
  | **Local** | **0.5** | **924 (558 + 366)** | **96%** |
  | Local | 0.3 | 4,935 (runaway) | 65% |
  | 10× slower spreading | 3 | 194 | 93% |

  - Very sensitive: below about 0.35, a colony's own patch feeds endless rim growth.
  - **Correction:** "local ground" was described to the user as "enough to feed a cell from the
    few µm around it". At the old cost it wasn't: one division costs 6 units, and a cell's
    ground holds about 1–2.
- **New E. coli founders land anywhere, with no rules:** every 6 bio-h at a random spot, even on
  bare ground or next to Myxo. This replaces B75's landing rules, which the live world could
  never meet.
- **Myxo come in from outside:** 5 groups of 20 plus 10 single cells (110; was 5 × 50 + 10).
  - Each seed arrives at a random time in the first 10 bio-h (`myxo_arrival_window` 600), at a
    random spot that still keeps every cell 30 µm from the E. coli (B47).
  - The world starts with E. coli only.
  - Replaces B50's "seeded once at the start" for Myxo.
- **Not added:** random nutrient pulses. Levels already rise and fall through eating and
  refilling.
- **Tests:** 70 pass.
  - The scout test was made deterministic: a scout's random turning over the test's 0.3 min has
    a spread of about 20°, but the test demanded under 15°, so it had been passing by luck.
  - The colony-overlap test now uses rich ground, since growth speed isn't what it checks.

Source: the user's choices; our runs; our assumptions for the numbers.

**Result of the full run with B78 (live world, 30 bio-h, seed 1; `checks/output/b78_full_30h.png`):**
a real predator–prey wave.
- **Prey first:** E. coli only at the start. They grew from 2 founders to about 2,018 cells by
  20 h, and new founders added a 3rd and 4th colony (at about 6 h and 12.5 h).
- **Hunters arrive and boom:**
  - The Myxo came in over the first 10 h (115 cells), then multiplied from 146 at 15 h to 985
    at 30 h (about ×9 in 20 h, roughly a 6 h generation; measured on prey: 5.5 h, Seef 2021).
  - The mean store held at 155–173; no cells were stringent.
- **With the pack:** up to about 440 Myxo were at prey at once (45%), up to 214 rippling and up
  to 24 killing at a time. About 2,870 kills by 30 h (matrix).
- **Prey crash under way:** E. coli fell from 2,018 at 20 h to 860 at 30 h. The middle colony
  was eaten from the inside, leaving bare ground full of Myxo.
- **The ground keeps its food:** mean nutrients 0.24–0.39 (0.03 in the B76 run). Rich patches
  remain for newcomers.
- **Spilled food:** it peaked at about 52,000 units (about 520 E. coli's worth) at 23–25 h and
  was eaten down to about 8,100 by 30 h.
- **To watch:**
  - With 985 Myxo the 150 µm world is crowded again: the hunters' boom.
  - Scouting stops once Myxo are well fed (store over 100).
  - 30 h doesn't show the rest of the cycle: whether Myxo starve back down and new colonies
    regrow for a second round.
- **Cost:** 44 min of computing for 30 bio-h, with up to about 3,000 cells.
- **No impossible energy jumps:** the largest rise of the mean store between ground updates
  with no births or arrivals was 0.71, which fits feeding at the measured rates.

**B79. Rippling keeps its living-prey trigger (B76): the user follows Berleman 2006 over the main paper's "after digestion".** *11 Oct 2026*
- **The conflict:** Saulnier 2026 reports that ripples "form inside the prey colony once the prey
  has been entirely digested", "following prey consumption and the onset of starvation"
  (Fig. 1b). Berleman 2006 found rippling starts when cells "make direct contact with either prey
  or large macromolecules".
- **The user's choice:** Berleman 2006, the study designed to find what triggers rippling.
  Rippling stays on ghosts and living prey (`ripple_live_prey_weight` 1). No code change.
- **Considered:** rippling only once the prey is digested, or only once starvation starts (the
  main paper's description).
- **Honest note:** the main paper's statement is also an experimental observation (its Fig. 1b
  time-lapse), not only its model. One way the two fit (our reading, untested): contact with prey
  can start rippling, while clear waves need cells packed on cleared ground.

Source: the user's choice; Berleman 2006; Saulnier 2026.

**B80. Bio-backed findings applied (the user's request): three measured values, starving cells follow the smell more, and a famine exit.** *11 Oct 2026*
- **Measured values adopted** (from the literature search in `parameters.md`):
  - `starved_lysis_delay` 30 → 120 bio-min: a starved E. coli bursts 2.0 ± 1.4 h after its
    membrane voltage collapses (Schink et al.). The spread isn't modelled; the death itself is
    already random.
  - `starvation_death_rate` 1 → 0.69 per bio-day: viability falls to 0.1% in 10 days (Schink
    et al.).
  - `scout_speed` 1.2 → 1.1: lone cells glide at 4.4 µm/min (Spormann & Kaiser 1999), against
    the paper's 4. It's a ratio of two studies' numbers.
  - `ecoli_divide_noise` stays ±10%, now marked measured (BioNumbers 110034).
- **Starving cells follow the smell more** (`stringent_smell` 1 → 1.5, as for scouts): the lipid
  attractant works only in starving cells, and nutrients block it (Kearns 2001). The size is
  ours, and a review reports the opposite sign in starved cells, so this is less certain than
  it looks.
- **The famine exit** (`myxo_famine.py`): a day (`famine_time` 24 bio-h) into stringent mode,
  each starving cell starts development and takes one fate:
  - **lysis, 70%** (`famine_lysis_share`): the cell dies, and its body plus what's left in its
    store spill as food, as in a starvation death (B39). Classic counts are 60–80%; O'Connor &
    Zusman 1988 disputed them (at least 80% survive).
  - **spore, 10%** (`famine_spore_share`): kept as a point on the ground (`world.spores`), out of
    the moving population, costing nothing.
  - **rod, the other 20%:** stays on as a stringent cell (persister-like peripheral rods,
    10–20%, O'Connor & Zusman 1991). It isn't drawn again unless it feeds and starves again.
  - **Timing:** lysis and aggregation begin about 24 h after starvation starts development
    (Lee 2012).
  - **Why 70/10/20:** it fits all three measured ranges (so would 75/10/15 or 80/10/10); 70% is
    the closest to the review's "about 60%".
  - **Simplified:** no fruiting bodies; spores don't germinate yet; and the fates don't depend
    on crowding, though real fruiting bodies need many cells.
- **Not applied: stringent mode starting when food runs out outside the cell** (Manoil &
  Kaiser 1980; Harris 1998). It isn't drop-in: every cell away from food would turn stringent
  within minutes, which under B71 stops all scouting and under B75 slows cells in swarm streams.
  Left for the user's decision.
  - **Meanwhile:** the famine's 24 h count from when a cell turns stringent (store below 20),
    not from when its food ran out, so a cell that left food well fed starts its famine later
    than a real one would.
- **Correction:** `parameters.md` said starving cells "last about 10 bio-days". Once stringent,
  the last 20 units last about 2 bio-days, as B70 says; the 10 was my arithmetic error.
- **Bookkeeping note (open):** a Myxo that dies still spills a 100-unit body on top of its store,
  although B75 counts the store as the cell's material, so every death adds 100 units. Lysis
  keeps the same rule (body + store). This props up survivors in a famine.
- **Tests:** 75 pass (5 new: fate shares, lysis food, no fates before a day or after feeding,
  the fates in the running engine, the starving smell).

Source: the user's request; the sources named above; our simplifications.

**Result of the famine check (live world, no prey, 5 × 20 + 10 Myxo arriving over 10 bio-h at a
store of 25, 40 bio-h, seed 1; `checks/output/b80_famine_check.png`):**
- Cells turned stringent about 1 h after arriving, and the famines came 24 h later (from 25.5 h),
  as set. By 40 h: 110 → 70 Myxo, 36 lysed, 4 became spores (about 10%).
- **Lysis food postpones the others' famine:** neighbours that eat the spill climb back above a
  store of 20, which resets their starvation clock to 0 (B75), so their 24 h start again. At 33 h
  only 12–24 of 70 cells were stringent; by 40 h 69 were again, on fresh clocks. A starving
  population therefore shrinks in waves about a day apart, not all at once.
  - **Realistic part:** developmental lysis is thought to feed the survivors.
  - **Not realistic:** in real Myxo a little food doesn't restart development from zero. The
    100-unit body (B80's bookkeeping note) also makes each crumb bigger: 36 lyses released about
    4,000 food units.
- Fed survivors (store between 20 and 100, no food around) scouted again, up to 14 at a time at
  33–35 h.
- **Cost:** 20 min of computing (I had estimated 5).

**B81. Stringent mode ends only after a real meal: a starving cell must eat its way back to a store of 70 (the user's idea and choice).** *12 Oct 2026* — **Replaced by B83:** starvation now ends when prey food within reach is back above 3 units; scraps never end it.
- **Why:** in the B80 famine check, crumbs from lysed neighbours lifted starving cells just above
  20. That reset their starvation clocks, so their famine started over, in waves a day apart.
- **The rule:** stringent mode starts when the store falls below 20 (B70) and ends only when it's
  back to `stringent_exit_level` 70. In between, the cell stays stringent: costs cut, no
  division, no scouting, and its starvation clock keeps running. A cell that never fell below
  20 isn't affected.
- **Backing:**
  - Developing Myxo respond to food like a switch: 12.5% nutrient medium let development go on,
    25% stopped it (Hoang & Kroos 2018). A crumb doesn't end starvation; a real meal does.
  - Food reverses development only before about 24–30 h of starvation (Rajagopalan & Kroos
    2014). That matches our famine exit at 24 h (B80, from Lee 2012).
  - The level 70 is the user's: the papers measure nutrient medium, not our units.
- **Considered:**
  - A fixed time window after leaving stringent mode (the user's other idea). It's only
    loosely backed: in *E. coli* the lag before regrowth grows with starvation time (Himeoka
    2022).
  - Exit levels of 80 or 100.
- **From 15 to 70** takes about one E. coli's worth of food (about 110 units at 50%). The cell
  comes out still hungry, so it may scout.
- **Tests:** 77 pass (2 new: a crumb keeps a cell stringent with its clock running; a crumb no
  longer postpones the famine).

Source: the user's idea and choice; Hoang & Kroos 2018; Rajagopalan & Kroos 2014.

**Result of the famine check with B81 (the B80 set-up; `checks/output/b81_famine_check.png`):**
- The famine now comes in one wave: all 110 cells took their fate between 25.5 and 35 h. 70
  lysed (64%), 12 became spores (11%) and 28 stayed on (25%), close to the 70/10/20 shares.
  Before B81, only 40 had taken a fate by 40 h.
- The survivors fed on the lysis spills and ate their way out of stringent mode: their mean store
  rose from about 13 to about 75 by 36 h, and some scouted again (there's no prey here). It's
  the picture of peripheral rods regrowing on what the lysed cells released.
- **Caveat:** most of that food comes from the dead cells' 100-unit bodies (B80's bookkeeping
  note). Counting only their stores, lysis would release about a tenth as much, and the
  survivors would stay stringent.
- **Cost:** 7 min of computing.

**B82. A dying or lysing Myxo keeps spilling its body (100) plus what's left in its store (the user's choice, option 1).** *12 Oct 2026* — **Replaced by B84:** only the store (the store is the whole cell).
- **Why:** a lysing cell gives up all its contents (proteins, enzymes, DNA, membranes), not only
  its reserves. That food is what lets the survivors recover after a famine (B81 check).
- **Size (the user asked whether Myxo, being bigger, should hold more than an E. coli):** by
  volume the two are about equal. A rod with round ends of radius r and length L has volume
  πr²(L − 2r) + (4/3)πr³:
  - our average E. coli (1 × 3 µm): about 2.1 µm³;
  - our Myxo (0.7 × 5 µm): about 1.8 µm³;
  - a real Myxo (0.5 µm wide, 6 µm long): about 1.2 µm³.

  Myxo is longer but thinner, so 100 units each (B75) stays.
- **Known inconsistency, parked:** at division the store is split (200 → 100 + 100) and the
  daughter's body appears without being paid for, so each division mints 100 units that come
  back as food when that cell dies. A proper fix re-scales the energy numbers (bodies paid for at
  division, the 5.5 h generation re-anchored).

Source: the user's choice; geometry; B75.

**B83. Outside food decides what real cells decide with outside food: starvation, its end and scouting follow the prey food within reach, not the store; scraps from dead Myxo keep cells alive but never end their starvation (the user's design).** *12 Oct 2026* — **Delay split in B84:** fast effects after 30 bio-min, starving behaviours after 2 bio-h.
- **Why (the user):** the store drove almost every rule, though real cells start the stringent
  response when food runs out outside (Manoil & Kaiser 1980; Harris 1998). The user asked for
  "the natural sense", and for scouting to be a lucky draw driven by outside food.
- **The starvation clock** starts when prey food within 2 µm of the head falls below
  `living_food` (1 unit: too little to cover running costs) and keeps running. It resets only
  when prey food within reach is back above 3 units, a real meal. The store plays no part.
- **Stringent mode** starts after `stringent_delay` of starving: 30 bio-min by default (the
  starvation signal rises fast, Manoil & Kaiser 1980). 3 bio-h (Harris's "period of starvation
  recognition") is run for comparison, as the user asked to see both. Effects as before; stringent
  cells now can't divide even when full.
- **The famine (B80) and the starving speed-up (B75)** count from when the prey food ran out, as
  the experiments time them (Lee 2012; Jelsbak 2002).
- **What ends starvation (the side chat's option 1):** prey food within reach above a meal level
  (3 units, the scouting level). That's what Hoang & Kroos varied: the food around the cells. A
  full cell on prey food exits at once, so the full-cell gap is closed.
- **Scraps (the user's idea):** what dead or lysed Myxo spill goes to its own map (`scraps`),
  which spreads and fades exactly like prey food (12 bio-h half-life). Scraps fill a store only up
  to `scrap_cap` 30 and never reset the clock: "eating trash just to stay alive", still starving,
  still looking for prey. This fits developmental lysis feeding the cells that stay behind, and
  Hoang & Kroos's finding that a small dose of food doesn't stop starvation.
- **Scouting (the user's design):** a lucky draw driven by prey food within reach, not by the
  store or by time.
  - The chance starts below 3 units (30% of top-speed food, 10 units) and rises in a straight
    line to its top at zero food.
  - At the top, 10% of cells scout at once: start rate 0.1/(0.9 × 10) ≈ 0.011 per real min with
    10-min spells. About half the cells get a turn within 10 bio-h.
  - A spell ends when prey food is back above 3 units, or at random.
  - Starving cells may scout, at no extra cost, keeping every starving perk. A starving scout
    moves at whichever is faster, its scout speed or its starving speed.
  - No measured share of scouts exists: Rombouts 2023 shows class shares only in figures.
- **Stays on the store:** division at 190 or more, death at 0, the hunger factor in uptake, and
  what a dead cell spills (B82).
- **Retired:** `starvation_level` (B70), `stringent_exit_level` (B81), `scout_food_threshold`
  (B71) and `hunger_drive`.
- **To watch in the runs:** the crowding slow-down (B75) now applies to every starving cell, so it
  may slow swarm streams; the famine now also hits lone travellers, though real fruiting bodies
  need many cells.
- **Tests:** 80 pass; the equivalence tests are still exact.

Source: the user's design and choices; Manoil & Kaiser 1980; Harris 1998; Hoang & Kroos 2018;
Rajagopalan & Kroos 2014; Lee 2012; Jelsbak 2002.

**Result of the famine checks with B83 (the B80 set-up, no prey, 40 bio-h; delays 30 bio-min and
3 bio-h; `checks/output/b83_famine_delay30.png`, `b83_famine_delay180.png`):**
- The famine came 24 h after each seed arrived, in one wave: by 34 h all 110 cells had taken
  their fate. 69 lysed (63%), 12 became spores (11%) and 29 stayed as rods (26%).
- The rods ate scraps up to the cap of 30 and stayed starving, still searching: 3–7 of them
  scouting at a time. About 5,000 units of scraps were left on the ground at 34 h, fading.
- At zero prey food, 8–12 of 110 cells scouted at a time (7–11%), the 10% chosen.
- The two delays gave the same fates (same random draws): with no prey at all, the famine timing
  doesn't depend on the delay. Only the stores differed: cells on the 3 bio-h delay paid full
  costs for longer (mean store 6.7 vs 16.0 at 24 h). The difference between the delays will show
  only in a world with prey.
- **Cost:** 9 min for both, run in parallel.

**Result of the full runs with B83 (live world, 60 bio-h, seed 1; delays 30 bio-min and 3 bio-h side by
side; `checks/output/b83_full_60h_delay30.png`, `b83_full_60h_delay180.png`):** a standoff, not a crash.

| | 30 bio-min delay | 3 bio-h delay |
|---|---|---|
| E. coli peak → low → at 60 h | 1,563 (22 h) → 649 (39 h) → 759 | 1,735 (17 h) → 711 (38 h) → 1,379 |
| Myxo at 30 h → 60 h | 909 → 1,772, still rising slowly | 1,113 → 1,510, levelling off |
| Stringent at 60 h | 1,397 (79%) | 755 (50%) |
| Mean Myxo store at 60 h | 168 | 156 |
| Famine fates by 60 h | 47 lysed, 7 spores (from 55 h) | 109 lysed, 18 spores (from 51 h) |

- **Both:** the first 30 h look like B78 (prey grow, hunters arrive and boom). Then the prey fall to
  about 650–710 by 38 h, and instead of a crash both sides hold: E. coli survive as many small
  patches between thick Myxo streams, new founders keep adding colonies (6 by 60 h), and the
  hunters level off at about 1,500–1,800.
- **The famine is a weak brake here:** it needs 24 h without prey food, and with prey patches
  scattered everywhere few cells go that long. It began only at 51–55 h.
- **Starving cells keep full stores:** cells that leave prey well fed turn stringent with stores
  of about 160 and, at a tenth of the costs, keep them. They can't divide, but they don't run
  down either, so when they reach prey again they divide at once; and when the famine does hit
  them, they lyse with full stores, most of which can't be used (scraps fill only to 30).
- **Why the short delay ends with more hunters and fewer prey:** cells crossing between patches
  turn stringent sooner and keep their stores; on the 3 h delay they pay full costs for longer.
- **Rippling fell** from about 110–180 (25–30 h) to about 20–30 at 60 h, as the colonies became
  small patches.
- **Not yet checked:** whether the crowding slow-down (B75) now slows the swarm streams, since
  50–79% of cells are stringent.
- **Cost:** 2.1–2.2 h each, run in parallel.
- **Decision (the user, 12 Oct 2026):** keep the 30 bio-min delay as the default (the fast
  response, Manoil & Kaiser 1980). Next: check the crowding slow-down, decide whether starving
  cells should use up their stores, then a longer run.

**Crowding check (12 Oct 2026; the paper's test boxes, 65 µm, 30 real min, starvation response off,
then each cell's crowding read and its speed were it stringent):**
- **Swarming** (370 cells, the paper's swarming density 0.088 cells/µm²): crowding median 0.72;
  77% of cells above 0.5. Just after turning stringent, 98% of swarming cells would glide slower,
  median ×0.83; after 15 h of starving the loner speed-up partly makes up for it (median ×0.96).
- **Rippling** (1,000 cells, 0.24 cells/µm²): crowding median 1.00; everyone at ×0.75.
- **So the B75 slow-down misfires:** swarm streams are locally nearly as dense as a rippling field,
  so the measure can't tell a stream from an aggregate. In a flat world one layer of 0.7 × 5 µm
  cells holds at most about 0.29 cells/µm², so no density threshold can single out real
  aggregates (multilayer mounds).

**B84. From the user's side chat: starving cells burn their surplus first, stringent effects come in two steps (30 bio-min and 2 bio-h), a dead Myxo leaves only what's left of its store, and the crowding slow-down is dropped.** *12 Oct 2026*
- **Surplus first (decided in the side chat):** the 90% cost cut protects only a cell's core, a
  newborn's 100; anything above is burned at the full rate first. A cell that left prey at 160
  slims to 100 in about 14 bio-h, then its costs nearly stop.
  - **Why:** stored fuel is used first when food runs out (storage-polymer review; Myxo burn their
    lipid bodies during development, Hoiczyk 2009; B22). The full rate on the surplus is our
    choice. Before, a starving cell kept about 160 for a day (B83 runs).
- **Two delays (the user's pick):**
  - after 30 bio-min of starving, the fast effects: cost cut, no division, better uptake. The alarm
    (p)ppGpp rises "rapidly" (Manoil & Kaiser 1980);
  - after 2 bio-h (`behaviour_delay`), the starving behaviours: keener smell and the speed-up.
    "The first few hours" of starvation are the period of starvation recognition (Harris 1998),
    and the lipid attractant is a developmental chemoattractant (Kearns 2001).
  - Considered: one 2 h delay for everything (about 6 more units spent per starvation), one
    30 min delay (B83).
- **A dead Myxo leaves only what's left of its store (the user's confirmation):** the store is the
  whole cell (a mother reaches 200 and splits into 100 + 100), so there's no separate body.
  - A cell that starves to zero has used itself up and leaves nothing; a lysing cell leaves its
    store as scraps (about 50–100 at the famine).
  - Replaces B82 and B39's body: they counted the body twice, about 100 free units per death.
    `myxo_body_content` is retired.
- **The crowding slow-down is dropped (the user's choice; the crowding part of B75):**
  - **Why:** the crowding check showed it misfires. Swarm streams are locally nearly as dense as a
    rippling field, so in a flat world it slowed 98% of starving swarming cells (median ×0.83) and
    can't single out real aggregates. Its basis (cells slow inside aggregates, Sliusarenko 2007)
    belongs to fruiting-body formation, which this project doesn't model.
  - Starving cells keep the measured speed-up (Jelsbak 2002).
  - Retired: `starvation_speed`, `crowded_density`, `crowding_radius` and the crowding map.
- **For after this project (the user):** a 3D version with fruiting bodies. Note: swarming and
  reversals are part of fruiting-body formation. Mutants of the reversal system (frz), most of
  which reverse only about every 2 h instead of every 6.8 min, can't aggregate properly and make
  "frizzy" filaments instead of fruiting bodies (Blackhart & Zusman 1985).
- **Tests:** 82 pass (new: surplus first; fast effects at 30 min, behaviours at 2 h).

Source: the user's choices; Hoiczyk 2009; Manoil & Kaiser 1980; Harris 1998; Kearns 2001; Jelsbak
2002; Sliusarenko 2007; Blackhart & Zusman 1985.

**Result of the famine check with B84 (the B80 set-up: no prey, seeds at a store of 25, 40 bio-h;
`checks/output/b84_famine_check.png`):**
- The same fates as with B83 (the same random draws): 69 lysed, 12 spores, 29 rods by 34 h.
- **Scraps are now small:** they peaked at about 370 units, against about 5,000 with the 100-unit
  body. Lysing cells give only what's left of their store (about 15 each here), so the rods'
  stores rose only from about 15 to about 20, not to the cap of 30.
- The other two changes don't show in this set-up: the seeds start at 25, below the core of 100,
  so there's no surplus to burn, and the 2 h behaviour delay changes smell and speed, which a
  world without prey doesn't measure. They matter for hunters that leave prey well fed.
- **Cost:** 8 min.

**Result of the 120 bio-h run with B84 (live world, seed 1; `checks/output/b84_full_120h.png`):** a
damped predator–prey cycle, with both sides holding on.

| | Prey (E. coli) | Hunters (Myxo) |
|---|---|---|
| First peak | about 1,270 (23–25 h) | 1,528 (65 h) |
| First low | 278 (64 h) | 1,235 (90 h) |
| Second peak | about 1,125 (95 h) | about 1,500 (110–115 h) |
| Second low | about 490 (110 h) | — |
| At 120 h | 789, rising | 1,464 |

- **The cycle:** the hunters lag the prey. When the prey bottom out (64 h), most hunters starve
  (93% stringent), the famine bites (641 lysed and 81 spores by 120 h, from 51 h on), the mean
  store falls from about 160 to 112 as cells burn their surplus, and the prey regrow to about
  1,100. Then the hunters recover and eat them down again, less deeply the second time (to about
  490 instead of 278).
- **Small swings for the hunters:** Myxo numbers moved only about ±10–20% around 1,400, while the
  prey moved about ×4, then ×2. Starving hunters last long at a tenth of the costs, so they
  shrink slowly.
- **Still crowded:** about 1,200–1,500 Myxo in the 150 µm world (about 0.06 cells/µm², near the
  paper's swarming density 0.09). The pictures show thick streams covering much of the ground,
  with prey in clumps between them. Rippling stayed low (about 10–110 cells).
- **Scraps pile up:** 13,000–23,000 units lay on the ground from 75 h on. Starving cells can only
  eat them up to a store of 30, so most fade unused.
- **Runs are repeatable:** a restart from a checkpoint matched the first attempt exactly at every
  logged time.
- **Cost:** about 4.3 h of computing in total, over three attempts (two sessions ended).

**B85. Thinning the crowd (the user's choices): hunters keep 30% of eaten food and starving cells pay 30% of their costs. A poorer ground was tested and backfired, so it isn't adopted yet.** *15 Oct 2026*
- **Why (the user):** about 1,400 Myxo and up to about 1,300 E. coli in the 150 µm world (B84) are
  too many. The target: at most about 500 prey and 200 Myxo, still cycling.
- **Efficiency 50% → 30%** (inside the measured 5–60%, del Giorgio & Cole 1998; B21's first value).
  A division now takes about 3.3 E. coli's worth of food instead of 2, so each prey feeds fewer
  hunters.
  - **Growth speed kept (my implementation choice):** `uptake_rate` and `uptake_max` are divided by
    the efficiency (0.5 → 0.83 per bio-min; 5 → 8.3 food units per bio-min). A cell gains store
    exactly as fast as before on any amount of food, so the measured 5.5 h generation (5.4 h in the
    model, B65) holds; it just eats 5/3 as much. Left alone, the generation would have slowed to
    8.9 bio-h, against Seef 2021.
  - The scouting and meal level (30% of top-speed food) stays 3 units. The reserve fills at a third
    of the efficiency, now worked out from it.
- **Starving costs 10% → 30%** on the core (the surplus above 100 still burns at the full rate
  first, B84). A starving cell loses about 30 units in the day before its famine instead of 10. Our
  number; the direction is backed (stringent response, Singer & Kaiser 1995).
- **A poorer ground (the user's "lower prey ceiling"), tested:** every patch's maximum multiplied by
  0.5, 0.35 or 0.25 (richness 0.15–0.5, 0.105–0.35, 0.075–0.25, from 0.3–1.0).

  | Ground | Prey alone at 12 h | 24 h | 30 h |
  |---|---|---|---|
  | ×1 (now) | about 2,200 | (stopped at 13 h with 3,049) | |
  | ×0.5 | 317 | 1,179 | 1,856 |
  | ×0.35 | 148 | 531 | 850 |
  | ×0.25 | 80 | 299 | 478 |

  With hunters (prey / Myxo; live world, seed 1, 48 bio-h; `checks/output/b85_full_48h_*.png`,
  `b85_diag_r50_*.png`):

  | Ground and hunters | 16 h | 32 h | 48 h |
  |---|---|---|---|
  | ×1, old hunters (B84) | 1,220 / 175 | 699 / 959 | 664 / 1,264 |
  | ×0.5, old hunters (50%, 10%) | 315 / 113 | 1,465 / 119 | 2,422 / 220 |
  | ×0.5, 50% and 30% | 372 / 114 | 1,205 / 137 | 2,760 / 208 |
  | ×0.5, new hunters (30%, 30%) | 347 / 110 | 1,119 / 99 | 1,939 / 115 |
  | ×0.35, new hunters | 185 / 110 | 706 / 63 | 1,346 / 60 |

  - **What happened:** on poorer ground the colonies are still few and small (about 100 cells in
    all at 8 h, against about 680 in B84) while the hunters arrive (0–10 bio-h). The hunters
    can't find them: their slime highways loop between the colonies, and few kills happen (prey
    remains on the ground at 20 h: about 100 units, against about 1,500 in B84). Some hunters starve
    into the famine. The colonies grow unchecked, and the prey overshoot to 1,300–2,800 by 48 h,
    while the hunters only begin to boom.
  - **The hunters' traits hardly matter in this first wave:** the old hunters, or 50% with 30%,
    did no better on the same ground (2,400–2,800 prey at 48 h; one seed, so the differences
    between them may be chance, A12).
  - **Not adopted:** richness stays 0.3–1.0 until the user decides (open questions).
- **Corrections (mine):**
  - My MCQ said "less food in the ground, so colonies stay small; the hunters follow". In the
    first wave it went the other way: small colonies starved the arriving hunters, and the prey
    escaped.
  - My MCQ said costlier starving "keeps the cycle swinging as numbers shrink". The textbook
    predator–prey model says the opposite (Rosenzweig & MacArthur 1963): hunters that convert food
    less well or die faster need more prey to break even, which steadies the balance. A lower prey
    ceiling steadies it too (the paradox of enrichment in reverse, Rosenzweig 1971).
- **What sets each level (the textbook model, as a guide):** the prey settle near the level at which
  a hunter just breaks even, which depends on the hunters (how well they find, kill and convert
  prey, and what they pay). The hunters settle at the number that the prey's growth at that level
  can feed, which depends on the ground. So weaker hunters mean fewer hunters but *more* prey; a
  poorer ground means fewer hunters. In B84 the prey averaged about 700 (278–1,189) from 30 h on,
  with about 1,350 hunters.
- **Tests:** 83 pass (3 updated for the new numbers; 1 new: at 30% a cell grows exactly as fast as at
  50% but uses 5/3 as much food).
- **Cost:** about 5 min per prey-only run (the full-ground one was stopped at 13 h, past 3,000
  cells); 25–30 min per 48 h run with hunters, two at a time.
- **The user's choices (16 Oct 2026):** both targets matter equally, so tuning toward about 500 prey
  and 200 hunters goes on (it may not be reachable with these rules in this world). Next: the old
  ground (richness 0.3–1.0) with the new hunters, 120 bio-h, seeds 1 and 2 in parallel
  (`checks/output/b85_full_120h_s1`, `_s2`), to see how far the hunter changes alone thin the hunters.
  Not chosen: ground ×0.7, hunters arriving later (12–24 bio-h), long runs on the half ground.

Source: the user's choices; del Giorgio & Cole 1998; Seef 2021; Singer & Kaiser 1995; Rosenzweig &
MacArthur 1963; Rosenzweig 1971; our runs.

**Result of the 120 bio-h runs with the B85 hunters on the old ground (live world, seeds 1 and 2;
`checks/output/b85_full_120h_s1.png`, `_s2.png`; side by side with B84 in `b85_compare_120h.png`):**
the hunter changes alone thin the hunters a little and fatten the prey a lot, as the textbook guide
predicted.

| | B84 (old hunters), seed 1 | B85 hunters, seed 1 | B85 hunters, seed 2 |
|---|---|---|---|
| Highest prey | 1,295 (24 h) | 2,396 (90 h) | 2,991 (28 h) |
| Highest hunters | 1,528 (65 h) | 1,316 (112 h) | 1,125 (60 h) |
| Prey, 60–120 h: mean (range) | 703 (278–1,189) | 1,758 (818–2,396) | 1,158 (601–1,649) |
| Hunters, 60–120 h: mean (range) | 1,395 (1,223–1,528) | 1,168 (1,060–1,316) | 994 (899–1,124) |
| Starving hunters, 60–120 h | 80% | 79% | 80% |
| Dormant prey, 60–120 h | 44% | 62% | 55% |
| Lysed / spores by 120 h | 641 / 81 | 309 / 53 | 560 / 75 |

- **Hunters 16–29% fewer, prey 65–150% more** than in B84. Both seeds stay far from the targets
  (about 500 prey, 200 hunters).
- **The cycle:** the prey swing (seed 2: 2,991 → about 400 → 1,650 → 1,030), but the hunters stay
  within about ±10%: most of them starve slowly on the slime highways while a minority feeds.
- **Where the prey hide:** more than half are dormant cells in clumps between the hunters' highways,
  which the hunters rarely reach.
- **The ground isn't the limit:** mean nutrients fall from about 0.39 to 0.15–0.23 and hold. At that
  level the ground still refills fast enough to grow about 200 E. coli per bio-hour, far more than
  the hunters harvest.
- **Seeds differ a lot:** seed 2's first prey wave was about twice seed 1's; single runs are
  indications only.
- **Cost:** about 3.2 h of computing per run, two at a time (the session ended once; both runs
  carried on from their checkpoints at 50 and 45 bio-h).
- **The user's choices (16 Oct 2026):**
  - The targets (about 500 prey, 200 hunters) count **after the first wave**, from about 60 bio-h:
    the first wave depends on how the world starts.
  - **Next test:** bare ground refills 6× slower (`nutrient_regrow_rate` 1/18,000 per bio-min,
    half-way back in about 9 bio-days instead of 1.5) with the hunters back at 50% efficiency
    (`uptake_rate` 0.5, `uptake_max` 5; starving costs stay 30%). By the textbook guide,
    B84-strength hunters hold the prey low while a sixth of the supply keeps their numbers down
    (roughly 200–250). A test on seed 1 only, as setting overrides; the defaults stay as they are
    until it's judged. Not chosen: refill ÷3, refill ÷6 with 30% hunters, fewer new colonies.

**B86. An average-world model, learned from the full simulation, explores the flexible settings before any more long runs (the user's idea).** *16 Oct 2026*
- **Why (the user):** "make a mathematical approximation first, keeping the vital params constant
  and shuffling some flexible ones that will keep the Myxo–E. coli counts cycling within a
  particular range". A full run takes 2–4 h; the model runs in a fraction of a second.
- **Vital and flexible:** measured and paper numbers stay fixed. Flexible are those marked tuned,
  assumed or your choice in `parameters.md`, plus efficiency within its measured 5–60%.
- **The model** (`predation-sim/meanfield/`): three numbers that change smoothly in time: mean ground
  nutrient, living E. coli, Myxo. Each process was read off the full simulation's statistics
  (4 bio-h windows from 8 runs):
  - **prey births** = a trickle (each prey lives on the food regrowing within about 4–10 µm² of it)
    plus growth at colony edges into fresh ground, which rises only with E^0.4 (only the edge
    grows). R² 0.94.
  - **kills** = a × E^1.3 × H^0.9 × (ground fullness)^1: hunters mostly catch growing cells at colony
    edges; dormant clumps on empty ground are rarely reached. R² 0.74.
  - **Myxo:** each kill becomes about 0.4 × efficiency new Myxo, and about 2–3% of Myxo are lost per
    bio-h (famine, starving to death). R² 0.73. The starving cost had no measurable effect.
- **Fit and test:** fitted to 6 runs' whole curves. The two runs held back (B85 seed 1, ground ×0.35)
  are matched as well as the others: E. coli typically within ×1.3–1.8, Myxo within ×1.2–1.5. The
  sim's own seed-to-seed spread is about ×1.5. The model is smooth: it gives the levels and the first
  wave, not the sim's random swings.
- **Found on the way: E. coli practically never starve to death in the sim.** A dormant cell's
  starvation clock restarts whenever 0.01 units of food regrow under it (`dormant_threshold`). That
  takes under an hour at today's refill and about 5 h at ÷6, never the 24 h needed before dying. So
  only hunters remove E. coli, and on empty ground they pile up as dormant clumps (the refill test:
  about 2,000 E. coli, 94% dormant). It's the E. coli version of the crumb problem solved for Myxo in
  B81 and B83. The model adds the starvation rule worked out from the sim's own rules (not fitted:
  no run had starving E. coli).
- **The scan** (`meanfield/scan.py`; refill ×1/40–×2, ground ×0.7 or ×1, efficiency 5–60%, wake level
  0.01–0.3; 1,232 combinations): **none keeps E. coli within 100–600 and Myxo within 30–250 from
  60 bio-h on.**
  - Closest: refill ÷16 to ÷40, ground ×0.7, efficiency 60%, wake level 0.03 or more. E. coli about
    700 (420–1,040), Myxo about 120 on average, but the first wave's hunters take longer than 60 bio-h
    to fall below 250.
  - **Why:** the prey settle where a hunter breaks even (the textbook guide, B85), and with today's
    hunters that is about 700 E. coli or more even at the top of the measured efficiency range.
  - **What would reach it:** hunters better at finding and killing prey (the model's kill scale `a`;
    `scan.py --search k`). At ×2: E. coli about 550–1,000. At ×4: E. coli 350–560 with Myxo 160–240
    (refill ÷2–÷3, ground ×0.7, efficiency 20–40%).
  - **No sustained cycles:** in every in-range case the model settles to steady numbers; the sim's
    swings come from chance and space, so they would ride on these levels.
- **Caveats:** the model is an average; the sim's spatial effects (highways, colonies found by
  chance, the start-up trap on poor ground) enter only through its fitted numbers. Settings far from
  the 8 runs (refill ÷40, wake level 0.3, better search) are extrapolations, to be checked in the
  full simulation.

- **Result of the refill test (B85 choices of 16 Oct: refill ÷6, 50% efficiency, 120 bio-h, seed 1;
  `checks/output/b85_refill6_eff50_s1.png`):** over 60–120 bio-h about 680 Myxo (507–780, falling to
  507 at the end; half of B84's) but about 2,150 E. coli (1,846–2,587, still rising), 96% of them
  dormant on nearly empty ground (mean nutrient 0.035). Few hunters, and prey that never starve, as
  the model explains.
- **The user's choices (16 Oct 2026):** irregular swings around steady levels are enough (no need
  for regular cycles). Next: short tests of what could make hunters about 4× better at finding prey,
  read as the model's kill scale `a`: prey smell ×4 (`chemo_strength` 8), colony smell ×4
  (`ecoli_attractant_rate` 8), 30% scouting at zero food (`scout_start_rate` 0.3/(0.7 × 10)), and
  all three together, against today's settings (live world, seed 1, 24 bio-h each, side by side).
  Not chosen: letting E. coli starve (a real meal to wake), testing the model's closest point,
  relaxing the targets.
- **Result of the hunting tests (live world, seed 1, 24 bio-h each; `checks/output/hunt_*.png`;
  `meanfield/hunting.py`):** none makes the hunters better at finding prey.

  | Test | Search scale vs today (from 10 h / from 14 h) | Kills by 24 h | E. coli / Myxo at 24 h |
  |---|---|---|---|
  | Today's settings | ×1.00 / ×1.00 | about 2,980 | 1,368 / 377 |
  | Prey smell ×4 | ×0.98 / ×0.86 | about 3,440 | 2,140 / 433 |
  | Colony smell ×4 | ×0.95 / ×0.96 | about 3,060 | 1,535 / 405 |
  | 30% scouting | ×0.97 / ×0.98 | about 2,850 | 1,701 / 389 |
  | All three | ×1.07 / ×1.19 | about 3,040 | 1,502 / 384 |

  - All within chance for single runs (about 10–20%, A12), far from the ×4 the model needs.
  - **Why (my reading):** kills need touches, and touches need movement. Movement keeps the paper's
    real speed (B4), while biology runs 10× faster, so per bio-hour a Myxo covers 10× less ground
    than a real one, as B66 noted. The smell and the scouts only steer that little movement.
  - **So the model's missing ×4 matches the speed-up:** at 2.5× instead of 10× a hunter would cover
    4× more ground per bio-hour. A hypothesis, untested; the cost is about 4× more computing per
    bio-hour, and a video in which biology moves 4× slower against the cells' gliding (closer to
    real life). **Tested below and wrong:** lower speed-ups hunt worse.
- **Model scans refreshed with the complete refill run (fit of 16 Oct, `meanfield/fitted.json`):**
  search ×1 and ×2: no combination in range; ×4: 30 combinations, best refill ÷2.6–÷3.3, ground
  ×0.7, efficiency 30%: E. coli 350–550, Myxo 180–240, steady.
- **The user's choices (16 Oct 2026, after the hunting tests):**
  - **The targets are relaxed:** about 700–1,000 E. coli and about 150 Myxo are acceptable.
  - **The user's view:** world (movement) time and biological time should not have been separated
    in the first place (B4). The split was made only to save computing: at real speed, 48 bio-h of
    predation would take days, and every run now would take 10× longer (a 120 bio-h run roughly a
    day and a half).
  - **Next:** two short runs at speed-ups 5× and 2.5× (24 bio-h, seed 1, side by side), measuring the
    search scale against the 10× runs (`hunt_speed5`, `hunt_speed2p5`).
- **Result of the speed-up tests (live world, seed 1, 24 bio-h; `checks/output/hunt_speed*.png`):**
  lower speed-ups make the hunters worse at finding prey per bio-hour, not better.

  | Speed-up | Search scale vs 10× | Kills by 24 h | E. coli / Myxo at 24 h | Myxo at prey |
  |---|---|---|---|---|
  | 10× (today) | ×1.00 | about 2,980 | 1,368 / 377 | 239 |
  | 5× | ×0.82 | about 3,120 | 1,935 / 370 | 241 |
  | 2.5× | ×0.60 | about 1,380 | 2,847 / 196 | 86 |

  - **Correction (mine):** the hypothesis above ("the model's missing ×4 matches the speed-up") is
    wrong. Covering more ground per bio-hour did not mean more kills.
  - **Likely why (untested):** slime trails and smells fade and spread on the biology clock (B31,
    B63), so at a lower speed-up a trail lasts more real minutes (at 2.5×, 144 real min instead of
    36) and the hunters stay locked in their highways for longer; each touch also pauses less often
    (B66's scaling), closer to the measured 30%.
  - **So the speed-up stays 10×** unless the user decides otherwise: lower ones hunt worse here and
    cost 2–4× more computing.
- **The model's candidates for the relaxed targets (refreshed fit), and the user's choice (16 Oct
  2026): test B and F side by side** (live world, seed 1, 150 bio-h; `checks/output/cand_B_150h`,
  `cand_F_150h`). If the sim agrees with the model, the better one becomes the new defaults.

  | | Settings | Model, after the first wave | Model, first-wave peaks |
  |---|---|---|---|
  | B | refill ÷20, ground ×0.7, efficiency 60%, wake level 0.03 | about 1,000 E. coli, 140 Myxo | E. coli about 1,400, Myxo about 400 |
  | F | refill ÷40, ground ×0.7, efficiency 60%, wake level 0.01 | about 990 E. coli, 125 Myxo | E. coli about 1,430, Myxo about 400 |
  | Today | defaults | about 1,350 E. coli, 810 Myxo | |

  - Both need efficiency 60% (the top of the measured 5–60%), reversing B85's 30%: at 30% the model
    gives about 2,900 E. coli and 60 Myxo. The uptake numbers are divided by it (B85: 0.42 and 4.2),
    so the 5.4 h generation holds.
  - The hunters take about 100 bio-h to come down from their first-wave peak, hence 150 bio-h.
- **Result of the candidate runs (`checks/output/cand_B_150h.png`, `cand_F_150h.png`):** the
  hunters land in the relaxed range; the prey don't, and the model missed them by more than ×2.

  | | E. coli, 60–150 h | Myxo, 60–150 h | At 150 h | Model said |
  |---|---|---|---|---|
  | B | 2,289 (2,057–2,640), 100% dormant | 209 (92–302), 93% starving | 2,057 / 99, falling | about 1,000 / 140 |
  | F | 2,467 (2,074–2,950), 99% dormant | 206 (133–253), 80–93% starving | 2,074 / 133 | about 990 / 125 |

  - **First wave:** on the ×0.7 ground the hunters started slowly (the start-up trap of B85, milder),
    and the prey reached 2,700–2,950 by 50–75 h, about 2.4× the model.
  - **After it:** by about 60 h the ground was empty (mean nutrient about 0.02–0.03) and every E. coli
    was dormant. Births nearly stopped (5–20 per bio-h) and the prey died slowly (net about 3–20 per
    bio-h), mostly by starving: in both runs the refill is now slow enough that a dormant cell can
    take more than a day to wake. **[Wrong, corrected in B87:** most were eaten. From 60 h on, kills
    ran at 6–26 per bio-h, against 1–3 starvation deaths per bio-h.**]**
  - **The hunters stay on their highways:** about 270 Myxo sat within 10 µm of prey, but only 13–94
    were fed and kills were rare. The pictures show why: a few thick slime highways run between the
    clumps, and the hunters hardly leave them (the trail lock-in of B62–B69).
  - **The model's limit:** being an average, it lets every hunter meet every prey. It can't hold
    prey in places the hunters never visit, so in this regime it underestimates the prey.

Source: the user's idea; our runs; Rosenzweig & MacArthur 1963.

**B87. E. coli can starve: dying starts as soon as a cell goes dormant, and only a real meal wakes it (the user's choice).** *16 Oct 2026*
- **Why:** uneaten E. coli piled up as dormant clumps that practically never died (B86): a trace of
  regrowing food (0.01 units) woke a dormant cell and restarted its starvation clock long before the
  24 h it needed to start dying. It's the E. coli version of the crumb problem solved for Myxo in
  B81 and B83.
- **No day of grace** (`dormancy_before_death` 1440 → 0 bio-min): a dormant cell (not a persister)
  dies at the measured 0.69 per day from the moment it goes dormant. Schink et al. found viability
  falls exponentially from early on in carbon starvation, with no fixed lag; this was noted in the
  literature check (B80) but not applied until now.
- **A real meal wakes a dormant cell** (new `wake_threshold` 0.2, the user's pick): a growing cell
  still goes dormant below 0.01, but a dormant one stays dormant, its clock running, until the food
  under it is back to 0.2, the level at which E. coli grow at half speed (the Monod constant already
  in the model, about a division's worth of food under the cell). A trace no longer resets it.
  - Considered: 0.1 (more cells wake, clumps fade more slowly) and 0.3 (close to Myxo's 30% meal
    rule, B83).
  - At today's refill a dormant cell waits about 18 bio-h to wake on the richest ground and about
    55 bio-h on the poorest, starving meanwhile.
- **Unchanged:** persisters (5%) never starve; a starving cell's contents still shrink to 25% over
  a day of starving, now its own setting (`starved_shrink_time` 1440 bio-min; it used the day of
  grace before).
- **Quick check (E. coli only, live world, seed 1, 13 bio-h):** colonies grow as before (2,843 cells
  at 13.3 h, against 3,049 under the old rules); starving matters only once centres stay dormant
  for hours.
- **Tests:** 85 pass (2 new: a trace keeps a dormant cell dormant with its clock running and a real
  meal wakes it, while a growing cell keeps growing on thin food; freshly dormant cells die at the
  measured rate, persisters never).
- **Next (the user's choice):** candidate B (refill ÷20, ground ×0.7, efficiency 60%) again with these
  rules, 150 bio-h, seed 1 (`checks/output/cand_B87_150h`).

Source: the user's choice; Schink et al. (Basan lab); B81, B83.

**Result of candidate B with the B87 rules (live world, seed 1, 150 bio-h; `checks/output/cand_B87_150h.png`;
beside the old rules in `cand_B87_compare.png`; the model against every run in `meanfield_vs_sim_b87.png`):**
the prey now starve and fall into the relaxed range, but mostly because one colony could never
starve (a mistake of mine, below); the hunters undershoot.

| | E. coli, 60–150 h | Myxo, 60–150 h | At 150 h | Model said, at 150 h |
|---|---|---|---|---|
| B, old E. coli rules | 2,289 (2,057–2,640), 100% dormant | 209 (92–302), 93% starving | 2,057 / 99 | about 1,000 / 140 |
| B, B87 rules | 1,201 (716–2,229), 97% dormant | 182 (76–301), 86% starving | 716 / 77, both still falling slowly | 692 / 120 |

- **E. coli starve now** (`checks/prey_budget.py`, per bio-h): the prey peaked at 2,371 (55 h).
  From 60 to 120 h, 11–28 starved and 7–11 were eaten per bio-h; under the old rules only 2–3
  starved. Starving cells die at the measured rate: at 85 h the checkpoint held 698 dormant cells
  that weren't persisters, so 0.69 per day should kill 20 per bio-h, and the run showed 20.
- **Found: a whole colony of persisters (my mistake in the build manual).** Daughters inherit the
  persister flag (`ecoli_body.daughters`), and a founder is a persister with a 5% chance. So "5% of
  cells never starve" (B40) had become "one colony in 20 never starves, the rest have none". It
  didn't show before because practically no E. coli starved.
  - Here colony 1 was one: at 85 h it held 713 of the 1,411 living E. coli, all persisters.
  - By 150 h about 490 of the 716 were still that colony, worked out from the starvation rate
    (6 deaths per bio-h ÷ 0.029 per cell per bio-h ≈ 210 dormant cells that can die).
  - With 5% persisters in every colony, colony 1 would have starved down to about 150, and the
    prey would probably have ended near 300–400 (a rough estimate of mine, not a run).
- **The hunters:** they peaked at 301 (87 h), and the famine (B80) followed: 201 lysed and 34
  spores by 150 h (old rules: 226 and 32), leaving 77, below the target of about 150. With fewer
  prey to eat, they fell faster than under the old rules.
- **The model** (with the B87 rules, 5% persisters per cell): its prey were ×2.2 too few at 60 h,
  then within ×1.1 from 120 h; the run's hunters were only 0.55–0.65 of the model's from 120 h.
  The late prey match is flattered by the persister colony, so the run is left out of fitting
  (`Run.fit`).
- **In the pictures:** the persister colony stays as dense strips cut by Myxo streams; the other
  clumps thin out to scattered single cells; the hunters keep to a few highways.
- **Correction (mine):** B86 said the prey in candidates B and F died "mostly by starving". They
  were mostly eaten: from 60 h on, 6–26 kills against 1–3 starvation deaths per bio-h. The note
  there is marked.
- **The model under the B87 rules, ground ×0.7, efficiency 60%** (E. coli / Myxo):

  | Refill | At 150 h | Mean, 150–300 h |
  |---|---|---|
  | ÷20 (candidate B) | 692 / 120 | 511 / 54 |
  | ÷10 | 847 / 157 | 810 / 85 |
  | ÷8 | 901 / 179 | 929 / 105 |
  | ÷6 | 959 / 217 | 1,069 / 145 |

- **Cost:** 1.6 h of computing.
- **Waiting for the user:** how persisters should work, and the next run. **Settled in B88.**

Source: our run; Schink et al. (Basan lab); Finkel 2006.

**B88. Each E. coli draws its own 5% chance of being a long-term survivor at birth; daughters don't inherit it (the user's choice).** *16 Oct 2026*
- **Why:** the persister flag was inherited (my build manual), so one founder in 20 started a
  colony that never starves and the rest had none: half the prey at 85 bio-h in the B87 run. B40
  meant 5% of cells.
- **Backing:**
  - Viability of starving E. coli falls exponentially (Schink et al.), as expected if every cell
    faces the same risk per hour: which cell survives is chance, not family.
  - Heritable survival does exist, but it comes later and works differently. GASP mutants (the
    first an *rpoS* allele) take over cultures starved for 10 days or more, by growing faster on
    the amino acids released by dying cells, not by never dying (Zinser & Kolter 1999; Finkel
    2006).
  - Our 5% (Finkel's 1–10% survivors) stays a stand-in for that long-term phase.
- **Considered:**
  - No permanent survivors (only the measured exponential death): little difference over
    150 bio-h (a colony starving since 60 h keeps about 7% instead of 12%), but old clumps would
    vanish in longer runs.
  - Keeping it inherited: no backing.
- **Code:** `seeding.persister_flags`, used for founders and for both daughters at every division
  (`ecoli_body.divide`). A new test checks that 4,000 persister mothers give about 5% persister
  daughters. 86 tests pass.
- **Next (the user's choice):** candidate B (ground ×0.7, efficiency 60%) with refill ÷6 and ÷10
  side by side, seed 1, 150 bio-h (`checks/output/cand_B88_r6_150h`, `cand_B88_r10_150h`). They
  bracket the model's best refill (÷8). The model at 150 h: ÷6 about 960 E. coli and 220 Myxo; ÷10
  about 850 and 160. Not chosen: ÷8 on seeds 1 and 2; ÷20 again (the fix alone).

Source: the user's choice; Schink et al. (Basan lab); Zinser & Kolter 1999; Finkel 2006.

**Result of refill ÷6 and ÷10 with the B88 persisters (live world, seed 1, 150 bio-h, side by side;
`checks/output/cand_B88_r6_150h.png`, `cand_B88_r10_150h.png`; with the B87 run in
`cand_B88_compare.png`):** each meets one target at 150 bio-h, neither meets both, and the hunters
are still falling.

| | E. coli, 90–150 h | Myxo, 90–150 h | At 150 h | Model said at 150 h (fit of 16 Oct) |
|---|---|---|---|---|
| ÷6 | 1,177 (1,083–1,354), settled | 249 (137–387) | 1,089 / 137, hunters falling | 959 / 217 |
| ÷10 | 859 (690–1,147), falling slowly | 199 (92–336) | 690 / 93, both falling | 847 / 157 |

- **The first wave as before:** the prey peaked at 2,146 (÷6) and 1,912 (÷10) at 54–56 h, about
  twice the model. The hunters peaked at 394 and 338 at 83–86 h. Then came the famine: 243 and 225
  lysed, 35 and 31 spores by 150 h.
- **No immortal colony:** the prey end as scattered single cells and small clumps all over the
  ground (87% dormant), and the hunters keep to a few thick highways.
- **Where the prey go after 120 h** (`checks/prey_budget.py`, per bio-h):
  - ÷6: 24–26 born, 3–7 eaten, 21–24 starved, so balanced;
  - ÷10: 15–16 born, 5–7 eaten, 14–16 starved, a net fall of about 5.
- **Model refit** with the ÷6 run (17 Oct, `meanfield/fitted.json`; the fit of 16 Oct is kept as
  `fitted_2026-10-16.json`). It predicts the held-out ÷10 run within ×1.30 for prey and ×1.23 for
  hunters, about as well as its training runs.
- **The model's forecast past 150 h** (refit; ground ×0.7, efficiency 60%; E. coli / Myxo):

  | Refill | Mean, 150–300 h | At 300 h |
  |---|---|---|
  | ÷4 | 1,613 / 174 | 1,733 / 144 |
  | ÷6 | 1,314 / 101 | 1,315 / 77 |
  | ÷8 | 1,066 / 76 | 1,016 / 54 |
  | ÷10 | 898 / 63 | 820 / 43 |

  - **The hunters keep falling:** the famine removes starving hunters faster than the thin, dormant
    prey can feed new ones. Bare ground refills half-way in about 9 bio-days (÷6) to 14 bio-days
    (÷10), so nothing settles within a run.
  - **So the targets pull against each other:** with refill alone, about 150 hunters in the long
    run come only with about 1,600–1,700 prey.
- **What could move both (the model, roughly):** fewer hunter losses. With all hunter losses ×0.6
  (famine and starving to death together, a crude stand-in), refill ÷8–÷10 gives about 830–950
  prey and 160–190 hunters over 150–300 h, though the hunters still slide (95–122 by 300 h).
- **Cost:** 2.2 h (÷6) and 1.9 h (÷10) of computing, side by side.

Source: our runs; the model (B86).

**B89 (under test). Fewer famine deaths: 20% of starving hunters lyse instead of 70% (the user's choice), tested at refill ÷8 and ÷10.** *17 Oct 2026*
- **Why:** with refill alone, the targets pull against each other (B88 result). The model says
  fewer hunter losses would move both: fewer prey, because more hunters stay to eat them, and more
  hunters.
- **Biology:** how many developing cells lyse is disputed (B80). The classic counts are 60–80%;
  O'Connor & Zusman 1988 argued the counting methods were flawed and found that at least 80%
  survive. 20% lysis is that end of the range.
- **The fates become** 20% lysis (`famine_lysis_share` 0.2), 10% spores (unchanged), 70% rods.
  Rods stay on as starving cells: they can still hunt and feed, or starve to death when their store
  runs out (at a starving cell's cost, a newborn's 100 lasts about 80 bio-h).
- **The test:** candidate B (ground ×0.7, efficiency 60%) with refill ÷8 and ÷10, seed 1, 150 bio-h,
  side by side, as setting overrides; the defaults stay until it's judged
  (`checks/output/cand_B89_r8_150h`, `cand_B89_r10_150h`).
- **The model can't represent this change directly** (its hunter losses are one fitted rate), so
  these runs are left out of fitting. Its rough stand-in, all hunter losses ×0.6, gave about 830–950
  prey and 160–190 hunters over 150–300 h.
- **Not chosen:** adopting ÷6 as it is; running ÷6 to 300 bio-h first.

Source: the user's choice; O'Connor & Zusman 1988 (in `sources.md`, "Cell death during development");
the model (B86).

**Result of the famine test (live world, seed 1, 150 bio-h, side by side;
`checks/output/cand_B89_r8_150h.png`, `cand_B89_r10_150h.png`; with B88's ÷10 in `cand_B89_compare.png`):**
fewer famine deaths keep far more hunters for the same prey, and the first wave no longer overshoots.
The prey are in range; the hunters are about twice the target and falling slowly.

| | E. coli, 90–150 h | Myxo, 90–150 h | At 150 h | Lysed / spores / rods alive at 150 h |
|---|---|---|---|---|
| ÷10, lysis 70% (B88) | 859 (690–1,147) | 199 (92–336) | 690 / 93 | 225 / 31 / 12 |
| ÷10, lysis 20% | 850 (687–1,159) | 308 (250–340) | 692 / 250 | 66 / 42 / 99 |
| ÷8, lysis 20% | 1,116 (908–1,304) | 309 (287–320) | 914 / 287 | 32 / 26 / 26 |

- **The paired comparison at ÷10** (identical to B88's ÷10 until the first famine, at about 25 bio-h):
  the prey ended the same (692 against 690), and the hunters 2.7× as many (250 against 93).
  - The extra hunters mostly starve on the highways. After 90 h they kill a little more (5–16
    against 5–8 per bio-h), but most prey losses are still starvation (14–24 per bio-h).
- **No first-wave overshoot:** the prey peaked at 1,313 (÷10, 31 h) and 1,307 (÷8, 89 h), against
  1,900–2,150 in the B87 and B88 runs. Possibly because early arrivals that starve before finding
  prey now mostly stay on and hunt; with one seed, it may also be chance.
- **The hunters at 150 h are still falling** (÷10: 340 at 103 h → 250; ÷8: 320 → 287). Rods pay a
  starving cell's cost (a newborn's 100 lasts about 80 bio-h), so many will starve to death only
  after 150 h.
- **The model's rough stand-in** (all hunter losses ×0.6) forecast 916 / 312 (÷8) and 876 / 279
  (÷10) at 150 h; the runs gave 914 / 287 and 692 / 250. Over 150–300 h it forecasts about 950 prey
  and 190 hunters (÷8) and 830 and 160 (÷10), still sliding (95–122 hunters by 300 h).
- **Cost:** 2.1 h each, side by side.

Source: our runs; the model (B86).

**B90. Tuning stops; the live app and the videos are built (milestones 7 and 8). The submission deadline is today (the user).** *17 Oct 2026*
- **Why (the user):** "You will never reach any conclusion doing this", a judgement error of mine:
  each tuning run opened a new question while the deliverables, the app and the video, were
  unbuilt. Tuning further can be done by eye in the app.
- **The settings for the videos and the app's first preset ("tuned (B89)"):** ground ×0.7, refill ÷8,
  Myxo keep 60% of eaten food (uptake divided by it), famine lysis 20%: the closest to the targets
  so far (B89 result). My pick under the deadline, as setting overrides; `settings.py`'s defaults
  are unchanged, and the app's preset choice switches back to them.
- **The app** (`app_live.py`, `ui_widgets.py`, `drawing.py`): the live world on the left, controls on
  the right.
  - **Live controls:** biology speed-up, pull toward prey smell, steps per frame, ground updates.
  - **On Reset:** preset, starting colonies, how long a full store lasts, the arriving Myxo's store,
    seed.
  - **Buttons:** Run/Pause, Reset, Save settings, and Record video (60 bio-h of the current settings
    in the background).
  - **Drawing:** ground (brown = rich), prey remains (mauve), slime (grey), E. coli (magenta; dormant
    darker), Myxo (green, brighter = better fed; scouts yellow; killing cells with a white rim),
    spores, a scale bar, a legend and the counts.
- **The recorder** (`run_record.py`): draws a frame every few real minutes, saves frames and a
  checkpoint (so a stopped recording carries on), and joins the frames into an MP4 at the end
  (`--encode-only` makes one from the frames so far). Two scenes:
  - **the whole live world**, 100 bio-h (`videos/predation_100h.mp4`; 2,401 frames at 30 fps, 80 s);
  - **close-ups of one colony** grown alone for 10 bio-h (470 cells, default settings), then four
    drops of Myxo at its edge (the B76 invasion test, with today's rules), 7.5 bio-h, zoomed in:
    - 80 Myxo (`videos/closeup_invasion.mp4`): they cut a channel through the colony and kill at
      its edges, but don't outpace its growth (470 → 571 E. coli);
    - 240 Myxo (`videos/closeup_240.mp4`): the colony is eaten (470 → 129 E. coli in 5 bio-h, up to
      10 hunters killing at once), leaving a field of prey remains with the hunters lined up across
      it and one surviving corner.
  - **Encoding:** `--quality 5–6` keeps a 30 s close-up at 9–15 MB (quality 8: 40–66 MB).
- **Not done, for lack of time:** the 500 µm record world (B2; it would take many hours); the final
  look (B41, open).

Source: the user's call; our runs (B89).

**B91. The app's layout and settings, and a wider video (the user's design).** *17 Oct 2026*
- **Runs live**, at a chosen speed: ×1 is real time (cells glide at their real 4 µm/min), up to ×600
  or as fast as the computer can.
- **Layout:** the world on the left, the cell counts against hours of biology below it (E. coli,
  dormant E. coli, M. xanthus, starving Myxo), and the main settings on the right. A Settings button
  at the world's top right opens the rest.
- **Every setting has one place** (`app_params.py`):
  - **main** (right panel): the major, tunable settings. Myxo food kept (with uptake divided by it,
    B85), ground refill, pull toward prey smell, smell leaked by E. coli, starving costs, the
    killer's share and scouting change the running world. Ground richness, starting colonies, new
    founders, arriving Myxo and the seed apply to the next world.
  - **advanced** (Settings): the other tuned or assumed settings.
  - **switches** (Settings): ten rules that can be turned off, among them killing on the biology
    clock, gliding over prey, the famine, scouts, the smells, rippling, new founders and E. coli
    starving.
  - **where studies disagree** (Settings), with the recommended option starred:
    - famine lysis: 20% ★ (O'Connor & Zusman 1988) or 70% (classic counts);
    - the rippling trigger: contact with prey ★ (Berleman 2006) or remains only (Saulnier 2026);
    - the stringent onset: 30 bio-min ★ (Manoil & Kaiser 1980) or 3 bio-h (Harris 1998);
    - starving Myxo speed: 1.5× ★ (Jelsbak 2002) or unchanged;
    - E. coli persisters: 5% ★ (Finkel 2006) or none (Schink et al.).
  - **fixed** (Settings, shown but not editable): measured or from the paper, such as the Myxo body,
    reversal and alignment rules (Saulnier 2026), E. coli size and growth (BioNumbers), starvation
    death (Schink), killing (Seef 2021), the 5.4 h generation and the famine timing (Lee 2012).
- **Recommended** = the B89 settings with every starred option, the app's starting point and its
  "Recommended" button. My reading of "the most optimal": the settings that came closest to the
  targets.
- **A wider video (the user):** with one colony in the middle, the E. coli covered too little of the
  frame. The new world video is 250 µm across (2.8× the area) with 10 starting colonies, founders
  and arriving Myxo scaled to the area (a founder every 130 bio-min; 14 groups of 20 and 28 single
  cells), drawn at 1,280 px. The cells are 5 px/µm instead of 7, so the frame holds more of them
  (`videos/world250_60h.mp4`).
- **Checked:** headless runs of the app with every kind of control driven by synthetic clicks (a live
  slider, a next-world slider, a switch off and on, an evidence option), and screenshots of both
  screens.

Source: the user's design; the sources named.

**B92. Reversals made visible (the user: "reversal isn't explicitly visible from the video").** *17 Oct 2026*
- **The leading pole** of every Myxo is drawn as a white dot, like MglA, which marks the leading pole
  and moves to the other end when a cell reverses. A reversal swaps the cell's disc order
  (`myxo_body.reverse`), so the dot jumps to the other end.
- **Orange for 15 s after a reversal** (`drawing.REVERSAL_FLASH`), so reversals stand out in dense
  streams.
- **Two new close-ups at the paper's own test settings** (65 µm box, A3; no prey, no scouts, no smell,
  slime that never fades, biology at real speed), with frames 3 s apart (20 real min in about 20 s):
  - **swarming:** 370 cells on bare ground (`videos/swarm_reversals.mp4`);
  - **rippling:** 1,000 cells on prey remains, ripple axis left to right (`videos/ripple_reversals.mp4`).
  The top line counts the cells that reversed in the last minute.
- **Why the population videos couldn't show it:** at 5–7 px/µm and 15 s between frames, a cell's
  ends are a few pixels apart and it reverses every few frames. The wide video was already
  recording with the old drawing, so its cells have no pole dot.

Source: the user's request; Saulnier 2026 (the test boxes); MglA at the leading pole (cell biology
reference, Part A).

**B93. The project is called MyxoHunt: "swarming, hunting and rippling of M. xanthus" (the user's choice).** *17 Oct 2026*
- **Where:** the README title, the app's window and panel; the GitHub repository will be `myxohunt`.
- **Considered:** WolfPack (after "wolf-pack" feeding, Berleman & Kirby 2009), Swarm & Ripple, and the
  working name Motility Sim.

Source: the user's choice.

**B94. MyxoHunt runs live in the browser, with all its sliders, as a static site Vercel can host (the user: "I want the live sim to be run on the app, with sliders").** *17 Oct 2026*
- **How:** Vercel only serves files and short requests, so the simulation runs in the visitor's
  browser.
  - **Pyodide:** Python compiled for the browser, with numpy and scipy; it runs the same engine as
    the desktop app, unchanged.
  - **The page** (`web/`): a background thread (`worker.js`) steps the world and sends frames, and the
    page (`app.js`) draws the world, the counts graph and the controls.
  - **The controls** come from the same catalogue (`app_params.py`) through
    `predation-sim/web_controller.py`: main settings, Settings panel, switches, evidence options
    with the recommended starred, fixed values.
  - `python web/build.py` copies the 21 simulation files the page needs into `web/py/`.
- **A browser-only fix:** the browser's Python is 32-bit, and `np.bincount` there refuses 64-bit
  indices. Three call sites now cast to the platform's index type (`contacts`, `myxo_alignment`,
  `myxo_energy`). On a PC nothing changes: 86 tests pass, the equivalence tests are still exact.
- **Speed, measured:**
  - about 27 ms of computing per 0.3 s step in the browser, against about 10–18 ms natively, so
    about ×8–10 real time at most;
  - the fixed part is the paper's 50 spring passes per step (`relax_springs`), which stay as
    validated;
  - so the biology speed-up moved to the main panel (default ×10; ×30 grows colonies 3× faster on
    screen).
- **Limits:** the first visit downloads about 25 MB (Python, numpy, scipy); no video recording in the
  browser; more cells make it slower.
- **Deploying:** import the GitHub repo in Vercel with the root directory `web` (framework "Other",
  no build command). Every push redeploys it.

Source: the user's request; Pyodide (pyodide.org); our measurements.

**B96. The web app gets scenes and zoom, so reversals and rippling can be seen live (the user: "the king of the project is barely observable").** *17 Oct 2026*
- **Why:** in the predation world only 2–3 hunters kill at a time (a kill lasts 2 bio-min, about 4 s
  on screen at ×30), the pole dots are too small to see reversals, and rippling almost never forms:
  hunters spread along slime highways at about 0.01 cells/µm², far below the paper's rippling
  density of 0.24. That last one is a model weakness, addressed separately by B95 (another
  session).
- **Scenes** (`web_controller.SCENES`):
  - predation world (as before);
  - colony attack: one colony grown 50 real min on full ground, then four drops of 60 Myxo at its
    edge;
  - swarming: the paper's 65 µm box with 370 cells;
  - rippling: the paper's box with 1,000 cells on prey remains.
  - The last three start from states pre-run on a PC (`web/make_scenes.py`, 30–50 real min), because
    they'd take minutes to form in the browser. Settings pickled before a field existed load with
    its default (`Settings.__setstate__`, B95).
- **Zoom:** mouse wheel to zoom, drag to move, double-click to fit (wrap-around safe). The attack
  scene opens on the colony.
- **Build:** `python web/build.py --head` copies the core files as last committed, so another
  session's unfinished edits don't ship.
- **Also:** the 250 µm world video finished (`videos/world250_60h.mp4`, 60 bio-h, 4,400 E. coli and
  1,372 Myxo at the end).

Source: the user's request; Saulnier 2026 (the test boxes).

**B95. Hunters reach and enter colonies: stream leaders, scouts and cells touching prey steer toward the prey smell, and scouts keep going until they find prey (the user's design).** *17 Oct 2026*
- **Why (the user):** the lead cell should follow the food and the others its slime; scouts should
  hunt until they find prey; hunters were only grazing colony edges, and rippling was barely visible.
  The smell only biased reversals, so on a trail the trail always won (B63, B66).
- **The rules** (each a setting, also in the app):
  - **Stream leaders**, followers that sense no slime ahead, turn toward the prey smell:
    Δθ = `smell_steer` · sin(φ − θ) · Δt, with φ pointing up the attractant at the head (default
    3/min). Followers keep taking their slime, so a stream follows its leader.
  - **Scouts** add the same turn to their random wandering.
  - **Invasion on contact** (`invade_on_contact`): a cell touching a living E. coli stops following
    slime and steers up the smell, into the colony, laying ordinary slime that others follow.
    A-motile cells penetrate colonies and groups follow them (Seef 2021).
  - **Scout spells** end when the scout finds prey food or starts starving (`scout_random_end` off;
    B83's random end stays an option). Starving cells don't start scouting (`stringent_scouts` off).
  - **Caps (the user's):** after a spell a cell rests 60 real min before it may scout again
    (`scout_rest_time`), and at most 10% of all cells scout at once (`scout_max_share`).
- **Backing:**
  - **Backed:** groups follow pioneers into prey (Seef 2021); lone A-motile foragers exist and cells
    switch between foraging and swarms (Rombouts 2023); starving cells move up the lipid attractant
    (Kearns 2001).
  - **Assumed:** steering. Measured Myxo chemotaxis works by biasing reversals (Kearns & Shimkets
    1998), and long-range attraction to living prey is unproven (B32). No study shows that low food
    or starvation triggers scouting; the spell rules and caps are ours. Speeds stay measured: scouts
    1.1×, starving loners 1.5× (B80, B75).
- **Test** (one colony grown alone for 10 bio-h, 470 E. coli, then four drops of 20 Myxo at its edge;
  5 bio-h; seed 1; values every 5 real min):

  | | E. coli | Rippling | Deep inside | With the colony | Myxo at the end |
  |---|---|---|---|---|---|
  | Old rules | 470 → 495 | 4–8 | 0–5 | 48 → 31 | 87 |
  | B95 | 470 → 161 | 9 → 35 | up to 13 | 72 → 89 | 97 |

  The hunters stay, enter and eat the colony, and rippling rises as they pack on its remains. One
  seed; the full predation world is not yet re-run.
- **Unchanged without prey smell:** the new turns are zero where the smell is flat, so the
  tick-for-tick equivalence with the paper's model stays exact.
- **Compatibility:** settings and worlds saved before B95 (checkpoints, the web scenes of B96) load
  with the new fields at their defaults (`Settings.__setstate__`, `myxo_modes.resting`).
- **Tests:** 89 pass (new: scouts stay until prey, rest afterwards, never exceed the cap; a
  starving scout stops unless allowed; the smell turn points up the smell and is zero where flat).

Source: the user's design; Seef 2021; Rombouts 2023; Kearns 2001; Kearns & Shimkets 1998; our test.

**B97. The review's recommendations, adopted by the user (23 Oct 2026): fix the tools, count events directly, let starving cells scout, lock the speed-up at 10×, and judge settings by a fixed pass rule on 4 seeds.** *23 Oct 2026*
- **Why:** an independent review (`docs/review-2026-10-23.md`) found that the tools, not the core
  model, had failed: single-seed comparisons were within chance (the two ÷10 runs of B88 and B89
  differed by 2–3 cell fates yet their prey ended up to 1.6× apart), the mean-field model behind
  B86–B89 created hunters from nothing, B95 had switched scouting off by accident, and the shipped
  Recommended preset had never been run as a population. The user chose every recommended option
  (D1–D6).
- **Scouting (D1):** under B95 a cell at zero prey food was past `stringent_delay` (30 bio-min,
  3 real min at 10×) almost at once and lost its scouting, so only 0.06% of cells scouted (review C3).
  The user first chose to move the block to `behaviour_delay` (2 bio-h; starvation recognition takes
  "the first few hours", Harris 1998). Tested in three 6 bio-h branches from the 100 h checkpoint
  each (target 3–10% scouts):

  | Rule | Scouts | Kills per hunter per bio-h |
  |---|---|---|
  | Before (B95) | 0.06% | 0.03–0.04 |
  | Block after 2 bio-h of starving | 0.7–1.2% | 0.06–0.08 |
  | The same with a 1 bio-h rest instead of 6 | 0.7–1.6% | 0.06–0.08 |
  | **Starving cells may scout** (`stringent_scouts` on) | **6.4–6.8%** | **0.11–0.13** |

  The 2 bio-h block fell short because most hunters on the highways have starved longer than that;
  the rest time doesn't matter. **The user chose "starving cells may scout"**, reversing B95's
  choice. Backing in direction: starving cells glide faster alone (Jelsbak 2002) and follow the lipid
  attractant (Kearns 2001); no study shows that starvation stops scouting. The 2 bio-h block stays
  as the switch's "off" setting. `myxo_modes.update_scouts`, `settings.stringent_scouts`.
- **Speed-up locked at 10× (D2):** slime is laid per real tick but fades per bio-minute, and scout
  timers run in real minutes, so changing the speed-up changes trail strength and scouting too
  (review C10). The B86 speed-up test is therefore confounded and doesn't show that lower speed-ups
  hunt worse. The slider is removed from both apps and the speed-up is listed as fixed.
- **Direct counters (`counters.py`):** births, founders, wakes, starvation deaths, kills, bursts,
  touches, pauses, scouting, clock resets, famine fates, and food and store by source and sink, as
  running totals in every stats row. A new test checks that food, scraps and the Myxo store close
  their ledgers to rounding. `checks/prey_budget.py`'s inferred numbers are no longer needed.
- **Tool fixes:** `check_populations.py` reads `False`/`0` as off (it read them as on), refuses to
  resume a checkpoint made with another seed or settings, and writes checkpoints atomically; the
  founder switch on a running world no longer drops a founder at every ground update; the
  `wake_threshold` comment no longer calls 0.2 the Monod half-speed level (that is 0.14).
- **The pass rule (D5, D6; `checks/judge_band.py`):** a seed passes over 150–300 bio-h if its means
  are 700–1,000 E. coli and 100–220 Myxo, at least 80% of hourly samples lie within 500–1,300 and
  75–300, it never drops below 210 and 45, and neither drifts more than 20% of its mean per
  100 bio-h. A setting passes if 3 of 4 seeds pass. Rippling, killing, starving and scouting are
  reported, not judged (D6).
- **Not changed (D4):** persisters stay immortal; their share is now counted, and slow persister
  death is offered only if they exceed 20% of the prey.
- **Next (D5):** the baseline: the Recommended preset with these fixes, seeds 1–4 to 300 bio-h, and
  prey only (no Myxo) seeds 1–2 to 250 bio-h. One lever (D3) is moved only if the baseline fails.
- **Checked by an independent code review** (three reviewers, each finding verified): the browser
  build was missing `counters.py`, a restart that left out an override wasn't caught, Windows could
  refuse the atomic file swap while another program had the file open, Myxo dropped in directly
  weren't counted, and the founder switch re-armed badly. All fixed (`seeding.add_myxo`,
  `check_populations.swap_in`).
- **Tests:** 96 pass (7 new); the tick-for-tick equivalence with the paper's model is still exact.

Source: the review of 23 Oct 2026; the user's choices; Harris 1998; Jelsbak 2002; Kearns 2001.

**B98. The baseline fails the band, and tuning stops for good (the user's choice): the Recommended preset with the B97 rules holds the prey far below the band while the hunters shrink slowly.** *24 Oct 2026*
- **The baseline** (B97's step 5): the Recommended preset with starving cells scouting, live world,
  seeds 1–4 meant to run to 300 bio-h, and prey only (no Myxo) seeds 1–2 to 250 bio-h, six runs in
  parallel (`checks/run_baseline.sh`; picture `checks/output/base_rec_compare.png`, drawn by
  `checks/plot_baseline.py`).
- **Verdict (`checks/judge_band.py`): 0 of 4 seeds pass.** The runs were stopped at 195–265 bio-h,
  once every seed had spent more than 20% of the 150–300 h window outside 500–1,300 E. coli, so none
  could pass whatever came after.

  | Seed | E. coli peak | Myxo peak | E. coli, 150 h to stop | Myxo, 150 h to stop | Myxo drift per 100 h |
  |---|---|---|---|---|---|
  | 1 | 1,637 (59 h) | 433 (92 h) | 340 (min 288) | 252 | −43% |
  | 2 | 2,040 (81 h) | 366 (112 h) | 311 (min 262) | 214 | −46% |
  | 3 | 1,580 (52 h) | 425 (85 h) | 222 (min 184) | 243 | −47% |
  | 4 | 1,783 (53 h) | 555 (74 h) | 92 (min 60) | 331 | −46% |
  | Target | | | 700–1,000 | 100–220 | under 20% |

- **What happens, from the direct counters (per bio-h, after 150 h):**
  - **The hunters hold the prey down.** They kill 7–13 E. coli per bio-h out of 10–17 births;
    another 1–6 starve. Scouting (6–10% of hunters, B97) is what changed: under B89 the prey sat at
    about 1,100.
  - **But the hunters barely grow.** 95–98% of them are starving, so they divide only 0.02–0.12 times
    per bio-h, while the famine takes 0.6–1.2 by lysis and 0.3–0.5 as spores. None starve to death:
    they reach their famine first. So they shrink only slowly, about 45% per 100 bio-h.
  - **They linger as starving rods.** With famine lysis at 20% (B89), 70% of famine cells stay on as
    rods that keep hunting for days (515–665 rod fates per run).
  - **The result is a deep, slow cycle,** not a band: prey crash below it while the hunters take
    hundreds of bio-hours to come down.
- **Prey alone settle above the band:** 1,113–1,187 E. coli at 250 bio-h (peaks about 3,000 at
  46–56 h), 89–90% dormant, 35–37% of them immortal persisters. With hunters, persisters are only
  3–9% of the prey, so slow persister death (D4) isn't triggered for the runs that matter.
- **The look (reported, not judged, D6):** essentially no rippling (0 cells on average), 0.1–0.2% of
  hunters in a killing pause, about 9.5% scouting.
- **What theory suggests, untested:** a higher hunter death rate raises the prey's balance level and
  lowers the hunters' (Rosenzweig & MacArthur 1963, B85). The agreed lever (D3) was the famine lysis
  share back toward the classic 60–80% (the app's other evidence option, 70%), one round on 4 seeds.
  Measuring the hunter balance point in short thinning branches first was the alternative.
- **The user's decision (24 Oct 2026): stop tuning and document.** The Recommended preset stays as it
  is in both apps; it does not hold the band, and the README says so.
- **Cost:** about 16 h of computing for the six runs, plus about 8 h lost when the laptop slept and
  the runs stopped (they resumed from their checkpoints).

Source: our runs; the user's choice; Rosenzweig & MacArthur 1963.

**B99 (under test). A branch test of famine lysis 70% from the stopped baseline states (the user's choice: a quick test before any full round).** *25 Oct 2026*
- **Why:** B98 ended with its theory untested. The user wasn't happy with that ending and chose a cheap
  test first: does a higher hunter death rate raise the prey and lower the hunters (Rosenzweig &
  MacArthur 1963)?
- **How** (`checks/branch_test.py`, `run_branches.sh`, `compare_branches.py`): each baseline seed was
  carried on from its last checkpoint (195–265 bio-h) for 40 bio-h, twice from the very same state and
  random numbers. One branch used famine lysis 70% (classic counts 60–80%, Wireman & Dworkin 1977; B80)
  and the other 20%, the control. Any difference between the two comes from the change. Picture:
  `checks/output/branch_compare.png`.

  | Seed | At the branch | +40 h, lysis 70% | +40 h, control (20%) |
  |---|---|---|---|
  | 1 | 295 / 207 | 461 / 111 | 271 / 183 |
  | 2 | 404 / 166 | 510 / 104 | 444 / 142 |
  | 3 | 229 / 198 | 464 / 120 | 438 / 171 |
  | 4 | 126 / 301 | 311 / 170 | 226 / 262 |
  | Target | | 700–1,000 / 100–220 | |

  (E. coli / Myxo.)
- **The hunters respond clearly:** in every seed they ended 27–39% below the control, inside their
  band.
- **The prey respond weakly:** they ended 6–70% above the control (seed 3 within chance), still at
  311–510, far below 700. They were rising by about 2–7 per bio-h at the end.
- **Why the prey move so little (direct counters, per bio-h):** kills hardly depend on hunter numbers
  (8–11 under 70% vs 10–11 in the control). A few dozen hunters at the prey do the killing; the
  starving majority on the highways doesn't. Kills fell by only 0–27% (mean about 13%).
- **Why the hunters can't grow back:**
  - 89–97% of them are starving. They take in 465–625 store units per bio-h, and 78–96% of that goes
    to running costs.
  - They're born at only 0.05–0.30 per bio-h, against 1.9–3.4 famine losses under 70%, so at +40 h
    they're still falling by 1–3 per bio-h.
  - The cause is in the rules: starving cells can't divide (B83), and a cell eating thin prey food (1–3
    units within reach) never ends its starvation. So food becomes upkeep, not offspring.
- **Open:** whether the prey reach 700 before the hunters fall below 45. **Answered below.**
- **Cost:** about 1 h of computing for the 8 branches, all in parallel.
- **Script change:** `branch_test.py` now keeps its final checkpoint, so a branch can be extended. It
  refuses to resume a branch with different settings.

**Result of the long branches (the user's choice: the four 70% branches carried on to +100 bio-h,
`checks/run_branches_long.sh`; the first 40 h repeated the short branches exactly):** the system settles,
a little below the band.

| Seed | +60 to +100 h: E. coli mean (range) | Myxo mean (range) | Myxo born / lost per bio-h |
|---|---|---|---|
| 1 | 526 (487–565) | 100 (96–105) | 0.53 / 0.45 |
| 2 | 546 (501–585) | 84 (80–93) | 0.53 / 0.81 |
| 3 | 570 (541–606) | 98 (92–109) | 0.53 / 0.83 |
| 4 | 629 (405–814), still rising | 125 (117–139), rising | 0.70 / 0.83 |
| Band | 700–1,000 (wide 500–1,300) | 100–220 (wide 75–300) | |

- **The hunters stop falling at about 85–100 in seeds 1–3.** Once fewer, they're better fed: 73–79%
  starving (89–97% before), and they're born 0.5–0.7 times per bio-h (0.05–0.3 before), close to
  their losses. So the B99 point that "food becomes upkeep, not offspring" holds for a crowded,
  starving population; it eases as the hunters thin out, and a balance point exists.
- **The prey level off at about 530–570 in seeds 1–3.** They're now held down by hunger as much as
  by the hunters: 10–11 starve per bio-h against 7–10 eaten.
- **Seed 4** started its branch earlier (195 bio-h), with more hunters and fewer prey. It is still
  climbing: 812 E. coli and 134 Myxo at +100 h.
- **Against the pass rule (informally;** the rule's window is 150–300 bio-h of a fresh run): seeds 1–3
  would meet the wide bands, minima and probably the drift limit, but fail both means. The prey are
  about 150–170 short and the hunters 0–16 short.
- **Cost:** about 1.1 h of computing for the four, in parallel.

Source: our runs; Rosenzweig & MacArthur 1963; Wireman & Dworkin 1977.

**B100 (under test). Faster ground refill on top of lysis 70%, branch-tested from the +100 h states (the user's choice).** *25 Oct 2026*
- **Why:** under lysis 70% both counts settle a little below their band means (B99). The prey are now
  limited by hunger about as much as by the hunters, so more prey food should lift the prey, and with
  them the hunters. In the textbook model a richer supply raises the hunters (Rosenzweig & MacArthur
  1963).
- **The test** (`checks/run_refill.sh`, `compare_refill.py`): from each seed's 70% branch at +100 bio-h,
  60 bio-h more with ground refill ÷6 (`nutrient_regrow_rate` 1/18,000 per bio-min) and ÷4 (1/12,000),
  against ÷8 (1/24,000, the Recommended value) carried on unchanged. All arms start from the same state
  and random numbers. That makes 12 runs in parallel.
- **The refill is tuned, not measured** (B68, B85).
- **Not testable this way:** ground richness. It is set once, when the world is made
  (`seeding.py`).
- **Not chosen:** a full round at 70% now (expected to fail on both means); accepting the balance at
  about 550 / 95.

**Result of the refill test (`checks/output/refill_compare.png`):** refill ÷6 brings both counts to the
lower edge of the band; ÷4 overshoots the prey, and its hunters are still booming.

| Seed | ÷8 (control), last 30 h | ÷6, last 30 h | ÷4, last 30 h |
|---|---|---|---|
| 1 | 585 / 96 | 711 / 111, both rising | 1,051 / 146, hunters rising fast |
| 2 | 543 / 86 | 695 / 96, both rising | 1,111 / 117, hunters rising fast |
| 3 | 503 / 100 | 697 / 108, both rising | 1,050 / 135, hunters rising fast |
| 4 | 641 / 181, prey falling | 791 / 192, prey falling | 1,047 / 235, above the hunter band |
| Band | 700–1,000 / 100–220 | | |

(E. coli / Myxo.)
- **More food lifts both, as the textbook guide predicts.** Prey births per bio-h went from 18–24
  (÷8) to 24–30 (÷6) and 36–43 (÷4). Hunter births went from 0.45–1.0 to 0.77–1.4 and 1.2–2.1, while
  famine losses fell, so the hunters grow.
- **÷6 is not settled at +60 h.** In seeds 1–3 the hunters were still gaining about 0.3–0.5 per bio-h.
  Seed 4 is the one seed in a visible cycle: its hunters reached about 200, and its prey were being
  eaten down (883 → 673) in every arm.
- **÷4 is heading into a boom.** The prey sit at about 1,050–1,190, and the hunters are born 6–15 times
  faster than they die, so the prey will likely be pulled down next.
- **Against the means of the pass rule (informally, last 30 bio-h):** at ÷6, seeds 1 and 4 meet both
  means. Seeds 2 and 3 miss by a hair: 695 and 697 E. coli, and seed 2 has 96 Myxo.
- **Cost:** about 1.6–1.8 h of computing for the 12, in parallel.

Source: our runs; Rosenzweig & MacArthur 1963.

**B101 (under test). The full round for famine lysis 70% + refill ÷6 (the user's choice).** *25 Oct 2026*
- **Why:** the branch tests (B99, B100) put both counts at the band's lower edge. Only fresh runs,
  judged by the B97 pass rule over 150–300 bio-h, can say whether the setting passes. A fresh run
  also has its own first wave, which the branches skipped.
- **The round** (`checks/run_round_r6.sh`): the Recommended preset with those two changes, seeds 1–4
  to 300 bio-h, all in parallel, judged by `checks/judge_band.py` at the end. Expected to take about
  15–20 h of computing with the laptop awake.
- **Not chosen:** extending the branches first; adopting the setting without a full round.

**Result of the full round (`checks/output/r6_compare.png`, drawn by `checks/plot_round.py`; verdict
from `checks/judge_band.py`): 1 of 4 seeds pass, so the setting doesn't pass (3 needed).** After the first
wave, both populations hold steady in a narrow range: the hunters sit inside their band in every seed,
and the prey sit just under theirs.

| Seed | E. coli mean, 150–300 h (min) | Myxo mean (min) | Drift per 100 h, E / H | Fails on |
|---|---|---|---|---|
| 1 | 541 (389) | 153 (128) | +9% / +2% | prey mean; only 73% of hours in 500–1,300 |
| 2 | 658 (291) | 139 (97) | +22% / +39% | prey mean; drift |
| 3 | 667 (444) | 131 (117) | +11% / −10% | prey mean |
| 4 | **752** (572) | **151** (129) | +11% / +20% | — (passes) |
| Band | 700–1,000 | 100–220 | under ±20% | |

- **Against the baseline (B98):** the prey means rose from 92–340 to 541–752, and the hunter means fell
  from 214–331 to 131–153. The B98 baseline was a slow slide; this round holds steady.
- **The first wave is still large:** prey peaked at 1,508–2,212 (44–63 bio-h) and hunters at 465–527
  (76–94 bio-h), then both came down by about 150 bio-h.
- **Per bio-h over 150–300 h (direct counters):** 25–28 E. coli born, 11–14 eaten and 10–15 starved;
  0.66–0.81 hunters born against 0.5–1.0 famine lyses and about 0.1 spores. No hunter starved to
  death. So the prey are held down about equally by the hunters and by hunger.
- **The look (reported, not judged):** essentially no rippling (0–0.1 cells on average), 0.3–0.4% of
  hunters killing at a time, 5–6% scouting, 69–82% starving. The rippling problem of B96 and B98
  remains.
- **The prey are still drifting up slowly** (+9 to +22% per 100 bio-h), so a longer run might reach
  the band. Seed 2 fails on drift for that reason.
- **Cost:** about 8.4 h of computing for the four, in parallel. My estimate had been 15–20 h.

Source: our runs.

**B102. The Recommended preset becomes famine lysis 70% + ground refill ÷6 in both apps (the user's choice).** *25 Oct 2026*
- **Why:** it doesn't pass the band (B101, 1 of 4 seeds), but it is far closer than the old preset.
  The old one (lysis 20%, refill ÷8) crashed the prey to about 100–350 (B98). The new one holds both
  populations steady, with the hunters in their band and the prey just under theirs.
- **Changes** (`app_params.py`):
  - `RECOMMENDED` refill ÷8 → ÷6;
  - the ★ on famine lysis moves from 20% (O'Connor & Zusman 1988) to 70% (the classic counts of
    60–80%, Wireman & Dworkin 1977). Both options stay selectable. The dispute itself is unresolved;
    70% is the choice that holds the populations closest to the band.
  - Unchanged: ground ×0.7, efficiency 60%, and the other ★ options.
- **Also:** `settings.py` defaults are unchanged (the preset is overrides); the web app is rebuilt;
  the README's known-limitation section is updated. 96 tests pass.

Source: the user's choice; B101; Wireman & Dworkin 1977; O'Connor & Zusman 1988.

**B103 (under test). A full round at refill ÷5 to lift the prey into the band (the user's choice).** *25 Oct 2026*
- **Why:** at ÷6 the prey sit 33–160 cells under the band's 700 mean. In the branch test (B100), ÷4
  overshot the prey (about 1,050–1,110) and set off a hunter boom. ÷5 lies between the two.
- **The round** (`checks/run_round_r5.sh`): the new Recommended preset (B102) with refill ÷5
  (`nutrient_regrow_rate` 1/15,000 per bio-min), seeds 1–4 to 300 bio-h, judged by
  `checks/judge_band.py`. About 8–9 h of computing.
- **If it passes,** ÷5 becomes the preset.

Source: the user's choice; B100, B101.

### Build progress
- **Milestone 1 (skeleton) done, 10 Oct 2026:** `settings.py`, `state.py`, `geometry.py`,
  `grids.py` and three test files in `predation-sim/`; 21 tests pass.
- **Milestone 2 (E. coli colonies), 10 Oct 2026, awaiting the user's look at the picture:**
  - **Files:** `seeding.py` (ground, E. coli), `ecoli_body.py`, `ecoli_life.py`, `contacts.py`,
    `predation.py` (lysis only), `fields_update.py`, `colonies.py`, `stats.py`, `engine.py`,
    and `checks/check_ecoli_growth.py`.
  - **Tests:** 29 pass.
  - **Result:** `checks/output/ecoli_growth.png`: 2 colonies of ~770 cells at 500 bio-min,
    with dormant centres and a growing rim. The user confirmed it looks right.
- **Milestone 3 (Myxo swarming among colonies), 10 Oct 2026:**
  - **Files:** `myxo_body.py`, `myxo_alignment.py`, `myxo_reversals.py`, Myxo seeding, and the
    full fast-step order in `engine.py` (killing still to come).
  - **Tests:** 38 pass, including the tick-for-tick equivalence with the reproduction (A13).
  - **Comparison run:** `checks/output/swarming_vs_reproduction.png`, within run-to-run noise
    (A12).
  - **Live world picture:** `checks/output/live_world_m3.png`.
- **Milestone 4 (killing on contact), 10 Oct 2026, mechanics done and verified:**
  - **Code:** pauses, kills and bursting in `predation.py`; step 9 in `engine.py`.
  - **Tests:** 43 pass. Pause rate, 80% kill success, ID bookkeeping, bursting into food,
    smell and wall, and paused cells standing still are all checked.
  - **Check:** `checks/check_predation.py` with `predation_attack_young.png` and
    `predation_attack_mature.png`.
  - **Not yet:** the predator–prey balance (B58) and Myxo staying at prey (B59) are open until
    milestone 6.
- **Milestone 6 (energy), done 10–11 Oct 2026, before milestone 5 (the user's choice):**
  - **Code:** `myxo_energy.py` (upkeep, uptake shared by hunger, reserve, division, death),
    plus B62–B68 (staying rules, colony smell, killer eats first, absorption ceiling,
    predation on the biology clock, scouts).
  - **Tests:** 53 pass.
  - **Open:** the full cycle doesn't complete yet (B69).
- **Milestone 5 (rippling and fading), done 11 Oct 2026:**
  - **Equivalence:** on prey matrix with axis 0, the engine matches the reproduction's
    rippling mode tick for tick (`tests/test_equivalence.py`).
  - **Fading check (`checks/check_ripple_fading.py`, `checks/output/ripple_fading.png`):** 300
    Myxo on a 25 µm matrix disc with its axis at 30° line up within hours (alignment with the
    axis 0.99).
  - **Shrinking and leaving:** cells cross the disc edge and join swarming streams, the matrix
    fades (half-life 12 bio-h), and by 25 bio-h no cell ripples. The swarm trails keep the old
    ripple direction for a while.
  - **Tests:** 54 pass.
- **B70–B71 (scout and stringent modes), 11 Oct 2026:** `myxo_modes.py` (new), eating within
  2 µm (`grids.disc_squares`), and a second slime layer for scouts (`fields.eps_scout`).
  59 tests pass.
- **B72, 11 Oct 2026:** per-cell smell boost (`myxo_modes.smell_factors`, used by
  `chemotaxis_factor`), stringent-only food affinity, and seeding clearance for every cell
  (`seeding.seed_clearance`). 61 tests pass.
- **B73 (energy bug fix), 11 Oct 2026:** `grids.diffuse` never returns negatives;
  `myxo_energy.share_food` and `food_demand` treat negative food as 0. 63 tests pass. The
  population runs are being redone as `checks/output/b73_*`.
- **B74–B75, 11 Oct 2026:**
  - Ghost smell and slow food fade (`fields_update`); 5 × 50 + 10 seeds by default.
  - The doubling store (`myxo_energy`); a starvation clock and crowding-dependent speed
    (`myxo_modes`, `fields_update.update_crowding`).
  - New E. coli founders (`seeding.add_due_founder`).
  - 67 tests pass.
- **B76, 11 Oct 2026:**
  - Myxo crawl over prey (`contacts.shoving_pairs`).
  - Living prey count toward the ripple trigger, and the ripple direction is averaged
    (`fields_update.smooth_prey_material`, `fields.axis_c_smooth`/`axis_s_smooth`).
  - Contact reversals off; the killer keeps 25%; a rippling count in the stats.
  - `checks/check_penetration.py`. 69 tests pass.
- **B77–B78, 11 Oct 2026:**
  - `checks/check_staying.py` (B77) and the at-prey count in the stats.
  - Local ground, whole-body feeding (`ecoli_life`) and random ground fill.
  - Rule-free E. coli founders, and Myxo arrivals (`seeding.add_due_myxo`).
  - 70 tests pass.
- **B79–B80, 11 Oct 2026:** `myxo_famine.py` (new; called right after the starvation clock in
  `engine.step_myxo`), `world.spores` and `world.myxo_lysed`, and rods, spores and lysed cells
  in the stats. 75 tests pass.
- **B81, 12 Oct 2026:** `stringent_exit_level`; `myxo_modes.stringent` keeps a cell stringent
  until it is back to 70, and `myxo_energy.upkeep` and the stats use it. 77 tests pass.
- **B83, 12 Oct 2026:** the starvation clock follows prey food (`myxo_modes.update_starve_clock`,
  column `starve_time`); stringent = starving past `stringent_delay`; scouting from prey food
  (`scout_chance`); a scraps map (`fields.scraps`) fed by dead and lysed Myxo and eaten up to
  `scrap_cap` (`myxo_energy.eat_from`, `absorb_scraps`); no division while stringent. 80 tests
  pass.
- **B84, 12 Oct 2026:** `myxo_energy.starving_cost` (surplus first); `behaviour_delay` and
  `myxo_modes.starving_behaviour`; dead and lysing cells leave only their store; the crowding map,
  `crowding()` and three settings removed. 82 tests pass.
- **12 Oct 2026, run safety:** the first 120 bio-h run was lost at 66.7 bio-h when the session
  ended. `checks/check_populations.py` now saves the stats and a checkpoint (`<name>.ckpt`) every
  30 real min; starting the same command again carries on from the checkpoint.
- **B85, 15 Oct 2026:** `efficiency` 0.3 with `uptake_rate` and `uptake_max` divided by it;
  `reserve_efficiency` is now worked out from `efficiency` (a property); `starvation_upkeep` 0.3;
  `checks/summarize_run.py` (a table of any population run). The build manual's checks table was
  brought up to date (four scripts were missing). 83 tests pass.
- **15 Oct 2026, run safety:** runs must be started as detached background tasks. Four runs started
  with `&` inside an ordinary command stopped when Claude's turn ended (2 min in); they carried on
  from their checkpoints.
- **B86, 16 Oct 2026:** `meanfield/` (new): `runs.py` (the runs it learns from), `model.py` (the
  equations), `fit.py` (learns the numbers; `fitted.json`), `compare.py` (model against every run),
  `scan.py` (flexible settings). Also `checks/compare_runs.py` (runs side by side). 83 tests pass.
- **B87, 16 Oct 2026:** `wake_threshold` and `starved_shrink_time` (new), `dormancy_before_death` 0;
  `ecoli_life.update_dormancy` keeps a dormant cell dormant until a real meal; `content_fraction`
  uses `starved_shrink_time`. `meanfield/hunting.py` (a run's search scale); the model knows each
  run's E. coli rules (`Run.wake`, `Run.grace`). 85 tests pass.
- **B87 result, 16 Oct 2026:** `checks/prey_budget.py` (births, kills and starvation deaths of a run);
  `checks/compare_runs.py` draws target ranges as bands; `Run.fit` leaves a run out of
  `meanfield/fit.py`; the legend of `meanfield/compare.py` no longer overlaps its axis label.
- **B88, 16 Oct 2026:** `seeding.persister_flags` (each newborn draws its own persister flag),
  used by `seeding.ecoli_seed`, `ecoli_body.daughters` and `ecoli_body.divide`. 86 tests pass.
- **Milestones 7 and 8 (B90), 17 Oct 2026:** `drawing.py` (with a `View` for close-ups),
  `ui_widgets.py`, `app_live.py` (checked headless with `--test`), `run_record.py` (scenes `world` and
  `closeup`, resumable, JPG frames joined into an MP4). 86 tests pass.
- **B91, 17 Oct 2026:** `app_params.py` (new: main, advanced, switches, evidence options, fixed values,
  the recommended settings); `app_live.py` rebuilt (speed from real time, graph below the world,
  Settings panel, scrolling); `ui_widgets.Toggle`, a star on recommended options;
  `drawing.draw_counts_graph`; `run_record.py` reads true/false settings.
- **B92–B94, 17 Oct 2026:** leading-pole dots and reversal flashes (`drawing`); `swarm` and `ripple`
  scenes (`run_record`); the name MyxoHunt; the browser version (`predation-sim/web_controller.py`,
  `web/` with `index.html`, `app.js`, `worker.js`, `style.css`, `build.py`); `np.intp` indices for
  `bincount`; the biology speed-up on the main panel. 86 tests pass.

- **17 Oct 2026, web drawing fix (B96):** after dragging the view far, parts of the ground went blank and Myxo crossing the view's edge were drawn as long straight lines across the world. The view centre now wraps back into the world, and a cell's outline breaks wherever it jumps across the screen. Pages load `app.js?v=2` so browsers don't keep the old code.

---

## Open questions
- **The band is not reached (B98, 24 Oct 2026):** with starving cells scouting, the hunters hold the
  prey at about 100–350 (target 700–1,000) and shrink only slowly through the famine. Tuning stopped
  by the user's choice. If it's ever resumed: famine lysis at 70% (D3) on 4 seeds, or first measure
  the hunter balance point in short thinning branches.
  **B99 (25 Oct 2026):** a 40 bio-h branch test at 70%. The hunters fell into their band in every seed
  and the prey rose slowly, but stayed at 311–510. Kills barely depend on hunter numbers, and starving
  hunters turn food into upkeep, not offspring. Carried on to +100 bio-h, three seeds settled at about
  530–570 E. coli and 85–100 Myxo, a little below both band means. Seed 4 was still rising
  (812 / 134).
  **B100 (25 Oct 2026):** adding refill ÷6 on top lifts both to the band's lower edge (about 700 /
  100–110, still rising slowly; seed 4 about 790 / 192). ÷4 overshoots the prey (about 1,050–1,110)
  while its hunters boom.
  **B101 (25 Oct 2026):** the full round of 70% + ÷6 passes 1 of 4 seeds. Both populations hold steady
  after the first wave: hunter means 131–153 (in band in all four seeds), prey means 541–752 (seed 4
  in band; seeds 2 and 3 at 658 and 667). Adopted as the Recommended preset (B102); a ÷5 round is
  running (B103).
- **Review of 23 Oct 2026 (`docs/review-2026-10-23.md`):** an independent check of code, data and docs. Main findings: the shipped Recommended preset (B89 + B95) was never run as a population; B95 blocks scouting by accident (`myxo_modes.py:114-116`); the mean-field model's scavenging term creates hunters from nothing (`meanfield/model.py:134`), so its picks for B86–B89 are unsupported; single-seed comparisons B85–B89 are within chance except the famine lysis share; slime and scout timers mix the real and biology clocks. Six decisions (D1–D6): the user chose every recommended option (B97).
- **From the B88 result (17 Oct 2026):** with refill alone, the two targets pull against each other
  (about 150 hunters in the long run only with about 1,600 prey). Being tested in B89: fewer famine
  deaths (20% lysis) at refill ÷8 and ÷10.
- **From the B87 result (16 Oct 2026):** persisters were inherited, so one colony in 20 never
  starved. **Settled in B88:** each newborn draws its own 5%. Next: refill ÷6 and ÷10 side by side.
- **From B86 (16 Oct 2026):** the average-world model says the targets need hunters about 4× better
  at finding prey, and that E. coli should be able to starve. The user relaxed the targets (about
  700–1,000 E. coli, 150 Myxo) and questioned the time split (B4); lower speed-ups are being tested.
  Still open: whether to change the speed-up for good (lower ones hunt worse in the tests). Settled
  in B87: E. coli can starve (a real meal to wake, no day of grace).
- **From B85 (15 Oct 2026): how to bring the numbers down.** The poorer ground starved the arriving
  hunters and the first prey wave overshot. The user (16 Oct 2026): both targets equally; first the
  old ground with the new hunters (120 bio-h, 2 seeds), then further tuning. Those runs: hunters
  16–29% fewer, prey 65–150% more than B84; next levers put to the user.
- **The video and app look:** colours, what's shown, zoom, slider layout. Left for later.
- **Next build steps:** milestones 7 (live app) and 8 (recording), after the B73 runs.
- **Obsolete since B83 (no store trigger any more):** **"Keep it 50 for stringent response" (the user, 11 Oct 2026) is not settled.** Built as:
  scouting peaks at about 50% just before stringent mode, which starts below a store of 20.
  If it meant "stringent mode starts below 50", that's the one setting `starvation_level`.
- **Still open from the B72 follow-ups (11 Oct 2026):**
  - **Settled in B83:** stringent mode starts after a while with no prey food around.
  - *(Before B83)* **When should stringent mode start?** Store below 20 (in use), or after a while with no
    food around (Harris 1998)? Since B75, daughters (about 100) no longer start on the line;
    the remaining issue is that all seeds start at 60 and switch together. B80: the outside
    trigger is the backed one, but it collides with scouting (B71); waiting for the user.
  - **Settled in B80:** stringent cells follow the smell more, like scouts (Kearns 2001).
- **From B80 (11 Oct 2026):**
  - Should spores germinate when food comes back, and should the famine exit need crowding
    (fruiting bodies need many cells)?
  - A dead Myxo's 100-unit body comes on top of its store (see B80's bookkeeping note). **Kept in
    B82;** the unpaid body at division is parked. **Settled in B84:** no separate body; a dead cell
    leaves only its store.
- **After this project (the user, 12 Oct 2026):** a 3D version with fruiting bodies.
  - **Settled in B81:** a crumb of food no longer resets the starvation clock; only a real meal
    (back to a store of 70) ends stringent mode.
- **From the user's question on trails (12 Oct 2026):** cells that get inside a colony ripple, and
  rippling cells lay no slime (A7), so they leave no trail for the pack to follow in. Real groups
  follow single pioneers into prey colonies (Seef 2021). A possible later rule: let them lay
  some slime (our assumption).
  - **Settled:** stringent speed (B75, by crowding); sticking to spilled food (B74, ghosts keep
    smelling instead of a new rule).
