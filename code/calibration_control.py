"""Factorial control for the interval calibration result (Section 4.3, Table S5).

Run from the repository root: python code/calibration_control.py -> data/calibration_control.json (about 5 minutes on two cores).

Two factors are crossed:
  substitute   actual    the sector-mean secondary factor of the main experiment (offset from the true value)
               random    s_j = m_j * eps_j with eps_j ~ lognormal, mean 1, GSD 2.0: an unbiased substitute whose
                         error is random and has the dispersion the widening assumes (no systematic offset)
  convention   median    draws s * exp(sigma z)               (median-preserving, as in the main experiment)
               mean      draws s * exp(sigma z - sigma^2/2)   (mean-preserving)
Coverage is that of the central 95% interval of 400 draws, over the 19 targets. Same grid as the main experiment for
the random, flow-weighted and sector-clustered patterns (nested participant orders), all four chaining depths and
four indicators, with 100 seeds (the strategic pattern is not part of the manuscript).
If the interval method is calibrated when the substitute error is random, the random/mean cell should be near 95%.
"""
import hashlib, json, sys, time
import numpy as np
sys.path.insert(0, "code")
from cascade import true_pcf, secondary_factors
from patterns import full_order, sample_from_order
from experiments2 import cascade_batch, RATES, TIERS, GSD, N_DRAWS, NOMINAL
from intervals import mean_preserving, coverage_width

SEEDS = range(100)
PATTERNS = ("random", "flow", "cluster")

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
sections = np.array([c[0] for c in inds]); supply = Z.sum(axis=1) + 1e-9
M = true_pcf(A, E); S = secondary_factors(M, inds); sigma = np.log(GSD)
rows = []; t0 = time.time()
for k, pol in enumerate(d["airpol"]):
    e, s_act, m = E[k], S[k], M[k]
    for pattern in PATTERNS:
        for seed in SEEDS:
            key = f"ctl|{pattern}|{seed}"
            rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
            order = full_order(pattern, n, rng, supply=supply, sections=sections, advantage=None)
            eps = rng.lognormal(-sigma ** 2 / 2, sigma, size=n)       # mean-1 substitute error, one draw per seed
            s_rnd = m * eps
            for rate in RATES:
                P = sample_from_order(order, n, rate)
                for tiers in TIERS:
                    rm = np.random.default_rng(int(hashlib.md5((key + f"|{k}|{rate}|{tiers}|mc").encode()).hexdigest()[:8], 16))
                    noise = rm.lognormal(0.0, sigma, size=(N_DRAWS, n))
                    row = dict(indicator=str(pol), pattern=pattern, rate=rate, tiers=(0 if tiers is None else tiers), seed=seed)
                    for name, s in (("actual", s_act), ("random", s_rnd)):
                        draws = cascade_batch(A, e, s[None, :] * noise, P, tiers)
                        d0 = cascade_batch(A, e, np.zeros((1, n)), P, tiers)
                        row[f"{name}_median"] = coverage_width(draws, m, tidx, NOMINAL)[0]
                        row[f"{name}_mean"] = coverage_width(mean_preserving(draws, d0, sigma), m, tidx, NOMINAL)[0]
                    rows.append(row)
    print(pol, f"{time.time()-t0:.0f}s", flush=True)
json.dump(rows, open("data/calibration_control.json", "w"))
print(len(rows))
