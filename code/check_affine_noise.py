"""Check that mean-preserving draws obtained from the affine shortcut in intervals.py equal a
direct computation (noise multiplied by exp(-sigma^2/2) before the cascade).
Run from the repository root: python code/check_affine_noise.py  (a few seconds)."""
import sys
import numpy as np
sys.path.insert(0, "code")
from cascade import true_pcf, secondary_factors
from patterns import full_order, sample_from_order
from experiments2 import cascade_batch
from intervals import mean_preserving

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
M = true_pcf(A, E); S = secondary_factors(M, inds)
sigma = np.log(2.0); c = np.exp(-sigma ** 2 / 2)
supply = Z.sum(axis=1) + 1e-9; sections = np.array([x[0] for x in inds])
rng = np.random.default_rng(1); worst = 0.0
for k in range(4):
    for pat in ("random", "flow", "cluster"):
        order = full_order(pat, n, np.random.default_rng(5), supply=supply, sections=sections, advantage=None)
        for rate in (0.0, 0.2, 0.6, 0.8, 1.0):
            P = sample_from_order(order, n, rate)
            for tiers in (1, 2, 3, None):
                noise = rng.lognormal(0, sigma, size=(50, n))
                dr = cascade_batch(A, E[k], S[k][None, :] * noise, P, tiers)
                direct = cascade_batch(A, E[k], S[k][None, :] * noise * c, P, tiers)
                d0 = cascade_batch(A, E[k], np.zeros((1, n)), P, tiers)
                worst = max(worst, float(np.max(np.abs(mean_preserving(dr, d0, sigma) - direct)
                                                / np.maximum(np.abs(direct), 1e-30))))
print(f"max relative difference {worst:.2e}")
assert worst < 1e-6
