"""Sensitivity of interval coverage to the assumed GSD (Fig. 7 material)."""
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

GSDS = [1.2, 1.5, 2.0, 2.5, 3.0]
out = {}
for k, pol in enumerate(d["airpol"]):
    e, s_row, m = E[k], S[k], M[k]
    for rate in (0.2, 0.8):
        for gsd in GSDS:
            covs = []
            for seed in range(10):
                key = f"gsd|{k}|flow|{rate}|{seed}"
                rng = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
                P = sample("flow", n, rate, rng, supply=supply, sections=sections)
                noise = rng.lognormal(0.0, np.log(gsd), size=(800, n))
                draws = cascade_batch(A, e, s_row[None, :] * noise, P, None)
                lo = np.percentile(draws, 2.5, axis=0)
                hi = np.percentile(draws, 97.5, axis=0)
                covs.append(np.mean((m[tidx] >= lo[tidx]) & (m[tidx] <= hi[tidx])) * 100)
            out[f"{pol}|{rate}|{gsd}"] = float(np.mean(covs))
json.dump(out, open("data/gsd_sweep.json", "w"), indent=1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 8, "axes.spines.top": False,
    "axes.spines.right": False, "grid.linewidth": 0.4, "grid.alpha": 0.35,
    "figure.dpi": 300, "savefig.bbox": "tight"})
fig, ax = plt.subplots(figsize=(3.6, 2.9))
CI = {"GHG": "#0072B2", "ACG": "#D55E00", "O3PR": "#009E73", "PM2_5": "#CC79A7"}
for pol in ("GHG", "ACG", "O3PR", "PM2_5"):
    for rate, ls, mk in ((0.2, "--", "s"), (0.8, "-", "o")):
        y = [out[f"{pol}|{rate}|{g}"] for g in GSDS]
        ax.plot(GSDS, y, ls, color=CI[pol], marker=mk, ms=3,
                lw=1.4 if rate == 0.8 else 1.0,
                alpha=1.0 if rate == 0.8 else 0.55)
ax.axhline(95, color="0.2", lw=1.0, ls=(0, (4, 2)))
ax.text(2.98, 95.8, "nominal 95%", fontsize=6.5, ha="right", color="0.25")
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], color=CI[p], lw=1.6,
                  label={"GHG": "GHG", "ACG": "Acid", "O3PR": "O$_3$ prec.",
                         "PM2_5": "PM$_{2.5}$"}[p]) for p in CI]
handles += [Line2D([0], [0], color="0.3", lw=1.4, marker="o", ms=3,
                   label="80% participation"),
            Line2D([0], [0], color="0.3", lw=1.0, ls="--", marker="s",
                   ms=3, alpha=0.55, label="20% participation")]
ax.legend(handles=handles, frameon=False, fontsize=6, ncol=2, loc="lower right")
ax.set_xlabel("Assumed geometric standard deviation of secondary factors")
ax.set_ylabel("95% interval coverage (%)")
ax.set_ylim(0, 104); ax.grid(True, axis="y")
fig.savefig("figs/figF_gsd_sweep.pdf"); fig.savefig("figs/figF_gsd_sweep.png", dpi=300)
print(json.dumps({k: round(v, 1) for k, v in out.items() if "|0.8|" in k}, indent=0))
