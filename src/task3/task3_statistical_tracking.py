# -*- coding: utf-8 -*-
"""
Task 3: Density Log-Histogram Temporal Tracking
================================================
Build log-density histograms for all 100 time steps.
Quantify and track the global density distribution shift over time.
5 figures, white bg, blue-red palette.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from tqdm import tqdm

from config import *
from data_loader import load_all_timesteps, compute_statistics, compute_density_histogram

print("=" * 60)
print("Task 3: Density Log-Histogram Temporal Tracking")
print("=" * 60)

# ── Load ──
print("Loading...")
all_data = load_all_timesteps(verbose=True)

# ── Compute histograms for all 100 steps ──
BINS = HIST_BINS
RANGE = DENSITY_RANGE
print("Computing histograms...")
hist_matrix = np.zeros((N_TIMESTEPS, BINS))
stats_all = []
for t in tqdm(range(N_TIMESTEPS)):
    h, edges, centers = compute_density_histogram(all_data[t], bins=BINS, range_=RANGE)
    hist_matrix[t] = h
    stats_all.append(compute_statistics(all_data[t]))

bin_centers = (edges[:-1] + edges[1:]) / 2
ts_arr = np.arange(N_TIMESTEPS)

# Extract key metrics
means   = np.array([s["mean"] for s in stats_all])
stds    = np.array([s["std"]  for s in stats_all])
skews   = np.array([s["skewness"] for s in stats_all])
p01s    = np.array([s["p01"] for s in stats_all])
p05s    = np.array([s["p05"] for s in stats_all])
p95s    = np.array([s["p95"] for s in stats_all])
p99s    = np.array([s["p99"] for s in stats_all])
mins    = np.array([s["min"] for s in stats_all])
maxs    = np.array([s["max"] for s in stats_all])

# ============================================================================
# Fig 3a: Density Evolution Heatmap
# ============================================================================
print("Fig 3a: Evolution heatmap...")
fig3a, ax3a = plt.subplots(figsize=(13, 6.5))
hist_log = np.log10(hist_matrix + 1)
im = ax3a.pcolormesh(bin_centers, ts_arr, hist_log, cmap="RdBu_r",
                      shading="auto", rasterized=True)

# Annotate representative steps
for ts in REPRESENTATIVE_STEPS:
    ax3a.axhline(y=ts, color=get_time_color(ts), lw=1.2, ls="--", alpha=0.6)

ax3a.annotate("Narrow peak\n(uniform)", xy=(9.45, 5), fontsize=9, color=BLUE_700,
              ha="center", fontweight="bold",
              bbox=dict(boxstyle="round", facecolor="white", edgecolor=BLUE_500, alpha=0.85))
ax3a.annotate("Broad peak\n+ tails\n(clumpy)", xy=(9.25, 93), fontsize=9, color=RED_500,
              ha="center", fontweight="bold",
              bbox=dict(boxstyle="round", facecolor="white", edgecolor=RED_500, alpha=0.85))

cb = plt.colorbar(im, ax=ax3a, pad=0.015)
cb.set_label("log₁₀(count + 1)", color=GRAY_600)
apply_style(ax3a, title="Fig 3a: Density Distribution Evolution Heatmap (100 steps)",
            xlabel="ln(ρ)", ylabel="Time Step")
fig3a.tight_layout()
fig3a.savefig(os.path.join(OUTPUT_DIR, "fig3a_heatmap.png"), facecolor=WHITE)
print("  -> fig3a_heatmap.png")

# ============================================================================
# Fig 3b: Distribution Peak & Width Tracking
# ============================================================================
print("Fig 3b: Peak & width tracking...")
# Find mode (histogram bin with max count) for each step
modes = np.array([bin_centers[np.argmax(hist_matrix[t])] for t in range(N_TIMESTEPS)])
# FWHM approximation: find bins where hist > max/2
fwhm = np.zeros(N_TIMESTEPS)
for t in range(N_TIMESTEPS):
    half_max = hist_matrix[t].max() / 2
    above = np.where(hist_matrix[t] >= half_max)[0]
    if len(above) >= 2:
        fwhm[t] = bin_centers[above[-1]] - bin_centers[above[0]]
    else:
        fwhm[t] = np.nan

fig3b, (axb1, axb2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axb1.plot(ts_arr, modes, color=BLUE_500, lw=2.5, label="Mode (peak location)")
axb1.plot(ts_arr, means, color=RED_500, lw=2, ls="--", label="Mean")
axb1.fill_between(ts_arr, means, modes, alpha=0.10, color=BLUE_500)
axb1.annotate(f"Mode shift: {modes[0]:.3f} → {modes[-1]:.3f}", xy=(N_TIMESTEPS-1, modes[-1]),
              fontsize=10, color=BLUE_500, fontweight="bold", ha="right", va="bottom")
apply_style(axb1, title="(a) Distribution Peak Location", ylabel="ln(ρ)")
axb1.legend(frameon=True, loc="upper right")

axb2.plot(ts_arr, fwhm, color=RED_500, lw=2.5, label="FWHM")
axb2.plot(ts_arr, stds, color=BLUE_500, lw=2, ls="--", label="Std σ")
axb2.fill_between(ts_arr, stds, fwhm, alpha=0.10, color=RED_500)
axb2.annotate(f"FWHM: {fwhm[1]:.3f} → {fwhm[-1]:.3f}", xy=(N_TIMESTEPS-1, fwhm[-1]),
              fontsize=10, color=RED_500, fontweight="bold", ha="right", va="bottom")
apply_style(axb2, title="(b) Distribution Width", xlabel="Time Step", ylabel="Width in ln(ρ)")
axb2.legend(frameon=True, loc="upper left")

fig3b.suptitle("Fig 3b: Distribution Peak Location & Width Evolution", color=BLACK,
               fontsize=14, fontweight="bold")
fig3b.tight_layout()
fig3b.savefig(os.path.join(OUTPUT_DIR, "fig3b_peak_width.png"), facecolor=WHITE)
print("  -> fig3b_peak_width.png")

# ============================================================================
# Fig 3c: Void & Peak Fraction Evolution
# ============================================================================
print("Fig 3c: Void/peak fractions...")
# Use ABSOLUTE density thresholds, not percentiles!
VOID_THRESH = 8.5   # ln(rho) below this = void
PEAK_THRESH = 12.0  # ln(rho) above this = peak

void_frac = np.array([(all_data[t] < VOID_THRESH).sum() / N_VOXELS * 100 for t in range(N_TIMESTEPS)])
peak_frac = np.array([(all_data[t] > PEAK_THRESH).sum() / N_VOXELS * 100 for t in range(N_TIMESTEPS)])
deep_void   = np.array([(all_data[t] < 8.0).sum() / N_VOXELS * 100 for t in range(N_TIMESTEPS)])
dense_peak  = np.array([(all_data[t] > 13.5).sum() / N_VOXELS * 100 for t in range(N_TIMESTEPS)])

fig3c, (axc1, axc2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

axc1.plot(ts_arr, void_frac, color=BLUE_500, lw=2.5, label=f"ln(rho) < {VOID_THRESH} (voids)")
axc1.plot(ts_arr, deep_void, color=BLUE_300, lw=2, ls="--", label=f"ln(rho) < 8.0 (deep voids)")
axc1.fill_between(ts_arr, void_frac, alpha=0.12, color=BLUE_500)
apply_style(axc1, title="(a) Void Fraction Evolution", ylabel="Volume Fraction (%)")
axc1.legend(frameon=True, loc="upper left")

axc2.plot(ts_arr, peak_frac, color=RED_500, lw=2.5, label=f"ln(rho) > {PEAK_THRESH} (peaks)")
axc2.plot(ts_arr, dense_peak, color=RED_300, lw=2, ls="--", label=f"ln(rho) > 13.5 (dense peaks)")
axc2.fill_between(ts_arr, peak_frac, alpha=0.12, color=RED_500)
apply_style(axc2, title="(b) Peak Fraction Evolution", xlabel="Time Step", ylabel="Volume Fraction (%)")
axc2.legend(frameon=True, loc="upper left")

fig3c.suptitle("Fig 3c: Void & Peak Volume Fraction Evolution", color=BLACK,
               fontsize=14, fontweight="bold")
fig3c.tight_layout()
fig3c.savefig(os.path.join(OUTPUT_DIR, "fig3c_fractions.png"), facecolor=WHITE)
print("  -> fig3c_fractions.png")

# ============================================================================
# Fig 3d: Temporal Derivative — Distribution Change Rate
# ============================================================================
print("Fig 3d: Temporal derivative...")
# How fast does each histogram bin change? Use central differences
deriv = np.zeros_like(hist_matrix)
for t in range(1, N_TIMESTEPS - 1):
    deriv[t] = (hist_matrix[t + 1] - hist_matrix[t - 1]) / 2.0

fig3d, ax3d = plt.subplots(figsize=(13, 6.5))
im3d = ax3d.pcolormesh(bin_centers, ts_arr, deriv, cmap="RdBu_r",
                        shading="auto", rasterized=True, vmin=-3000, vmax=3000)
ax3d.axhline(y=50, color=GRAY_600, lw=0.8, ls=":")
cb3d = plt.colorbar(im3d, ax=ax3d, pad=0.015)
cb3d.set_label("d(count)/dt", color=GRAY_600)
apply_style(ax3d, title="Fig 3d: Distribution Change Rate — d(histogram)/dt",
            xlabel="ln(ρ)", ylabel="Time Step")
ax3d.annotate("Voids growing\n(blue)", xy=(8.1, 70), fontsize=9, color=BLUE_700,
              fontweight="bold", ha="center",
              bbox=dict(boxstyle="round", facecolor="white", edgecolor=BLUE_500, alpha=0.85))
ax3d.annotate("Peaks growing\n(red)", xy=(13.0, 70), fontsize=9, color=RED_500,
              fontweight="bold", ha="center",
              bbox=dict(boxstyle="round", facecolor="white", edgecolor=RED_500, alpha=0.85))
ax3d.annotate("Mid depleting\n(mass transfer)", xy=(10.5, 70), fontsize=9, color=GRAY_600,
              fontweight="bold", ha="center",
              bbox=dict(boxstyle="round", facecolor="white", edgecolor=GRAY_400, alpha=0.85))
fig3d.tight_layout()
fig3d.savefig(os.path.join(OUTPUT_DIR, "fig3d_derivative.png"), facecolor=WHITE)
print("  -> fig3d_derivative.png")

# ============================================================================
# Fig 3e: Ridge plot — stacked histograms
# ============================================================================
print("Fig 3e: Ridge plot...")
ridge_steps = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 99]
fig3e, ax3e = plt.subplots(figsize=(12, 9))
y_offset = 0
offsets = []
max_h = max(hist_matrix[ts].max() for ts in ridge_steps)

for i, ts in enumerate(ridge_steps):
    h = hist_matrix[ts]
    color = get_time_color(ts)
    alpha_val = 0.9 if ts in [0, 99] else 0.45
    lw_val = 2.5 if ts in [0, 99] else 1.0
    ax3e.plot(bin_centers, h + y_offset, color=color, lw=lw_val, alpha=alpha_val)
    if ts in [0, 50, 99]:
        ax3e.text(RANGE[0] - 0.08, y_offset + max_h * 0.3, f"t={ts}", color=color,
                  fontsize=10, fontweight="bold", ha="right", va="center")
    offsets.append(y_offset)
    y_offset += max_h * 1.15

ax3e.set_ylim(-max_h * 0.1, y_offset)
apply_style(ax3e, title="Fig 3e: Density Histogram Ridge Plot — Distribution Evolution",
            xlabel="ln(ρ)", ylabel="")
ax3e.set_yticks([])
fig3e.tight_layout()
fig3e.savefig(os.path.join(OUTPUT_DIR, "fig3e_ridge.png"), facecolor=WHITE)
print("  -> fig3e_ridge.png")

# ============================================================================
print("\n" + "=" * 60)
print("Task 3 Summary")
print("=" * 60)
print(f"  Mode shift:        {modes[0]:.3f} -> {modes[-1]:.3f}  ({modes[-1]-modes[0]:+.3f})")
print(f"  FWHM growth:       {fwhm[1]:.3f} -> {fwhm[-1]:.3f}  (+{(fwhm[-1]/fwhm[1]-1)*100:.1f}%)")
print(f"  Void frac ln<8.5:  {void_frac[0]:.2f}% -> {void_frac[-1]:.2f}%  (+{void_frac[-1]-void_frac[0]:.2f} pp)")
print(f"  Peak frac ln>12:   {peak_frac[0]:.2f}% -> {peak_frac[-1]:.2f}%  (+{peak_frac[-1]-peak_frac[0]:.2f} pp)")
print(f"  Deep void ln<8.0:  {deep_void[0]:.3f}% -> {deep_void[-1]:.3f}%  (+{deep_void[-1]-deep_void[0]:.3f} pp)")
print(f"  Dense peak ln>13.5:{dense_peak[0]:.3f}% -> {dense_peak[-1]:.3f}%  (+{dense_peak[-1]-dense_peak[0]:.3f} pp)")
print("\nDone!")
