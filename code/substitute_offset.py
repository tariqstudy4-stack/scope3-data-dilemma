"""Offset of the sector-average substitute and within-section dispersion (Sections 3.4 and 4.3, Table S5c).

Run from the repository root: python code/substitute_offset.py -> data/substitute_offset.json

For each indicator and each of the 19 manufacturing targets, the footprint is computed with no primary data
(participation 0, so every supplier is represented by its secondary factor) and compared with the ground truth.
Reported: the mean signed relative error over targets (positive = the substitute overstates the footprint),
the mean absolute error (the database-only floor is its median), and the median geometric standard deviation of the
true intensities within a NACE section (sections with two or more industries), with the share of
(indicator, section) cells whose dispersion is below the assumed GSD of 2.0.
"""
import json, sys
import numpy as np
sys.path.insert(0, "code")
from cascade import true_pcf, secondary_factors
from experiments2 import cascade_batch, GSD

d = np.load("data/matrices.npz", allow_pickle=True)
A, E = d["A"], d["E"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
sections = np.array([c[0] for c in inds])
M = true_pcf(A, E); S = secondary_factors(M, inds)
P0 = np.zeros(n, dtype=bool)
out = {"multiplier_mean_at_assumed_gsd": float(np.exp(np.log(GSD) ** 2 / 2)), "indicators": {}}
gsds = []
for k, pol in enumerate(d["airpol"]):
    est = cascade_batch(A, E[k], S[k][None, :], P0, None)[0]
    rel = (est[tidx] - M[k][tidx]) / M[k][tidx]
    out["indicators"][str(pol)] = dict(mean_signed_error_pct=float(100 * rel.mean()),
                                       mean_abs_error_pct=float(100 * np.abs(rel).mean()),
                                       median_abs_error_pct=float(100 * np.median(np.abs(rel))),
                                       share_overstated=float((rel > 0).mean()))
    for s in sorted(set(sections)):
        idx = np.where(sections == s)[0]
        if len(idx) >= 2 and np.all(M[k][idx] > 0):
            gsds.append(float(np.exp(np.std(np.log(M[k][idx]), ddof=1))))
out["within_section_gsd"] = dict(median=float(np.median(gsds)), share_below_assumed=float(np.mean(np.array(gsds) < GSD)), n_cells=len(gsds))
json.dump(out, open("data/substitute_offset.json", "w"), indent=1)
print(json.dumps(out, indent=1))
