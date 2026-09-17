"""Regenerates figures/fig_experiment_design.png.

Standalone script (no dependency on the rest of code/): draws the
experimental design / reproducibility pipeline diagram described in
README.md Fig. A1, from a fixed content spec below, so anyone can
reproduce or restyle the figure without re-deriving the pipeline from
the result files.

Style: "slate ledger" -- cool teal accent, sharp-cornered boxes with a
colored left accent bar, sans-serif type, straight/orthogonal
connectors. Deliberately different from the companion imputation-
benchmark repository's fig_experiment_design.png (warm amber, rounded
boxes, numbered badges, serif type, curved connectors); the two
figures describe different pipelines and are not meant to look
interchangeable.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = "Liberation Sans"

INK = "#20302f"
BOX_FILL = "#ffffff"
BOX_EDGE = "#c7d1d0"
BAR_NORMAL = "#7a8a89"
TEAL_FILL = "#e4f1ef"
TEAL_EDGE = "#0f4c4c"
BAR_TEAL = "#e0623c"
BG = "#f6f8f8"

fig, ax = plt.subplots(figsize=(8.9, 11.6), dpi=220)
ax.set_xlim(0, 10)
ax.set_ylim(0, 13.4)
ax.axis("off")
fig.patch.set_facecolor("white")
ax.add_patch(Rectangle((-0.2, -0.2), 10.4, 13.8, facecolor=BG,
                        edgecolor="none", zorder=0))


def box(cx, cy, w, h, text, highlight=False, fontsize=8.8, bold_first=None):
    fill = TEAL_FILL if highlight else BOX_FILL
    edge = TEAL_EDGE if highlight else BOX_EDGE
    bar = BAR_TEAL if highlight else BAR_NORMAL
    x0, y0 = cx - w / 2, cy - h / 2
    patch = Rectangle((x0, y0), w, h, linewidth=1.1, edgecolor=edge,
                       facecolor=fill, zorder=2)
    ax.add_patch(patch)
    ax.add_patch(Rectangle((x0, y0), 0.09, h, linewidth=0,
                            facecolor=bar, zorder=3))
    ax.text(cx + 0.05, cy, text, ha="center", va="center", fontsize=fontsize,
            color=INK, zorder=4, linespacing=1.5, family="Liberation Sans")


def elbow(p_from, p_to, mid_frac=0.5):
    """Orthogonal (elbow) connector: drop straight down from the source,
    then straight across, then straight down into the destination --
    distinct from the imputation figure's curved connectors."""
    x0, y0 = p_from
    x1, y1 = p_to
    ym = y0 - (y0 - y1) * mid_frac
    path = [(x0, y0), (x0, ym), (x1, ym)]
    for i in range(len(path) - 1):
        ax.add_patch(FancyArrowPatch(
            path[i], path[i + 1], arrowstyle="-", linewidth=1.15,
            color="#4b5a59", zorder=1, shrinkA=0, shrinkB=0,
        ))
    ax.add_patch(FancyArrowPatch(
        (x1, ym), p_to, arrowstyle="-|>", mutation_scale=11,
        linewidth=1.15, color="#4b5a59", zorder=1, shrinkA=0, shrinkB=1,
    ))


def straight(p_from, p_to):
    ax.add_patch(FancyArrowPatch(
        p_from, p_to, arrowstyle="-|>", mutation_scale=11,
        linewidth=1.15, color="#4b5a59", zorder=1, shrinkA=1, shrinkB=1,
    ))


# Title
ax.text(5, 13.05, "Experimental design and reproducibility pipeline",
         ha="center", va="center", fontsize=16, weight="bold", color=INK,
         family="Liberation Sans")
ax.text(5, 12.62, "PCF tier-by-tier cascade benchmark over the EU-27 "
                   "technosphere (PACT v3 / Catena-X RB v4)",
         ha="center", va="center", fontsize=10, color="#4b5a59",
         family="Liberation Sans")

# Row 1: data sources
box(2.6, 11.75, 4.6, 1.15,
    "Eurostat naio_10_cp1750\nEU-27 symmetric input-output table\n"
    "64-industry NACE Rev.2, 2022")
box(7.4, 11.75, 4.6, 1.15,
    "Eurostat env_ac_ainah_r2\nAir emissions accounts\nby NACE Rev.2, 2022")
straight((2.6, 11.75 - 0.575), (4.85, 10.4 + 0.42))
straight((7.4, 11.75 - 0.575), (5.15, 10.4 + 0.42))

# Row 2: build_matrices.py
box(5, 10.4, 8.6, 0.85,
    "build_matrices.py\nmatrix construction → API-vs-published check",
    fontsize=9.0)
straight((5, 10.4 - 0.42), (5, 9.2 + 0.45))

# Row 3: matrices.npz
box(5, 9.2, 8.6, 0.9,
    "data/matrices.npz — technosphere A, extension E,\n"
    "64 industries × 4 impact indicators (GHG, ACG, O3PR, PM2.5)",
    fontsize=8.8)

# Row 4: cascade.py (highlight) + patterns.py
box(3.15, 7.55, 5.3, 1.85,
    "cascade.py\nPCF tier-chaining model\n\n"
    "rj = ej + Σi Aij · r̂i   (if j participates)\n"
    "rj = sj                       (otherwise)",
    highlight=True, fontsize=8.6)
box(7.9, 7.55, 3.9, 1.85,
    "patterns.py — factorial design\n"
    "• adoption: random / flow / cluster / strategic\n"
    "• participation: 0–100% (8 rates)\n"
    "• chaining depth: T=1, 2, 3, converged\n"
    "• seeds: 10 (main grid), 400 (replicate)",
    fontsize=7.7)
elbow((5, 9.2 - 0.45), (3.15, 7.55 + 0.925), mid_frac=0.4)
straight((7.9, 7.55), (3.15 + 2.65, 7.55))

# Row 5: experiments.py
box(5, 5.85, 8.6, 0.95,
    "experiments.py  /  experiments2.py <indicator>\n"
    "cascade all 3(4) patterns × 8 rates × 4 tiers × seeds → "
    "propagate to 19 manufacturing targets", fontsize=8.3)
elbow((3.15, 7.55 - 0.925), (5, 5.85 + 0.475), mid_frac=0.5)

# Row 6: results
box(2.6, 4.55, 4.6, 0.95,
    "data/results.json\n(10 seeds / condition)", fontsize=9.0)
box(7.4, 4.55, 4.6, 0.95,
    "data/results_400_*.json\n(400 seeds / condition)", fontsize=9.0)
straight((5, 5.85 - 0.475), (2.6, 4.55 + 0.475))
straight((5, 5.85 - 0.475), (7.4, 4.55 + 0.475))

# Row 7: four checks
checks = [
    ("gsd_sweep(2).py", "GSD sensitivity\n1.2 – 10.0"),
    ("strength_sweep.py", "self-selection\nλ sensitivity"),
    ("robustness_check2.py", "noisy self-assessment,\nper-indicator R²"),
    ("validate_cascade.py /\nverify_all.py", "independent checks"),
]
xs7 = [1.35, 3.75, 6.15, 8.55]
for x, (name, desc) in zip(xs7, checks):
    box(x, 3.05, 2.15, 1.3, f"{name}\n{desc}", fontsize=7.3)
straight((2.6, 4.55 - 0.475), (1.35, 3.05 + 0.65))
straight((2.6, 4.55 - 0.475), (3.75, 3.05 + 0.65))
straight((7.4, 4.55 - 0.475), (6.15, 3.05 + 0.65))
straight((7.4, 4.55 - 0.475), (8.55, 3.05 + 0.65))

# Row 8: finalize_stats.py (highlight)
box(5, 1.25, 8.8, 1.05,
    "finalize_stats.py  →  figures/make_figs.py\n"
    "floor / halving-threshold statistics → Figs. 2–5",
    highlight=True, fontsize=9.2)
for x in xs7:
    straight((x, 3.05 - 0.65), (5, 1.25 + 0.525))

plt.tight_layout()
plt.savefig("fig_experiment_design.png", dpi=220, facecolor="white")
print("saved fig_experiment_design.png")
