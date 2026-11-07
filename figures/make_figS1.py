"""Fig. S1 of the SI: schematic of one cascade step (a tier-1 supplier that reports primary data, one tier-2 supplier that
discloses and one that does not, whose place is taken by the sector-average factor). Schematic only; no data.
Run from the repository root: python figures/make_figS1.py -> figures/figS1_cascade.png"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plt.rcParams.update({"font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans"})
fig, ax = plt.subplots(figsize=(4.4, 2.7), dpi=200); ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
def box(x, y, w, h, t, fc, ec, fs=7, tc="black"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, linespacing=1.2, color=tc)
def arr(x1, y1, x2, y2, c="k", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=8, lw=1.1, color=c, linestyle=ls))
box(0.2, 4.6, 2.9, 1.1, "Tier-2 supplier\n(primary)", "#72d6a8", "#1a7f55")
box(0.2, 2.5, 2.9, 1.1, "Tier-2 supplier\n(not disclosing)", "#c9c9c9", "#666")
box(3.9, 3.4, 2.4, 1.3, "Tier-1 supplier\n(primary)", "#72d6a8", "#1a7f55")
box(7.2, 3.4, 2.5, 1.3, "Assessed\nmanufacturer", "#0072B2", "#004a75", tc="white")
box(3.6, 0.3, 3.0, 1.1, "Sector-average\ndatabase", "#ffd23f", "#8a6d00")
box(7.2, 0.4, 2.6, 1.7, "DPP carries PCF +\nprimary data share\n(PACT 4.2.2)", "#dff1fb", "#2a9bd6", fs=6.3)
arr(3.1, 5.0, 3.9, 4.4); ax.text(3.35, 5.0, "$r_i$", fontsize=8, style="italic")
arr(3.1, 3.0, 3.9, 3.6, c="#d62728", ls="--"); ax.text(3.35, 2.95, "x", color="#d62728", fontsize=9)
arr(5.1, 1.4, 5.1, 3.4, c="#8a6d00"); ax.text(5.25, 2.3, "$s_i$", fontsize=8, style="italic", color="#8a6d00")
arr(6.3, 4.05, 7.2, 4.05); ax.text(6.55, 4.25, "$r_j$", fontsize=8, style="italic")
arr(8.45, 3.4, 8.45, 2.1)
plt.savefig(os.path.join(ROOT, "figures", "figS1_cascade.png"), bbox_inches="tight", pad_inches=.05); plt.close()
