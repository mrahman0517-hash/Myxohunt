#!/bin/sh
# B103: the full round for lysis 70% + refill ÷5 (after B101: ÷6 passed 1 of 4): the Recommended preset with those two
# changes, seeds 1-4 to 300 bio-h (1,800 real min at 10x), all in parallel, one thread each, judged
# by checks/judge_band.py. Each run saves a checkpoint every 30 real min; running this again carries
# on, and skips runs that already finished (their picture exists and no checkpoint is left).
# Usage (from predation-sim/):  sh checks/run_round_r5.sh
PY=../.venv/Scripts/python.exe
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
SET="nutrient_regrow_rate=6.666666666666667e-05 richness_min=0.21 richness_max=0.7 efficiency=0.6 \
uptake_rate=0.4166666666666667 uptake_max=4.166666666666667 famine_lysis_share=0.7 ripple_live_prey_weight=1.0 \
stringent_delay=30.0 stringent_loner_speed=1.5 persister_fraction=0.05"
done_already() { [ -f checks/output/$1.png ] && [ ! -f checks/output/$1.ckpt ]; }
for s in 1 2 3 4; do
  done_already r5_s$s ||
  $PY -X utf8 checks/check_populations.py 1800 $s r5_s$s $SET >> checks/output/r5_s$s.log 2>&1 &
done
wait
