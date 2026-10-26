"""
app_params.py — every setting the live app shows, sorted as the user asked (17 Oct 2026, B91):

- MAIN: the major, tunable settings, in the right-hand panel;
- ADVANCED: the other tunable or assumed settings, in the settings panel (⚙, top right of the world);
- EFFECTS: switches that turn a whole rule off;
- EVIDENCE: rules where studies disagree, one option per study, the recommended one marked ★;
- FIXED: measured or from the paper, shown but not editable.

Each setting says when a change takes effect: at once ("live") or when a new world starts ("reset").
The app starts from RECOMMENDED: the settings closest to the targets so far (B103, adopted in B104)
with the recommended option of every EVIDENCE rule.
"""
from dataclasses import dataclass, field

REFILL_BASE = 1.0 / 3000.0          # 1/bio min, the B68 refill; the app shows refill as ÷N of it
RICH_LO, RICH_HI = 0.3, 1.0         # B48's richness range; the app shows ground as × of it
ARRIVAL_GROUP = 20                  # Myxo per arriving group (B78)


def efficiency_changes(eff):
    """Myxo keep `eff` of eaten food; uptake is divided by it so the 5.4 h generation holds (B85)."""
    return dict(efficiency=eff, uptake_rate=0.25 / eff, uptake_max=2.5 / eff)


def scouting_changes(pct, s):
    """`pct`% of cells scout at once at zero prey food (B83): start rate = p / ((1 − p) · spell)."""
    p = pct / 100.0
    return dict(scout_start_rate=p / ((1.0 - p) * s.scout_episode) if p < 1 else 1.0)


@dataclass
class Param:
    """One adjustable setting. `changes(value, settings)` gives the settings it sets (default: its
    own key); `read(settings)` gives the shown value back (default: the setting itself)."""
    key: str
    label: str
    lo: float
    hi: float
    step: float
    when: str = "live"
    backing: str = ""
    fmt: str = "{:g}"
    changes: object = None
    read: object = None

    def settings_for(self, value, s):
        """The settings this value sets."""
        return self.changes(value, s) if self.changes else {self.key: value}

    def value_from(self, s):
        """The value to show for these settings."""
        return self.read(s) if self.read else getattr(s, self.key)


MAIN = [
    Param("efficiency", "Myxo keep of eaten food", 0.05, 0.6, 0.05, backing="measured 5–60%", fmt="{:.0%}",
          changes=lambda v, s: efficiency_changes(v)),
    Param("refill", "Ground refill speed", 1, 40, 1, backing="tuned", fmt="÷{:g}",
          changes=lambda v, s: dict(nutrient_regrow_rate=REFILL_BASE / v),
          read=lambda s: round(REFILL_BASE / s.nutrient_regrow_rate)),
    Param("chemo_strength", "Pull toward prey smell", 0, 5, 0.1, backing="tuned"),
    Param("smell_steer", "Leaders, scouts and invaders steer to smell", 0, 10, 0.5, backing="assumed",
          fmt="{:g}/min"),
    Param("ecoli_attractant_rate", "Smell leaked by living E. coli", 0, 10, 0.5, backing="assumed"),
    Param("starvation_upkeep", "Starving cells pay of their costs", 0.05, 1, 0.05, backing="assumed", fmt="{:.0%}"),
    Param("killer_share", "Killer keeps of each kill", 0, 1, 0.05, backing="assumed", fmt="{:.0%}"),
    Param("scouting", "Scouting at zero prey food", 0, 40, 1, backing="your choice", fmt="{:g}%",
          changes=lambda v, s: scouting_changes(v, s),
          read=lambda s: round(100 * s.scout_start_rate * s.scout_episode / (1 + s.scout_start_rate * s.scout_episode))),
    Param("ground", "Ground richness", 0.2, 1.5, 0.05, when="reset", backing="assumed", fmt="×{:g}",
          changes=lambda v, s: dict(richness_min=RICH_LO * v, richness_max=RICH_HI * v),
          read=lambda s: round(s.richness_max / RICH_HI, 2)),
    Param("start_colonies", "Starting E. coli colonies", 1, 12, 1, when="reset", backing="your choice"),
    Param("ecoli_seed_interval", "New E. coli founder every", 0, 24, 1, when="reset", backing="assumed",
          fmt="{:g} bio-h", changes=lambda v, s: dict(ecoli_seed_interval=60.0 * v),
          read=lambda s: round(s.ecoli_seed_interval / 60.0)),
    Param("myxo_groups", "Arriving Myxo groups (×20)", 0, 15, 1, when="reset", backing="your choice"),
    Param("seed", "Random seed", 1, 50, 1, when="reset", backing="technical"),
]

ADVANCED = [
    Param("eps_fade_time", "Slime trails fade over", 30, 1440, 30, backing="tuned", fmt="{:g} bio-min"),
    Param("matrix_ripple_threshold", "Prey material that starts rippling", 0.05, 1, 0.05, backing="tuned"),
    Param("matrix_half_life", "Prey remains half-life", 60, 2880, 60, backing="tuned", fmt="{:g} bio-min"),
    Param("ghost_attractant_rate", "Smell shed by prey remains", 0, 10, 0.5, backing="assumed"),
    Param("attractant_decay_time", "Smell fades over", 10, 240, 10, backing="tuned", fmt="{:g} bio-min"),
    Param("attractant_diffusion", "Smell spreads", 5, 200, 5, backing="tuned", fmt="{:g} µm²/bio-min"),
    Param("nutrient_per_um", "E. coli nutrient use per µm of growth", 0.3, 3, 0.05, backing="tuned"),
    Param("monod_half_saturation", "E. coli Monod constant", 0.05, 1, 0.05, backing="assumed"),
    Param("dormant_threshold", "E. coli go dormant below", 0.001, 0.1, 0.001, backing="assumed"),
    Param("wake_threshold", "Dormant E. coli wake at", 0.01, 0.5, 0.01, backing="your choice"),
    Param("nutrient_diffusion", "Ground nutrients spread", 0, 10, 0.1, backing="tuned", fmt="{:g} µm²/bio-min"),
    Param("food_decay_time", "Spilled food fades over", 60, 4320, 60, backing="assumed", fmt="{:g} bio-min"),
    Param("food_diffusion", "Spilled food spreads", 0, 50, 1, backing="tuned", fmt="{:g} µm²/bio-min"),
    Param("pause_rate", "Killing pauses per minute of touch", 0.1, 3, 0.05, backing="tuned"),
    Param("living_food", "Prey food below which a cell starves", 0.1, 5, 0.1, backing="assumed"),
    Param("behaviour_delay", "Starving behaviours begin after", 0, 600, 10, backing="assumed", fmt="{:g} bio-min"),
    Param("scrap_cap", "Scraps fill a store at most to", 0, 100, 5, backing="your choice"),
    Param("stringent_affinity", "Starving cells' uptake boost", 1, 2, 0.05, backing="assumed", fmt="×{:g}"),
    Param("division_rate_max", "Myxo division rate at the cap", 0.005, 0.05, 0.001, backing="tuned",
          fmt="{:.3f}/bio-min"),
    Param("scout_episode", "Scouting spell lasts (if spells end at random)", 2, 30, 1, backing="assumed",
          fmt="{:g} min"),
    Param("scout_rest_time", "Rest after a spell before scouting again", 0, 240, 10, backing="your choice",
          fmt="{:g} min"),
    Param("scout_max_share", "Most cells scouting at once", 0.01, 0.5, 0.01, backing="your choice", fmt="{:.0%}"),
    Param("scout_turn_noise", "Scouts' random turning", 0, 1, 0.05, backing="assumed", fmt="{:g} rad²/min"),
    Param("scout_slime", "Scout slime strength", 1, 5, 0.5, backing="assumed", fmt="×{:g}"),
    Param("scout_smell", "Scouts' smell boost", 1, 3, 0.1, backing="assumed", fmt="×{:g}"),
    Param("stringent_smell", "Starving cells' smell boost", 1, 3, 0.1, backing="assumed", fmt="×{:g}"),
    Param("absorb_radius", "Myxo eat within", 0.5, 5, 0.5, backing="assumed", fmt="{:g} µm"),
    Param("energy_start", "Arriving Myxo store", 20, 200, 5, when="reset", backing="assumed"),
    Param("myxo_singles", "Arriving single Myxo", 0, 50, 1, when="reset", backing="your choice"),
    Param("myxo_arrival_window", "Myxo arrive over", 0, 1440, 60, when="reset", backing="assumed", fmt="{:g} bio-min"),
    Param("patch_size", "Rich/poor patch size", 10, 80, 5, when="reset", backing="tuned", fmt="{:g} µm"),
    Param("box", "World size (cost grows with area)", 100, 300, 10, when="reset", backing="technical",
          fmt="{:g} µm"),
    Param("grid_every", "Ground maps update every", 1, 50, 1, backing="technical", fmt="{:g} ticks"),
]


@dataclass
class Switch:
    """A rule that can be turned off: `off` gives the settings that switch it off."""
    label: str
    off: dict
    note: str = ""


EFFECTS = [
    Switch("Killing on the biology clock (B66)", dict(scale_predation=False),
           "off: one kill takes 2 real min, as measured, but hunters starve"),
    Switch("Myxo glide over prey (B76)", dict(myxo_crawl_over_prey=False), "off: Myxo and E. coli shove each other"),
    Switch("Famine: starving Myxo lyse, sporulate or stay (B80)", dict(famine_exit=False)),
    Switch("Scouts (B71, B83)", dict(scout_start_rate=0.0)),
    Switch("Cells touching prey invade the colony (B95)", dict(invade_on_contact=False),
           "off: they keep following slime past the colony edge"),
    Switch("Scouts keep going until they find prey (B95)", dict(scout_random_end=True),
           "off: spells also end at random (B83)"),
    Switch("Starving cells may scout (B97)", dict(stringent_scouts=False), "off: cells starving over 2 bio-h stop scouting"),
    Switch("Pull toward prey smell (B10, B32)", dict(chemo_strength=0.0)),
    Switch("Living E. coli leak smell (B63)", dict(ecoli_attractant_rate=0.0)),
    Switch("Prey remains keep smelling (B74)", dict(ghost_attractant_rate=0.0)),
    Switch("Rippling on prey (B11, B76)", dict(matrix_ripple_threshold=1e9)),
    Switch("New E. coli founders (B75)", dict(ecoli_seed_interval=0.0), "off: no new founders from now on"),
    Switch("E. coli starve to death (B34, B87)", dict(starvation_death_rate=0.0)),
]


@dataclass
class Evidence:
    """A rule where studies disagree: options (label, settings, source); `best` is recommended."""
    label: str
    options: list
    best: int = 0


EVIDENCE = [
    Evidence("Starving Myxo that lyse in the famine", [
        ("20%: at least 80% survive (O'Connor & Zusman 1988)", dict(famine_lysis_share=0.2)),
        ("70%: classic counts of 60–80% (Wireman & Dworkin 1977)", dict(famine_lysis_share=0.7))], best=1),
    Evidence("What starts rippling", [
        ("contact with prey, living or dead (Berleman 2006)", dict(ripple_live_prey_weight=1.0)),
        ("prey remains only, after digestion (Saulnier 2026)", dict(ripple_live_prey_weight=0.0))]),
    Evidence("Stringent response after prey food runs out", [
        ("30 bio-min: (p)ppGpp rises fast (Manoil & Kaiser 1980)", dict(stringent_delay=30.0)),
        ("3 bio-h: starvation recognition (Harris 1998)", dict(stringent_delay=180.0))]),
    Evidence("Speed of starving Myxo away from others", [
        ("1.5× faster after 15 h (Jelsbak & Søgaard-Andersen 2002)", dict(stringent_loner_speed=1.5)),
        ("unchanged", dict(stringent_loner_speed=1.0))]),
    Evidence("Long-term E. coli survivors", [
        ("5% never starve (Finkel 2006)", dict(persister_fraction=0.05)),
        ("none: viability falls to 0.1% in 10 days (Schink et al.)", dict(persister_fraction=0.0))]),
]

FIXED = [
    ("Myxo body", "10 discs 0.5 µm apart, 0.7 µm wide, glide at 4 µm/min", "Saulnier 2026"),
    ("Myxo reversals", "F* = 3/min, f_T = 0.08, refractory 20 s–5 min, 20 s memory", "Saulnier 2026; authors' code"),
    ("Alignment", "γ = 11/min toward slime and the ripple axis; pili feel slime 5 µm ahead", "Saulnier 2026"),
    ("Tick", "0.3 s", "authors' code"),
    ("Biology speed-up", "×10: growth, killing and starving run 10× faster than gliding. Locked: slime and "
     "scout timers run on the real clock, so another value changes the balance", "B4, B97"),
    ("E. coli size", "1 µm wide, born 2 µm, divide at 4 µm ± 10%", "BioNumbers"),
    ("E. coli growth", "doubling 20 min on the richest ground; each cell's speed ± 20%", "BioNumbers; Wang 2010"),
    ("E. coli starvation death", "0.69 per day from dormancy; burst 2 h after death", "Schink et al."),
    ("Killing", "80% of pauses kill, 2 min after pausing", "Seef 2021"),
    ("Myxo store", "newborn 100, divides from 190 into two of ~100", "B75 (adder: Taheri-Araghi 2015)"),
    ("Myxo generation on prey", "5.4 h (uptake ceiling anchored to it)", "Seef 2021: 5.5 h"),
    ("Famine timing", "fates taken 24 h after prey food ran out; 10% spores", "Lee 2012; O'Connor & Zusman 1991"),
    ("Scout speed", "1.1× (4.4 µm/min)", "Spormann & Kaiser 1999"),
]

# The B103 settings (closest to the targets so far; famine lysis 70% comes from EVIDENCE) with the
# recommended EVIDENCE options.
RECOMMENDED = dict(nutrient_regrow_rate=REFILL_BASE / 5, richness_min=RICH_LO * 0.7, richness_max=RICH_HI * 0.7,
                   **efficiency_changes(0.6))
for _rule in EVIDENCE:
    RECOMMENDED.update(_rule.options[_rule.best][1])
