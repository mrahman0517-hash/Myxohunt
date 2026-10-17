# Parameter review: what's backed by biology and what's ours

A snapshot of every setting in `predation-sim/settings.py` on 16 Oct 2026 (after B88), sorted
by how well it's backed. "B" numbers point to `decision-log.md`; papers are in `sources.md`.

## How to read the "Backing" column

| Label | Meaning |
|---|---|
| **Paper** | From Saulnier et al. 2026's model, fitted to their experiments and validated in our rebuild (A11, A13) |
| **Code** | From the authors' released code (numerical choices inside their model) |
| **Measured** | A value measured in the literature |
| **Anchored** | Set so that the model reproduces a measured rate or share |
| **Direction backed** | Biology says which way it goes; the size is our guess |
| **Tuned** | Adjusted by watching the simulation; no measurement exists |
| **Assumed** | Our guess; no measurement exists |
| **Your choice** | A design choice you made (seeds, world size, presets) |
| **Technical** | A computing setting, not biology |

## Summary

| Backing | Count | Where they are |
|---|---|---|
| Paper | 18 | Myxo body, reversals, slime trails, rippling turn |
| Code | 8 | Time step, slime grid, numerical details |
| Measured | 19 | E. coli size, doubling, division spread and starvation death (from the start of starvation), killing (Seef 2021), food efficiency, starving speed-up, scout speed, the famine exit |
| Anchored | 3 | Pause rate, uptake ceiling (5.5 h generation), prey value |
| Direction backed | 7 | Doubling before division, stringent cost cut, rippling on prey, starving cells' smell, the famine switch |
| Tuned | 16 | Ground, smell, spreading, fading, colony size |
| Assumed | 31 | Food sharing, stringent details, newcomers, ripple trigger details, the starving food level and the two delays, how fast a starving E. coli's contents shrink |
| Your choice | 16 | Seeds, world size, speed-up, starvation preset, scrap cap, scouting share and level, E. coli's meal level |
| Technical | 6 | Grid updates, contact points, units |
| **Total** | **124** | |

- **Well backed:** how a Myxo moves, swarms and ripples (27 numbers from the paper and its
  code); how it kills (Seef 2021); how fast both species can grow.
- **Ours:** almost all of the ecology: how much food the ground holds and refills, how spilled
  food spreads and fades, the energy bookkeeping, scouts, the prey smell and the newcomers.
- **So:** the speed of every process is mostly backed by measurements, but *where the
  predator–prey balance settles* is decided by tuned and assumed numbers, plus two rules that
  have no number at all (see below).

## The balance levers

The settings and rules that decide whether populations stay in balance or boom and crash.

**A guide from the textbook predator–prey model (Rosenzweig & MacArthur 1963; B85):** the prey
settle near the level at which a hunter just breaks even, so the *hunter* levers below set the prey
number; the hunters settle at the number the prey's growth at that level can feed, so the *prey*
levers set the hunter number. Weaker hunters therefore mean fewer hunters but more prey. B85 also
found a trap: a poorer ground kept the early colonies too small for the arriving hunters to find,
so the first prey wave overshot.

### Predators: gains

| Lever | Now | Backing | Effect on the balance |
|---|---|---|---|
| `efficiency` | 0.30 (0.50 before B85) | Measured (range 5–60%; del Giorgio & Cole 1998) | Share of eaten food kept: a division now takes about 3.3 E. coli instead of 2, so each prey feeds fewer hunters (B85) |
| `uptake_max` | 8.3 food/bio-min (5 at 50%) | Anchored (5.5 h generation on prey; Seef 2021) | Top growth speed of a well-fed Myxo; divided by the efficiency (as is `uptake_rate`), so cells grow as fast as before and only use more food (B85) |
| `division_threshold`, `energy_full` | 190, 200 | Direction backed (cells double their contents first; Taheri-Araghi 2015) | About 3.3 kills' worth per division at 30% (2 at 50%) |
| `ecoli_content` | 100 | Anchored (E. coli ≈ one Myxo cell's worth, from their sizes) | Food per kill |
| `killer_share` | 0.25 | Assumed (your number) | 75% of each kill spills for others |
| `food_diffusion` | 5 µm²/bio-min | Tuned | Spills spread about 120 µm in 12 h, so every Myxo in the world shares every kill |
| `food_decay_time` | 12 bio-h half-life | Assumed | How long uneaten spills last |
| `absorb_radius` | 2 µm | Assumed | How far from its head a cell collects spilled food |

### Predators: losses

| Lever | Now | Backing | Effect on the balance |
|---|---|---|---|
| `starvation_preset` | slow (a newborn's 100 lasts 24 bio-h) | Your choice (survival data disputed) | How fast a hungry cell runs down |
| `living_food`, `stringent_delay`, `behaviour_delay` | 1 unit of prey food within reach; 30 bio-min for the fast effects, 2 bio-h for the behaviours | Mechanism backed (Manoil & Kaiser 1980; Harris 1998), numbers ours | Starvation starts when prey food runs out, not when the store runs low (B83, B84) |
| Meal level, `scrap_cap` | prey food above 3 units ends starvation; scraps fill a store only to 30 | Switch-like response backed (Hoang & Kroos 2018); numbers yours | Crumbs and scraps keep starving cells alive without ending their starvation, so famines come on time (B83) |
| `starvation_upkeep` | 0.3 (costs cut to 30%; 0.1 before B85) on the core only | Direction backed (stringent response), size ours | A starving cell burns anything above a newborn's 100 at the full rate first (stored fuel first, Hoiczyk 2009), then pays 30%: its core would last about 3.3 bio-days (10 at 0.1), but the famine exit comes after 1; in that day it loses about 30 units instead of 10 (B80, B84, B85). (An earlier version of this table said "about 10 bio-days" for the last 20 units, my arithmetic error: those lasted about 2.) |
| `famine_time`, `famine_lysis_share`, `famine_spore_share` | a day after prey food ran out: 70% lyse, 10% spores, 20% rods | Measured (Lee 2012; classic counts 60–80% lysis, disputed; O'Connor & Zusman 1991) | The brake: most starving hunters leave a day after their prey food ran out, and their scraps keep the rest alive (B80, B83) |

### Predators: spreading out

| Lever | Now | Backing | Effect on the balance |
|---|---|---|---|
| `scout_start_fraction`, `scout_start_rate` | below 3 units of prey food within reach; 10% at once at zero food | Your choice (no measured share) | Who explores: cells short of prey food, starving or not; the store plays no part (B83) |
| `scout_episode` | 10 min | Assumed | Spells end at random, so cells take turns |
| `chemo_strength` | 2 | Tuned (mechanism backed: Kearns & Shimkets 1998) | How strongly the smell biases movement |
| `scout_smell`, `stringent_smell` | 1.5×, 1.5× | Assumed / direction backed (Kearns 2001) | Hungry scouts and starving cells follow the smell more (B72, B80) |

### Prey

| Lever | Now | Backing | Effect on the balance |
|---|---|---|---|
| `ecoli_doubling` | 20 bio-min | Measured (rich medium) | Top prey growth speed |
| `nutrient_per_um` | 0.5 | Tuned (B78) | Colony size; 0.3 runs away, 1 stays small |
| `nutrient_regrow_rate` | 1/3000 per bio-min | Tuned | How fast bare ground recovers (half-way in about 35 bio-h) |
| `nutrient_diffusion` | 0.1 µm²/bio-min | Tuned (B78) | How far a colony reaches for food |
| `richness_min`, `richness_max` | 0.3, 1.0 | Assumed | How rich the ground can be. ×0.5 or ×0.35 (B85 test) kept early colonies too small for the arriving hunters to find, and the first prey wave overshot to 1,300–2,800 by 48 h |
| `ecoli_seed_interval` | 6 bio-h | Assumed | How often new prey appears |

### Newcomers

| Lever | Now | Backing | Effect on the balance |
|---|---|---|---|
| Myxo seeds | 5 × 20 + 10 over the first 10 bio-h | Your choice; arrival window assumed | How many hunters start the wave |

## Literature search for 16 settings (11 Oct 2026)

Details and links are in `sources.md`.

| Setting (now) | What the search found | Status |
|---|---|---|
| `ecoli_divide_noise` (±10%) | Spread of division length about 10% (BioNumbers 110034; 13.5% in an older study) | **Measured**, value unchanged |
| `starved_lysis_delay` (30 bio-min) | Lysis 2.0 ± 1.4 h after the voltage collapse (Schink et al. preprint) | **Adopted in B80:** 120 bio-min |
| `starvation_death_rate` (1 per bio-day) | Viability falls to 0.1% in 10 days, about 0.69 per day (Schink et al. preprint) | **Adopted in B80:** 0.69 per bio-day |
| `scout_speed` (1.2×) | Wild-type cells glide at 4.4 µm/min (Spormann & Kaiser 1999); the model uses 4 | **Adopted in B80:** 1.1× |
| `starvation_level` (store below 20) | Running out of amino acids, carbon or phosphate outside raises (p)ppGpp "rapidly"; development starts within hours (Manoil & Kaiser 1980; Harris 1998) | **Applied in B83:** starvation starts when prey food within reach runs out |
| `stringent_smell` (1×) | The PE attractant works only under starvation, and nutrients block it (Kearns 2001). One review reports PE raising reversals in starved cells (sign unclear) | **Adopted in B80:** ×1.5, as for scouts (the size is ours) |
| `starvation_preset`, `starvation_upkeep` (once stringent, the last 20 units last about 2 days) | Real starving Myxo don't just wait. From about 24 h about 60% (classic counts 60–80%) lyse, about 10% become spores, and 10–20% stay as peripheral rods (Lee 2012; O'Connor & Zusman 1991; a review) | **Adopted in B80** as the famine exit: 70% / 10% / 20%, a day into stringent mode |
| `dormancy_before_death` (24 bio-h) | No fixed lag: in carbon starvation viability falls from early on (Schink); in rich batch culture the onset varies by hours to days (Finkel) | **Adopted in B87:** no lag (0) |
| `starved_content_min` (25%) | Survivors recycle dead cells' biomass (Schink 2019), but no share is given | Stays assumed (direction backed) |
| `chemo_strength`, `chemo_factor_range` | PE suppresses reversals and cells adapt after about 1 h (Kearns & Shimkets 1998); the size is only in the blocked full text | Stay tuned / assumed |
| `scout_start_rate`, `scout_episode` | Switching is very frequent and equally likely both ways; scouts are groups of 1–20 cells (Rombouts 2023). Rates and class shares only in figures | No measured share; since B83 the rate gives your 10% at once |
| `scout_turn_noise` | Only in figures (Rombouts 2023) | Stays assumed |
| `matrix_half_life` | Ripples form once prey is fully digested and persist "over extended periods"; a colony is digested within 48 h (Saulnier 2026) | Stays tuned |
| `matrix_ripple_threshold` | Murein from many bacteria triggers ripples, but no dose is given (Shimkets & Kaiser 1982) | Stays tuned |

- **Outcome:** 4 numbers have measured values (1 already right, 3 adopted in B80). 2 rules and 1
  new rule now have biological backing (the smell boost and the famine exit adopted in B80; the
  stringent trigger waits for your decision). 9 stay ours: their values exist only in figures or
  blocked full texts, or were never measured.
- **Against an earlier decision:** the main paper says ripples form "once the prey has been
  entirely digested". That counts against B76, where living prey also trigger rippling. You
  chose to follow Berleman 2006 and keep B76 (B79).

## Full list

### World and computing

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `box` | 150 µm (record 500) | Your choice | B2 |
| `seed` | 1 | Technical | Repeatable runs |
| `dt` | 0.005 min (0.3 s) | Code | A7 |
| `grid_every` | 20 ticks | Technical | B51 |
| `speedup` | 10× | Your choice | B4; slow biology only, movement stays real |
| `coarse_grid` | 1 µm | Technical | B35 |
| `eps_grid` | 0.3 µm | Code | B35 |

### Myxo body and movement

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `n_nodes`, `node_spacing` | 10 discs, 0.5 µm | Paper | 5 µm cell; the literature gives 5–7 µm |
| `disc_diam` | 0.7 µm | Paper | Measured width in the paper |
| `speed` | 4 µm/min | Paper | Literature 2–4 µm/min |
| `k_spring`, `k_rep` | 50, 450 | Paper | |
| `traction_scale`, `spring_passes_per_node` | 10, 5 | Code | A7 |

### Reversals (the frustration rule)

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `R_star`, `R_min` | 5 min, 20 s | Paper | Longest and shortest lock-out after a reversal |
| `f_T`, `alpha_F`, `alpha_R` | 0.08, 75, 100 | Paper | A7 |
| `memory` | 20 s | Paper | |
| `F_star`, `beta` | 3/min, 2/min | Code | A2, A7 |

### Slime trails and rippling

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `gamma_ripple`, `gamma_eps` | 11/min, 11/min | Paper | |
| `sense_radius`, `view_angle`, `eps_c_min`, `eps_deposit` | 5 µm, 180°, 0.1, 2 | Paper | |
| `n_sectors`, `eps_choice_tolerance` | 5, 0.8 | Code | |
| `eps_fade_time` | 360 bio-min | Tuned | B31, B64 (your choice of 6 h); trail decay has never been measured; the authors' code uses about 100 h |
| `matrix_ripple_threshold` | 0.3 per µm² | Tuned | B43 |
| `matrix_sense_radius` | 3 µm | Assumed | B43 |
| `ripple_live_prey_weight` | 1 | Direction backed | Contact with prey triggers rippling (Berleman 2006); B76, kept in B79 |
| `matrix_per_ghost` | 1 | Tuned | A unit |
| `matrix_half_life` | 12 bio-h | Tuned | B12; how long ghosts last is unmeasured |

### Prey smell (chemotaxis through reversals)

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `chemo_strength` | 2 | Tuned | The mechanism is backed (Kearns & Shimkets 1998; Berleman 2008); the strength isn't |
| `chemo_factor_range` | 0.2–5× | Assumed | |
| `attractant_per_lysis` | 1 | Tuned | |
| `ecoli_attractant_rate` | 2 per bio-min | Assumed | B63; plausible (outer-membrane vesicles, PE), not shown |
| `ghost_attractant_rate` | 2 per bio-min | Assumed | B74 |
| `attractant_diffusion`, `attractant_decay_time` | 50 µm²/bio-min, 60 bio-min | Tuned | |

### E. coli

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `ecoli_width`, `ecoli_birth_length`, `ecoli_divide_length` | 1, 2, 4 µm | Measured | BioNumbers |
| `ecoli_doubling` | 20 bio-min | Measured | Rich medium |
| `ecoli_speed_noise` | ±20% | Measured (roughly) | B55; mother-machine studies |
| `ecoli_divide_noise` | ±10% | Measured | B53; spread of division length about 10% (BioNumbers 110034) |
| `monod_half_saturation` | 0.2 | Assumed | Nutrient units are ours |
| `nutrient_per_um` | 0.5 | Tuned | B78 |
| `ecoli_mobility` | 1 | Tuned | |
| `dormant_threshold` | 0.01 | Assumed | Below it a growing cell goes dormant |
| `wake_threshold` | 0.2 | Your choice | B87; a real meal wakes a dormant cell and restarts its starvation clock (the Monod half-speed level); a trace no longer does |
| `dormancy_before_death` | 0 (none) | Measured | B34, B87; viability falls from the start of starvation (Schink et al.); 24 bio-h before |
| `starvation_death_rate` | 0.69 per bio-day | Measured | B34, B80; viability falls to 0.1% in 10 days (Schink et al.) |
| `persister_fraction` | 5% | Measured | Finkel 2006: 1–10% survive long-term. Each newborn draws its own chance; daughters don't inherit it (B88; inherited before, so one colony in 20 never starved) |
| `starved_lysis_delay` | 120 bio-min | Measured | B45, B80; lysis 2.0 ± 1.4 h after the voltage collapse (Schink et al.) |
| `starved_content_min` | 25% | Assumed | B45 |
| `starved_shrink_time` | 24 bio-h | Assumed | B45, B87; how long a starving cell's contents take to shrink to 25% (was tied to the day of grace) |
| `ecoli_points` | 5 per rod | Technical | |

### Ground

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `nutrient_regrow_rate` | 1/3000 per bio-min | Tuned | B68 |
| `richness_min`, `richness_max` | 0.3, 1.0 | Assumed | B48 (your "moderate" range); units are ours |
| `patch_size` | 30 µm | Tuned | B48 |
| `nutrient_diffusion` | 0.1 µm²/bio-min | Tuned | B78; real small molecules spread thousands of times faster (our world is shrunk) |
| `nutrient_start_min`, `nutrient_start_max` | 30–100% of each patch's maximum | Assumed | B78 |

### Spilled food

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `ecoli_content` | 100 | Anchored | B75; similar cell sizes (BioNumbers; the paper's Myxo size) |
| `food_diffusion` | 5 µm²/bio-min | Tuned | B17 |
| `food_decay_time` | 12 bio-h half-life | Assumed | B74 |

### Killing

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `pause_rate` | 0.71/min while touching | Anchored | About 30% of touches pause (Seef 2021) |
| `kill_delay` | 2 min | Measured | Seef 2021 |
| `kill_success` | 80% | Measured | Seef 2021 |
| `scale_predation` | on | Your choice | B66: kills run on the biology clock |
| `touch_distance` | 0.95 µm | Technical | Half-widths plus a margin |
| `prey_contact_signal` | off | Assumed rule, switched off | B62, B76 |
| `myxo_crawl_over_prey` | on | Assumed | B76; stands in for the 3D colony Myxo penetrate (Seef 2021) |
| `ecoli_push_share` | 0.8 (unused while crawling) | Assumed | B62 |

### Myxo energy

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `energy_newborn` | 100 | Technical | The unit: one normal newborn |
| `energy_full`, `division_threshold` | 200, 190 | Direction backed | B75; cells double before dividing (Taheri-Araghi 2015) |
| `energy_cap` | 210 | Assumed | B22 |
| `efficiency` | 30% | Measured (range) | B21, B75, B85; del Giorgio & Cole 1998 (5–60%); 50% in B75 |
| `reserve_efficiency` | ⅓ of `efficiency` (10%) | Direction backed | B22; storage costs extra (Hoiczyk 2009), the third is ours; follows `efficiency` automatically since B85 |
| `uptake_rate` | 0.83 per bio-min (0.5 at 50%) | Tuned | B85: divided by the efficiency, so the store gained from thin food is unchanged |
| `uptake_max` | 8.3 per bio-min (5 at 50%) | Anchored | B65, B75, B85; 5.4 h mean generation vs 5.5 h measured (Seef 2021); at 30% without re-anchoring it would be 8.9 h |
| `division_rate_max` | 1/60 per bio-min | Tuned | |
| `killer_share` | 25% | Assumed | B76; your number |
| `energy_start` | 60 | Your choice | B20 |
| `starvation_preset` | slow (24 bio-h) | Your choice | B23; survival data disputed |
| `living_food` | 1 unit of prey food within reach | Assumed | B83; below it a cell is starving outside and its clock starts (was `scout_food_threshold`, B71) |
| `stringent_delay` | 30 bio-min | Assumed | B83, B84; the fast effects (cost cut, no division, better uptake): the alarm (p)ppGpp rises fast (Manoil & Kaiser 1980) |
| `behaviour_delay` | 2 bio-h | Assumed | B84; the starving behaviours (keener smell, speed-up): "the first few hours" of starvation recognition (Harris 1998) |
| `scrap_cap` | 30 | Your choice | B83; scraps from dead Myxo keep a cell alive but never end its starvation |
| `starvation_upkeep` | 30%, on the core only | Direction backed | B70, B84, B85; the stringent response cuts costs (Singer & Kaiser 1995); stored fuel above a newborn's 100 is burned first at the full rate (Hoiczyk 2009); 10% before B85 |
| `stringent_loner_speed` | 1.5× | Measured | Jelsbak 2002 |
| `stringent_speedup_time` | 15 bio-h | Measured | Jelsbak 2002 |
| `stringent_affinity` | 1.15× | Assumed | B72; by analogy with E. coli "hunger" (Ferenci) |
| `famine_exit` | on | Direction backed | B80; starving Myxo leave through development. Ours is simplified: no fruiting bodies, and spores don't germinate yet |
| `famine_time` | 24 bio-h after prey food ran out | Measured | B80, B83; lysis and aggregation begin about 24 h after starvation (Lee 2012) |
| `famine_lysis_share` | 70% | Measured | B80; classic counts 60–80%, disputed (O'Connor & Zusman 1988 found ≥80% survive) |
| `famine_spore_share` | 10% (the other 20% stay as rods) | Measured | B80; about 10% spores; 10–20% peripheral rods (O'Connor & Zusman 1991) |

### Scouts

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `scout_start_rate` | 0.011 per real min at zero prey food | Your choice | B83; 10% of cells short of prey food scout at any moment, about half get a turn within 10 bio-h; no measured share exists |
| `scout_episode` | 10 min | Assumed | B70, B71; that cells switch often is backed (Rombouts 2023), the timing isn't |
| `scout_start_fraction` | 0.3 of top-speed food (3 units) | Your choice | B83; scouting starts below it, and a starving cell's real meal is above it |
| `scout_turn_noise` | 0.2 rad²/min | Assumed | B67 |
| `scout_speed` | 1.1× | Measured | B71, B80; lone cells glide at 4.4 µm/min (Spormann & Kaiser 1999), against the paper's 4 |
| `scout_slime`, `scout_slime_fade` | 2×, 2× | Assumed | B71 |
| `scout_smell` | 1.5× | Assumed | B72; starving cells follow the lipid smell (Kearns 2001), no study singles out scouts |
| `stringent_smell` | 1.5× | Direction backed | B80; the lipid attractant works only in starving cells (Kearns 2001); the size is ours |
| `absorb_radius` | 2 µm | Assumed | B71; extracellular digestion is backed, the reach isn't |

### Seeds and newcomers

| Setting | Value | Backing | Source or note |
|---|---|---|---|
| `myxo_groups`, `myxo_group_size`, `myxo_singles` | 5, 20, 10 | Your choice | B78 |
| `myxo_group_radius` | 6.5 µm | Assumed | Same packing as earlier groups |
| `myxo_arrival_window` | 10 bio-h | Assumed | B78 |
| `myxo_min_dist_colony` | 30 µm | Your choice | B47 |
| `ecoli_seed_interval` | 6 bio-h | Assumed | B75, B78 |
| `start_colonies`, `seed_min_dist_ecoli` | 2, 75 µm | Your choice | B44, B56 |
| `colors` | magenta / green | Your choice | B41, provisional |

## Rules that have no number

Some of what decides the balance isn't a setting at all.

| Rule | Now | Backing |
|---|---|---|
| Killing on contact | Yes | Measured (Seef 2021) |
| Rippling on prey material (ghosts and living prey) | Yes | Backed (Shimkets & Kaiser 1982; Berleman 2006) |
| Swarming along slime trails | Yes | Paper |
| No division while starving | Yes | Backed (stringent response) |
| Starving Myxo leave the world (spores, fruiting bodies or lysis) | **Yes since B80:** lysis and spores a day into stringent mode; no fruiting bodies, and spores don't germinate yet | Measured shares and timing (Lee 2012; O'Connor & Zusman 1991) |
| Stringent mode starts when food runs out outside the cell | **Yes since B83** (30 bio-min after prey food within reach runs out) | Backed (Manoil & Kaiser 1980; Harris 1998); the delay is ours |
| Scraps from dead Myxo keep cells alive but never end starvation | **Yes since B83** (a store up to 30) | Fits developmental lysis feeding survivors; a small dose of food doesn't stop starvation (Hoang & Kroos 2018) |
| Who scouts | Cells short of prey food (below 3 units within reach), starving or not; the store plays no part (B83) | Your design; no measured share |
| Crowding slows division | No | No evidence found either way |
