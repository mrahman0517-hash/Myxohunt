"""
settings.py — every number the simulation uses, in one place.

Each value has its unit and a source tag:
  [paper]   Saulnier et al. 2026          [code]     the authors' released code
  [biology] an entry in docs/sources.md   [assumed]  our choice, no measurement exists
  [tuned]   a starting value, adjusted by watching the simulation
"Bxx" numbers point to docs/decision-log.md.
"""
import json
from dataclasses import dataclass, field, asdict, fields

import numpy as np

STARVATION_PRESETS = {"very fast": 180, "fast": 360, "medium": 720, "slow": 1440}  # bio min a full store lasts (B23)
COLONY_OPTIONS = (1, 2, 4, 8)                       # choices for start_colonies (B44)
WORLD_SIZES = {"live": 150.0, "record": 500.0}      # µm (B2)
START_COLONIES = {"live": 2, "record": 4}           # default start_colonies per mode (B44)
SEED_DISTANCES = {"live": 75.0, "record": 150.0}    # µm between starting colonies per mode (B56)


@dataclass
class Settings:
    # ---- world ---------------------------------------------------------------
    box: float = 150.0               # µm      side of the wrap-around square (B2)
    seed: int = 1                    #         random seed, so a run can be repeated exactly
    dt: float = 0.005                # min     one tick = 0.3 s [code]
    grid_every: int = 20             # ticks   between ground-grid updates (B51) [assumed]
    speedup: float = 10.0            # ×       slow biology runs this much faster than movement (B4). Locked in
                                     #         the apps at 10: slime and scout timers run on the real clock, so
                                     #         another value changes the balance (B97)
    coarse_grid: float = 1.0         # µm      nutrients, food, attractant, matrix (B35) [assumed]
    eps_grid: float = 0.3            # µm      slime grid [code]

    # ---- Myxo body and motion ---------------------------------------------------
    n_nodes: int = 10                #         discs per cell [paper]
    node_spacing: float = 0.5        # µm      [paper]
    disc_diam: float = 0.7           # µm      cell width [paper]
    speed: float = 4.0               # µm/min  [paper]
    k_spring: float = 50.0           # 1/min   [paper]
    k_rep: float = 450.0             # 1/(µm·min) repulsion cap [paper]
    traction_scale: int = 10         #         head pulled at speed × 10 [code]
    spring_passes_per_node: int = 5  #         5·10 = 50 spring passes per tick [code]

    # ---- reversals (frustration rule) -------------------------------------------
    R_star: float = 5.0              # min     maximum refractory period [paper]
    R_min: float = 1.0 / 3.0         # min     minimum refractory period, 20 s [paper]
    F_star: float = 3.0              # 1/min   maximum reversal rate [code]
    f_T: float = 0.08                #         threshold on the smoothed signal s [paper]
    alpha_F: float = 75.0            #         steepness of the rate curve [paper]
    alpha_R: float = 100.0           #         steepness of the refractory curve [paper]
    memory: float = 1.0 / 3.0        # min     frustration memory, 20 s [paper]
    beta: float = 2.0                # 1/min   memory decay rate [code]

    # ---- alignment: rippling axis and slime trails --------------------------------
    gamma_ripple: float = 11.0       # 1/min   pull toward the ripple axis [paper]
    gamma_eps: float = 11.0          # 1/min   pull toward slime trails [paper]
    sense_radius: float = 5.0        # µm      how far ahead pili feel slime [paper]
    view_angle: float = np.pi        # rad     semicircle ahead of the head [paper]
    n_sectors: int = 5               #         wedges in the semicircle [code]
    eps_c_min: float = 0.1           #         weakest slime a cell can detect [paper]
    eps_choice_tolerance: float = 0.8  #       wedges within 80% of the best count as good [code]
    eps_deposit: float = 2.0         # 1/min   slime laid per µm moved [paper]
    eps_fade_time: float = 360.0     # bio min slime fades over hours (B31) [tuned]
    matrix_ripple_threshold: float = 0.3  #    ripple above this much prey material (ghosts + living prey)
                                          #    per µm², averaged around the head (B43, B46, B76) [tuned]
    matrix_sense_radius: float = 3.0      # µm averaging circle around the head (B43) [assumed]
    ripple_live_prey_weight: float = 1.0  #    a living E. coli counts like one ghost toward the ripple trigger:
                                          #    contact with prey starts rippling (Berleman 2006) (B76);
                                          #    0 = ghosts only (B11) [assumed]
    matrix_per_ghost: float = 1.0         #    matrix left by one dead E. coli [tuned]
    matrix_half_life: float = 720.0       # bio min (B12) [tuned]

    # ---- pull toward prey (chemotaxis through reversals, B10, B32) ----------------
    chemo_strength: float = 2.0      #         0 = pure paper model [tuned]
    chemo_factor_range: tuple = (0.2, 5.0)  #  clip for the reversal multiplier [assumed]
    attractant_per_lysis: float = 1.0       #  units released by one burst E. coli [tuned]
    ecoli_attractant_rate: float = 2.0      #  units per bio min leaked by each living E. coli
                                            #  (outer-membrane vesicles, PE); 0 = off (B63, B68) [assumed]
    ghost_attractant_rate: float = 2.0      #  units per bio min per ghost (1 matrix unit): the empty envelope
                                            #  keeps shedding its PE-rich membrane like a living cell, fading
                                            #  with the matrix (B74); 0 = off [assumed]
    attractant_diffusion: float = 50.0      #  µm²/bio min [tuned]
    attractant_decay_time: float = 60.0     #  bio min [tuned]

    # ---- E. coli -------------------------------------------------------------------
    ecoli_width: float = 1.0         # µm      [biology] BioNumbers
    ecoli_birth_length: float = 2.0  # µm      [biology] BioNumbers
    ecoli_divide_length: float = 4.0  # µm     [biology] BioNumbers
    ecoli_divide_noise: float = 0.4  # µm      spread (SD) of division lengths, ~10%: measured ~10% (BioNumbers 110034) (B53, B80) [biology]
    ecoli_speed_noise: float = 0.2   #         spread (SD) of each cell's own growth speed, redrawn every cycle (B55) [biology]
    ecoli_points: int = 5            #         contact points per rod [assumed]
    ecoli_doubling: float = 20.0     # bio min with plenty of food [biology]
    monod_half_saturation: float = 0.2  #      nutrient level for half-speed growth [assumed]
    nutrient_per_um: float = 0.5     #         nutrient used per µm of growth: on local ground this gives colonies
                                     #         of ~370–560 cells by 500 bio-min, still growing at their rims (B78;
                                     #         3 in B54/B75 with fast spreading; 0.3 runs away, 1 stays small) [tuned]
    ecoli_mobility: float = 1.0      #         × mean push on a rod [tuned]
    dormant_threshold: float = 0.01  #         nutrient level below which growth stops and a cell goes dormant [assumed]
    wake_threshold: float = 0.2      #         nutrient level that wakes a dormant cell and restarts its starvation
                                     #          clock: a real meal, not a trace. A chosen level, equal to the Monod
                                     #          constant K but not the half-speed level, which is K/(1 + 2K) = 0.14
                                     #          (B97 correction); 0.01 before (B87) [your choice]
    dormancy_before_death: float = 0.0  # bio min dormant before the death phase: none, starving E. coli lose
                                     #          viability from early on (Schink et al.) (B34, B87; 1440 before) [biology]
    starvation_death_rate: float = np.log(1000.0) / (10 * 1440.0)  # 1/bio min: viability falls to 0.1% in
                                     #          10 days, ~0.69 per day (Schink et al.) (B34, B80; 1 per day before) [biology]
    persister_fraction: float = 0.05  #        long-term survivors (B34, B40) [biology]
    starved_lysis_delay: float = 120.0  # bio min from starvation death to burst: lysis follows the membrane
                                     #          voltage collapse after 2.0 ± 1.4 h (Schink et al.) (B45, B80; 30 before) [biology]
    starved_content_min: float = 0.25  #       food left in a cell that starved to death (B45) [assumed]
    starved_shrink_time: float = 1440.0  # bio min of starving over which a cell's contents shrink to
                                     #          starved_content_min (B45's day, kept in B87) [assumed]

    # ---- ground nutrients (B33, B48) -----------------------------------------------
    nutrient_regrow_rate: float = 1.0 / 3000.0  # 1/bio min, dN/dt = r(richness − N): slow replenishing (B68) [tuned]
    richness_min: float = 0.3        #         poorest ground (B48)
    richness_max: float = 1.0        #         richest ground (B48)
    patch_size: float = 30.0         # µm      size of rich/poor patches (B48) [tuned]
    nutrient_diffusion: float = 0.1  # µm²/bio min: local ground. Enough to feed a cell from the few µm
                                     #   around it; a colony drains only its own patch plus ~25 µm over 30 bio-h
                                     #   (B78; 10 in B54, which let two colonies drain the whole live world) [tuned]
    nutrient_start_min: float = 0.3  #         each patch starts filled to a random share of its maximum,
    nutrient_start_max: float = 1.0  #         between these two (B78) [assumed]

    # ---- food released by dead cells (B17, B21, B39) --------------------------------
    ecoli_content: float = 100.0     #         material in an average (3 µm) E. coli, in store units: about one
                                     #         Myxo cell's worth, as the two are similar in size (B21, B75)
    food_diffusion: float = 5.0      # µm²/bio min [tuned]
    food_decay_time: float = 1038.8  # bio min (e-folding) = a 12 bio-h half-life, the same as the ghosts, so
                                     #   spilled food and its smell fade together (B74; ∞ in B70, 600 before) [assumed]

    # ---- predation (B14, B15) ------------------------------------------------------
    touch_distance: float = 0.95     # µm      Myxo disc centre to E. coli point: (0.7 + 1.0)/2 + 0.1
    pause_rate: float = 0.71         # 1/real min while touching: 30% of 0.5-min touches [tuned]
    kill_delay: float = 2.0          # real min from pause to burst [biology] Seef 2021
    kill_success: float = 0.8        #         share of pauses that kill [biology] Seef 2021
    scale_predation: bool = True     #         run pauses and kills on the biology clock (pause_rate × speedup,
                                     #         kill_delay ÷ speedup), so kills per Myxo generation stay
                                     #         realistic; single encounters then look faster than measured (B66)
    prey_contact_signal: float = 0.0  #         Frz signal while touching living prey (> f_T gives rapid reversals
                                      #        on the spot). Off since B76: after a kill cells glide on into the
                                      #        colony, as Seef 2021 filmed (0.15 in B62, B68) [assumed]
    myxo_crawl_over_prey: bool = True  #       Myxo and E. coli never shove each other: Myxo glide over and between
                                      #        prey, a stand-in for the 3D colony; touches still kill (B76) [assumed]
    ecoli_push_share: float = 0.8    #         share of a Myxo–E. coli shove taken by the E. coli (only used when
                                      #        myxo_crawl_over_prey is off): higher = Myxo push into colonies (B62) [assumed]

    # ---- Myxo energy (B20–B28, B75): the store counts a cell's material; 100 = a normal newborn ----
    energy_start: float = 60.0       #         seeds start partly starved (B20)
    energy_newborn: float = 100.0    #         a normal, well-fed newborn: one cell's worth of material (B75)
    energy_full: float = 200.0       #         doubled: a second cell's worth built, ready to split (B75)
    energy_cap: float = 210.0        #         top of the reserve (B22, B75)
    efficiency: float = 0.30         #         share of eaten food kept: measured 5–60% (del Giorgio & Cole 1998);
                                     #          30% so each prey feeds fewer hunters (B85; 50% in B75, 30% in B21)
    uptake_rate: float = 0.25 / 0.30  # 1/bio min, fraction of a square's food. Both uptake numbers are
                                     #   divided by efficiency (B85: 0.5 and 5 at 50%), so a cell grows just
                                     #   as fast on any amount of food and only uses more of it [tuned]
    uptake_max: float = 2.5 / 0.30   # food units/bio min at most: on plentiful food a newborn divides after
                                     #   5.4 bio-h on average, the measured 5.5 h on prey (B65, re-anchored
                                     #   in B75 and B85) [biology-anchored]
    killer_share: float = 0.25       # share of a kill's contents the killer absorbs at once; the rest
                                     #   spills for the pack (wolf-pack sharing) (B65, B76; 0.5 before) [assumed]
    living_food: float = 1.0         #         prey food within absorb_radius below which a cell is starving outside:
                                     #          too little to cover its running costs. Its starvation clock starts
                                     #          (B83; scout_food_threshold in B71) [assumed]
    stringent_delay: float = 30.0    # bio min  of starving before the fast stringent effects (cost cut, division
                                     #          stop, better uptake): the alarm (p)ppGpp rises fast when food runs out
                                     #          (Manoil & Kaiser 1980) (B83, B84) [assumed]
    behaviour_delay: float = 120.0   # bio min  of starving before the starving behaviours (keener smell, speed
                                     #          change): "the first few hours" of starvation recognition (Harris
                                     #          1998); the attractant is a developmental one (Kearns 2001) (B84) [assumed]
    scrap_cap: float = 30.0          #         food from dead Myxo (scraps) can fill a cell's store only up to this:
                                     #          it keeps a cell alive but never ends its starvation (B83) [your choice]
    starvation_upkeep: float = 0.3   #         its running costs drop to this share (stringent response) (B70),
                                     #          on its core only: anything above a newborn's 100 is burned at
                                     #          the full rate first, as stored fuel is used first (B84);
                                     #          0.1 before B85 [assumed]
    stringent_loner_speed: float = 1.5  # ×     a starving cell speeds up to this over stringent_speedup_time
                                     #          (starving cells glide ~1.5× faster after 15 h, Jelsbak 2002) (B75)
    stringent_speedup_time: float = 900.0  #    bio min (15 h) to get there (Jelsbak 2002) (B75)
    stringent_affinity: float = 1.15  # ×       stringent cells take up scarce food 15% more readily (B72) [assumed]
    starvation_preset: str = "slow"  #         key of STARVATION_PRESETS: a newborn's store lasts 24 bio-h (B23)
    division_threshold: float = 190.0  #       division possible once the store has about doubled; each
                                     #          daughter gets half, ~100 (B24, B75)
    division_rate_max: float = 1.0 / 60.0  # 1/bio min at the cap [tuned]
    famine_exit: bool = True         #         a day into starvation, starving cells begin development and
                                     #          each takes one fate: lyse, become a spore, or stay on as a rod (B80)
    famine_time: float = 1440.0      # bio min of starving (since prey food ran out) before that: lysis and
                                     #          aggregation begin about 24 h after starvation starts
                                     #          development (Lee 2012) (B80, B83) [biology]
    famine_lysis_share: float = 0.7  #         share that lyse, their contents feeding the rest: classic counts 60–80%,
                                     #          disputed (O'Connor & Zusman 1988 found ≥80% survive) (B80) [biology]
    famine_spore_share: float = 0.1  #         share that become spores (~10%); the rest (20%) stay as persister-like
                                     #          peripheral rods (10–20%, O'Connor & Zusman 1991) (B80) [biology]

    # ---- seeds (B8, B44, B47, B50) ----------------------------------------------------
    myxo_groups: int = 5             #         (B64, B74; was 3 in B8)
    myxo_group_size: int = 20        #         (B78, the user's choice; 50 in B74, 30 in B64)
    myxo_singles: int = 10           #         (B64, was 7 in B8)
    myxo_group_radius: float = 6.5   # µm      keeps the same packing as 30 cells in 8 µm (B74, B78) [assumed]
    myxo_arrival_window: float = 600.0  # bio min: each Myxo seed comes in from outside at a random time
                                     #          within this window, at a random spot; 0 = all at the start (B78) [assumed]
    myxo_min_dist_colony: float = 30.0  # µm   from every Myxo cell (the group's edge) to any E. coli (B47, B72)
    ecoli_seed_interval: float = 360.0  # bio min between new E. coli founders (6 h), each at a random spot with
                                     #          no placement rules (B75, B78); 0 = none [assumed]
    # ---- scout mode (B67, B71, B83): cells short of prey food explore off-trail (A-motility) ----
    scout_start_rate: float = 0.1 / (0.9 * 10.0)  # 1/real min at zero prey food: with scout_episode, 10% of
                                     #   such cells scout at any moment, and about half get a turn within
                                     #   10 bio-h (B83; 0.1 in B71, half at once) [your choice]
    scout_episode: float = 10.0      # real min a scouting spell lasts on average (B70) [assumed]
    scout_start_fraction: float = 0.3  #       scouting starts below this share of top-speed food and rises to
                                     #          its top at zero food; starvation ends above it (B83) [your choice]
    scout_turn_noise: float = 0.2    # rad²/min random turning: paths stay straight for ~20 µm (B67) [assumed]
    scout_speed: float = 1.1         # ×        scouts glide 10% faster: lone cells glide at 4.4 µm/min (Spormann &
                                     #          Kaiser 1999) against the paper's 4 (B71, B80; 1.2 before) [biology]
    scout_slime: float = 2.0         # ×        scout slime counts double for followers (B71) [assumed]
    scout_slime_fade: float = 2.0    # ×        and fades this many times more slowly (B71) [assumed]
    scout_smell: float = 1.5         # ×        scouts follow the prey smell this much more strongly (B72) [assumed]
    stringent_smell: float = 1.5     # ×        the same for stringent cells: the lipid attractant works only in
                                     #          starving cells (Kearns 2001); the size, as for scouts, is ours
                                     #          (B72, B80; 1 = no boost before) [assumed, direction biology]
    scout_random_end: bool = False   #          a scouting spell ends only when the scout finds prey food (or starts
                                     #          starving); True = also at random, every scout_episode on average (B95) [your choice]
    scout_rest_time: float = 60.0    # real min a cell must wait after a spell before it may scout again (B95) [your choice]
    scout_max_share: float = 0.1     #          at most this share of all Myxo scout at once (B95) [your choice]
    stringent_scouts: bool = True    #          starving cells may scout (B97, the user's choice: 6-7% scouts, kills ×3-4 in
                                     #          branch tests); off = a scout that has starved for behaviour_delay (2 bio-h)
                                     #          stops and no cell starving that long starts (~1% scouts). Off in B95, when
                                     #          the block came at stringent_delay and switched scouting off [your choice]
    smell_steer: float = 3.0         # 1/min    cells leading a stream (no slime ahead), scouts, and cells touching
                                     #          living prey turn toward the prey smell: Δθ = rate·sin(φ − θ)·Δt (B95) [assumed]
    invade_on_contact: bool = True   #          a cell touching living prey stops following slime and steers up the
                                     #          smell into the colony, laying slime others follow (A-motile invasion,
                                     #          Seef 2021) (B95) [assumed]
    absorb_radius: float = 2.0       # µm       cells absorb food from the ground within this distance of
                                     #          their head (extracellular digestion) (B71) [assumed]
    start_colonies: int = 2          #         (B44); options COLONY_OPTIONS
    seed_min_dist_ecoli: float = 75.0  # µm    between starting colonies; 150 in the record world (B56) [assumed]

    # ---- drawing (provisional, B41) ---------------------------------------------------
    colors: dict = field(default_factory=lambda: {
        "ecoli": (230, 60, 160), "myxo": (80, 220, 90), "background": (12, 12, 16)})

    # ---- derived values ----------------------------------------------------------------
    @property
    def memory_length(self) -> int:
        """Number of stored frustration values (66 for 20 s at 0.3 s per tick)."""
        return int(self.memory / self.dt)

    @property
    def survive_time(self) -> float:
        """Bio minutes a full food store lasts without eating, from the chosen preset (B23)."""
        return STARVATION_PRESETS[self.starvation_preset]

    @property
    def reserve_efficiency(self) -> float:
        """Above energy_full the reserve fills at a third of the normal efficiency (B22)."""
        return self.efficiency / 3

    @property
    def top_speed_food(self) -> float:
        """Prey food within reach at which a cell eats as fast as it can: uptake hits uptake_max (10)."""
        return self.uptake_max / self.uptake_rate

    @property
    def scout_food(self) -> float:
        """Prey food within reach below which scouting can start, and above which a starving cell has
        found a real meal: 30% of top-speed food, 3 units (B83)."""
        return self.scout_start_fraction * self.top_speed_food

    # ---- saving and loading -------------------------------------------------------------
    def __setstate__(self, state):
        """Unpickling: settings saved before a field existed get that field's default (B95), so
        older checkpoints and web scenes still load."""
        defaults = Settings()
        self.__dict__.update({f.name: getattr(defaults, f.name) for f in fields(self)})
        self.__dict__.update(state)

    def to_json(self, path):
        """Write all settings to a JSON file, so a run can be repeated or recorded later."""
        with open(path, "w", encoding="utf8") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def from_json(cls, path):
        """Read settings written by to_json. Unknown keys are ignored; tuples are restored."""
        with open(path, encoding="utf8") as fh:
            data = json.load(fh)
        known = {f.name for f in fields(cls)}
        data = {k: v for k, v in data.items() if k in known}
        if "chemo_factor_range" in data:
            data["chemo_factor_range"] = tuple(data["chemo_factor_range"])
        if "colors" in data:
            data["colors"] = {k: tuple(v) for k, v in data["colors"].items()}
        return cls(**data)


def make_settings(mode="live", **overrides):
    """Settings for the live window or a recorded video, with any values changed by name."""
    base = Settings(box=WORLD_SIZES[mode], start_colonies=START_COLONIES[mode],
                    seed_min_dist_ecoli=SEED_DISTANCES[mode])
    for name, value in overrides.items():
        if not hasattr(base, name):
            raise AttributeError(f"unknown setting: {name}")
        setattr(base, name, value)
    return base
