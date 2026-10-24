#!/bin/sh
# The review's step 5 (B97): the Recommended preset with the B97 fixes, seeds 1-4 to 300 bio-h
# (1,800 real min at 10x), and prey only (no Myxo) seeds 1-2 to 250 bio-h, all in parallel, one
# thread each. Each run saves a checkpoint every 30 real min; running this again carries on, and
# skips runs that already finished (their picture exists and no checkpoint is left).
# Usage (from predation-sim/):  sh checks/run_baseline.sh
PY=../.venv/Scripts/python.exe
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
REC="nutrient_regrow_rate=4.1666666666666665e-05 richness_min=0.21 richness_max=0.7 efficiency=0.6 \
uptake_rate=0.4166666666666667 uptake_max=4.166666666666667 famine_lysis_share=0.2 ripple_live_prey_weight=1.0 \
stringent_delay=30.0 stringent_loner_speed=1.5 persister_fraction=0.05"
done_already() { [ -f checks/output/$1.png ] && [ ! -f checks/output/$1.ckpt ]; }
for s in 1 2 3 4; do
  done_already base_rec_s$s ||
  $PY -X utf8 checks/check_populations.py 1800 $s base_rec_s$s $REC >> checks/output/base_rec_s$s.log 2>&1 &
done
for s in 1 2; do
  done_already prey_rec_s$s ||
  $PY -X utf8 checks/check_populations.py 1500 $s prey_rec_s$s $REC myxo_groups=0 myxo_singles=0 >> checks/output/prey_rec_s$s.log 2>&1 &
done
wait
