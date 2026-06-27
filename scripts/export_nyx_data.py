"""
export_nyx_data.py — 将真实 Nyx 模拟数据导出为前端 JSON
==========================================================
读取 100 个 .dat 文件 + processed/ 二级数据，生成前端所需的 JSON。

用法：
  python export_nyx_data.py

输出 (写入 output/frontend_data/):
  timeline.json       — 100 步全量统计 (mean, std, skew, kurt, voidPct, peakPct, 分类占比)
  histogram_t073.json — 单步密度直方图 (bins, edges, centers, counts)
  t0_t99_radar.json   — t=0 和 t=99 的 6 指标雷达数据
"""

import numpy as np
import json, csv, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE, HIST_BINS
from data_loader import load_timestep, load_all_timesteps

OUT = os.path.join(OUTPUT_DIR, "frontend_data")
os.makedirs(OUT, exist_ok=True)

print("=" * 60)
print("Nyx → Frontend JSON Exporter")
print("=" * 60)

# ============================================================================
# 1. 加载全局统计 (已有 processed 数据)
# ============================================================================
print("\n[1/4] Loading global statistics...")
stats_path = os.path.join(os.path.dirname(OUTPUT_DIR), "processed", "global_statistics.json")
with open(stats_path) as f:
    all_stats = json.load(f)

cat_path = os.path.join(os.path.dirname(OUTPUT_DIR), "processed", "category_fractions.csv")
cat_data = np.zeros((100, 10))
with open(cat_path) as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        t = int(row[0])
        cat_data[t] = [float(v) for v in row[1:]]

# ============================================================================
# 2. 生成 timeline.json
# ============================================================================
print("[2/4] Generating timeline.json...")
timeline = []
for step, s in enumerate(all_stats):
    # 10 分类 → 4 分类
    void_frac  = cat_data[step, 0:3].sum()   # deep_void + void + near_void
    sheet_frac = cat_data[step, 3:6].sum()   # sub_filament + cool_filament + warm_filament
    fila_frac  = cat_data[step, 6:8].sum()   # proto_cluster + cluster_halo
    node_frac  = cat_data[step, 8:10].sum()  # cluster_core + extreme_peak

    timeline.append({
        "t": step,
        "mean":     round(s["mean"], 6),
        "std":      round(s["std"], 6),
        "skew":     round(s["skewness"], 6),
        "kurt":     round(s["kurtosis"], 6),
        "voidPct":  round(s["void_frac_8.5"], 6),
        "peakPct":  round(s["peak_frac_12.0"], 6),
        "voidFrac":  round(float(void_frac), 4),
        "sheetFrac": round(float(sheet_frac), 4),
        "filaFrac":  round(float(fila_frac), 4),
        "nodeFrac":  round(float(node_frac), 4),
    })

with open(os.path.join(OUT, "timeline.json"), "w") as f:
    json.dump(timeline, f, indent=2)
print(f"  → {os.path.join(OUT, 'timeline.json')} ({len(timeline)} records)")

# ============================================================================
# 3. 生成 histogram_t073.json
# ============================================================================
print("[3/4] Generating histogram_t073.json...")
step = 73
data = load_timestep(step)
flat = data.ravel()
hist_counts, hist_edges = np.histogram(flat, bins=HIST_BINS, range=DENSITY_RANGE)
hist_centers = ((hist_edges[:-1] + hist_edges[1:]) / 2).tolist()

histogram = {
    "step": step,
    "bins": HIST_BINS,
    "range": list(DENSITY_RANGE),
    "edges": hist_edges.tolist(),
    "centers": [round(c, 4) for c in hist_centers],
    "counts": hist_counts.tolist(),
    "mean": float(flat.mean()),
    "std": float(flat.std()),
}

with open(os.path.join(OUT, "histogram_t073.json"), "w") as f:
    json.dump(histogram, f, indent=2)
print(f"  → {os.path.join(OUT, 'histogram_t073.json')}")

# ============================================================================
# 4. 生成 t0_t99_radar.json
# ============================================================================
print("[4/4] Generating t0_t99_radar.json...")
s0 = all_stats[0]
s99 = all_stats[99]

radar = {
    "indicators": [
        {"name": "Mean",   "max": 10.5},
        {"name": "Std",    "max": 0.6},
        {"name": "Skew",   "max": 1.0},
        {"name": "Kurt",   "max": 2.2},
        {"name": "Peak%",  "max": 0.2},
        {"name": "Void%",  "max": 4.0},
    ],
    "t0": [
        round(s0["mean"], 6),
        round(s0["std"] * 10, 6),     # 缩放到 0-0.6
        round(s0["skewness"], 6),
        round(s0["kurtosis"] / 2, 6),  # 缩放到 0-1.1
        round(s0["peak_frac_12.0"] * 100, 6),
        round(s0["void_frac_8.5"], 6),
    ],
    "t99": [
        round(s99["mean"], 6),
        round(s99["std"] * 10, 6),
        round(s99["skewness"], 6),
        round(s99["kurtosis"] / 2, 6),
        round(s99["peak_frac_12.0"] * 100, 6),
        round(s99["void_frac_8.5"], 6),
    ],
}

with open(os.path.join(OUT, "t0_t99_radar.json"), "w") as f:
    json.dump(radar, f, indent=2)
print(f"  → {os.path.join(OUT, 't0_t99_radar.json')}")

# ============================================================================
print("\n[DONE] Copy output/frontend_data/*.json to your React app's public/data/")
print(f"   Output: {OUT}")
