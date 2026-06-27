"""
phase_portrait.py — 密度-梯度相图 (Phase Portrait)
ln(ρ) vs |∇ρ| — 展示宇宙结构在相空间中的分布
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, sobel
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

STEP = 73
print(f"Phase Portrait — t={STEP}")

data = load_timestep(STEP).astype(np.float64)

s = gaussian_filter(data, sigma=1.0)
gx = sobel(s, axis=2) / 2.0; gy = sobel(s, axis=1) / 2.0; gz = sobel(s, axis=0) / 2.0
grad = np.sqrt(gx**2 + gy**2 + gz**2)

rng = np.random.default_rng(42)
idx = rng.choice(data.size, size=50000, replace=False)
rho = data.ravel()[idx]; g = grad.ravel()[idx]

# ── 新配色 ──
ALICE  = '#DAE8FB'  # 浅冰蓝 背景
THISTLE = '#F2D2FF' # 柔和薰衣草紫 卡片
PEARL  = '#75CBD1'  # 珍珠水蓝 低密度标注
DUSK   = '#3E5BA3'  # 黄昏深蓝 中密度
DEEP   = '#0C0D45'  # 极深海军蓝 文字/边框

# hexbin colormap: pearl → dusk → deep
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list('cosmic', [PEARL, DUSK, DEEP])

fig, ax = plt.subplots(figsize=(10, 8))
fig.patch.set_facecolor('#09080D')
ax.set_facecolor('#0D0B14')

hb = ax.hexbin(rho, g, gridsize=80, bins='log', cmap=cmap, mincnt=1, linewidths=0)

def an(text, xy, c, bg):
    ax.annotate(text, xy=xy, fontsize=10, color=c, ha='center', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor=bg, edgecolor=c, alpha=0.85))

an('Voids\n低密度·低梯度', (8.5, 0.005), PEARL, '#09080D')
an('Filaments\n纤维·中梯度', (9.8, 0.022), PEARL, '#09080D')
an('Cluster Edges\n团簇·高梯度', (12.5, 0.06), PEARL, '#09080D')
an('Peak Cores\n核心·低梯度', (13.5, 0.005), PEARL, '#09080D')

ax.set_xlabel('ln(ρ) 密度', color='#C5C3D8', fontsize=13, fontweight='bold')
ax.set_ylabel('|∇ρ| 梯度幅值', color='#C5C3D8', fontsize=13, fontweight='bold')
ax.set_title(f'Phase Portrait — t={STEP}  |  ρ vs |∇ρ|  |  50K voxels sampled',
             color='white', fontsize=14, pad=12, fontweight='bold')

ax.tick_params(colors='#6B6880')
for spine in ax.spines.values(): spine.set_color('#242233')

cb = fig.colorbar(hb, ax=ax, label='log(count)', pad=0.02)
cb.ax.yaxis.label.set_color('#C5C3D8')
cb.ax.tick_params(colors='#6B6880')

out = os.path.join(OUTPUT_DIR, "phase_portrait")
os.makedirs(out, exist_ok=True)
path = os.path.join(out, f"phase_t{STEP:04d}.png")
fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='#09080D')
plt.close(fig)
print(f"Done -> {path}")
