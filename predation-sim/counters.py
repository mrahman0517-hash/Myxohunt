"""
counters.py — running totals of what happened in a run: births, kills, starvation deaths, wakes,
famine fates, scouting, touches, and where food and store came from and went (review of 23 Oct
2026, step 2). Until now kills and starvation deaths were inferred from the maps
(checks/prey_budget.py); these count them directly, and the food and store totals let a test
check that nothing is created or lost.

The totals live in world.counters, a plain dict made on first use, so worlds saved before it
existed (checkpoints, web scenes) still load.
"""

NAMES = (
    # E. coli
    "ecoli_divisions", "ecoli_founders", "ecoli_wakes", "ecoli_starved", "ecoli_killed", "ecoli_burst",
    # Myxo
    "myxo_divisions", "myxo_arrived", "myxo_starved_dead", "famine_lysed", "famine_spores", "famine_rods",
    "touch_ticks", "pauses", "scout_starts", "scout_minutes", "clock_resets",
    # food, in food units: spilled on the ground by cause, eaten, and lost from the maps (fade)
    "kill_content", "food_spilled_kill", "food_spilled_starved", "food_eaten_killer", "food_eaten",
    "scraps_spilled", "scraps_eaten", "food_lost", "scraps_lost",
    # Myxo store, in store units: gained by source, and spent or carried off
    "store_from_kills", "store_from_food", "store_from_scraps", "store_upkeep", "store_arrived",
    "store_lysed", "store_spored", "store_dead",
)


def table(world):
    """The world's dict of totals, made on first use."""
    return world.__dict__.setdefault("counters", {})


def add(world, name, amount=1):
    """Add `amount` to the total called `name`."""
    c = table(world)
    c[name] = c.get(name, 0.0) + float(amount)


def totals(world):
    """Every total, in NAMES order, 0 for anything that hasn't happened yet."""
    c = table(world)
    return {name: c.get(name, 0.0) for name in NAMES}
