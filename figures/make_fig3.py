"""Fig. 3 of the manuscript: median GHG error by chaining depth and participation (flow-weighted, 400 seeds).

Run from the repository root after code/chaining_depth_check.py: python figures/make_fig3.py
Reads data/chaining_depth.json and writes figures/fig3_chaining_depth.png.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "chaining_depth.json")))
mat = np.array([d["median"][k] for k in ("1", "2", "3", "converged")])
rates = [int(round(r * 100)) for r in d["rates"]]
plt.rcParams["font.family"] = "serif"
fig, ax = plt.subplots(figsize=(3.7, 2.23), dpi=200)
im = ax.imshow(mat, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=16)
ax.set_xticks(range(len(rates))); ax.set_xticklabels(rates, fontsize=7)
ax.set_yticks(range(4)); ax.set_yticklabels(["1", "2", "3", "converged"], fontsize=7)
ax.set_xlabel("Participation (%)", fontsize=8); ax.set_ylabel("Chaining depth (tiers)", fontsize=8)
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6.3, color="white" if v > 11 else "black")
cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Median error (%)", fontsize=7); cb.ax.tick_params(labelsize=6.5)
plt.tight_layout()
plt.savefig(os.path.join(ROOT, "figures", "fig3_chaining_depth.png"))
