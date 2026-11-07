"""Fig. 2 of the manuscript: median greenhouse gas error against participation for the three adoption patterns,
converged chaining, bands = interquartile range over 400 seeds.
Run from the repository root after code/summarize_main.py: python figures/make_fig2.py -> figures/fig2_error_participation.png"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(ROOT, "data", "summary_main.json")))
R = [int(round(r * 100)) for r in s["rates"]]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5})
col = {"random": "#1f77b4", "flow": "#ff7f0e", "cluster": "#2ca02c"}
lab = {"random": "Random adoption", "flow": "Largest suppliers first", "cluster": "Sector consortia"}
fig, ax = plt.subplots(figsize=(3.4, 2.35), dpi=300)
for p in ("random", "flow", "cluster"):
    iqr = np.array(s["fig2"][p + "_iqr"])
    ax.plot(R, s["fig2"][p], marker="o", ms=3, lw=1.3, color=col[p], label=lab[p])
    ax.fill_between(R, iqr[:, 0], iqr[:, 1], color=col[p], alpha=.13, lw=0)
floor = s["fig2"]["flow"][0]
ax.axhline(floor, color="gray", ls="--", lw=.7); ax.text(2, floor + .35, f"database-only floor ({floor:.2f}%)", fontsize=5.5, color="gray")
ax.axhline(floor / 2, color="gray", ls=":", lw=.7); ax.text(2, floor / 2 + .35, "half the floor", fontsize=5.5, color="gray")
ax.set_xticks(R); ax.set_xlim(-2, 102); ax.set_ylim(0, 17)
ax.set_xlabel("Suppliers providing primary PCFs (%)"); ax.set_ylabel("Median impact error (%)")
ax.legend(fontsize=5.8, frameon=False, loc="upper right", bbox_to_anchor=(1, .93))
for k in ("top", "right"): ax.spines[k].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(ROOT, "figures", "fig2_error_participation.png")); plt.close()
