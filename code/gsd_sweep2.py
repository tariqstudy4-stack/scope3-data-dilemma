"""Extended GSD sweep (restores the Fig. 7 material the abstract referred
to, and extends it past the original 3.0 cap to check whether acid-gas
coverage genuinely saturates or was just still rising at the old cap)."""
import hashlib, json
import numpy as np
from cascade import true_pcf, secondary_factors
from patterns import sample
from experiments import cascade_batch

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z = d["A"], d["E"], d["Z"]
inds = list(d["industries"]); n = len(inds)
tidx = np.array([inds.index(c) for c in d["manuf"]])
sections = np.array([c[0] for c in inds]); supply = Z.sum(axis=1) + 1e-9
M = true_pcf(A, E); S = secondary_factors(M, inds)

GSDS = [1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0]
SEEDS = 200
out = {}
for k, pol in enumerate(d["airpol"]):
    e, s_row, m = E[k], S[k], M[k]
    for rate in (0.2, 0.8):
        for gsd in GSDS:
            covs = []
            for seed in range(SEEDS):
                key = f"gsd2|{k}|flow|{rate}|{seed}"
                rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
                P = sample("flow", n, rate, rng, supply=supply, sections=sections)
                noise = rng.lognormal(0.0, np.log(gsd), size=(800, n))
                draws = cascade_batch(A, e, s_row[None, :] * noise, P, None)
                lo = np.percentile(draws, 2.5, axis=0)
                hi = np.percentile(draws, 97.5, axis=0)
                covs.append(np.mean((m[tidx] >= lo[tidx]) & (m[tidx] <= hi[tidx])) * 100)
            out[f"{pol}|{rate}|{gsd}"] = float(np.mean(covs))
json.dump(out, open("data/gsd_sweep_ext.json", "w"), indent=1)
for pol in ("GHG", "ACG", "O3PR", "PM2_5"):
    print(pol, "@80%:", [round(out[f"{pol}|0.8|{g}"], 1) for g in GSDS])
