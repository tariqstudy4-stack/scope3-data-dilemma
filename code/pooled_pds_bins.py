"""Pooled greenhouse gas error by realised primary data share (Section 4.1 and Table S2b of the manuscript).

Run from the repository root after equal_pds_check.py: python code/pooled_pds_bins.py -> data/pooled_pds_bins.json
Runs of the three adoption patterns (400 seeds, eight rates, converged chaining) are pooled and grouped by realised
PDS within five points of 20, 30, ..., 90 percent; the median absolute percentage error and the run count are stored.
"""
import os, json
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "equal_pds_check.json")))
ghg = [r for r in d if r["indicator"] == "GHG"]
out = {}
for c in range(20, 100, 10):
    x = [r["mape"] for r in ghg if abs(r["pds"] * 100 - c) <= 5]
    out[str(c)] = {"median_mape": float(np.median(x)), "n": len(x)}
json.dump(out, open(os.path.join(ROOT, "data", "pooled_pds_bins.json"), "w"), indent=1)
print("written data/pooled_pds_bins.json")
