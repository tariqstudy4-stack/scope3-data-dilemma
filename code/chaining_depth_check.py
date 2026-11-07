"""Chaining depth against participation for greenhouse gases (Fig. 3, Table S6 of the manuscript).

Run from the repository root: python code/chaining_depth_check.py  -> data/chaining_depth.json
Flow-weighted adoption, 400 seeds, point estimates (no Monte Carlo). The participant ordering of each seed is
shared across rates and tier depths (same keys as code/experiments2.py), so differences between depths are paired.
Writes the median error per depth and rate, and the paired difference (one tier minus converged) with its
standard error over the 400 seeds.
"""
import os, sys, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, HERE)
import numpy as np
from cascade import secondary_factors, true_pcf, mape
from patterns import full_order, sample_from_order

RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
TIERS = [1, 2, 3, None]
d = np.load(os.path.join(ROOT, "data", "matrices.npz"), allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
sections = np.array([c[0] for c in inds]); supply = Z.sum(axis=1) + 1e-9
M = true_pcf(A, E); S = secondary_factors(M, inds)
k = list(d["airpol"]).index("GHG")
e, s, m = E[k], S[k], M[k]

def cascade(P, tiers):
    r = s.copy()
    for _ in range(200 if tiers is None else tiers):
        r_new = np.where(P, e + r @ A, s)
        if tiers is None and np.max(np.abs(r_new - r)) < 1e-12:
            r = r_new; break
        r = r_new
    return e + r @ A

res = {(r, t): [] for r in RATES for t in TIERS}
for seed in range(400):
    rng = np.random.default_rng(int(hashlib.md5(f"flow|{seed}".encode()).hexdigest()[:8], 16))
    order = full_order("flow", n, rng, supply=supply, sections=sections, advantage=None)
    for r in RATES:
        P = sample_from_order(order, n, r)
        for t in TIERS:
            res[(r, t)].append(mape(cascade(P, t), m, tidx))

out = {"rates": RATES,
       "median": {("converged" if t is None else str(t)): [float(np.median(res[(r, t)])) for r in RATES] for t in TIERS},
       "paired_1_minus_converged": {}}
for r in RATES:
    dd = np.array(res[(r, 1)]) - np.array(res[(r, None)])
    out["paired_1_minus_converged"][str(r)] = [float(dd.mean()), float(dd.std(ddof=1) / np.sqrt(len(dd)))]
json.dump(out, open(os.path.join(ROOT, "data", "chaining_depth.json"), "w"), indent=1)
print("written data/chaining_depth.json")
