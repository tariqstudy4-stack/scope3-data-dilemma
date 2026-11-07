"""Fig. S2 of the SI: median error against participation for the four indicators and three adoption patterns, converged chaining.
Run from the repository root after code/summarize_main.py: python figures/make_figS2.py -> figures/figS2_indicators.png"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = json.load(open(os.path.join(ROOT, "data", "summary_main.json")))
R = [int(round(r * 100)) for r in s["rates"]]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5})
col = {"random": "#1f77b4", "flow": "#ff7f0e", "cluster": "#2ca02c"}
lab = {"random": "Random adoption", "flow": "Largest suppliers first", "cluster": "Sector consortia"}
names = {"GHG": "Greenhouse gases", "ACG": "Acid gases", "O3PR": "Ozone precursors", "PM2_5": "PM2.5"}
fig, axs = plt.subplots(2, 2, figsize=(3.4, 2.55), dpi=300, sharex=True)
for ax, k in zip(axs.ravel(), names):
    for p in col:
        ax.plot(R, s["figS2"][k][p], marker="o", ms=2, lw=1, color=col[p], label=lab[p])
    ax.axhline(s["figS2"][k]["flow"][0] / 2, color="gray", ls=":", lw=.6)
    ax.set_title(names[k], fontsize=6.5, pad=2); ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_ylim(0, 25)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
for ax in axs[1]: ax.set_xlabel("Participation (%)", fontsize=6)
for ax in axs[:, 0]: ax.set_ylabel("Median error (%)", fontsize=6)
h, l = axs[0, 0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=3, fontsize=5.3, frameon=False, bbox_to_anchor=(.5, -.01))
plt.tight_layout(rect=(0, .05, 1, 1)); plt.savefig(os.path.join(ROOT, "figures", "figS2_indicators.png")); plt.close()
