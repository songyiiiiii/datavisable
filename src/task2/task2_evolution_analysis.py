# -*- coding: utf-8 -*-
"""
Task 2: Cosmic Density Evolution Analysis
==========================================
Statistical analysis + visualization of 100-timestep density evolution.
5 figures, white bg, blue-gray-red palette consistent with Task 1.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.stats import gaussian_kde
from tqdm import tqdm

from config import *
from data_loader import load_all_timesteps, compute_statistics, compute_density_histogram

print("=" * 60)
print("Task 2: Cosmic Density Evolution Analysis")
print("=" * 60)

# ── Load data ──
print("Loading 100 time steps...")
all_data = load_all_timesteps(verbose=True)

# ── Compute stats for all 100 steps ──
print("Computing statistics...")
stats_all = [compute_statistics(all_data[t]) for t in tqdm(range(N_TIMESTEPS))]

means   = np.array([s["mean"]   for s in stats_all])
medians = np.array([s["median"] for s in stats_all])
stds    = np.array([s["std"]    for s in stats_all])
iqrs    = np.array([s["iqr"]    for s in stats_all])
skews   = np.array([s["skewness"] for s in stats_all])
kurts   = np.array([s["kurtosis"] for s in stats_all])
mins    = np.array([s["min"]    for s in stats_all])
maxs    = np.array([s["max"]    for s in stats_all])
p01s    = np.array([s["p01"]    for s in stats_all])
p99s    = np.array([s["p99"]    for s in stats_all])
spreads = np.array([s["spread_99_01"] for s in stats_all])

ts_arr = np.arange(N_TIMESTEPS)

# ============================================================================
# Fig 2a: Statistical Evolution Dashboard (4 panels)
# ============================================================================
print("Fig 2a: Stats dashboard...")
fig2a = plt.figure(figsize=(14, 11))
gs = GridSpec(2, 2, figure=fig2a, hspace=0.32, wspace=0.28)

# (a) Central tendency
ax0 = fig2a.add_subplot(gs[0, 0])
ax0.plot(ts_arr, means, color=BLUE_500, lw=2.2, label="Mean")
ax0.plot(ts_arr, medians, color=RED_500, lw=1.8, ls="--", label="Median")
ax0.fill_between(ts_arr, medians, means, alpha=0.12, color=BLUE_500)
apply_style(ax0, title="(a) Central Tendency", xlabel="Time Step", ylabel="ln(ρ)")
ax0.legend(frameon=True, loc="upper right")

# (b) Dispersion
ax1 = fig2a.add_subplot(gs[0, 1])
ax1.plot(ts_arr, stds, color=RED_500, lw=2.2, label="Std σ")
ax1.plot(ts_arr, iqrs, color=BLUE_500, lw=1.8, ls="--", label="IQR")
ax1.fill_between(ts_arr, stds, alpha=0.12, color=RED_500)
apply_style(ax1, title="(b) Dispersion (Clumpification)", xlabel="Time Step", ylabel="Density units")
ax1.legend(frameon=True, loc="upper left")

# (c) Shape
ax2 = fig2a.add_subplot(gs[1, 0])
ax2.plot(ts_arr, skews, color=RED_300, lw=2.2, label="Skewness γ₁")
ax2.plot(ts_arr, kurts, color=BLUE_300, lw=1.8, ls="--", label="Exc. Kurtosis γ₂")
ax2.axhline(y=0, color=GRAY_300, lw=0.8, ls=":")
ax2.fill_between(ts_arr, 0, skews, alpha=0.10, color=RED_300)
apply_style(ax2, title="(c) Distribution Shape", xlabel="Time Step", ylabel="Statistic")
ax2.legend(frameon=True, loc="upper left")

# (d) Extremes
ax3 = fig2a.add_subplot(gs[1, 1])
ax3.plot(ts_arr, maxs, color=RED_500, lw=2, label="Max")
ax3.plot(ts_arr, p99s, color=RED_300, lw=1.5, ls="--", label="P99")
ax3.plot(ts_arr, mins, color=BLUE_500, lw=2, label="Min")
ax3.plot(ts_arr, p01s, color=BLUE_300, lw=1.5, ls="--", label="P01")
ax3.fill_between(ts_arr, p99s, maxs, alpha=0.12, color=RED_500)
ax3.fill_between(ts_arr, mins, p01s, alpha=0.12, color=BLUE_500)
apply_style(ax3, title="(d) Extreme Values — Bipolarization", xlabel="Time Step", ylabel="ln(ρ)")
ax3.legend(frameon=True, loc="center right", fontsize=8)

fig2a.suptitle("Fig 2a: Cosmic Density Statistical Evolution Dashboard",
               color=BLACK, fontsize=16, fontweight="bold", y=1.01)
fig2a.savefig(os.path.join(OUTPUT_DIR, "fig2a_stats_dashboard.png"), facecolor=WHITE)
print("  -> fig2a_stats_dashboard.png")

# ============================================================================
# Fig 2b: Violin plot
# ============================================================================
print("Fig 2b: Violin plot...")
fig2b, ax2b = plt.subplots(figsize=(16, 7))
violin_steps = list(range(0, N_TIMESTEPS, 5))
violin_data = []
for ts in violin_steps:
    flat = all_data[ts].ravel()
    rng = np.random.default_rng(42)
    flat = rng.choice(flat, size=min(50000, len(flat)), replace=False)
    violin_data.append(flat)

parts = ax2b.violinplot(violin_data, positions=violin_steps, showmeans=True,
                         showmedians=True, widths=4.5)
for i, body in enumerate(parts["bodies"]):
    body.set_facecolor(get_time_color(violin_steps[i]))
    body.set_alpha(0.55)
for pn in ["cmeans", "cmedians", "cmins", "cmaxes", "cbars"]:
    if pn in parts: parts[pn].set_color(GRAY_500); parts[pn].set_linewidth(0.7)

ax2b.plot(violin_steps, [all_data[ts].mean() for ts in violin_steps],
          color=RED_500, lw=1.5, ls="--", alpha=0.7)
apply_style(ax2b, title="Fig 2b: Density Distribution Evolution — Violin Plot (every 5 steps)",
            xlabel="Time Step", ylabel="ln(ρ)")
fig2b.tight_layout()
fig2b.savefig(os.path.join(OUTPUT_DIR, "fig2b_violin_evolution.png"), facecolor=WHITE)
print("  -> fig2b_violin_evolution.png")

# ============================================================================
# Fig 2c: t=0 vs t=99 histogram overlay
# ============================================================================
print("Fig 2c: Histogram overlay...")
fig2c, ax2c = plt.subplots(figsize=(11, 7))
hist0, _, c0 = compute_density_histogram(all_data[0], bins=128, range_=DENSITY_RANGE)
hist99, _, c99 = compute_density_histogram(all_data[99], bins=128, range_=DENSITY_RANGE)
ax2c.fill_between(c0, hist0, alpha=0.55, color=BLUE_500, label="t=0 (Initial)")
ax2c.fill_between(c99, hist99, alpha=0.50, color=RED_500, label="t=99 (Final)")
ax2c.axvspan(7.5, 8.5, alpha=0.06, color=BLUE_500)
ax2c.axvspan(12.0, 15.0, alpha=0.06, color=RED_500)
ax2c.text(8.0, max(hist0.max(), hist99.max())*0.88, "Voids\ndeepen", ha="center",
          fontsize=10, color=BLUE_500, fontweight="bold")
ax2c.text(13.5, max(hist0.max(), hist99.max())*0.88, "Peaks\ngrow", ha="center",
          fontsize=10, color=RED_500, fontweight="bold")
apply_style(ax2c, title="Fig 2c: Density Histogram — t=0 vs t=99",
            xlabel="ln(ρ)", ylabel="Voxel Count")
ax2c.legend(frameon=True)
fig2c.tight_layout()
fig2c.savefig(os.path.join(OUTPUT_DIR, "fig2c_histogram_compare.png"), facecolor=WHITE)
print("  -> fig2c_histogram_compare.png")

# ============================================================================
# Fig 2d: Joint distribution (hexbin)
# ============================================================================
print("Fig 2d: Joint distribution...")
fig2d, ax2d = plt.subplots(figsize=(9, 8))
rng = np.random.default_rng(42)
idx = rng.choice(N_VOXELS, size=20000, replace=False)
f0 = all_data[0].ravel()[idx]
f99 = all_data[99].ravel()[idx]
hb = ax2d.hexbin(f0, f99, gridsize=70, cmap="Reds", mincnt=1, bins="log", alpha=0.85)
lims = [7.3, 15.2]
ax2d.plot(lims, lims, ":", color=GRAY_400, lw=1.2, alpha=0.7)
apply_style(ax2d, title="Fig 2d: Voxel Density Joint Distribution — t=0 vs t=99",
            xlabel="t=0 ln(ρ)", ylabel="t=99 ln(ρ)")
cb = plt.colorbar(hb, ax=ax2d, pad=0.02)
cb.set_label("Voxel count (log)", color=GRAY_600)
fig2d.tight_layout()
fig2d.savefig(os.path.join(OUTPUT_DIR, "fig2d_joint_dist.png"), facecolor=WHITE)
print("  -> fig2d_joint_dist.png")

# ============================================================================
# Fig 2e: Clumpification metric trends
# ============================================================================
print("Fig 2e: Clumpification metrics...")
fig2e, axes = plt.subplots(2, 3, figsize=(16, 10))
metrics = [
    ("Std σ", stds, RED_500),
    ("IQR", iqrs, BLUE_500),
    ("Skewness γ₁", skews, RED_300),
    ("Exc. Kurtosis γ₂", kurts, BLUE_300),
    ("P99−P01 Spread", spreads, RED_500),
    ("Max/Min Ratio", maxs/mins, BLUE_500),
]
for idx, (name, vals, color) in enumerate(metrics):
    ax = axes.flat[idx]
    ax.plot(ts_arr, vals, color=color, lw=2.2)
    ax.fill_between(ts_arr, vals.min(), vals, alpha=0.10, color=color)
    z = np.polyfit(ts_arr, vals, 1)
    ax.plot(ts_arr, np.poly1d(z)(ts_arr), "--", color=GRAY_400, lw=1, alpha=0.5)
    pct = (vals[-1]/vals[0]-1)*100
    ax.text(0.98, 0.90, f"{pct:+.1f}%", transform=ax.transAxes, fontsize=11,
            color=color, fontweight="bold", ha="right")
    apply_style(ax, title=f"({chr(97+idx)}) {name}",
                xlabel="Time Step" if idx>=3 else "", ylabel="")
fig2e.suptitle("Fig 2e: Clumpification Quantification Panel",
               color=BLACK, fontsize=15, fontweight="bold", y=1.01)
fig2e.tight_layout()
fig2e.savefig(os.path.join(OUTPUT_DIR, "fig2e_clumpification.png"), facecolor=WHITE)
print("  -> fig2e_clumpification.png")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 60)
print("Task 2 Summary")
print("=" * 60)
print(f"  σ:     {stds[0]:.4f} -> {stds[-1]:.4f} (+{(stds[-1]/stds[0]-1)*100:.1f}%)")
print(f"  IQR:   {iqrs[0]:.4f} -> {iqrs[-1]:.4f} (+{(iqrs[-1]/iqrs[0]-1)*100:.1f}%)")
print(f"  Min:   {mins[0]:.3f} -> {mins[-1]:.3f}")
print(f"  Max:   {maxs[0]:.3f} -> {maxs[-1]:.3f}")
print(f"  Skew:  {skews[0]:.3f} -> {skews[-1]:.3f}")
print(f"  Spread:{spreads[0]:.3f} -> {spreads[-1]:.3f} (+{(spreads[-1]/spreads[0]-1)*100:.1f}%)")
print("\nDone!")
