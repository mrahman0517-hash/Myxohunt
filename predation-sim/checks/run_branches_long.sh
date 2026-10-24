#!/bin/sh
# B99, second step: the four lysis-70% branches carried on to 100 bio-h from the same baseline states
# (the first 40 bio-h repeat the short branches), all 4 in parallel, one thread each. Running this
# again carries on from the checkpoints.
# Usage (from predation-sim/):  sh checks/run_branches_long.sh
PY=../.venv/Scripts/python.exe
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for s in 1 2 3 4; do
  $PY -X utf8 checks/branch_test.py br70L_s$s base_rec_s$s 100 famine_lysis_share=0.7 >> checks/output/br70L_s$s.log 2>&1 &
done
wait
