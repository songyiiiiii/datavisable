"""生成比赛配图 — RWB 配色: 转移矩阵 + 成分堆叠面积 + 疏密直方图"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import matplotlib.patches as mpatches
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR

report_img = os.path.join(OUTPUT_DIR, "report_images")
os.makedirs(report_img, exist_ok=True)

# RWB 配色
BLUE  = '#2166AC'
RED   = '#B2182B'
WHITE = '#FFFFFF'
LBLUE = '#92C5DE'
LRED  = '#F4A582'
GRAY  = '#E2E6EC'

# ═══════════════════════════════════════════════════════
# 图 A: 状态转移矩阵 t=0→99
# ═══════════════════════════════════════════════════════
LABELS = ['Void', 'Sheet', 'Filament', 'Node']
# 真实转移数据 (来自 sankey_transition)
MATRIX = [
    [74.8, 24.9,  0.3,  0.0],
    [ 3.8, 88.3,  7.9,  0.0],
    [ 0.2, 48.0, 51.0,  0.8],
    [ 0.0,  2.8, 64.2, 33.0],
]

fig, ax = plt.subplots(figsize=(8, 7))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# 自定义 RWB heatmap
for i in range(4):
    for j in range(4):
        v = MATRIX[i][j] / 100
        # RWB: 低=蓝, 中=白, 高=红
        if v < 0.5:
            color = (BLUE if v < 0.01 else
                     (0.13+(0.5-v/0.5)*0.87, 0.40+(0.5-v/0.5)*0.60, 0.67+(0.5-v/0.5)*0.33))
        else:
            color = (1.0-(1.0-v)/0.5*0.3, 1.0-(1.0-v)/0.5, 1.0-(1.0-v)/0.5)
        # 简化: 用 matplotlib colormap
        pass
        rect = FancyBboxPatch((j, 3-i), 0.9, 0.9, boxstyle="round,pad=0.02",
                              facecolor=plt.cm.RdBu_r(v), edgecolor='white', linewidth=2)
        ax.add_patch(rect)
        c = 'white' if v > 0.6 else '#1E293B'
        ax.text(j+0.45, 3-i+0.45, f'{MATRIX[i][j]}%', ha='center', va='center',
                fontsize=15, fontweight='bold', color=c, fontfamily='monospace')

ax.set_xlim(0, 4); ax.set_ylim(0, 4)
ax.set_xticks([0.45, 1.45, 2.45, 3.45]); ax.set_xticklabels(LABELS, fontsize=14, fontweight='bold')
ax.set_yticks([0.45, 1.45, 2.45, 3.45]); ax.set_yticklabels(LABELS[::-1], fontsize=14, fontweight='bold')
ax.set_title('State Transition Matrix: t=0 → t=99', fontsize=16, fontweight='bold', pad=15)
ax.text(2, -0.6, '→  Target Structure', ha='center', fontsize=12, color='#64748B')
ax.text(-1.2, 2, 'Source  Structure  ←', ha='center', fontsize=12, color='#64748B', rotation=90)
ax.axis('equal')
fig.savefig(os.path.join(report_img, "figA_transition_matrix.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("figA done")

# ═══════════════════════════════════════════════════════
# 图 B: 密度成分演化堆叠面积图
# ═══════════════════════════════════════════════════════
cat_path = os.path.join(os.path.dirname(OUTPUT_DIR), 'processed', 'category_fractions.csv')
cats = np.zeros((100, 10))
with open(cat_path) as f:
    reader = csv.reader(f); next(reader)
    for row in reader:
        t = int(row[0])
        cats[t] = [float(v) for v in row[1:]]

# 10类→4类: void(0:3) sheet(3:6) filament(6:8) node(8:10)
void  = cats[:,0:3].sum(axis=1)
sheet = cats[:,3:6].sum(axis=1)
fila  = cats[:,6:8].sum(axis=1)
node  = cats[:,8:10].sum(axis=1)

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white'); ax.set_facecolor('white')
ts = np.arange(100)
ax.fill_between(ts, 0, void, color='#2166AC', alpha=0.85, label='Void (空洞)')
ax.fill_between(ts, void, void+sheet, color='#92C5DE', alpha=0.85, label='Sheet (薄片)')
ax.fill_between(ts, void+sheet, void+sheet+fila, color='#F4A582', alpha=0.85, label='Filament (纤维)')
ax.fill_between(ts, void+sheet+fila, void+sheet+fila+node, color='#B2182B', alpha=0.85, label='Node (节点)')
ax.set_xlabel('Time Step t', fontsize=13); ax.set_ylabel('Volume Fraction %', fontsize=13)
ax.set_title('Density Structure Composition Evolution (100 Steps)', fontsize=15, fontweight='bold')
ax.legend(fontsize=11, loc='upper left'); ax.set_ylim(0, 100)
ax.grid(True, alpha=0.3, color='#E2E6EC')
fig.savefig(os.path.join(report_img, "figB_composition.png"), dpi=150, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("figB done")

# ═══════════════════════════════════════════════════════
# 图 C: 疏密直方图 (t=0 vs t=99) — 红白蓝对比版
# ═══════════════════════════════════════════════════════
# 已生成 fig2_histogram_compare.png, 确认存在
if os.path.exists(os.path.join(report_img, "fig2_histogram_compare.png")):
    print("figC already exists as fig2_histogram_compare.png")

print(f"\nDone -> {report_img}/")
