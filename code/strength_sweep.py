"""Self-selection strength sensitivity sweep (Tier-1 revision item).

Parameterizes the strategic/self-selected adoption rule with a gaming
strength multiplier lambda: sampling weight = exp(lambda * advantage /
std(advantage)). lambda=1 reproduces the manuscript's reported "strategic"
pattern exactly (same weight formula as patterns.strategic_order).
lambda=0 collapses to uniform (=random pattern). Larger lambda = suppliers
weight their own favorability more heavily when deciding whether to
volunteer early.

Also used to directly test the Devil's Advocate's circularity hypothesis:
S (secondary/database factors) is computed ONCE from the full population
before this sweep runs and is never recomputed based on which industries
happen to be participating at a given rate -- confirmed by inspection of
experiments2.py (S = secondary_factors(M, inds) computed once, reused
unchanged across every pattern/rate/seed). This script's results also
serve as an empirical check: if the reversal appeared only because of a
shrinking-averaging-pool artifact, weakening lambda toward 0 would not
smoothly reduce the effect toward the random-pattern baseline -- but S
itself is fixed regardless of lambda, so any such artifact is structurally
impossible here.
"""
import hashlib, json
import numpy as np
from cascade import secondary_factors, true_pcf, mape
from patterns import _weighted_order, sample_from_order

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
M = true_pcf(A, E)
S = secondary_factors(M, inds)
airpol = list(d["airpol"])

adv_parts = []
for k in range(len(airpol)):
    num = S[k] - M[k]
    z = (num - num.mean()) / (num.std() + 1e-12)
    adv_parts.append(z)
advantage = np.mean(adv_parts, axis=0)


def cascade_batch(e, s_row, P, tiers=None):
    R = s_row[None, :].copy()
    for _ in range(200):
        R_new = np.where(P[None, :], e[None, :] + R @ A, s_row[None, :])
        if np.max(np.abs(R_new - R)) < 1e-12:
            R = R_new
            break
        R = R_new
    return (e[None, :] + R @ A)[0]


LAMBDAS = [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
RATES = [0.0, 0.20, 0.40, 0.60, 0.80]
SEEDS = 150

out = {}
for k, pol in enumerate(airpol):
    e, s_row, m = E[k], S[k], M[k]
    for lam in LAMBDAS:
        for rate in RATES:
            errs = []
            for seed in SEEDS and range(SEEDS):
                key = f"strength|{pol}|{lam}|{rate}|{seed}"
                rng = np.random.default_rng(
                    int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
                scale = np.std(advantage) + 1e-9
                w = np.exp(lam * advantage / scale)
                order = _weighted_order(n, rng, w)
                P = sample_from_order(order, n, rate)
                pt = cascade_batch(e, s_row, P)
                errs.append(mape(pt, m, tidx))
            out[f"{pol}|{lam}|{rate}"] = float(np.median(errs))
    print(pol, "done", flush=True)

json.dump(out, open("data/strength_sweep.json", "w"), indent=1)

floor = {pol: out[f"{pol}|0.0|0.0"] for pol in airpol}
print("\nFloor (0% participation, same for all lambda):", floor)
print("\nMedian error by lambda at 80% participation:")
for pol in airpol:
    row = [round(out[f"{pol}|{lam}|0.8"], 2) for lam in LAMBDAS]
    print(f"  {pol}: floor={floor[pol]:.2f}  lambdas{LAMBDAS} -> {row}")
print("\nMedian error by lambda at 40% participation:")
for pol in airpol:
    row = [round(out[f"{pol}|{lam}|0.4"], 2) for lam in LAMBDAS]
    print(f"  {pol}: floor={floor[pol]:.2f}  lambdas{LAMBDAS} -> {row}")
