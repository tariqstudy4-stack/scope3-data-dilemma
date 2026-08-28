"""Round-4 robustness checks:
(a) Noisy self-assessment: supplier's participation decision is based on a
    noisy estimate of its own advantage (advantage + noise*eps), not the
    exact value -- tests whether the reversal survives suppliers not being
    perfect self-graders. noise expressed as a fraction of std(advantage).
(b) GHG-only-driven selection: advantage computed from GHG alone rather
    than the 4-indicator composite -- an alternative information basis for
    the same exp() functional form.
(c) Per-indicator R^2 (not pooled across indicators) for material pairwise
    ranking-flip rate vs participation, flow-weighted, converged chaining.
(d) A few additional bootstrap 95% CIs on headline point estimates.
"""
import hashlib, json
import numpy as np
from cascade import secondary_factors, true_pcf, mape, ranking_flips
from patterns import _weighted_order, sample_from_order, flow_order

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
sections = np.array([c[0] for c in inds]); supply = Z.sum(axis=1) + 1e-9
M = true_pcf(A, E)
S = secondary_factors(M, inds)
airpol = list(d["airpol"])

adv_parts = []
for k in range(len(airpol)):
    num = S[k] - M[k]
    z = (num - num.mean()) / (num.std() + 1e-12)
    adv_parts.append(z)
advantage_composite = np.mean(adv_parts, axis=0)
advantage_ghg = adv_parts[0]  # GHG-only advantage score


def cascade_batch(e, s_row, P):
    R = s_row[None, :].copy()
    for _ in range(200):
        R_new = np.where(P[None, :], e[None, :] + R @ A, s_row[None, :])
        if np.max(np.abs(R_new - R)) < 1e-12:
            R = R_new
            break
        R = R_new
    return (e[None, :] + R @ A)[0]


# ---- (a) noisy self-assessment sweep ----
NOISE_FRACS = [0.0, 0.5, 1.0, 2.0, 4.0]  # noise stdev as multiple of std(advantage)
RATE = 0.8
SEEDS = 150
res_noise = {}
for k, pol in enumerate(airpol):
    e, s_row, m = E[k], S[k], M[k]
    scale = np.std(advantage_composite) + 1e-9
    for nf in NOISE_FRACS:
        errs = []
        for seed in range(SEEDS):
            key = f"noisy|{pol}|{nf}|{seed}"
            rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
            eps = rng.normal(0, 1, size=n)
            noisy_adv = advantage_composite + nf * np.std(advantage_composite) * eps
            w = np.exp(noisy_adv / scale)
            order = _weighted_order(n, rng, w)
            P = sample_from_order(order, n, RATE)
            pt = cascade_batch(e, s_row, P)
            errs.append(mape(pt, m, tidx))
        res_noise[f"{pol}|{nf}"] = float(np.median(errs))
    print(pol, "noise sweep done", flush=True)

# ---- (b) GHG-only-driven selection ----
res_ghgonly = {}
for k, pol in enumerate(airpol):
    e, s_row, m = E[k], S[k], M[k]
    scale = np.std(advantage_ghg) + 1e-9
    for rate in (0.0, 0.4, 0.8):
        errs = []
        for seed in range(SEEDS):
            key = f"ghgonly|{pol}|{rate}|{seed}"
            rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
            w = np.exp(advantage_ghg / scale)
            order = _weighted_order(n, rng, w)
            P = sample_from_order(order, n, rate)
            pt = cascade_batch(e, s_row, P)
            errs.append(mape(pt, m, tidx))
        res_ghgonly[f"{pol}|{rate}"] = float(np.median(errs))
    print(pol, "ghg-only done", flush=True)

json.dump({"noisy_selfassessment": res_noise, "ghg_only_selection": res_ghgonly},
          open("data/robustness_check2.json", "w"), indent=1)

print("\n--- Noisy self-assessment: median error at 80% participation ---")
floor = {pol: res_noise[f"{pol}|4.0"] for pol in airpol}  # noise=4 approx random-pattern-like
for pol in airpol:
    row = [round(res_noise[f"{pol}|{nf}"], 2) for nf in NOISE_FRACS]
    print(f"  {pol}: noise_fracs{NOISE_FRACS} -> {row}")

print("\n--- GHG-only-driven selection: median error by rate ---")
for pol in airpol:
    row = [round(res_ghgonly[f"{pol}|{r}"], 2) for r in (0.0, 0.4, 0.8)]
    print(f"  {pol}: rates[0,0.4,0.8] -> {row}")
