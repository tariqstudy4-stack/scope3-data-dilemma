"""Fig. 4 of the manuscript: coverage of the 95% Monte Carlo interval against participation, flow-weighted adoption,
converged chaining, 400 seeds, for the two lognormal conventions (solid: median-preserving, dashed: mean-preserving).
Run from the repository root after code/summarize_main.py: python figures/make_fig4.py -> figures/fig4_coverage.png"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(ROOT, "data", "summary_main.json")))
R = [int(round(r * 100)) for r in s["rates"]][:-1]          # 100% is omitted: the interval has zero width
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5})
names = {"GHG": "Greenhouse gases", "ACG": "Acid gases", "O3PR": "Ozone precursors", "PM2_5": "PM2.5"}
col = {"GHG": "#1f77b4", "ACG": "#d62728", "O3PR": "#2ca02c", "PM2_5": "#9467bd"}
fig, ax = plt.subplots(figsize=(3.4, 2.4), dpi=300)
for i in names:
    c = s["coverage"][f"{i}|flow|0"]
    ax.plot(R, c["median"][:-1], marker="o", ms=2.6, lw=1.2, color=col[i])
    ax.plot(R, c["mean"][:-1], marker="s", ms=2.2, lw=1.0, ls="--", color=col[i])
ax.axhline(95, color="gray", ls=":", lw=.8); ax.text(44, 96.3, "nominal 95%", fontsize=5.5, color="gray")
ax.set_xticks(R); ax.set_xlim(-2, 82); ax.set_ylim(40, 102)
ax.set_xlabel("Suppliers providing primary PCFs (%)"); ax.set_ylabel("Interval coverage (%)")
h = [Line2D([0], [0], color=col[i], lw=1.2) for i in names] + [Line2D([0], [0], color="k", lw=1.2), Line2D([0], [0], color="k", lw=1.0, ls="--")]
ax.legend(h, list(names.values()) + ["median-preserving", "mean-preserving"], fontsize=5.2, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, -.2))
for k in ("top", "right"): ax.spines[k].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(ROOT, "figures", "fig4_coverage.png")); plt.close()
