# Build manual: predation simulation (`predation-sim/`)

A complete specification for building the *M. xanthus* (Myxo) × *E. coli* predation simulation
and its pygame app. It's written so a coding agent can build it step by step without guessing.

**Read first:**
- `CLAUDE.md` (root): project brief and working rules.
- `docs/decision-log.md`: every decision and why. Decision IDs (B14 etc.) are cited below.
- `docs/sources.md`: the evidence behind the decisions.
- `paper-reproduction/functions.py`: validated physics, which gets copied in.

**Status:** draft 1, 10 October 2026. Numbers marked **[tuned]** are starting values to adjust
by watching the simulation. Any change to them is logged in `decision-log.md`.

---

## 0. Rules for the agent

1. **Don't modify `paper-reproduction/`.** It's the validated reference. When a function is
   reused, copy it into the new file and add the comment
   `# copied from paper-reproduction/functions.py:<name>` above it.
2. **One small job per file.** No function longer than about 25 lines; split anything longer
   into helpers.
3. **Docstring on every function, in plain words.** Then `Args:` (name, shape, unit) and
   `Returns:`. Example:
   ```python
   def monod_factor(nutrient, half_saturation):
       """How fast E. coli can grow given the food under it: 0 (no food) to 1 (plenty).

       Args:
           nutrient: (M,) nutrient level under each cell, 0..1.
           half_saturation: nutrient level at which growth is half of maximum.
       Returns:
           (M,) growth factor between 0 and 1.
       """
       return nutrient / (half_saturation + nutrient)
   ```
4. **Speed:** numpy arrays, one row per cell, and no Python loops over cells. Loops over a
   handful of colonies or UI widgets are fine.
5. **Units:** µm for lengths, minutes for time. Every `Settings` field has a comment giving
   its unit and its source tag: `[paper]`, `[code]` (the authors' code), `[biology]` (a
   `sources.md` entry), `[assumed]` or `[tuned]`.
6. **Two clocks.**
   - **Real time `t`:** advances by `dt` per step. Movement, reversals and killing run on it.
   - **Biological time:** `t × speedup`. All "slow biology" runs on it: E. coli growth, Myxo
     upkeep, uptake and division, nutrient regrowth, digestion, and all fading.
   - In code, slow processes advance by `dt_bio = (real time since their last update) ×
     speedup` (B4). Cell biology updates every tick, so `dt_bio = dt·speedup`. Ground grids
     update every `grid_every` ticks, so `dt_bio = grid_every·dt·speedup` (B51).
7. **Randomness only through `world.rng`** (a `numpy.random.Generator`), so runs are
   reproducible from a seed.
8. **Build in the milestone order of section 6.** After each milestone, run its checks and
   show the user a picture before going on. Ask before any run longer than about 10 minutes.
9. **Log decisions.** New or changed decisions go into `decision-log.md` as they're made, and
   new outside facts into `sources.md`.

## 1. Setup

- **Code location:** `predation-sim/` at the project root. Run everything from inside that
  folder.
- **Environment:** the shared venv `../.venv`. Add these to `../requirements.txt` and install
  them:
  ```
  pygame>=2.5
  imageio>=2.34
  imageio-ffmpeg>=0.5
  pytest>=8.0
  ```
- **Entry points:** `python app_live.py` (the interactive window), `python run_record.py`
  (headless video) and `python -m pytest tests`.

## 2. How the simulation works (overview)

**Each step, real time `dt` = 0.005 min (0.3 s).** These are the fast processes, in order
(`engine.step_fast`):
1. Which Myxo ripple: a cell ripples if the prey material around its head (ghosts and living
   prey, B76) is at or above the threshold, and it then uses the local ripple axis.
2. Remember head positions.
3. Traction on Myxo that aren't paused, each at its own speed (scouts ×1.1, B71, B80; cells
   starving for 2 bio-h or more speed up with time starving, ×1 to ×1.5, B75, B84).
4. Contacts: push apart overlapping Myxo–Myxo and E. coli–E. coli pairs (Myxo crawl over prey,
   B76), and list the Myxo–E. coli touches.
5. Myxo springs.
6. Alignment:
   - Rippling cells turn toward their local axis.
   - Swarming cells that are moving lay EPS. Trail followers turn toward trails, sensing
     ordinary and scout slime together; scouts lay their own, stronger slime layer and wander
     off-trail (B67, B71).
7. Frustration, memory and signal, for cells that aren't paused (B16). Each cell compares its
   real movement with its own intended speed (B71).
8. Reversals for cells that aren't paused. The post-refractory rate is multiplied by the
   chemotaxis factor (B32), whose strength is ×1.5 for scouts and stringent cells (B72, B80). Then scout mode switches
   on or off for each cell, from the prey food within reach (B71, B83).
9. Predation: start new pauses, count down existing pauses, finish kills (B14, B15).
10. Wrap positions into the box.

**Cell biology, also every tick, sped up: `dt_bio = dt × speedup`** (`engine.step_cells`, B51).
Cheap per-cell bookkeeping, so it runs every tick and cells grow smoothly:
1. **E. coli:** grow (Monod), consume nutrients, divide, go dormant, die of starvation (the
   body stays intact for a short delay), then burst (lysis) with reduced food (B45).
2. **Myxo energy:** the starvation clock, which follows the prey food within reach (B83); the
   famine exit, a day after the prey food ran out: lyse, become a spore or stay on as a rod (B80);
   upkeep (cut to 30% on the core in stringent mode, B84, B85); uptake of prey food, then scraps up to `scrap_cap`, from
   the ground within 2 µm of the head (shared by hunger); division once the store has doubled
   (never scouts or stringent cells; each daughter gets half, B75); death (B70, B71).

**Every `grid_every` ticks (default 20 = 0.1 min real; a setting, can be 1):** the ground
grids, using `dt_bio = grid_every × dt × speedup` (`engine.step_grids`, B51). This is the
expensive part, because each update processes whole maps:
1. **Fields:** nutrients regrow toward `richness` and diffuse; food diffuses and fades
   (half-life 12 bio-h, B74); ghosts add attractant, which diffuses and decays (B74); matrix
   and both EPS layers fade (scout slime more slowly, B71).
2. **Prey material smoothing:** recompute `matrix_smooth`, `axis_c_smooth` and `axis_s_smooth`
   from ghosts and living prey (B43, B76).
3. **Newcomers:** a new E. coli founder when one is due (every `ecoli_seed_interval`, anywhere, B75,
   B78), and any Myxo seeds whose arrival time has come (B78).
4. **Stats:** record counts. (The crowding map was step 3 until B84.)

Grid *deposits* (EPS laid, nutrients consumed, food and matrix from lysis, food taken up)
still happen every tick where they occur. Only the whole-map spreading, fading and smoothing
wait for `grid_every`.

**Lysis** (`predation.lyse_ecoli`) is the same whether the cell was killed or starved. It
removes the rod and deposits:
- food = `ecoli_content` × length/3;
- attractant;
- matrix, plus that colony's axis, into the nematic axis fields.

## 3. Data structures (`state.py`)

All per-cell arrays have the number of cells as their first dimension. Rows are added and
removed only through `append_rows` and `keep_rows`, so every array stays in step.

### `MyxoCells` (N cells)

| Field | Shape, type | Meaning |
|---|---|---|
| `nodes` | (N, 10, 2) float64 | Disc positions, not wrapped; disc 0 is the head |
| `age` | (N,) float64 | Real min since the last reversal (reversal clock) |
| `memory` | (N, K) float64 | Recent frustration values, K = 66 (ring buffer) |
| `mem_slot` | (N,) int64 | Each cell's latest memory slot. Per cell, so paused cells freeze (B16) |
| `signal` | (N,) float64 | Smoothed frustration s, 0..1 |
| `energy` | (N,) float64 | Food store, 0..210: 100 = a normal newborn, 200 = doubled and ready to split, 200–210 the reserve (B20, B75) |
| `pause_left` | (N,) float64 | Real min left in a killing pause; 0 = not paused |
| `pause_target` | (N,) int64 | `uid` of the E. coli being killed; −1 = none |
| `scout` | (N,) bool | True while in scout mode (B71). Newborn and seeded cells start False |
| `starve_time` | (N,) float64 | Bio min since the cell's prey food ran out (its starvation clock); 0 when fed. Daughters copy their mother's (B75, B83) |
| `uid` | (N,) int64 | Unique ID, never reused |

### `EColiCells` (M cells)

| Field | Shape, type | Meaning |
|---|---|---|
| `centre` | (M, 2) float64 | Rod centre, wrapped into the box |
| `angle` | (M,) float64 | Rod direction (rad) |
| `length` | (M,) float64 | Tip-to-tip length (µm), 2 to about 4 |
| `colony` | (M,) int64 | Colony ID (index into `World.colony_axis`) |
| `dormant` | (M,) bool | True = stopped growing for lack of food |
| `starve_time` | (M,) float64 | Biological min spent dormant |
| `persister` | (M,) bool | True = never dies of starvation (the long-term survivors, B34); drawn for each newborn, not inherited (B88) |
| `lysis_timer` | (M,) float64 | −1 = alive. ≥ 0 = dead but intact, with that many bio min until it bursts (B45) |
| `divide_at` | (M,) float64 | This cell's own division length, drawn at birth: 4 µm ± 10% (B53) |
| `speed_factor` | (M,) float64 | This cell's own growth speed, drawn at birth: 1 ± 0.2, clipped 0.4–1.6 (B55) |
| `uid` | (M,) int64 | Unique ID, increasing. The array stays sorted because rows are only appended or removed |

### `Fields`

**Fine grid:** spacing about 0.3 µm (the EPS needs it).
- `eps` (n_f, n_f): slime amount.
- `eps_scout` (n_f, n_f): slime laid by scouts, at `scout_slime` × the normal amount. Followers
  sense `eps` + `eps_scout`; it fades `scout_slime_fade` times more slowly (B71).

**Coarse grid:** spacing 1.0 µm, n_c = round(box/1.0).
- `richness` (n_c, n_c): fixed per-spot maximum nutrient level, 0.3..1.0, made once at the
  start as smooth random patches (B48).
- `nutrients` (n_c, n_c): ground nutrients, 0..richness. They start equal to `richness` and
  regrow toward it (B33, B48).
- `food`: prey food, the contents of killed or burst E. coli.
- `scraps`: what dead or lysed Myxo spill. It spreads and fades like prey food, but only keeps cells alive (B83).
- `attractant`: lipid signal from lysis (B32).
- `matrix`: prey-matrix amount (B11).
- `matrix_smooth`: prey material, ghosts (`matrix`) plus living prey × `ripple_live_prey_weight`,
  averaged over a disc of radius `matrix_sense_radius` (3 µm) around each square. Recomputed in
  every grid update by `grids.disc_average`, and used for the ripple check (B43, B76).
- `axis_c_smooth`, `axis_s_smooth`: the doubled-angle sums of ghosts and living prey,
  averaged the same way; the ripple direction is read from these (B76).
- `axis_c`, `axis_s`: the matrix-weighted sums of cos 2θ₀ and sin 2θ₀ (B13). The local ripple
  axis is ½ · atan2(axis_s, axis_c). Using doubled angles means overlapping colonies blend
  their axes smoothly.

### `World`

`settings`, `rng`, `myxo`, `ecoli`, `fields`, `t` (real min), `bio_t` (biological min,
summed from each dt_bio so it stays right when the speed-up slider changes), `step_count`, `next_uid`,
`colony_axis` (a growable list of ripple axes per colony, uniform random in [0, π)), and
`eps_offsets` (the sensing table, built once), `myxo_arrivals` (the (bio min, cells) of Myxo seeds
still to come in, B78), `next_ecoli_seed` (bio min when the next
new E. coli founder is due, B75), `spores` (an (S, 2) array of where Myxo spores wait, B80) and
`myxo_lysed` (Myxo lysed in famines so far, B80).

### Helper functions in `state.py`

| Function | Params | Returns | Summary |
|---|---|---|---|
| `empty_myxo(K)` | memory length | `MyxoCells` with N = 0 | Empty population with the right shapes |
| `empty_ecoli()` | — | `EColiCells` with M = 0 | Same, for E. coli |
| `append_rows(cells, new)` | two cell objects of the same class | None, in place | Join `new` onto `cells`, field by field |
| `keep_rows(cells, mask)` | (N,) bool | None, in place | Keep only the rows where mask is True |
| `count(cells)` | — | int | Number of rows |
| `new_uids(world, n)` | how many | (n,) int64 | Hand out the next n unique IDs |

## 4. Settings (`settings.py`)

`@dataclass Settings` with every value below as a default, plus `to_json(path)` and
`from_json(path)`. Constants for the app: `STARVATION_PRESETS`, `COLONY_OPTIONS`,
`WORLD_SIZES` and `START_COLONIES`. Also:
- **`make_settings(mode, **overrides)`** gives live or record settings with any values changed
  by name, and rejects unknown names.
- **Derived properties:** `memory_length` (66) and `survive_time` (from the preset).

| Group | Name | Default | Unit | Source / note |
|---|---|---|---|---|
| World | `box` | 150 (live) / 500 (record) | µm | B2 |
| | `seed` | 1 | — | RNG seed |
| | `dt` | 0.005 | min | [code] |
| | `grid_every` | 20 | ticks between ground-grid updates | B51 [assumed]; app slider 1–50. Cell biology always runs every tick |
| | `speedup` | 10 | × | B4; slider 1–30 |
| | `coarse_grid` | 1.0 | µm | [assumed] |
| | `eps_grid` | 0.3 | µm | [code] |
| Myxo body | `n_nodes`, `node_spacing`, `disc_diam`, `speed` | 10, 0.5, 0.7, 4.0 | –, µm, µm, µm/min | [paper] |
| | `k_spring`, `k_rep` | 50, 450 | | [paper] |
| | `traction_scale`, `spring_passes_per_node` | 10, 5 | | [code] |
| Reversals | `R_star`, `R_min`, `F_star`, `f_T`, `alpha_F`, `alpha_R` | 5, 1/3, 3, 0.08, 75, 100 | | [paper]/[code], as in `paper-reproduction/datatypes.py` |
| | `memory`, `beta` | 1/3, 2.0 | min, 1/min | [paper]/[code] |
| Alignment | `gamma_ripple`, `gamma_eps` | 11, 11 | 1/min | [paper] |
| | `sense_radius`, `view_angle`, `n_sectors`, `eps_c_min`, `eps_choice_tolerance`, `eps_deposit` | 5, π, 5, 0.1, 0.8, 2.0 | | [paper]/[code] |
| | `eps_fade_time` | 360 | bio min | B31 [tuned] |
| | `matrix_ripple_threshold` | 0.3 | matrix units, about one dead cell's wall per square | [tuned] |
| | `matrix_sense_radius` | 3.0 | µm | B43 [assumed] |
| | `ripple_live_prey_weight` | 1.0 | ghosts per living E. coli | B76 [assumed]: a living E. coli counts like one ghost toward the ripple trigger, since contact with prey starts rippling (Berleman 2006); 0 = ghosts only |
| | `matrix_per_ghost` | 1.0 | matrix units | [tuned] |
| | `matrix_half_life` | 720 | bio min | B12 [tuned] |
| Chemotaxis | `chemo_strength` | 2.0 | — | B10/B32; slider 0–5 (0 = pure paper) [tuned] |
| | `chemo_factor_range` | (0.2, 5.0) | — | Clip for the reversal multiplier [assumed] |
| | `attractant_per_lysis` | 1.0 | units | [tuned] |
| | `ecoli_attractant_rate` | 2.0 | units per bio min per living E. coli | B63, B68 [assumed]: faint smell from living colonies (outer-membrane vesicles, PE); 0 = off |
| | `ghost_attractant_rate` | 2.0 | units per bio min per ghost (matrix unit) | B74 [assumed]: ghosts keep shedding their PE-rich envelope while they last, so eaten spots keep smelling of prey; 0 = off |
| | `attractant_diffusion` | 50 | µm²/bio min | [tuned] |
| | `attractant_decay_time` | 60 | bio min | [tuned] |
| E. coli | `ecoli_width` | 1.0 | µm | [biology] BioNumbers |
| | `ecoli_birth_length`, `ecoli_divide_length`, `ecoli_divide_noise` | 2.0, 4.0, 0.4 | µm | [biology]; noise B53, B80 [biology]: ~10%, BioNumbers 110034 |
| | `ecoli_speed_noise` | 0.2 | — | B55 [biology]: SD of each cell's own growth speed, redrawn at every birth, clipped 0.4–1.6 |
| | `ecoli_points` | 5 | points per rod for contacts | [assumed] |
| | `ecoli_doubling` | 20 | bio min | [biology] |
| | `monod_half_saturation` | 0.2 | nutrient units | [assumed] |
| | `nutrient_per_um` | 0.5 | nutrient used per µm of growth | B78 [tuned]: on local ground, colonies of about 370–560 cells by 500 bio-min, still growing at their rims; 0.3 runs away, 1 stays small (3 in B54/B75 with fast spreading) |
| | `ecoli_mobility` | 1.0 | × mean push on a rod | [tuned] |
| | `dormant_threshold` | 0.01 | nutrient level | [assumed]: below it a growing cell goes dormant |
| | `wake_threshold` | 0.2 | nutrient level | B87 [the user's choice]: a dormant cell wakes, and its starvation clock restarts, only at a real meal (the Monod half-speed level), not at a trace |
| | `dormancy_before_death` | 0 | bio min | B34, B87 [biology]: no day of grace; viability falls from the start of starvation (Schink et al.); 1440 before |
| | `starvation_death_rate` | ln(1000)/(10·1440) | 1/bio min | B34, B80 [biology]: viability falls to 0.1% in 10 days, ~0.69 per bio-day (Schink et al.; 1/1440 before) |
| | `persister_fraction` | 0.05 | — | B34 [biology]: 90–99% die |
| | `starved_lysis_delay` | 120 | bio min from death to burst | B45, B80 [biology]: lysis 2.0 ± 1.4 h after the membrane voltage collapses (Schink et al.; 30 before) |
| | `starved_content_min` | 0.25 | fraction of content left at death | B45 [assumed] |
| | `starved_shrink_time` | 1440 | bio min | B45, B87 [assumed]: starving time over which a cell's contents shrink to `starved_content_min` |
| Nutrients | `nutrient_regrow_rate` | 1/3000 | 1/bio min | B68 [tuned]: dN/dt = r(richness − N), slow replenishing (was 1/600) |
| | `richness_min`, `richness_max` | 0.3, 1.0 | nutrient units | B48 |
| | `patch_size` | 30 | µm | B48 [tuned] |
| | `nutrient_diffusion` | 0.1 | µm²/bio min | B78 [tuned]: local ground, so a colony drains its own patch plus about 25 µm over 30 bio-h (10 in B54 let two colonies drain the whole live world) |
| | `nutrient_start_min`, `nutrient_start_max` | 0.3, 1.0 | share of each square's maximum | B78 [assumed]: each patch starts filled to a random share between these |
| Food | `ecoli_content` | 100 | store units per average 3 µm cell | B21, B75: about one Myxo cell's worth (similar sizes) |
| | `food_diffusion` | 5 | µm²/bio min | B17 [tuned] |
| | `food_decay_time` | 1038.8 | bio min (e-folding) | B74 [assumed]: a 12 bio-h half-life, the same as the ghosts, so food and its smell fade together (∞ in B70, 600 before) |
| Predation | `touch_distance` | 0.95 | µm, between a Myxo disc centre and an E. coli point | (0.7 + 1.0)/2 + 0.1 margin |
| | `pause_rate` | 0.71 | 1/real min while touching | B15 [tuned]: 30% of 0.5-min touches |
| | `kill_delay` | 2.0 | real min | B14 [biology] |
| | `kill_success` | 0.8 | — | B14 [biology] |
| | `scale_predation` | True | — | B66: pause rate × speed-up and kill delay ÷ speed-up, so kills per Myxo generation stay realistic; single encounters look faster than measured |
| | `prey_contact_signal` | 0.0 | signal level | B62, B76 [assumed]: off, so after a kill cells glide on into the colony (Seef 2021); above f_T it would cause rapid reversals on contact (0.15 before) |
| | `myxo_crawl_over_prey` | True | — | B76 [assumed]: Myxo and E. coli never shove each other, standing in for the 3D colony that A-motile cells penetrate; touches still kill |
| | `ecoli_push_share` | 0.8 | — | B62, B68 [assumed]: share of a Myxo–E. coli shove taken by the E. coli; only used when `myxo_crawl_over_prey` is off |
| | `killer_share` | 0.25 | — | B65, B76 [assumed]: share of a kill's contents the killer absorbs at once; the rest spills for the pack |
| Energy | `energy_start` | 60 | units | B20: seeds start partly starved |
| | `energy_newborn` | 100 | units | B75: a normal, well-fed newborn, one cell's worth of material |
| | `energy_full`, `energy_cap` | 200, 210 | units | B22, B75: doubled (ready to split); top of the reserve |
| | `efficiency`, `reserve_efficiency` | 0.30, efficiency/3 (a property) | — | B21, B22, B75, B85: measured 5–60% (del Giorgio & Cole 1998); 30% since B85 so each prey feeds fewer hunters (50% in B75); a third of that in the reserve |
| | `uptake_rate` | 0.25/0.30 ≈ 0.83 | 1/bio min (fraction of the food within reach) | [tuned]; divided by `efficiency` in B85 (0.5 at 50%), so the store gained from a given amount of food per minute is unchanged |
| | `absorb_radius` | 2.0 | µm | B71 [assumed]: cells take food from every square within this distance of the head (digestion by secreted enzymes) |
| | `uptake_max` | 2.5/0.30 ≈ 8.3 | food units per bio min | B65, B75, B85 [biology-anchored]: on plentiful food a newborn divides after 5.4 bio-h on average (measured 5.5 h on prey, Seef 2021); divided by `efficiency` in B85 (5 at 50%; left at 5, the generation would slow to 8.9 bio-h) |
| | `starvation_preset` | "slow" | key | B23, B68, B75: a newborn's store (100) lasts 24 bio-h at full cost |
| | `living_food` | 1.0 | prey food units within `absorb_radius` | B83 [assumed]: below this a cell is starving outside (too little to cover its running costs) and its starvation clock starts (was `scout_food_threshold`, B71) |
| | `stringent_delay` | 30 | bio min | B83, B84 [assumed]: starving this long brings the fast effects (cost cut on the core, no division, ×1.15 uptake); the alarm (p)ppGpp rises fast (Manoil & Kaiser 1980) |
| | `behaviour_delay` | 120 | bio min | B84 [assumed]: starving this long brings the starving behaviours (×1.5 smell, speed-up); "the first few hours" of starvation recognition (Harris 1998) |
| | `scrap_cap` | 30 | units | B83 [the user's choice]: scraps from dead Myxo fill a store only up to this, so they keep a cell alive but never end its starvation |
| | `starvation_upkeep` | 0.3 | × normal upkeep | B70, B84, B85 [assumed number; direction backed]: stringent mode cuts running costs to 30% on the core (a newborn's 100; 10% before B85); anything above is burned at the full rate first |
| | `stringent_loner_speed`, `stringent_speedup_time` | 1.5, 900 | ×, bio min | B75, B84 [biology]: a cell showing starving behaviour speeds up to 1.5× over 15 bio-h of starving (Jelsbak 2002); no slow-down when packed (dropped in B84) |
| | `stringent_affinity` | 1.15 | × uptake rate | B72 [assumed]: stringent cells take up scarce food 15% more readily; scouts get no boost (replaces B71's `hungry_affinity` 1.5) |
| | `division_threshold` | 190 | units | B24, B75: division possible once the store has about doubled; each daughter gets half (no separate cost) |
| | `division_rate_max` | 1/60 | 1/bio min at the cap (210) | [tuned] |
| Famine | `famine_exit` | True | — | B80: a day into stringent mode, starving cells begin development and take a fate (`myxo_famine.py`) |
| | `famine_time` | 1440 | bio min in stringent mode | B80 [biology]: lysis and aggregation begin about 24 h after starvation (Lee 2012) |
| | `famine_lysis_share`, `famine_spore_share` | 0.7, 0.1 | — | B80 [biology]: 70% lyse (classic counts 60–80%, disputed), 10% become spores, the other 20% stay on as persister-like rods (10–20%, O'Connor & Zusman 1991) |
| Seeds | `myxo_groups`, `myxo_group_size`, `myxo_singles` | 5, 20, 10 | | B78, the user's choice (5, 50, 10 in B74; 5, 30, 10 in B64) |
| | `myxo_arrival_window` | 600 | bio min | B78 [assumed]: each Myxo seed comes in from outside at a random time within this window; 0 = all at the start |
| Scouts | ~~`scout_fraction`~~ | removed | — | B67, B68; replaced by the hunger trigger below (B71) |
| | `scout_start_rate` | 0.1/(0.9·10) ≈ 0.011 | 1/real min | B83 [the user's choice]: the rate at zero prey food; with 10-min spells, 10% of such cells scout at any moment and about half get a turn within 10 bio-h. × (1 − food/`scout_food`) below `scout_food`, 0 above |
| | `scout_start_fraction` | 0.3 | share of top-speed food | B83 [the user's choice]: `scout_food` = 0.3 × `top_speed_food` (`uptake_max`/`uptake_rate` = 10) = 3 units of prey food within reach. Below it scouting can start; above it a starving cell has found a real meal |
| | `scout_episode` | 10 | real min | B70, B71 [assumed]: average length of a scouting spell. With the start rate, up to about half of the hungriest cells scout at once |
| | `scout_turn_noise` | 0.2 | rad²/min | B67 [assumed]: scouts' random turning; paths stay straight for about 20 µm |
| | `scout_speed` | 1.1 | × speed | B71, B80 [biology]: scouts glide at 4.4 µm/min, as lone cells do (Spormann & Kaiser 1999; 1.2 before) |
| | `scout_slime`, `scout_slime_fade` | 2.0, 2.0 | × | B71 [assumed]: scout slime counts double for followers and fades half as fast |
| | `scout_smell`, `stringent_smell` | 1.5, 1.5 | × `chemo_strength` | B72, B80 [assumed size]: scouts and stringent cells follow the prey smell more strongly; the lipid attractant works only in starving cells (Kearns 2001) (`stringent_smell` 1 before B80) |
| | `myxo_group_radius` | 6.5 | µm | B74, B78 [assumed]: the same packing as 30 cells in 8 µm |
| | `myxo_min_dist_colony` | 30 | µm from any E. coli to a Myxo seed centre | B47 |
| | `start_colonies` | 4 (record) / 2 (live) | | B44; options (1, 2, 4, 8). No reseeding afterwards |
| | `seed_min_dist_ecoli` | 75 (live) / 150 (record) | µm between starting seeds | B56 [assumed]; set per mode by `make_settings` (`SEED_DISTANCES`) |
| Drawing | `colors` | E. coli magenta (230, 60, 160); Myxo green (80, 220, 90); background (12, 12, 16) | RGB | Provisional; matches the paper's Fig. 1a mCherry/GFP. The final look is still open |

```python
STARVATION_PRESETS = {"very fast": 180, "fast": 360, "medium": 720, "slow": 1440}  # bio min a full store lasts (B23)
COLONY_OPTIONS = (1, 2, 4, 8)
WORLD_SIZES = {"live": 150.0, "record": 500.0}
```

## 5. Files and functions

All files are in `predation-sim/`. Shapes: N = number of Myxo, M = number of E. coli, n = 10
discs. "Copied" means copied from `paper-reproduction/functions.py` and adapted only as noted.

### `geometry.py`: small maths helpers

| Function | Params | Returns | Summary |
|---|---|---|---|
| `unit(v)` | (..., 2) | (..., 2) | Copied. Scale vectors to length 1 |
| `angle_of(vec)` | (..., 2) | (...) rad | Copied. Direction of each vector |
| `wrap_angle(a)` | array | array | Copied. Bring angles into (−π, π] |
| `min_image(d, box)` | (..., 2), float | (..., 2) | Copied. Shortest separation across the wrapped edges |
| `wrap_points(p, box)` | (..., 2) | (..., 2) | Positions folded into [0, box); guards box itself → 0 |
| `rod_points(centre, angle, length, k, width)` | (M,2), (M,), (M,), int, µm | (M, k, 2) | k evenly spaced points along each rod. The end points sit at ±(length − width)/2, so discs as wide as the rod span exactly `length` tip to tip |
| `axis_from_fields(c, s)` | arrays | array rad | Nematic axis ½·atan2(s, c) |

### `grids.py`: everything about grids (no biology here)

| Function | Params | Returns | Summary |
|---|---|---|---|
| `make_grid(box, spacing)` | floats | (n, n) zeros, true spacing | Square grid whose spacing divides the box exactly |
| `cell_index(points, box, n)` | (P,2), float, int | ix, iy (P,) int | Which square each point is in (wrapped) |
| `sample(grid, points, box)` | grid, (P,2) | (P,) | Value of the square under each point |
| `deposit(grid, points, amounts, box)` | grid, (P,2), (P,) or float | None | Add amounts to squares, using `np.add.at` so repeats add up |
| `diffuse(grid, D, dt, spacing)` | grid, µm²/min, min, µm | new grid, never negative | Exact periodic diffusion: FFT, multiply by exp(−D·k²·dt), inverse FFT. Stable for any dt. Cache the kernel per (shape, D·dt). The FFT leaves ±1e-17 rounding errors; set the negative ones to 0, since amounts can't be negative (B73) |
| `fade(grid, fade_time, dt)` | grid, min, min | None, in place | Multiply by exp(−dt/fade_time) |
| `regrow(grid, ceiling, rate, dt)` | grid, grid of maxima, 1/min, min | None, in place | N ← ceiling − (ceiling − N)·exp(−rate·dt): fast when far below the spot's own maximum, levels off at it (B48) |
| `random_patches(n, spacing, patch_size, lo, hi, rng)` | ints/floats | (n, n) grid | Smooth random field: white noise → `disc_average` with radius patch_size/2 → rescaled linearly to [lo, hi] (B48) |
| `gradient(grid, points, box, spacing)` | grid, (P,2) | (P,2) | Central-difference gradient at each point's square (wrapped) |
| `disc_average(grid, radius, spacing)` | grid, µm, µm | new grid | Wrap-around average over a disc around each square: FFT convolution with a normalised disc kernel, cached per (shape, radius) (B43) |
| `disc_offsets(radius, spacing)` | µm, µm | dx, dy (K,) int | Square offsets covering a disc, cached (B71) |
| `disc_squares(grid, points, box, radius, spacing)` | grid, (P,2) | flat (P,K) int, values (P,K) | The squares within `radius` of each point (wrapped) as flat indices ix·n + iy, and their values (B71) |

### `seeding.py`: starting cells

| Function | Params | Returns | Summary |
|---|---|---|---|
| `make_myxo(world, starts, headings)` | (k,2), (k,) | `MyxoCells` | Straight 10-disc chains from each start along the heading. Ages random in [0, R*); energy `energy_start`; memory zeros; `mem_slot` 0; not scouts; starvation clock 0; new uids |
| `add_due_founder(world)` | — | None | When `bio_t` ≥ `next_ecoli_seed`: one new E. coli founder (`ecoli_seed`) at a random spot, no rules; the next is due `ecoli_seed_interval` later (B75, B78) |
| `myxo_group(world, centre)` | (2,) | `MyxoCells` | `myxo_group_size` cells at random spots within `myxo_group_radius`. Shared random direction ±20°, each cell randomly forward or reversed |
| `initial_myxo(world)` | — | None | Schedule the groups and single cells: each gets a random arrival time within `myxo_arrival_window` (B78); seeds due at time 0 are placed at once. Run after `initial_ecoli` |
| `add_due_myxo(world)` | — | None | Place every seed whose arrival time has come, at a spot from `myxo_spot`, so that no disc starts within `myxo_min_dist_colony` of an E. coli (B47, B72, B78). Called at every ground update |
| `seed_clearance(s)` | Settings | µm | `myxo_min_dist_colony` + `myxo_group_radius` + one body length (4.5 µm): how far a seed's centre must stay from every E. coli (B72) |
| `initial_ground(world)` | — | None | Make `richness` with `grids.random_patches`; fill each patch to a random share of it (a second patch map between `nutrient_start_min` and `nutrient_start_max`) (B48, B78). Run first |
| `myxo_spot(world, tries)` | — | (2,) | A random spot at least `seed_clearance` from every E. coli (wrapped distance; up to 200 tries, then the farthest spot tried) (B47, B72) |
| `uniform_myxo(world, n, aligned_axis=None)` | int, rad or None | None | Validation only: n cells at random positions, with random headings or along one axis (half each way), like the reproduction's quick tests |
| `divide_lengths(world, k)`, `speed_factors(world, k)`, `persister_flags(world, k)` | int | (k,) | Each newborn E. coli's own division length, growth speed (B53, B55) and persister flag (a `persister_fraction` chance, B88) |
| `ecoli_seed(world, position)` | (2,) | `EColiCells` (1 cell) | One rod, birth length, random angle, new colony ID with a random axis added to `colony_axis`, persister flag drawn |
| `initial_ecoli(world)` | — | None | `start_colonies` seeds, at least `seed_min_dist_ecoli` apart (try random points, up to 200 tries). These are the only seeds ever made (B44) |

### `myxo_body.py`: Myxo mechanics (copied physics)

| Function | Params | Returns | Summary |
|---|---|---|---|
| `head_direction(nodes)` | (N,n,2) | (N,2) | Copied. Unit vector from disc 1 to disc 0 |
| `traction(nodes, heading, moving, s, speed_factor=None)` | …, (N,) bool, Settings, (N,) | None | Copied, plus a `moving` mask (paused cells get no pull) and each cell's own speed factor (B71). Keep the paper code's order of multiplication, so a factor of 1 gives identical numbers |
| `relax_springs(nodes, s)` | (N,n,2) | (N,2) heading | Copied. 50 passes; returns the heading after relaxation |
| `rotate_heads(nodes, angle, which)` | (N,), (N,) bool | None | Copied. Turn the head disc about disc 1 |
| `reverse(nodes, flip)` | (N,) bool | None | Swap head and tail of the flipped cells: `nodes[flip] = nodes[flip, ::-1]` |
| `wrap_cells(nodes, box)` | — | None | Copied from `engine.py` step 5. Shift each whole cell so its head is in the box |
| `split_cell(nodes_one, s)` | (n,2) | (n,2) | Daughter body: a copy shifted 0.8 µm sideways (perpendicular to the body). Repulsion then separates them |

### `myxo_alignment.py`: rippling axis and EPS trails

| Function | Params | Returns | Summary |
|---|---|---|---|
| `ripple_mask(world, heads)` | (N,2) | (N,) bool | True where `fields.matrix_smooth` (ghosts and living prey) under the head ≥ `matrix_ripple_threshold` (B11, B43, B76) |
| `local_axis(world, heads)` | (N,2) | (N,) rad | Ripple axis under each head, from the averaged `axis_c_smooth`/`axis_s_smooth` (B76) |
| `ripple_turn(theta, axis, s)` | (N,), (N,) | (N,) rad | Adapted copy: Δθ = γ′·sin 2(axis − θ)·dt with a per-cell axis |
| `scout_turn(k, s, rng)` | int | (k,) rad | Scouts' small random turns: √(2·`scout_turn_noise`·dt) × a normal random number (B67) |
| `eps_lay(eps, spacing, tails, s, amount=1.0)` | (k,2) | None | Copied. Add a·v·dt·amount under each rear disc (amount `scout_slime` for scouts, into `eps_scout`) |
| `sensing_offsets(spacing, s)` | — | (ox, oy, table) | Copied. Built once and kept in `world.eps_offsets` |
| `wedge_sums(eps, spacing, heads, theta, offsets, s, extra=None)` | — | (k,5), (k,) | Slime in each of the 5 wedges ahead, and the strongest square seen. `extra` (scout slime) is sampled at the same squares and added |
| `eps_turn(eps, spacing, heads, theta, offsets, s, rng, extra=None)` | — | (k,) rad | Copied. The five-wedge trail-following turn, sensing `eps` + `extra` |

### `myxo_reversals.py`: frustration and reversals

| Function | Params | Returns | Summary |
|---|---|---|---|
| `frustration(v_target, v_real)` | (k,2), (k,2) | (k,) | Copied. f = 1 − v_t·v_r / max(|v_t|², |v_r|²) |
| `memory_weights(s)` | — | (K,) weights, norm | Copied |
| `write_memory(memory, mem_slot, f, active)` | (N,K), (N,), (N,), (N,) bool | None | For active cells only: advance `mem_slot` by 1 (mod K) and store f there |
| `smoothed_signal(memory, mem_slot, weights, norm)` | — | (N,) | Adapted copy with a per-cell slot: lag = (mem_slot[:,None] − arange(K)) % K, then sum(memory·weights[lag], axis 1)/norm |
| `refractory_period(sig, s)` | (N,) | (N,) min | Copied |
| `reversal_rate(sig, s)` | (N,) | (N,) 1/min | Copied |
| `chemotaxis_factor(world, heads, heading, boost=None)` | (N,2), (N,2), (N,) | (N,) | B32. up = heading · ∇attractant at the head; factor = clip(exp(−chemo_strength·boost·up), range). Less reversing when heading uphill. `boost` is each cell's smell factor (B72). All ones when the strength is 0 |
| `reversal_probability(age, sig, factor, s)` | (N,)×3 | (N,) | Adapted copy: 0 inside the refractory period; else (1 − exp(−rate·factor))·dt |
| `decide_reversals(world, active, heading)` | — | (N,) bool | Age the active cells by dt, compute the probability (0 for inactive cells), roll the dice, reset the age of flipped cells to 0 |

### `ecoli_body.py`: E. coli as rigid rods

| Function | Params | Returns | Summary |
|---|---|---|---|
| `contact_points(ecoli, s)` | — | (M·k, 2) wrapped | All rod points for the contact search (k = `ecoli_points`) |
| `apply_pushes(ecoli, disp, s)` | (M·k, 2) point displacements | None | Rigid-body update: centre += mobility·mean(disp); angle += mobility·Σ cross(r, d)/Σ|r|², where r is each point's offset from the centre; re-wrap centres |
| `grow(ecoli, rate, dt_bio)` | (M,) 1/min | (M,) growth in µm | length ← length·exp(rate·dt_bio); return the added length |
| `divide(world)` | — | None | Rods at or above the divide length (each cell's own threshold = divide length ± noise) split into two of half length, centred at ±L/4 along the axis, angle + N(0, 0.05). Daughters keep the colony; each daughter draws its own division length, growth speed and persister flag (B53, B55, B88); one daughter gets a new uid |

### `ecoli_life.py`: food, dormancy and starvation death

| Function | Params | Returns | Summary |
|---|---|---|---|
| `monod_factor(nutrient, K)` | (M,), float | (M,) | Growth factor n(1 + K)/(K + n): 0 with no food, exactly 1 on the richest ground (1.0), half at n = K/(1 + 2K) (B33, B54) |
| `growth_rates(world)` | — | (M,) 1/bio min | ln2/doubling × Monod × the cell's `speed_factor`; 0 for dormant and dead-intact cells |
| `nutrient_under(world)` | — | (M,) | Mean nutrient at each rod's contact points: a rod feeds along its whole body (B78) |
| `consume(world, grown)` | (M,) µm | None | Subtract grown × `nutrient_per_um`, an equal share at each of the rod's contact points; clip at 0 (B78) |
| `update_dormancy(world, dt_bio)` | — | None | A growing cell with nutrient below `dormant_threshold` goes dormant; a dormant cell stays dormant until its nutrient is back to `wake_threshold` (a real meal, B87). While dormant `starve_time += dt_bio`; on waking it resets to 0 |
| `starvation_deaths(world, dt_bio)` | — | None | Alive, dormant, not a persister, and `starve_time` > `dormancy_before_death` → die with chance 1 − exp(−rate·dt_bio). Dying sets `lysis_timer = starved_lysis_delay`; the body stays (B45) |
| `content_fraction(ecoli, s)` | — | (M,) 0.25..1 | Food left inside: 1 − (1 − starved_content_min)·min(starve_time/starved_shrink_time, 1). Equals 1 for cells that never starved (B45, B87) |
| `count_down_lysis(world, dt_bio)` | — | (M,) bool | Subtract dt_bio from the timers of dead-intact cells; return the cells whose timer has reached 0 (these get passed to `lyse_ecoli`) |

### `contacts.py`: one shared contact search per step

| Function | Params | Returns | Summary |
|---|---|---|---|
| `all_points(world)` | — | points (P,2), diam (P,), owner (P,), kind (P,) | Myxo discs (diameter 0.7, kind 0) then E. coli points (diameter 1.0, kind 1), wrapped |
| `find_pairs(points, box, rmax)` | — | (Q,2) int | `cKDTree(points, boxsize=box).query_pairs(rmax, output_type="ndarray")` with rmax = 1.0 + 0.1 |
| `drop_bonded(pairs, kind, owner, local)` | — | pairs | Remove pairs of neighbouring discs in the same Myxo chain, and points of the same E. coli rod |
| `push_amounts(points, pairs, diam, box, s)` | — | (P,2) displacements | Adapted from the copied `repulsion`: per pair D = (dᵢ + dⱼ)/2 and push (D − r)²/max(r − 0.9D, 2/k_r)·dt along the line between centres; only pairs with r < D; summed with bincount |
| `myxo_ecoli_touches(points, pairs, kind, owner, box, s)` | — | (T,2) [myxo row, ecoli row] | Mixed pairs closer than `touch_distance`, deduplicated |
| `shoving_pairs(pairs, kind, s)` | (Q,2) | (Q',2) | With `myxo_crawl_over_prey`, drop the Myxo–E. coli pairs from the pushing (they still count as touches) (B76) |
| `resolve_contacts(world)` | — | touches | Run the above; push only `shoving_pairs`; add the displacements to Myxo discs; pass E. coli point displacements to `apply_pushes`; return all touches for predation |

### `predation.py`: pauses, kills and lysis (B14–B17)

| Function | Params | Returns | Summary |
|---|---|---|---|
| `start_pauses(world, touches)` | (T,2) | None | Ignore touches with dead-intact E. coli (`lysis_timer` ≥ 0). For free Myxo (pause_left = 0) touching live prey: chance 1 − exp(−pause_rate·dt) to pause. Set pause_left = `kill_delay` and pause_target = the touched E. coli's uid (the first if several) |
| `count_down_pauses(world)` | — | (N,) bool | Subtract dt from paused cells; return the cells whose pause has just ended |
| `finish_kills(world, ended)` | (N,) bool | None | For each ended pause whose target still exists (look up the uid with `np.searchsorted`), lyse it with chance `kill_success`. Clear the pause fields either way |
| `lyse_ecoli(world, dead)` | (M,) bool | None | For each bursting rod: food += content·(L/3)·`content_fraction`, attractant += `attractant_per_lysis`, matrix += `matrix_per_ghost`, axis_c/axis_s += matrix·cos/sin 2θ₀ (its colony's axis), spread over its k points; then `keep_rows(~dead)` |

### `myxo_energy.py`: food store, growth and death (B20–B28)

| Function | Params | Returns | Summary |
|---|---|---|---|
| `starving_cost(energy, dt_bio, full, cut, core)` | (N,) | (N,) | What a stringent cell spends in dt_bio: the surplus above `core` at the full rate first, then the core at the cut rate (exact for any step) (B84) |
| `upkeep(world, dt_bio)` | — | None | energy −= 100/`STARVATION_PRESETS[preset]`·dt_bio, or `starving_cost` for cells in stringent mode (B70, B84). The reserve is spent first automatically, because it's the part above 200 |
| `hunger(energy, s)` | (N,) | (N,) 0..1 | (cap − energy)/cap: 1 when empty, 0 at the cap (B26) |
| `food_demand(world, grid, dt_bio)` | — | demand (N,K), flat (N,K) | Food in `grid` within `absorb_radius` of each head (`grids.disc_squares`). Rate = min(uptake_rate·affinity·food around, `uptake_max`); total = min(rate·dt_bio, food around)·hunger, split over the squares in proportion to their food (B26, B65, B71) |
| `share_food(grid, demand, flat)` | — | (N,K) taken | Sum demand per square; where it exceeds the food in `grid`, scale everyone down in proportion (hungry cells keep the larger share). Treat negative food as 0, so the scale always lies in [0, 1] (B73) |
| `absorb(energy, taken, s)` | (N,), (N,) | new energy, leftover | `efficiency` (30%) up to 200, a third of that in the reserve up to 210; food beyond the cap is left over (B21, B22, B75, B85) |
| `absorb_scraps(energy, taken, s)` | (N,), (N,) | new energy, leftover | `efficiency`, but only up to `scrap_cap`; the rest is left over (B83) |
| `eat_from(world, grid, dt_bio, absorb_fn, eaters)` | — | None | `food_demand` (only for `eaters`) → `share_food` → `absorb_fn`; remove what was eaten from the squares and put leftovers back where they came from |
| `uptake(world, dt_bio)` | — | None | `eat_from` prey food (`absorb`, every cell), then scraps (`absorb_scraps`, cells below `scrap_cap`) (B83) |
| `division_chance(energy, dt_bio, s)` | (N,) | (N,) | 0 below 190, else 1 − exp(−rate_max·(E − 190)/(210 − 190)·dt_bio) |
| `divide_myxo(world, dt_bio)` | — | None | Only cells that are not paused, not scouting (B71), not stringent (B25, B83) and at 190 or more roll the chance. For each dividing cell: E ← E/2 for mother and daughter (two normal newborns, nothing created; B75); daughter body from `split_cell`; copy age/memory/signal and the starvation clock; not a scout; new uid; append |
| `starvation_deaths_myxo(world)` | — | None | Energy ≤ 0: remove the row. The store is the whole cell, so nothing spills (B84) |

### `myxo_modes.py`: the starvation clock, stringent mode and scout mode (B70, B71, B83)

All of these read the prey food within reach, never the store (B83). The clock runs on the
biology clock; scout switching is fast, so it runs on the real clock, every tick, like movement.

| Function | Params | Returns | Summary |
|---|---|---|---|
| `food_around(world)` | — | (N,) | Prey food summed over the squares within `absorb_radius` of each head; scraps don't count |
| `stringent(world)` | — | (N,) bool | `starve_time` ≥ `stringent_delay` (B83) |
| `update_starve_clock(world, dt_bio)` | — | None | Prey food ≥ `scout_food` (a real meal): clock 0. Otherwise, if the clock is running or prey food is below `living_food`: clock += dt_bio. Scraps never reset it (B83) |
| `starving_behaviour(world)` | — | (N,) bool | `starve_time` ≥ `behaviour_delay` (B84) |
| `starving_speed(world)` | — | (N,) | 1 + (`stringent_loner_speed` − 1)·min(`starve_time`/`stringent_speedup_time`, 1) (B75, B84) |
| `scout_chance(world, food)` | (N,) | (N,) | `scout_start_rate` × (1 − food/`scout_food`), clipped to [0, 1] (B83) |
| `update_scouts(world)` | — | None | Non-scouts start with chance `scout_chance`·dt; scouts stop when prey food is back at `scout_food` or with chance dt/`scout_episode`. Starving cells may scout. With `scout_start_rate` 0 everyone is set to non-scout and no random numbers are drawn (keeps the equivalence tests exact) |
| `mode_factors(world, scout_value, starving_value, starving)` | floats, (N,) bool | (N,) | 1 for ordinary cells, the scout value for scouts, the starving value for the `starving` cells (which wins) |
| `speed_factors(world)` | — | (N,) | 1; `scout_speed` for scouts; `starving_speed` for cells showing starving behaviour; the larger of the two for a starving scout (B83, B84) |
| `affinity_factors(world)` | — | (N,) | `mode_factors` with 1, `stringent_affinity`, stringent cells (B72, B84) |
| `smell_factors(world)` | — | (N,) | `mode_factors` with `scout_smell`, `stringent_smell`, cells showing starving behaviour; passed to `chemotaxis_factor` (B72, B84) |

### `myxo_famine.py`: the famine exit (B80)

A day after their prey food ran out, starving cells begin development and each takes one fate.
every tick in `engine.step_myxo`, right after the starvation clock.

| Function | Params | Returns | Summary |
|---|---|---|---|
| `starting_development(world, dt_bio)` | — | (N,) bool | `starve_time` reached `famine_time` in this tick (once per famine, since only a real meal resets the clock) |
| `draw_fates(world, n)` | int | (n,) | LYSE with chance `famine_lysis_share`, SPORE with `famine_spore_share`, else ROD |
| `lyse(world, rows)` | rows | None | Deposit what's left of each cell's store as scraps at its centre (no separate body, no matrix; B84); count them in `world.myxo_lysed` |
| `sporulate(world, rows)` | rows | None | Add the cells' centres to `world.spores` |
| `famine_exit(world, dt_bio)` | — | None | If `famine_exit` is on and someone is due: draw fates, lyse, sporulate, and remove both from the Myxo arrays; rods stay as they are. No random numbers are drawn unless a cell is due |

### `fields_update.py`: slow field changes

| Function | Params | Returns | Summary |
|---|---|---|---|
| `update_fields(world, dt_bio)` | — | None | regrow nutrients toward `richness`, then diffuse them; diffuse+fade food and scraps (B83); add the ghosts' smell (`ghost_attractant_rate` × matrix × dt_bio, B74), then diffuse+fade attractant; fade matrix, axis_c, axis_s by the same factor (matrix half-life → fade time = half-life/ln2); fade EPS, and `eps_scout` with fade time `eps_fade_time`·`scout_slime_fade` (B71) |
| `live_prey_maps(world)` | — | 3 coarse grids | Living E. coli per µm² (each cell spread over its k points), and the cos 2θ / sin 2θ of their colonies' ripple directions (B76) |
| `smooth_prey_material(world)` | — | None | `matrix_smooth`, `axis_c_smooth`, `axis_s_smooth` = disc averages of ghosts + `ripple_live_prey_weight` × living prey (B43, B76) |
| `refresh_sensed_maps(world)` | — | None | `smooth_prey_material`; run at every ground update and once when the world is built (the crowding map was removed in B84) |

### `colonies.py`: colony bookkeeping only (no reseeding, B44)

| Function | Params | Returns | Summary |
|---|---|---|---|
| `living_colonies(world)` | — | (C,) int array | Unique `ecoli.colony` values that still have living cells |
| `colony_sizes(world)` | — | dict ID → count | Cells per living colony, for stats and the on-screen display |

### `engine.py`: the only place that decides the order of events

| Method | Summary |
|---|---|
| `Simulation(settings, seed_cells=True)` | Build the `World`: grids, the EPS sensing table, then `initial_ground`, `initial_ecoli` and `initial_myxo`, in that order. `t = 0`. `seed_cells=False` leaves both populations empty, for validation runs that place their own cells |
| `turn(active, heading)` | Fast step 6 (alignment), split out of `step_fast` to keep it short. Followers lay into `eps`, scouts into `eps_scout`; followers sense both (B71) |
| `update_signal(active, heading, head_before, speed_factor)` | Fast step 7 (frustration into each active cell's memory). The intended velocity is speed·speed_factor·heading, so cells at their own speed aren't falsely jammed (B71) |
| `step_fast()` | Fast steps 1–10 from section 2, each a one-line call to the functions above. Active = `pause_left == 0`. Speed factors come from `myxo_modes.speed_factors`; `myxo_modes.update_scouts` runs right after the reversals |
| `step_cells()` | Cell-biology steps from section 2 with `dt_bio = dt·speedup`, every tick |
| `step_grids()` | Grid steps from section 2 with `dt_bio = grid_every·dt·speedup` |
| `step()` | `step_fast()`; `step_cells()`; every `grid_every` ticks, `step_grids()`; advance `t` and `step_count` |
| `run_for(real_minutes, callback=None)` | Loop `step()`; call `callback(world)` every frame interval if given |
| `bio_time()` | Biological minutes elapsed (sum of dt_bio, so it stays correct when the speedup slider changes) |

### `stats.py`

| Function | Returns | Summary |
|---|---|---|
| `snapshot(world)` | dict | t, bio time, Myxo count, E. coli count, number of colonies, mean Myxo energy, number rippling, number paused, number scouting, number in stringent mode, number at prey (B77), rods, spores and lysed so far (B80), scraps on the ground (B83) |
| `StatsLog.add(world)` / `StatsLog.to_csv(path)` | — | Append a snapshot each grid update; save it as CSV |

### `drawing.py`: renders onto a pygame `Surface` (shared by live and record)

Built 17 Oct 2026 (B90).

| Function | Summary |
|---|---|
| `View(box, size, centre=None, span=None)` | What a picture shows: the whole box, or a square `span` µm wide around `centre` (wrap-around safe). `to_screen(points)` µm → pixels (y up the screen); `crop(grid, spacing)` the part of a ground map in view |
| `grid_surface(rgb, alpha=None)` | A map (x first, y up) as a pygame Surface, flipped for the screen, optionally with per-pixel alpha |
| `draw_background(surf, world, view)` | Nutrients (cream = empty → light brown = rich), the matrix as a mauve tint (strength = matrix / ripple threshold), then slime (grey, alpha ∝ slime/0.5); each map smooth-scaled to the canvas |
| `draw_ecoli(surf, world, view)` | Each rod as a thick line with round ends, 1 µm wide in pixels (at least 1 px): magenta, dormant darker, dead-intact grey-pink |
| `draw_myxo(surf, world, view)` | Each cell as a polyline through its discs, 0.7 µm wide: green, brighter with the store (store/200); scouts yellow-green; cells in a killing pause with a white rim |
| `crosses_edge(a, b, view)` | Segments longer than half the box in pixels (where a cell crosses the wrap-around edge) are skipped |
| `draw_spores(surf, world, view)` | Pale green dots, 1.5 µm across |
| `draw_hud(surf, world, font, view, title)` | Top bar: (optional title,) biological time, E. coli (dormant), Myxo (killing, starving). Bottom bar: a two-line legend; a scale bar (20, 10 or 5 µm) |
| `draw_world(surf, world, font=None, view=None, title="")` | All of the above, back to front |

### `ui_widgets.py`: tiny home-made widgets (no extra library)

| Class / method | Summary |
|---|---|
| `Slider(label, lo, hi, value, step)` with `draw(surf, font)`, `handle(event) → bool changed`, `.value` | Horizontal slider |
| `Choice(label, options, index)` | Click to cycle through fixed options (colony count, starvation preset) |
| `Button(label, action)` | Calls `action()` on click |

### `app_live.py`: the interactive window (B1)

Built 17 Oct 2026 (B90), rebuilt to the user's design the same day (B91). As built:
- **Layout:** the world (square, sized to the screen, at most 820 px) with a Settings button at its
  top right; the counts graph below it (`drawing.draw_counts_graph`); the right panel (400 px) with
  playback speed, buttons and the main settings, scrolled with the mouse wheel (`ScrollList`).
- **Playback speed:** ×1 = real time up to ×600, or as fast as possible; each frame steps the world
  to keep up, within 0.12 s of computing.
- **Buttons:** Pause/Run, New world, Recommended, Record video (60 bio-h of the chosen settings in
  the background, live world), Save settings (`settings_live.json`).
- **Settings panel** (over the world and graph): advanced sliders, switches, the evidence options
  (recommended starred), the fixed values. Esc closes it.
- **What each control sets** comes from `app_params.py` (below). The chosen settings are kept as
  overrides of `make_settings("live")`; live ones are also written into the running world.
- **Keys:** space = run/pause, r = new world, s = screenshot to `../videos/`.
- **Headless test:** `python app_live.py --test N [--settings]` runs N frames without a screen and
  saves a screenshot.

### `app_params.py`: what the app lets you change (B91)

| Name | Summary |
|---|---|
| `Param(key, label, lo, hi, step, when, backing, fmt, changes, read)` | One adjustable setting. `when` is "live" or "reset". `changes(value, settings)` gives the settings it sets (e.g. efficiency also sets `uptake_rate` and `uptake_max`, B85; refill ÷N sets `nutrient_regrow_rate`). `read(settings)` gives the shown value back |
| `MAIN`, `ADVANCED` | The right panel's settings and the Settings panel's sliders |
| `Switch(label, off, note)`, `EFFECTS` | Rules that can be turned off, with the settings that do it; the app restores the previous values when one is turned back on |
| `Evidence(label, options, best)`, `EVIDENCE` | Rules where studies disagree: options of (label with source, settings), the recommended one first |
| `FIXED` | The fixed values shown with their sources |
| `RECOMMENDED` | The B89 settings plus every recommended evidence option: the app's starting point |

The plan:

The plan:
- **Window:** 1100 × 800. Canvas 800 × 800 on the left, panel on the right.
- **Live controls**, which change the running world at once:
  - `speedup`: 1–30.
  - `chemo_strength`: 0–5.
  - steps per frame: 1–100.
  - `grid_every`: 1–50 (B51), to compare batched against every-tick ground updates.
- **Reset controls**, which apply on Reset:
  - `start_colonies` choice.
  - starvation preset choice.
  - `energy_start`: 20–100.
  - seed.
- **Buttons:**
  - **Run/Pause**.
  - **Reset**: builds a new `Simulation`.
  - **Save settings**: writes `settings_live.json`.
  - **Record with these settings**: saves `settings_record.json` with box 500 and starts
    `run_record.py` in a subprocess.
- **Main loop:** handle events → if running, call `sim.step()` the chosen number of times →
  draw → 30 fps cap.

### `run_record.py`: headless video (B1)

Built 17 Oct 2026 (B90). As built:
- **Command:** `python run_record.py NAME [--scene world|closeup] [--grow 60] [--group-size 20]
  [--minutes 600] [--frame-every 0.25] [--seed 1] [--size 1024] [--fps 30] [--quality 8]
  [--encode-only] [setting=value ...]`.
- **Scenes:**
  - `world`: the live world from the start;
  - `closeup`: one colony grown alone for `--grow` real minutes, then four drops of 20 Myxo at its
    edge (`checks/check_penetration.grown_colony`), drawn with a `View` zoomed in on the colony.
- **Robust to stops:** each frame is saved as `../videos/NAME/frames/frame_#####.jpg`, with a
  checkpoint every `--save-every` real minutes. Starting the same command again carries on, and
  `--encode-only` joins the frames saved so far into `../videos/NAME.mp4` (imageio, libx264).
- **Also saves** `../videos/NAME/stats.csv`, and prints progress every 10 real minutes.

The plan:
- **Command:** `python run_record.py --settings settings_record.json --minutes 600 --frame-every 0.5 --out ../videos/run1.mp4`
- **Headless:** set `os.environ["SDL_VIDEODRIVER"] = "dummy"` before importing pygame. Draw
  each frame with `drawing.py` onto a 1000 × 1000 surface.
- **Writing:** `pygame.surfarray.array3d` → transpose → `imageio.get_writer(out, fps=30)`.
- **Output:** also saves `stats.csv` next to the video, prints progress every 10 real minutes,
  and makes the output folder if it's missing.

### `checks/`: milestone check scripts (pictures and comparisons, slower than tests)

| Script | What it shows |
|---|---|
| `check_ecoli_growth.py [bio_min] [seed] [max_cells]` | Milestone 2: E. coli colonies on patchy ground plus the growth curve (E. coli only) |
| `check_swarming.py [real_min] [seed]` | Milestone 3: the new engine at the reproduction's swarming quick-test settings vs `paper-reproduction/results` (ours and the authors') |
| `check_live_world.py [real_min] [seed] [name]` | Any milestone: a picture of the default live world (ground, slime, E. coli, Myxo) |
| `check_predation.py [grow_min] [attack_min] [seed]` | Milestone 4: one colony grown alone, then four drops of 20 Myxo at its edge. Snapshot strip plus touch statistics (touch durations, share of touches with a pause, pauses that killed, kills per touch) |
| `check_ripple_fading.py [real_min] [seed]` | Milestone 5: a disc of prey matrix makes Myxo ripple along its axis; as it fades the spot shrinks and cells drift back to swarming |
| `check_populations.py [real_min] [seed] [name] [setting=value ...]` | Milestone 6 onward: the full live world over time (4 snapshots plus population curves, `<name>.png` and `<name>_stats.csv`). `setting=value` pairs make variant runs (e.g. `myxo_groups=0 myxo_singles=0` for E. coli only). Saves a checkpoint (`<name>.ckpt`) every 30 real min of model time (5 bio-h); the same command carries on from it after a stop |
| `check_penetration.py [grow_min] [attack_min]` | B76: one grown colony and four drops of Myxo at its edge under rule variants: kills, cells killing at a time, Myxo deep inside |
| `check_staying.py [grow_min] [attack_min]` | B77: the same set-up under variants meant to hold the pack at the prey: kills, Myxo near the colony at the end, rippling cells |
| `compare_runs.py out run[:short[:long]] ... [--targets prey,myxo]` | B85: up to three population runs on one picture (`<out>.png`): E. coli on top, Myxo below, against bio-hours, with optional dashed target lines (or pale bands for ranges, e.g. `--targets 700-1000,150`); colour-blind-safe colours and labels at the line ends |
| `summarize_run.py name [name ...] [--every hours]` | B85: a table of a finished (or checkpointed) `check_populations` run every few bio-hours (prey, Myxo, stringent share, scouts, at prey, rippling, mean store, famine fates, food, scraps), then its highest prey and Myxo numbers |
| `prey_budget.py name [name ...] [--every hours]` | B87: where a run's prey go, per bio-h in each window: births, kills by Myxo and starvation deaths. Every burst leaves 1 unit of matrix fading with a 12 bio-h half-life, so bursts = dM/dt + fade × M; starved cells burst 2 bio-h after dying, so starvation deaths ≈ dead-intact cells / 2; kills = bursts − starvation deaths; births = net change + kills + starvation deaths |

Pictures go to `checks/output/`.

### `meanfield/`: the average-world model (B86)

A stand-in for the full simulation when exploring settings: the live world as three numbers that
change smoothly in time (mean ground nutrient n, living E. coli E, Myxo H), with each process read
off the full simulation's own runs. A 300 bio-h run takes about 0.05 s. It approximates the levels
(E. coli within about ×1.5, Myxo within about ×1.3), not the random swings; settings it picks must
be checked in the full simulation.

| File | What it does |
|---|---|
| `runs.py` | The finished runs it learns from (`RUNS`: name, efficiency, starving cost, richness and refill multipliers, the E. coli wake level and day of grace, and `fit`: False keeps a run out of fitting but still draws it) and `load(run)` for their stats |
| `model.py` | `World` (settings in model units), `Fitted` (learned numbers), `rates`, `dormant_death_rate` (E. coli starvation worked out from the sim's wake-up rule), `rhs`, `simulate(world, fitted, hours)`, `world_for(run)` |
| `fit.py [--holdout name ...]` | Learns the free numbers by least squares on the whole curves of each training run (every run with `fit` True that isn't held out) (log E. coli, log Myxo, ground); prints the mismatch per run, held-out runs included; writes `fitted.json` |
| `compare.py [out]` | Model against every run, one panel each (`checks/output/<out>.png`) |
| `scan.py [prey_lo prey_hi myxo_lo myxo_hi] [--search k]` | Runs every combination of refill speed, richness, efficiency (5–60%) and E. coli wake level for 300 bio-h; marks those that stay in the target ranges from 60 bio-h on; `--search k` makes hunters k times better at finding prey (`meanfield_scan*.png`, `.csv`) |

### `tests/`: pytest, fast, no plotting

| Test file | Checks |
|---|---|
| `test_geometry.py` | `min_image`, `wrap_points`, `rod_points` (end points at ±(L − width)/2), and the doubled-angle axis encoding (10°/190° → 10°; 0°+60° → 30°) |
| `test_state_settings.py` | `append_rows`/`keep_rows` keep columns in step; IDs never reused; settings modes, presets and JSON round-trip |
| `test_grids.py` | `diffuse` conserves the total and spreads a spike; `regrow` approaches the ceiling grid; `random_patches` stays within [lo, hi]; `deposit` adds repeated points; `sample` matches `deposit` |
| `test_reversals.py` | `frustration` gives the worked cases in `model-foundations.md` §3.4; the refractory period and rate match the paper-reproduction functions; frozen (inactive) cells keep `mem_slot` and age |
| `test_ecoli.py` | One seed with plenty of nutrients doubles in about 20 bio min (±5%); division conserves total length; size and speed spread ±10%; no growth at zero nutrient; dormancy, starvation death and delayed lysis; a dormant cell needs a real meal to wake, and freshly dormant cells already die at the measured rate (B87); persisters are drawn for each newborn, so persister mothers have about 5% persister daughters (B88); lysis writes the colony direction; growing colonies don't overlap |
| `test_myxo.py` | Frustration worked cases; reversal curves and per-cell memory identical to the reproduction; a free cell moves at 4 µm/min; paused cells stand still with clock and memory frozen; reversal swaps head and tail; the pull toward prey only acts when switched on; scouts ignore slime; scouts and starving loners glide at their own speeds; smell and affinity boosts; starving speed by crowding; a starving scout is never slower; the starvation clock follows prey food, not the store; 10% scout at zero prey food and about half get a turn in 10 bio-h; scouting needs scarce prey food; seeds start away from colonies and come in over 10 bio-h |
| `test_energy.py` | A newborn's store lasts the preset; stringent mode cuts costs to 30% on the core, after burning the surplus above 100 at the full rate (B84, B85); one E. coli gives 30 below 200 and a third of that in the reserve; uptake sharing favours hungry cells; eating within 2 µm only; no free energy from rounding noise; division needs a doubled store (two newborns of 100), never for scouts or stringent cells; a cell that starved to zero leaves nothing (B84); scraps fill a store only to 30, prey food past it (B83); at 30% a cell grows exactly as fast as at 50% but uses 5/3 as much food (B85) |
| `test_predation.py` | Prey found by ID after other cells die; about 30% of Myxo pause during 0.5 min of touching; a finished pause kills about 80% of the time (1,000 trials); a kill leaves food, smell and wall; in the running engine a Myxo beside prey pauses, stands still and kills it |
| `test_famine.py` | A day into stringent mode about 70% lyse, 10% sporulate and 20% stay as rods, and rods aren't redrawn; lysis spills only the store, as scraps, no prey food or matrix (B84); no fates (and no random numbers) before a day, after feeding, or when switched off; the fates happen in the running engine; scraps and thin prey food don't postpone the famine; lysis spills scraps (B80, B83) |
| `test_equivalence.py` | The Myxo engine matches `paper-reproduction` tick for tick (positions and signals) for 400 ticks from identical cells and random numbers (A13) |
| `test_engine_smoke.py` | 60-cell world for 200 steps: no NaN, all cells inside the box, arrays the same length |

## 6. Build milestones (in order, with a check after each)

1. **Skeleton.** `settings.py`, `state.py`, `geometry.py`, `grids.py`, the tests for them, and
   the requirements.
   - **Check:** `pytest` passes.
2. **E. coli only.** `seeding` (E. coli), `ecoli_body`, `ecoli_life`, `contacts` (E. coli
   only), the `fields_update` nutrient part, and `colonies`.
   - **Check:** a picture after about 300 bio min (live box) showing round colonies with no
     overlaps; growth slows at the centre.
   - **Check:** doubling time in plenty of food ≈ 20 bio min.
   - **Show:** a plot of cell count against bio time.
3. **Myxo swarming among colonies.** E. coli are obstacles only, with no predation yet. Add
   `myxo_body`, `myxo_alignment` (EPS only), `myxo_reversals` and full `contacts`.
   - **Check:** at the paper-reproduction swarming settings (370 Myxo, box 65, no E. coli),
     the mean time between reversals is about 3.5–4.0 min and unimodal. Compare with
     `paper-reproduction/results/swarming_seed1.npz`.
4. **Predation.** `predation.py`, plus food, attractant and matrix deposits.
   - **Check:** a colony is eaten from the edge inward, about 26% of touches kill (measure it
     from logs), and paused cells stand still.
5. **Rippling and fading.** `ripple_mask`, `local_axis`, `ripple_turn`, and matrix fade.
   - **Check:** waves along the colony's axis on the digested area (show a picture and a
     kymograph along that axis), and cells drift away as the matrix fades.
   - **Check:** with box 65, matrix 1 everywhere and axis 0, the time between reversals is
     two-peaked like `rippling_seed1.npz`.
6. **Energy.** `myxo_energy.py` and the chemotaxis factor.
   - **Check:** population curves over a long live run make sense: growth after feeding, and
     starvation deaths far from prey.
   - **Check:** turning `chemo_strength` from 0 to 2 shortens the time to find the first
     prey (average over 3 seeds).
7. **App.** `drawing.py`, `ui_widgets.py`, `app_live.py`.
   - **Check:** the user runs it; the sliders work; Reset applies the reset settings.
   - **Done 17 Oct 2026 (B90):** checked headless (`--test`); waiting for the user's own run.
8. **Recording.** `run_record.py` with `stats.csv`.
   - **Check:** a 30-min test video plays. Ask the user before the full 500 µm run.
   - **Done 17 Oct 2026 (B90):** a 100 bio-h video of the live world and a close-up of one colony;
     the 500 µm run was not made (too slow for the deadline).

## 7. Open items (don't decide alone; ask the user)

- **Final visual style:** colours, what's shown, zoom.
- **Verify:** Ferenci (B26) and Thiery 2022 before citing them.
- **The authors'-code comparison (A9):** a separate task in `paper-reproduction/`, not part of
  this build.
- **Changes to any [tuned] default:** log them in `decision-log.md` with the reason.
