import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rates_pct = [0, 5, 10, 20, 40, 60, 80, 100]

# ---------- Fig 2: GHG error vs participation, 3 honest patterns, converged ----------
fig2 = json.load(open("/tmp/work/fig2_data.json"))
fig, ax = plt.subplots(figsize=(5.0, 3.4), dpi=200)
colors = {"random": "#1f77b4", "flow": "#ff7f0e", "cluster": "#2ca02c"}
labels = {"random": "Random adoption", "flow": "Largest suppliers first", "cluster": "Sector consortia"}
for pat in ["random", "flow", "cluster"]:
    med = fig2[pat]["med"]; q25 = fig2[pat]["q25"]; q75 = fig2[pat]["q75"]
    ax.plot(rates_pct, med, marker="o", color=colors[pat], label=labels[pat], linewidth=1.8, markersize=4)
    ax.fill_between(rates_pct, q25, q75, color=colors[pat], alpha=0.15, linewidth=0)
floor = fig2["random"]["med"][0]
ax.axhline(floor, color="gray", linestyle="--", linewidth=1)
ax.text(2, floor + 0.4, "pure database floor", fontsize=7, color="gray")
ax.axhline(floor / 2, color="gray", linestyle=":", linewidth=1)
ax.text(2, floor / 2 + 0.4, "half the floor", fontsize=7, color="gray")
ax.set_xlabel("Suppliers providing primary PCFs (%)")
ax.set_ylabel("Median impact error (%)")
ax.set_xlim(-2, 102)
ax.set_ylim(0, 17)
ax.legend(fontsize=7, loc="upper right", frameon=False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("/tmp/work/newfig2.png")
plt.close()

# ---------- Fig 3: heatmap, GHG error by chaining depth x participation, flow ----------
fig3 = json.load(open("/tmp/work/fig3_data.json"))
rows_order = ["1", "2", "3", "0"]
row_labels = ["1", "2", "3", "converged"]
mat = np.array([fig3[k] for k in rows_order])
fig, ax = plt.subplots(figsize=(5.0, 3.0), dpi=200)
im = ax.imshow(mat, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=16)
ax.set_xticks(range(len(rates_pct)))
ax.set_xticklabels(rates_pct)
ax.set_yticks(range(len(row_labels)))
ax.set_yticklabels(row_labels)
ax.set_xlabel("Participation (%)")
ax.set_ylabel("Chaining depth (tiers)")
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        v = mat[i, j]
        color = "white" if v > 10 else "black"
        ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=7, color=color)
cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Median error (%)", fontsize=8)
plt.tight_layout()
plt.savefig("/tmp/work/newfig3.png")
plt.close()

# ---------- Fig 4: coverage vs participation, 4 indicators, flow, tiers=converged ----------
fig4 = json.load(open("/tmp/work/fig4_data.json"))
rates7 = rates_pct[:-1]
fig, ax = plt.subplots(figsize=(5.0, 3.4), dpi=200)
colors4 = {"GHG": "#1f77b4", "ACG": "#ff7f0e", "O3PR": "#2ca02c", "PM2_5": "#d62728"}
labels4 = {"GHG": "GHG (CO2e)", "ACG": "Acid gases (SO2e)", "O3PR": "O3 precursors (NMVOCe)", "PM2_5": "PM2.5"}
for ind in ["GHG", "ACG", "O3PR", "PM2_5"]:
    ax.plot(rates7, fig4[ind], marker="o", color=colors4[ind], label=labels4[ind], linewidth=1.8, markersize=4)
ax.axhline(95, color="gray", linestyle="--", linewidth=1)
ax.text(60, 96, "nominal 95%", fontsize=7, color="gray")
ax.set_xlabel("Suppliers providing primary PCFs (%)")
ax.set_ylabel("95% interval coverage (%)")
ax.set_xlim(-2, 82)
ax.set_ylim(30, 102)
ax.legend(fontsize=7, loc="lower left", frameon=False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("/tmp/work/newfig4.png")
plt.close()

print("done")
