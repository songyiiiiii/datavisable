"""生成比赛答题卡配图"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR

report_img = os.path.join(OUTPUT_DIR, "report_images")
os.makedirs(report_img, exist_ok=True)

# ── 图1: 5帧演化对比 ──
steps = [10, 30, 50, 70, 90]
fig, axes = plt.subplots(1, 5, figsize=(22, 5))
fig.patch.set_facecolor('white')
for ax, s in zip(axes, steps):
    img_path = os.path.join(OUTPUT_DIR, "volume_final", f"t{s:04d}.png")
    if os.path.exists(img_path):
        img = plt.imread(img_path)
        ax.imshow(img)
    ax.set_title(f't={s:03d}', fontsize=14, fontweight='bold', color='#1E293B')
    ax.axis('off')
fig.suptitle('Cosmic Density Evolution — Five Key Timesteps', fontsize=18, fontweight='bold', y=0.98)
fig.savefig(os.path.join(report_img, "fig1_evolution_5frames.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("fig1 done")

# ── 图2: 直方图 t=0 vs t=99 ──
from data_loader import load_timestep
d0 = load_timestep(0).ravel()
d99 = load_timestep(99).ravel()
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(d0, bins=100, range=(7.5, 14.5), alpha=0.5, color='#2166AC', label='t=0 (Early Uniform)')
ax.hist(d99, bins=100, range=(7.5, 14.5), alpha=0.5, color='#B2182B', label='t=99 (Mature Web)')
ax.set_xlabel('ln(ρ)', fontsize=13); ax.set_ylabel('Voxel Count', fontsize=13)
ax.set_title('Density Distribution: t=0 vs t=99', fontsize=15, fontweight='bold')
ax.legend(fontsize=12); ax.grid(True, alpha=0.3, color='#E2E6EC')
fig.patch.set_facecolor('white')
fig.savefig(os.path.join(report_img, "fig2_histogram_compare.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("fig2 done")

# ── 图3: 统计指标时间序列 ──
import json
with open(os.path.join(os.path.dirname(OUTPUT_DIR), 'processed', 'global_statistics.json')) as f:
    stats = json.load(f)

fig, axes = plt.subplots(2, 2, figsize=(12, 9))
ts = np.arange(100)
axes[0,0].plot(ts, [s['std'] for s in stats], color='#B2182B', lw=2)
axes[0,0].set_title('Std σ (Clumpification)', fontweight='bold'); axes[0,0].grid(True, alpha=0.3)
axes[0,1].plot(ts, [s['mean'] for s in stats], color='#2166AC', lw=2)
axes[0,1].set_title('Mean μ', fontweight='bold'); axes[0,1].grid(True, alpha=0.3)
axes[1,0].plot(ts, [s['void_frac_8.5'] for s in stats], color='#4393C3', lw=2, label='Void% (<8.5)')
axes[1,0].plot(ts, [s['peak_frac_12.0']*100 for s in stats], color='#B2182B', lw=2, label='Peak% (>12.0)×100')
axes[1,0].set_title('Void & Peak Fractions', fontweight='bold'); axes[1,0].legend(); axes[1,0].grid(True, alpha=0.3)
axes[1,1].plot(ts, [s['skewness'] for s in stats], color='#D6604D', lw=2, label='Skew γ₁')
axes[1,1].plot(ts, [s['kurtosis'] for s in stats], color='#4393C3', lw=2, label='Kurt γ₂')
axes[1,1].set_title('Skewness & Kurtosis', fontweight='bold'); axes[1,1].legend(); axes[1,1].grid(True, alpha=0.3)
fig.patch.set_facecolor('white')
fig.savefig(os.path.join(report_img, "fig3_stat_timeline.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("fig3 done")

print(f"\nAll report images -> {report_img}/")
