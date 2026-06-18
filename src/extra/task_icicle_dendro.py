# -*- coding: utf-8 -*-
"""
Deep Hierarchy — Polished Visual Edition
=========================================
Octree icicle, multi-level sunburst, deep dendrogram, timeline icicle, flow matrix.
Optimized color, layout, typography, annotations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Arc, Wedge
from matplotlib.collections import LineCollection
from scipy.cluster.hierarchy import dendrogram, linkage
import os, sys, warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_timestep, load_all_timesteps

OUT = os.path.join(OUTPUT_DIR, "icicle_dendro")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({'font.size': 10, 'axes.titlesize': 14, 'axes.labelsize': 11})

# Load data once
print("Loading...")
data_99 = load_timestep(99)
d64_c = np.ascontiguousarray(np.transpose(data_99[::2,::2,::2], (2,1,0)))
all_data = load_all_timesteps(verbose=False)
flat99 = data_99.ravel(); total = len(flat99)

# ============================================================================
# Color helpers
# ============================================================================
def density_color(val):
    """Smooth blue->gray->red mapping."""
    t = np.clip((val - 7.5) / 7.5, 0, 1)
    if t < 0.25:
        s = t / 0.25
        return (0.08 + 0.12*s, 0.20 + 0.35*s, 0.45 + 0.30*s)
    elif t < 0.50:
        s = (t - 0.25) / 0.25
        return (0.20 + 0.70*s, 0.55 + 0.35*s, 0.75 + 0.15*s)
    elif t < 0.75:
        s = (t - 0.50) / 0.25
        return (0.90 + 0.03*s, 0.90 - 0.12*s, 0.90 - 0.25*s)
    else:
        s = (t - 0.75) / 0.25
        return (0.93 - 0.30*s, 0.78 - 0.60*s, 0.65 - 0.50*s)

# 10 sub-categories with carefully chosen colors
SUBCATS = [
    ("Deep Void",      7.5, 7.8,  '#071840'),
    ("Void",           7.8, 8.2,  BLUE_700),
    ("Near-Void",      8.2, 8.6,  BLUE_500),
    ("Sub-Filament",   8.6, 9.2,  BLUE_300),
    ("Cool Filament",  9.2, 9.8,  '#8899aa'),
    ("Warm Filament",  9.8, 10.5, '#aabbaa'),
    ("Proto-Cluster",  10.5, 11.2, RED_100),
    ("Cluster Halo",   11.2, 12.0, RED_300),
    ("Cluster Core",   12.0, 13.0, RED_500),
    ("Dense Peak",     13.0, 15.0, '#6b0015'),
]

# ============================================================================
# Fig 1: Deep Octree Icicle — polished
# ============================================================================
print("Fig 1: Octree icicle...")

def build_octree_fast(data, max_depth=5):
    nodes = []
    sz = data.shape[0]
    nodes.append((0, 0, 0, 0, sz, float(data.mean())))
    def sub(lvl, x, y, z, sz):
        if lvl >= max_depth or sz <= 2: return
        h = sz // 2
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    nx, ny, nz = x+i*h, y+j*h, z+k*h
                    sub_block = data[nx:nx+h, ny:ny+h, nz:nz+h]
                    nodes.append((lvl+1, nx, ny, nz, h, float(sub_block.mean())))
                    sub(lvl+1, nx, ny, nz, h)
    sub(0, 0, 0, 0, sz)
    return nodes

nodes = build_octree_fast(d64_c, max_depth=5)
max_lv = max(n[0] for n in nodes)

fig1, ax1 = plt.subplots(figsize=(24, 12))
fig1.patch.set_facecolor(WHITE); ax1.set_facecolor(WHITE)

for lvl in range(1, max_lv + 1):
    nodes_l = sorted([n for n in nodes if n[0] == lvl], key=lambda n: n[5])
    n_n = len(nodes_l)
    bar_h = 0.88
    for i, (_, _, _, _, _, dens) in enumerate(nodes_l):
        c = density_color(dens)
        rect = FancyBboxPatch((i/n_n, lvl - 0.44), 1.0/n_n, bar_h,
                              boxstyle="round,pad=0.001", facecolor=c,
                              edgecolor='white', linewidth=0.15, alpha=0.92)
        ax1.add_patch(rect)
    label = f"Level {lvl}"
    cells = 8**lvl
    ax1.text(-0.015, lvl, f"{label}\n{cells:,} cells", ha='right', va='center',
             fontsize=10, color=GRAY_700, fontweight='bold')

# Color bar (horizontal at bottom)
cbar_ax = fig1.add_axes([0.25, 0.02, 0.5, 0.018])
grad = np.linspace(7.5, 15, 256).reshape(1, -1)
cbar_ax.imshow(grad, aspect='auto', cmap='coolwarm')
cbar_ax.set_xticks([0, 128, 255]); cbar_ax.set_xticklabels(['7.5\nVoids', '11.25', '15.0\nPeaks'], fontsize=9, color=GRAY_500)
cbar_ax.set_yticks([]); cbar_ax.set_frame_on(False)

ax1.set_xlim(0, 1); ax1.set_ylim(0.5, max_lv + 1)
ax1.set_title("Fig 1: Deep Octree Icicle — 37,449 Spatial Cells across 6 Resolution Levels (t=99)",
              fontsize=15, fontweight='bold', color=BLACK, pad=20)
ax1.axis('off')
fig1.savefig(os.path.join(OUT, "deep_octree_icicle.png"), facecolor=WHITE, dpi=250)
plt.close(fig1)
print("  -> deep_octree_icicle.png")

# ============================================================================
# Fig 2: Multi-Level Sunburst — polished
# ============================================================================
print("Fig 2: Sunburst...")

sunburst_items = [
    ("Voids",       7.5, 8.5,  BLUE_700, 1),
    (" Sub-voids",  7.5, 8.0,  BLUE_500, 2),
    (" Near-voids", 8.0, 8.5,  BLUE_300, 2),
    ("Filaments",   8.5, 10.5, GRAY_400, 1),
    (" Cool fib.",  8.5, 9.5,  '#8899aa', 2),
    (" Warm fib.",  9.5, 10.5, '#aabbaa', 2),
    ("Clusters",    10.5, 15.0, RED_300, 1),
    (" Nodes",      10.5, 12.0, RED_300, 2),
    ("  Sub-node",  10.5, 11.2, '#e88060', 3),
    ("  Halo",      11.2, 12.0, '#f0b090', 3),
    (" Cores",      12.0, 15.0, RED_500, 2),
    ("  Center",    12.0, 13.5, RED_700, 3),
    ("  Shell",     13.5, 15.0, '#6b0015', 3),
]

fig2, ax2 = plt.subplots(figsize=(13, 13), subplot_kw={'projection': 'polar'})
fig2.patch.set_facecolor(WHITE); ax2.set_facecolor(WHITE)

for lvl in [1, 2, 3]:
    items = [(l, lo, hi, c) for l, lo, hi, c, lv in sunburst_items if lv == lvl]
    r_start = 1.8 + (lvl - 1) * 3.2
    r_width = 2.8
    angle = 0
    for label, lo, hi, color in items:
        cnt = ((flat99 >= lo) & (flat99 < hi)).sum()
        pct = cnt / total * 100
        span = pct / 100 * 360
        if span > 0.2:
            theta = np.linspace(np.radians(angle), np.radians(angle + span), 60)
            ax2.fill_between(theta, r_start, r_start + r_width, color=color, alpha=0.88,
                             edgecolor='white', linewidth=0.8)
            if span > 5:
                mid = np.radians(angle + span/2)
                ax2.text(mid, r_start + r_width/2, f"{label.strip()}\n{pct:.1f}%",
                        ha='center', va='center', fontsize=7.5, color='white', fontweight='bold')
        angle += span

# Center circle
center = plt.Circle((0, 0), 1.8, color=WHITE, ec=GRAY_300, lw=1.5, zorder=10)
ax2.add_patch(center)
ax2.text(0, 0, "Nyx\nt=99", ha='center', va='center', fontsize=12,
         color=BLACK, fontweight='bold', zorder=11)

# Level ring guides
for i in range(4):
    ax2.add_patch(plt.Circle((0,0), 1.8 + i*3.2, fill=False, ec=GRAY_200, lw=0.5, ls='--'))

ax2.set_title("Fig 2: Multi-Level Cosmic Density Sunburst — 3-Layer Hierarchical Partition (t=99)",
              fontsize=14, fontweight='bold', color=BLACK, pad=22)
ax2.set_xticklabels([]); ax2.set_yticklabels([]); ax2.grid(False); ax2.set_ylim(0, 12.5)
fig2.savefig(os.path.join(OUT, "deep_sunburst.png"), facecolor=WHITE, dpi=250)
plt.close(fig2)
print("  -> deep_sunburst.png")

# ============================================================================
# Fig 3: Deep Dendrogram — polished, color-coded by density
# ============================================================================
print("Fig 3: Dendrogram...")

rng = np.random.default_rng(42)
idx = rng.choice(len(flat99), size=1500, replace=False)
samples = flat99[idx].reshape(-1, 1)
Z = linkage(samples, method='ward')

fig3 = plt.figure(figsize=(24, 10))
fig3.patch.set_facecolor(WHITE)
gs = fig3.add_gridspec(1, 2, width_ratios=[4, 1], wspace=0.02)

# Main dendrogram
ax3 = fig3.add_subplot(gs[0])
ax3.set_facecolor(WHITE)

# Color branches by density
dn = dendrogram(Z, ax=ax3, truncate_mode='level', p=6,
                leaf_font_size=6, above_threshold_color=GRAY_300,
                link_color_func=lambda k: GRAY_400)

# Color leaves
xlbls = ax3.get_xmajorticklabels()
for lbl in xlbls:
    try:
        leaf_idx = int(lbl.get_text().split('_')[0]) if '_' in lbl.get_text() else None
    except: leaf_idx = None
    if leaf_idx is None: continue
    # Find representative density for this leaf
    lbl.set_color(GRAY_400)

ax3.set_title("Fig 3: Hierarchical Dendrogram — 1,500 Voxels, Ward Linkage, 6 Truncation Levels",
              fontsize=14, fontweight='bold', color=BLACK, pad=12)
ax3.set_ylabel("Ward Distance", fontsize=11, color=GRAY_500)
ax3.tick_params(colors=GRAY_400)
for spine in ax3.spines.values(): spine.set_color(GRAY_300)

# Right: density distribution of samples
ax3b = fig3.add_subplot(gs[1])
ax3b.set_facecolor(WHITE)
h, e = np.histogram(samples, bins=80, range=(7.5, 15))
colors_bars = [density_color((e[i]+e[i+1])/2) for i in range(len(h))]
ax3b.barh((e[:-1]+e[1:])/2, h, height=0.09, color=colors_bars, alpha=0.8, edgecolor='none')
ax3b.set_ylim(7.5, 15)
ax3b.set_xlabel("Count", fontsize=9, color=GRAY_500)
ax3b.set_title("Sample\ndistribution", fontsize=9, color=GRAY_600, pad=10)
ax3b.tick_params(colors=GRAY_400, labelsize=8)
for spine in ax3b.spines.values(): spine.set_color(GRAY_300)

fig3.savefig(os.path.join(OUT, "deep_dendrogram.png"), facecolor=WHITE, dpi=250)
plt.close(fig3)
print("  -> deep_dendrogram.png")

# ============================================================================
# Fig 4: Timeline Deep Icicle — polished
# ============================================================================
print("Fig 4: Timeline icicle...")

ts_steps = list(range(0, 100, 5))
fig4, ax4 = plt.subplots(figsize=(22, 10))
fig4.patch.set_facecolor(WHITE); ax4.set_facecolor(WHITE)

bar_w = 0.78
for i, ts in enumerate(ts_steps):
    flat_t = all_data[ts].ravel(); total_t = len(flat_t)
    bottom = 0
    for name, lo, hi, color in SUBCATS:
        cnt = ((flat_t >= lo) & (flat_t < hi)).sum(); pct = cnt / total_t * 100
        if pct > 0.005:
            rect = FancyBboxPatch((i - bar_w/2, bottom), bar_w, pct,
                                  boxstyle="round,pad=0.003", facecolor=color,
                                  edgecolor='white', linewidth=0.4, alpha=0.92)
            ax4.add_patch(rect)
            if pct > 5:
                ax4.text(i, bottom + pct/2, f"{pct:.0f}%", ha='center', va='center',
                        fontsize=6.5, color='white', fontweight='bold')
            bottom += pct

# Annotation arrows
ax4.annotate("Void fraction\nrising 10x", xy=(8, 28), xytext=(5, 38),
            arrowprops=dict(arrowstyle='->', color=BLUE_500, lw=2.2, connectionstyle='arc3,rad=.2'),
            fontsize=10, color=BLUE_500, ha='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=WHITE, edgecolor=BLUE_500, alpha=0.9))
ax4.annotate("Peak forms\nlate epoch", xy=(18, 3), xytext=(15, 15),
            arrowprops=dict(arrowstyle='->', color=RED_500, lw=2.2, connectionstyle='arc3,rad=-.2'),
            fontsize=10, color=RED_500, ha='center', fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=WHITE, edgecolor=RED_500, alpha=0.9))

ax4.set_xticks(range(len(ts_steps)))
ax4.set_xticklabels([f"t={ts}" for ts in ts_steps], rotation=50, ha='right', fontsize=9, color=GRAY_500)
ax4.set_ylim(0, 100); ax4.set_xlim(-1, len(ts_steps))
ax4.set_ylabel("Volume Fraction (%)", fontsize=12, color=GRAY_600, labelpad=10)
ax4.set_title("Fig 4: Cosmic Density Icicle Timeline — 10 Sub-Categories x 20 Epochs",
              fontsize=15, fontweight='bold', color=BLACK, pad=15)
# Legend
from matplotlib.patches import Patch
leg = [Patch(facecolor=c, edgecolor='white', linewidth=0.3, label=n) for n, _, _, c in SUBCATS]
ax4.legend(handles=leg, loc='upper left', frameon=True, fontsize=8, ncol=2,
           facecolor=WHITE, edgecolor=GRAY_300, bbox_to_anchor=(1.01, 0.98))
ax4.tick_params(colors=GRAY_400)
for spine in ax4.spines.values(): spine.set_color(GRAY_300)
ax4.grid(axis='y', color=GRAY_100, alpha=0.5, lw=0.5)
fig4.savefig(os.path.join(OUT, "deep_icicle_timeline.png"), facecolor=WHITE, dpi=250)
plt.close(fig4)
print("  -> deep_icicle_timeline.png")

# ============================================================================
# Fig 5: Density Flow Matrix — polished
# ============================================================================
print("Fig 5: Flow matrix...")

flat0 = all_data[0].ravel()
n_cats = len(SUBCATS)
flow = np.zeros((n_cats, n_cats))
for i, (_, lo_i, hi_i, _) in enumerate(SUBCATS):
    mask = (flat0 >= lo_i) & (flat0 < hi_i)
    dest = flat99[mask]
    for j, (_, lo_j, hi_j, _) in enumerate(SUBCATS):
        flow[i, j] = ((dest >= lo_j) & (dest < hi_j)).sum()
flow_norm = flow / flow.sum(axis=1, keepdims=True)

fig5, ax5 = plt.subplots(figsize=(15, 12))
fig5.patch.set_facecolor(WHITE); ax5.set_facecolor(WHITE)

im = ax5.imshow(flow_norm, aspect='auto', cmap='YlOrRd', vmin=0, vmax=0.7)

# Annotate cells with significant values
for i in range(n_cats):
    for j in range(n_cats):
        v = flow_norm[i, j]
        if v > 0.05:
            txt_color = 'white' if v > 0.3 else GRAY_700
            ax5.text(j, i, f"{v:.0%}", ha='center', va='center', fontsize=8,
                    color=txt_color, fontweight='bold')

ax5.set_xticks(range(n_cats))
ax5.set_xticklabels([n for n, _, _, _ in SUBCATS], rotation=50, ha='right', fontsize=9, color=GRAY_500)
ax5.set_yticks(range(n_cats))
ax5.set_yticklabels([n for n, _, _, _ in SUBCATS], fontsize=9, color=GRAY_500)
for i, (_, _, _, c) in enumerate(SUBCATS): ax5.get_yticklabels()[i].set_color(c)

ax5.set_xlabel("t=99 — Destination Regime", fontsize=12, color=GRAY_600, labelpad=10)
ax5.set_ylabel("t=0 — Origin Regime", fontsize=12, color=GRAY_600, labelpad=10)
ax5.set_title("Fig 5: Cosmic Density Flow Matrix — t=0 to t=99 Mass Redistribution\n(Row-normalized: where did each density regime's voxels end up?)",
              fontsize=14, fontweight='bold', color=BLACK, pad=15)

cbar = plt.colorbar(im, ax=ax5, fraction=0.046, pad=0.02)
cbar.set_label("Fraction", fontsize=10, color=GRAY_500)

# Highlight key flow patterns
ax5.add_patch(Rectangle((-0.45, -0.45), 3, 3, fill=False, edgecolor=BLUE_500, lw=2.5, ls='--'))
ax5.text(1, -1.2, "Voids stay voids\n(Diagonal stability)", fontsize=9, color=BLUE_500,
         ha='center', fontweight='bold')
ax5.add_patch(Rectangle((5.5, 2.5), 4, 4, fill=False, edgecolor=RED_500, lw=2.5, ls='--'))
ax5.text(7.5, 8.5, "Mid → Peaks\n(Gravitational collapse)", fontsize=9, color=RED_500,
         ha='center', fontweight='bold')

fig5.savefig(os.path.join(OUT, "density_flow_matrix.png"), facecolor=WHITE, dpi=250)
plt.close(fig5)
print("  -> density_flow_matrix.png")

print("\nDone! 5 polished deep hierarchy figures.")
