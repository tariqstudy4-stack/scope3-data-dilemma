"""Summary of the factorial control (Section 4.3, Table S5).

Run from the repository root after code/calibration_control.py:
    python code/summarize_control.py -> data/calibration_control_summary.json
Cells: substitute (actual sector-mean factor, random mean-1 lognormal error with GSD 2.0) crossed with the lognormal
convention of the widening (median-preserving, mean-preserving). Coverage is the mean over the three adoption patterns
and 100 seeds at converged chaining, by indicator and participation rate, and pooled over indicators ("ALL").
"""
import collections, json
import numpy as np

rows = json.load(open("data/calibration_control.json"))
CELLS = ("actual_median", "actual_mean", "random_median", "random_mean")
RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
acc = collections.defaultdict(list)
for r in rows:
    if r["tiers"] != 0:
        continue
    for c in CELLS:
        acc[(r["indicator"], c, r["rate"])].append(r[c])
        acc[("ALL", c, r["rate"])].append(r[c])
out = {"rates": RATES, "n_rows_converged": sum(1 for r in rows if r["tiers"] == 0), "cells": CELLS, "coverage": {}}
for ind in ("GHG", "ACG", "O3PR", "PM2_5", "ALL"):
    for c in CELLS:
        out["coverage"][f"{ind}|{c}"] = [float(np.mean(acc[(ind, c, r)])) for r in RATES]
json.dump(out, open("data/calibration_control_summary.json", "w"), indent=1)
for c in CELLS:
    v = out["coverage"][f"ALL|{c}"]
    print(c, "0%:", round(v[0], 1), "80%:", round(v[6], 1))
