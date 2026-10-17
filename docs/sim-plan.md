# *M. xanthus* Predation Simulation — Project Plan

## What we're building

A 2D physics simulation, rendered with a 3D-style surface, of *Myxococcus xanthus* predating growing, randomly-nucleating *E. coli* colonies. As Myxo digests prey, the digested ground becomes rippling territory; prey-free ground stays swarming territory. Both movement modes run on the *same* reversal rule (cells flip direction when congested) — only the alignment rule differs between zones. This is grounded in Saulnier et al. 2026 (*Nat. Phys.*, DOI: [10.1038/s41567-026-03416-y](https://doi.org/10.1038/s41567-026-03416-y)) plus their released code, [github.com/MignotLab/SpatialPatternsCollectives](https://github.com/MignotLab/SpatialPatternsCollectives) (MIT license), which implements everything the paper describes for one fixed prey patch. The growth / feeding / 3D layer is ours to design.

## Status at a glance

| Layer | Status | Source |
|---|---|---|
| Cell body & motion | Have | Methods + repo |
| Reversal rule (frustration → RP, rate) | Have, with 2 numeric conflicts flagged | Methods + `reversals.py` |
| Swarming alignment (EPS trails) | Have | `extracellular_matrix.py` |
| Rippling alignment | Have, but the axis is imposed, not derived | Fig. 4c + `alignment.py` |
| Theory tier (1D PDE, stability) | Have — optional for a live sim | Fig. 2 + `guzzo/` |
| Calibrated parameters | Have, 4 categories | Methods |
| Validation targets | Have | Figs. 1, 3, 5, 6 |
| Prey growth / nucleation | Missing | — |
| Feeding / kill / digestion rate | Missing | — |
| Prey → rippling trigger | Missing (paper imposes one fixed axis) | — |
| Predator birth/death | Missing (paper conserves N exactly) | — |
| "3D" | Not modeled anywhere in the source | Rendering choice only |
| Live performance at paper scale | Concern | NumPy + KD-tree, built for offline runs |

---

## Two things worth re-anchoring on, mid-read

**It's spatial, not a feed → ripple → swarm timer.** Per cell, yes, the switch happens in time — swarm while a patch still has food, ripple once that patch is exhausted and starving. But at the population level, rippling and swarming are two *standing* zones that coexist side by side, separated by a sharp boundary tracking the original prey footprint. Rippling only ever appears where digested prey matrix has been laid down, and stays there. It isn't "prey gone everywhere, so now everyone ripples" — it's "wherever the ground carries prey matrix, cells there ripple; everywhere else, they swarm." A single cell crosses that boundary and switches within minutes.

**Reversals aren't governed by density; they're governed by congestion.** The paper tests both local density and directional density as reversal triggers and finds neither explains swarming reversals, and only a weak correlation for rippling. What generalizes across both zones is *frustration* — how far a cell's actual velocity deviates from where it "meant" to go — and that one signal drives both the refractory period and the post-refractory reversal rate. So there's one reversal rule for the whole sim, not a rippling-only "density-dependent reversal" rule. What's rippling-only vs. swarming-only is purely the alignment rule.

---

## What we already have

### 1. Single-cell body & motion
Each cell is a chain of 10 point-nodes ("discs") linked by springs, 0.5 µm apart, giving a ~5 µm body at 0.7 µm width. The head node is tracted forward along the body axis at a constant 4 µm/min; the rest of the chain follows. A Hookean spring along the chain (k_s = 50 min⁻¹) keeps body shape, and short-range repulsion between any two nodes (k_r = 450 µm⁻¹min⁻¹) stops overlap. Integration step: dt ≈ 0.005 min (~0.3 s). Packing into groups isn't a separate rule — it falls out of repulsion + trail-following + alignment acting together.

### 2. The reversal rule
Every cell carries a clock, r = time since its last reversal (the model's stand-in for the real RomR-relocation timer). No reversal while r < RP; past that, it reverses at rate R. Both RP and R are driven by one signal, frustration f:

f = 1 − (v_target·v_actual) / max(|v_target|², |v_actual|²)

v_target is the velocity the cell "should" have with nothing in its way (its own body-axis direction at constant speed); v_actual is what it really achieved that step. f is smoothed over recent history so one frame can't flip a decision.

RP and R move in opposite directions as f rises:

- RP(f) = R* − (R* − R_min)/(1 + e^(−α_R(f−f_T)))
- R(f) = F* / (1 + e^(−α_F(f−f_T)))

with R*=5 min, R_min=20 s, f_T=0.08, α_R=100, α_F=75 (all fit to the measured reversal-interval distributions, not derived from first principles).

**Flag before hardcoding:** F* is 30 min⁻¹ in the paper's Methods text, but the released 2D code uses 3 min⁻¹, and the separate 1D PDE code uses a third value (10 min⁻¹) for its own, differently-scaled model. Not necessarily errors — the 1D and 2D models are independently calibrated — but don't carry one model's F* into another; sanity-check whichever we pick against the TBR means (≈3.2 min rippling, ≈3.7 min swarming, Fig. 1e,f) once a first cut is running. Also: f's memory window is labeled "20 s" (d) plus a second constant "β, 2 min" in the Methods table, but in the code that second constant behaves as a decay *rate* (min⁻¹), not a duration — use it that way.

### 3. How a cell picks a heading
The only rule that differs between zones.
- **Swarming — trail-following.** A moving cell deposits EPS into a grid under itself (rate 2/min, cap 10), senses forward through a semicircular cone (view angle π) out to about one body-length (~5 µm), splits that cone into sectors, and steers toward whichever sector holds the most EPS above a detection floor (c_min = 0.1 absolute, i.e. 1% of EPS_max). Trails barely decay on our timescales, so a worn route stays worn.
- **Rippling — forced axis.** On matrix-covered ground, cells are nudged toward one shared direction (a nematic torque — head vs. tail doesn't matter) with no self-reinforcement. The paper is explicit that *why* prey matrix produces this one global axis, rather than trail-following, is still biologically unresolved — they impose it because it reproduces the alignment they measured, not because they've derived it. That axis is a free choice for every prey patch we create — see open item **C** below.

### 4. Why any of this produces *patterns* (the theory tier)
Two continuum (PDE) models sit under the agent model and answer "under what conditions do waves exist" rather than "what does one cell do."
- The **age-structured model** tracks right- and left-moving densities u⁺(t,x,r), u⁻(t,x,r). Everything reduces to two numbers: S = RP/T_REV (how pacemaker-like vs. Poisson-like the reversal timing is) and C, the log-log sensitivity of the combined timescale to the signal. Waves only emerge in the "high-signalling" regime (where RP itself, not just the rate, shrinks with congestion), and only once S is large enough. This is the formal version of "RP modulation matters" and the paper's central theoretical claim.
- A **phase-structured variant** (reversal timing as a phase on [0,π] instead of a literal clock) is used only as a robustness check — skip it unless we want a second, independent derivation.
- Worth keeping on hand for grading our own output: **nematic order**, O(r) = ⟨(1/N_i(r)) Σ_j [2cos²(θ_i−θ_j)−1]⟩_i, averaged over neighbors within a ring of radius r. This is literally Fig. 1c/5f — how they (and we) tell "rippling-aligned" from "swarming-locally-aligned-only," numerically.

### 5. Calibrated parameters
| Symbol | Meaning | Value | Category |
|---|---|---|---|
| R* | max refractory period | 5 min | literature (ref. 24) |
| ε, N_D | inter-node spacing, node count | 0.5 µm, 10 → 5 µm body | literature |
| H | trail-sensing horizon | ≈5 µm | literature (ref. 6) |
| c_min | min. detectable EPS | 0.1 (absolute; = EPS_max/100 in code) | literature (ref. 8) |
| D | cell width | 0.7 µm | measured |
| v | cell speed | 4 µm/min | measured |
| R_min | min. refractory period | 20 s | measured, from TBR data |
| k_s | spring constant | 50 min⁻¹ | ad hoc |
| k_r | repulsion strength | 450 µm⁻¹min⁻¹ | ad hoc |
| 2α | trail-sensing view angle | π (semicircle) | ad hoc |
| a, EPS_max | EPS deposition rate, cap | 2/min, 10 | ad hoc |
| γ′, γ | rippling / EPS alignment strength | 11 µm/min each | ad hoc |
| F* | max reversal rate | 30 min⁻¹ (paper) / 3 min⁻¹ (2D code) | ad hoc — ⚠ conflicting |
| d, β | frustration memory window, decay | 20 s, "2 min" (behaves as 2 min⁻¹ in code) | ad hoc — ⚠ mislabeled |
| f_T | congestion threshold | 0.08 | fit to TBR data |
| α_F, α_R | reversal-rate / RP steepness | 75, 100 | fit to TBR data |

### 6. Validation targets to hold ourselves to
- TBR distribution: bimodal in rippling (mean ≈3.2 min, two peaks — wave-collision vs. counter-wave reversal), unimodal in swarming (≈3.7 min).
- Nematic order: stays high out to ~90 µm in rippling; collapses within ~20 µm in swarming.
- Reversals cluster in a cell's own top frustration quartile: ~50% of rippling reversals, ~44% of swarming reversals.
- Residence time: cells stay roughly 1.8× longer per visit in rippling ground than swarming ground (≈121 vs. ≈67 min in the paper's runs) — this is *why* rippling ground stays denser with no birth/death needed.
- A reversal-incapable (*frzE*-like) subpopulation never gets trapped this way and gets spatially sorted out of rippling territory over time — a good independent check once we support mixed populations.

### 7. Resources in hand
- Paper: DOI [10.1038/s41567-026-03416-y](https://doi.org/10.1038/s41567-026-03416-y)
- Code (MIT): [github.com/MignotLab/SpatialPatternsCollectives](https://github.com/MignotLab/SpatialPatternsCollectives) — `simulation/agent_based_model_myxo/` for the 2D model (`reversals.py`, `extracellular_matrix.py`, `alignment.py`, `repulsion.py`, `bacteria_movement.py`, `parameters.py`); `simulation/pde_model/guzzo/` for the 1D age-structured model; `scripts/simu_2d/` for the exact run scripts behind each figure.
- Raw data: Figshare, DOI [10.6084/m9.figshare.30667151](https://doi.org/10.6084/m9.figshare.30667151)

---

## What's still ours to design

**A. Prey colonies — birth, growth, footprint.** Nothing here at all: the paper's assay is one pre-grown *E. coli* spot, placed once, imaged for 48 h. We need our own nucleation rate, starting size, and growth law (exponential toward a carrying capacity is the obvious default, but it's our call).

**B. Feeding / kill / digestion.** Also absent — the paper only states that a whole colony is invaded and digested within 48 h, with no per-cell kill rate and no dependence on local Myxo density. A reasonable starting rule: local digestion rate ∝ local Myxo density on that patch of prey — an assumption, not something the paper gives us.

**C. Digested prey → rippling trigger.** No rule for this either — the paper hand-picks one axis and imposes it uniformly, and says its real biological origin is unresolved. With many colonies of different shapes scattered around, we need to decide: one alignment axis per colony (long axis? radial from center?), and how newly-digested ground blends into a neighboring rippling zone's axis versus holding its own.

**D. Predator population.** The 2D model conserves total cell count exactly (periodic boundaries, no births or deaths — even the reversal-incapable mutant is sorted, not killed). Myxo growing as it eats is entirely our addition.

**E. "3D."** Every measurement and every model here is 2D — confocal imaging of a flat colony, a 2D agent simulation. "3D" for us can only be a rendering choice (prey biomass as a height field, camera perspective) layered on 2D physics, not an actual 3D reversal/alignment model — the paper gives no basis for inventing one.

**F. Time compression.** Real predation runs ~48 h; the paper's simulated *pattern* dynamics (waves stabilizing, density ratios settling) run over 500 simulated minutes of "bio-time," separate from wall-clock. We need our own mapping from real predation hours to prey-growth events and pattern-settling time — nothing forces these to line up.

**G. Performance ceiling.** Their own runs (9,000 rippling / 3,330 swarming cells, up to ~50,000 for coexistence sweeps) are NumPy plus a KD-tree for neighbor lookups — fine for an offline paper figure, not obviously fine for a live view. I'd plan for a few thousand agents at most in anything interactive; beyond that probably wants pre-computing or batching.

---

## Proposed build order
*(open to reordering — this is a suggestion, not a commitment)*

1. Reproduce rippling-only and swarming-only against the §6 validation targets, at a few hundred to ~1,000 cells, using the paper's own fixed-mask geometry (no prey growth yet). This proves the reversal + alignment core is right before anything is built on top of it.
2. Replace the fixed mask with a live field: wherever prey matrix has been deposited, cells there use rippling alignment; elsewhere, EPS. Test against one static prey colony (closest to the real assay) before colonies start appearing dynamically.
3. Add prey colonies as a separate layer — nucleation, growth, and a digestion rule that writes into the matrix field (decisions **A**/**B**/**C**).
4. Add whichever predator-population rule we pick (**D**), and the rendering layer for "3D" (**E**).
5. Tune the time-compression mapping (**F**) last, once steps 1–4 behave — it only affects pacing, not correctness.
