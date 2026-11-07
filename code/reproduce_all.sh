#!/usr/bin/env bash
# Regenerates every number, table and figure cited in the manuscript and the SI from the stored matrices.
# Run from the repository root:  bash code/reproduce_all.sh   (set JOBS=2 to run the four 400-seed chunks two at a time)
# Wall-clock time per step is appended to logs/timing.log.
set -euo pipefail
mkdir -p logs
JOBS=${JOBS:-1}
step() { local t0=$(date +%s); "$@"; echo "$(( $(date +%s) - t0 )) s  $*" >> logs/timing.log; }

step python code/experiments.py                       # ten-seed grid -> data/results.json, results.csv
step python code/verify_all.py                        # needs data/results.json
step python code/check_affine_noise.py
# 400-seed grid, one indicator per call -> data/results_400_<k>.json
if [ "$JOBS" -gt 1 ]; then
  step python code/experiments2.py 0 & step python code/experiments2.py 1 & wait
  step python code/experiments2.py 2 & step python code/experiments2.py 3 & wait
else
  for k in 0 1 2 3; do step python code/experiments2.py $k; done
fi
step python code/summarize_main.py                    # Table 1, Figs. 2 and 4, Fig. S2
step python code/calibration_control.py               # factorial control -> data/calibration_control.json
step python code/summarize_control.py                 # Table S5
step python code/substitute_offset.py                 # Table S5c, within-section GSD
step python code/gsd_sweep2.py                        # Table S4
step python code/equal_pds_check.py
step python code/equal_pds_ci.py                      # Table S2
step python code/pooled_pds_bins.py                   # Table S2b
step python code/sensitivity_analysis.py
step python code/sensitivity_variants.py              # Table 2, Table S3
step python code/c29_check.py                         # Table S3b
step python code/chaining_depth_check.py              # Fig. 3, Table S6
step python code/finalize_stats.py
for f in make_fig1 make_fig2 make_fig3 make_fig4 make_figS1 make_figS2; do step python figures/$f.py; done
