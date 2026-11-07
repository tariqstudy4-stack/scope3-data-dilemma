"""Summaries of the 400-seed grid used by Table 1, Fig. 2, Fig. 4, Fig. S2 and Table S5b.

Run from the repository root after code/experiments2.py (or with the four data/results_400_*.json files in place):
    python code/summarize_main.py   ->  data/summary_main.json   (small file, committed)
Medians are taken over seeds and targets as in the manuscript; coverage is the mean over seeds.
"median" and "mean" denote the lognormal convention of the widening (see code/intervals.py).
"""
import collections, glob, json
import numpy as np

rows = []
for f in sorted(glob.glob("data/results_400_*.json")):
    rows += json.load(open(f))
IND = ["GHG", "ACG", "O3PR", "PM2_5"]
PAT = ["random", "flow", "cluster", "strategic"]
RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
g = collections.defaultdict(lambda: collections.defaultdict(list))
for x in rows:
    k = (x["indicator"], x["pattern"], x["tiers"], x["rate"])
    for f in ("mape", "coverage", "coverage_m1", "rel_width", "rel_width_m1", "flips", "n_pairs"):
        g[k][f].append(x[f])
med = lambda k, f: float(np.median(g[k][f]))
avg = lambda k, f: float(np.mean(g[k][f]))
out = {"n_rows": len(rows), "rates": RATES}

# Table 1 (flow-weighted, converged chaining)
t1 = {}
for i in IND:
    floor = med((i, "flow", 0, 0.0), "mape")
    halved = next((r for r in RATES if med((i, "flow", 0, r), "mape") <= floor / 2), None)
    t1[i] = dict(floor=floor, halved_at=halved,
                 cov0_median=avg((i, "flow", 0, 0.0), "coverage"), cov0_mean=avg((i, "flow", 0, 0.0), "coverage_m1"),
                 cov80_median=avg((i, "flow", 0, 0.8), "coverage"), cov80_mean=avg((i, "flow", 0, 0.8), "coverage_m1"),
                 width_narrowing_median=1 - med((i, "flow", 0, 0.8), "rel_width") / med((i, "flow", 0, 0.0), "rel_width"),
                 width_narrowing_mean=1 - med((i, "flow", 0, 0.8), "rel_width_m1") / med((i, "flow", 0, 0.0), "rel_width_m1"))
out["table1"] = t1

# Fig. 2 (GHG error against participation, converged chaining): median and interquartile range over seeds
f2 = {}
for p in PAT:
    f2[p] = [med(("GHG", p, 0, r), "mape") for r in RATES]
    f2[p + "_iqr"] = [[float(np.percentile(g[("GHG", p, 0, r)]["mape"], 25)), float(np.percentile(g[("GHG", p, 0, r)]["mape"], 75))] for r in RATES]
out["fig2"] = f2

# Fig. S2 (median error, all indicators, three patterns)
out["figS2"] = {i: {p: [med((i, p, 0, r), "mape") for r in RATES] for p in PAT[:3]} for i in IND}

# Fig. 4 and Table S6: coverage against participation, by indicator, pattern, depth and convention
cov = {}
for i in IND:
    for p in PAT:
        for t in (0, 1, 2, 3):
            cov[f"{i}|{p}|{t}"] = dict(median=[avg((i, p, t, r), "coverage") for r in RATES],
                                       mean=[avg((i, p, t, r), "coverage_m1") for r in RATES],
                                       width_median=[med((i, p, t, r), "rel_width") for r in RATES],
                                       width_mean=[med((i, p, t, r), "rel_width_m1") for r in RATES])
out["coverage"] = cov
json.dump(out, open("data/summary_main.json", "w"), indent=1)
for i in IND:
    print(i, {k: round(v, 3) if isinstance(v, float) else v for k, v in t1[i].items()})
