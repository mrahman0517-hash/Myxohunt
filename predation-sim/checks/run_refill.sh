#!/bin/sh
# B100: from each lysis-70% branch at +100 bio-h (B99), 60 bio-h more with ground refill ÷6 and ÷4
# (from ÷8), and the 70% branch carried on unchanged as the control (to +160 h), all 12 in parallel,
# one thread each. Running this again carries on from the checkpoints.
# Usage (from predation-sim/):  sh checks/run_refill.sh
PY=../.venv/Scripts/python.exe
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for s in 1 2 3 4; do
  # a frozen copy of the +100 h state to branch from, since the control moves br70L's checkpoint on
  [ -f checks/output/br70L100_s$s.ckpt ] || cp checks/output/br70L_s$s.ckpt checks/output/br70L100_s$s.ckpt
  $PY -X utf8 checks/branch_test.py br70L_s$s base_rec_s$s 160 famine_lysis_share=0.7 >> checks/output/br70L_s$s.log 2>&1 &
  $PY -X utf8 checks/branch_test.py rf6_s$s br70L100_s$s 60 nutrient_regrow_rate=5.555555555555556e-05 >> checks/output/rf6_s$s.log 2>&1 &
  $PY -X utf8 checks/branch_test.py rf4_s$s br70L100_s$s 60 nutrient_regrow_rate=8.333333333333333e-05 >> checks/output/rf4_s$s.log 2>&1 &
done
wait
