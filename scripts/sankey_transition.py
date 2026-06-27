"""
sankey_transition.py — 宇宙结构转变桑基图数据
Void → Sheet → Filament → Node 各步之间的体素迁移
"""
import numpy as np
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

# 快速分类 (密度阈值法, 足够精确)
def classify(data_3d):
    web = np.zeros_like(data_3d, dtype=np.uint8)
    web[data_3d < 8.5] = 0
    web[(data_3d >= 8.5) & (data_3d < 9.7)] = 1
    web[(data_3d >= 9.7) & (data_3d < 11.2)] = 2
    web[data_3d >= 11.2] = 3
    return web

NAMES = ['Void', 'Sheet', 'Filament', 'Node']

step_from, step_to = 0, 99
d0 = classify(load_timestep(step_from)).ravel()
d99 = classify(load_timestep(step_to)).ravel()

# 随机采样 200K 体素加速
rng = np.random.default_rng(42)
idx = rng.choice(len(d0), size=200000, replace=False)
f0, f99 = d0[idx], d99[idx]

matrix = np.zeros((4, 4), dtype=int)
for i in range(4):
    for j in range(4):
        matrix[i, j] = ((f0 == i) & (f99 == j)).sum()

print(f"Transition Matrix t={step_from} → t={step_to}:")
print(f"{'':>10} {'→Void':>8} {'→Sheet':>8} {'→Filament':>8} {'→Node':>8}")
for i in range(4):
    row = '  '.join(f'{matrix[i,j]/matrix[i].sum()*100:6.1f}%' for j in range(4))
    print(f'{NAMES[i]:>10} {row}')

# 转成 ECharts Sankey 格式
sankey = {"nodes": [], "links": []}
for i in range(4):
    sankey["nodes"].append({"name": f"t={step_from} {NAMES[i]}"})
for j in range(4):
    sankey["nodes"].append({"name": f"t={step_to} {NAMES[j]}"})
for i in range(4):
    for j in range(4):
        if matrix[i, j] > 0:
            sankey["links"].append({
                "source": f"t={step_from} {NAMES[i]}",
                "target": f"t={step_to} {NAMES[j]}",
                "value": int(matrix[i, j])
            })

out = os.path.join(OUTPUT_DIR, "frontend_data", "sankey_transition.json")
with open(out, 'w') as f: json.dump(sankey, f, indent=2)
print(f"\nExported -> {out}")
