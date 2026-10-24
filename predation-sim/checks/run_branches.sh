#!/bin/sh
# B99: from each stopped baseline run (B98), 40 bio-h with famine lysis at 70% (treatment) and at
# 20% as before (control), all 8 in parallel, one thread each. Running this again carries on.
# Usage (from predation-sim/):  sh checks/run_branches.sh
PY=../.venv/Scripts/python.exe
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for s in 1 2 3 4; do
  [ -f checks/output/br70_s$s\_stats.csv ] && [ ! -f checks/output/br70_s$s.ckpt ] ||
  $PY -X utf8 checks/branch_test.py br70_s$s base_rec_s$s 40 famine_lysis_share=0.7 >> checks/output/br70_s$s.log 2>&1 &
  [ -f checks/output/br20_s$s\_stats.csv ] && [ ! -f checks/output/br20_s$s.ckpt ] ||
  $PY -X utf8 checks/branch_test.py br20_s$s base_rec_s$s 40 famine_lysis_share=0.2 >> checks/output/br20_s$s.log 2>&1 &
done
wait
