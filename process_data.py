# -*- coding: utf-8 -*-
"""
Nyx Data Processing Pipeline — Secondary Data Generation
==========================================================
Processes raw 100-step 128^3 density fields into structured secondary data
for all visualization tasks. Outputs organized CSV/JSON/NPY files.

Run once: python process_data.py
"""

import numpy as np
import json, csv, os, sys
from tqdm import tqdm

sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_all_timesteps

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed")
os.makedirs(OUT, exist_ok=True)

print("=" * 60)
print("Nyx Data Processing Pipeline")
print("=" * 60)

# ============================================================================
# Step 0: Load raw data
# ============================================================================
print("\n[0/8] Loading 100 time steps...")
all_data = load_all_timesteps(verbose=True)

# ============================================================================
# Step 1: Per-timestep global statistics → JSON
# ============================================================================
print("\n[1/8] Computing global statistics...")

stats_list = []
for t in tqdm(range(N_TIMESTEPS), desc="Stats"):
    flat = all_data[t].ravel()
    p = np.percentile(flat, [0.1, 1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9])
    from scipy.stats import skew, kurtosis
    stats_list.append({
        "step": t,
        "min":  float(flat.min()),
        "max":  float(flat.max()),
        "mean": float(flat.mean()),
        "std":  float(flat.std()),
        "median": float(np.median(flat)),
        "skewness": float(skew(flat)),
        "kurtosis": float(kurtosis(flat)),
        "p01": float(p[1]), "p05": float(p[2]), "p10": float(p[3]),
        "p25": float(p[4]), "p50": float(p[5]), "p75": float(p[6]),
        "p90": float(p[7]), "p95": float(p[8]), "p99": float(p[9]),
        "p999": float(p[10]),
        "iqr": float(p[6] - p[4]),
        "spread_99_01": float(p[9] - p[1]),
        "void_frac_8.5": float((flat < 8.5).sum() / flat.size * 100),
        "void_frac_8.0": float((flat < 8.0).sum() / flat.size * 100),
        "peak_frac_12.0": float((flat > 12.0).sum() / flat.size * 100),
        "peak_frac_13.5": float((flat > 13.5).sum() / flat.size * 100),
        "total_voxels": int(flat.size),
    })

with open(os.path.join(OUT, "global_statistics.json"), 'w') as f:
    json.dump(stats_list, f, indent=2)
print("  -> global_statistics.json (%d records)" % len(stats_list))

# Also as CSV
with open(os.path.join(OUT, "global_statistics.csv"), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=stats_list[0].keys())
    w.writeheader(); w.writerows(stats_list)
print("  -> global_statistics.csv")

# ============================================================================
# Step 2: Density histograms (all 100 steps) → NPY + JSON
# ============================================================================
print("\n[2/8] Computing density histograms...")

hist_data = np.zeros((N_TIMESTEPS, HIST_BINS), dtype=np.int32)
for t in tqdm(range(N_TIMESTEPS), desc="Histograms"):
    hist_data[t], edges = np.histogram(all_data[t].ravel(), bins=HIST_BINS, range=DENSITY_RANGE)

np.save(os.path.join(OUT, "histogram_matrix.npy"), hist_data)
np.save(os.path.join(OUT, "histogram_edges.npy"), edges)
np.save(os.path.join(OUT, "histogram_centers.npy"), (edges[:-1] + edges[1:]) / 2)

# Save histogram summary as JSON for quick reference
hist_json = {
    "n_steps": N_TIMESTEPS,
    "n_bins": HIST_BINS,
    "density_range": list(DENSITY_RANGE),
    "bin_centers": ((edges[:-1] + edges[1:]) / 2).tolist(),
    "peak_count_per_step": [int(hist_data[t].max()) for t in range(N_TIMESTEPS)],
    "peak_bin_per_step": [int(np.argmax(hist_data[t])) for t in range(N_TIMESTEPS)],
}
with open(os.path.join(OUT, "histogram_summary.json"), 'w') as f:
    json.dump(hist_json, f, indent=2)
print("  -> histogram_matrix.npy (shape=%s)" % str(hist_data.shape))
print("  -> histogram_summary.json")

# ============================================================================
# Step 3: Density category volume fractions → CSV
# ============================================================================
print("\n[3/8] Computing density category fractions...")

categories = [
    ("deep_void",    7.5, 7.8),
    ("void",         7.8, 8.2),
    ("near_void",    8.2, 8.6),
    ("sub_filament", 8.6, 9.2),
    ("cool_filament",9.2, 9.8),
    ("warm_filament",9.8, 10.5),
    ("proto_cluster",10.5, 11.2),
    ("cluster_halo", 11.2, 12.0),
    ("cluster_core", 12.0, 13.0),
    ("extreme_peak", 13.0, 15.0),
]

with open(os.path.join(OUT, "category_fractions.csv"), 'w', newline='') as f:
    headers = ["step"] + [c[0] for c in categories]
    w = csv.writer(f); w.writerow(headers)
    for t in range(N_TIMESTEPS):
        flat = all_data[t].ravel()
        row = [t]
        for name, lo, hi in categories:
            row.append(round(float(((flat >= lo) & (flat < hi)).sum() / flat.size * 100), 6))
        w.writerow(row)
print("  -> category_fractions.csv (%d rows x %d columns)" % (N_TIMESTEPS, len(categories)+1))

# ============================================================================
# Step 4: Time-derivative of histogram → NPY
# ============================================================================
print("\n[4/8] Computing distribution time derivatives...")

deriv = np.zeros_like(hist_data, dtype=np.float32)
for t in range(1, N_TIMESTEPS - 1):
    deriv[t] = (hist_data[t+1] - hist_data[t-1]) / 2.0
np.save(os.path.join(OUT, "histogram_derivative.npy"), deriv)
print("  -> histogram_derivative.npy")

# ============================================================================
# Step 5: Voxel tracking sample → NPY
# ============================================================================
print("\n[5/8] Sampling voxel tracking data...")

rng = np.random.default_rng(42)
n_track = 5000
track_indices = rng.choice(N_VOXELS, size=n_track, replace=False)
track_data = np.zeros((N_TIMESTEPS, n_track), dtype=np.float32)
for t in tqdm(range(N_TIMESTEPS), desc="Tracking"):
    flat = all_data[t].ravel()
    track_data[t] = flat[track_indices]

np.save(os.path.join(OUT, "track_indices.npy"), track_indices)
np.save(os.path.join(OUT, "track_data.npy"), track_data)

track_summary = {
    "n_tracked": n_track,
    "t0_mean": float(track_data[0].mean()),
    "t99_mean": float(track_data[99].mean()),
    "gained_density_pct": float((track_data[99] > track_data[0]).sum() / n_track * 100),
    "lost_density_pct": float((track_data[99] < track_data[0]).sum() / n_track * 100),
}
with open(os.path.join(OUT, "track_summary.json"), 'w') as f:
    json.dump(track_summary, f, indent=2)
print("  -> track_data.npy (%d voxels x %d steps)" % (n_track, N_TIMESTEPS))

# ============================================================================
# Step 6: Subsampled 3D data for visualization → NPY
# ============================================================================
print("\n[6/8] Creating subsampled datasets...")

# 32^3 for interactive 3D viewer
SS = 4
sub_data = np.zeros((N_TIMESTEPS, GRID_SIZE//SS, GRID_SIZE//SS, GRID_SIZE//SS), dtype=np.float32)
for t in range(N_TIMESTEPS):
    sub_data[t] = all_data[t][::SS, ::SS, ::SS]
np.save(os.path.join(OUT, "subsampled_32.npy"), sub_data)
print("  -> subsampled_32.npy (shape=%s)" % str(sub_data.shape))

# ============================================================================
# Step 7: Evolution summary → JSON
# ============================================================================
print("\n[7/8] Generating evolution summary...")

s0, s99 = stats_list[0], stats_list[99]
evolution_summary = {
    "description": "Evolution metrics from t=0 to t=99",
    "sigma_change_pct": round((s99["std"] / s0["std"] - 1) * 100, 2),
    "iqr_change_pct": round((s99["iqr"] / s0["iqr"] - 1) * 100, 2),
    "spread_change_pct": round((s99["spread_99_01"] / s0["spread_99_01"] - 1) * 100, 2),
    "min_change": round(s99["min"] - s0["min"], 4),
    "max_change": round(s99["max"] - s0["max"], 4),
    "void_frac_8.5_growth": round(s99["void_frac_8.5"] / s0["void_frac_8.5"], 1),
    "skewness_t0": round(s0["skewness"], 4),
    "skewness_t99": round(s99["skewness"], 4),
    "kurtosis_t0": round(s0["kurtosis"], 4),
    "kurtosis_t99": round(s99["kurtosis"], 4),
    "three_phase_model": {
        "phase_I_linear":  "t=0-30:  narrow peak, uniform derivative, initial instability",
        "phase_II_accel":  "t=30-70: peak broadening, tail growth, nonlinear collapse",
        "phase_III_asymp": "t=70-99: broad peak, decelerating derivative, quasi-equilibrium",
    }
}
with open(os.path.join(OUT, "evolution_summary.json"), 'w') as f:
    json.dump(evolution_summary, f, indent=2)
print("  -> evolution_summary.json")

# ============================================================================
# Step 8: Readme for processed data
# ============================================================================
print("\n[8/8] Writing processed data documentation...")

readme = """# Processed Data Documentation

## File Index

| File | Format | Size | Content |
|------|--------|------|---------|
| global_statistics.json/csv | JSON/CSV | 100 records | Per-timestep stats (mean, std, skew, kurt, percentiles, fractions) |
| histogram_matrix.npy | NPY int32 | 100x128 | Density histograms for all time steps |
| histogram_derivative.npy | NPY float32 | 100x128 | Time-derivative of histograms dH/dt |
| histogram_summary.json | JSON | — | Histogram metadata (edges, peaks per step) |
| category_fractions.csv | CSV | 100x11 | Volume % for 10 density categories per step |
| track_data.npy | NPY float32 | 100x5000 | 5000 tracked voxels across 100 steps |
| track_summary.json | JSON | — | Tracking statistics |
| subsampled_32.npy | NPY float32 | 100x32x32x32 | 4x subsampled 3D data |
| evolution_summary.json | JSON | — | Key evolution metrics summary |

## Density Categories

| Category | Range ln(rho) |
|----------|---------------|
| deep_void | 7.5 - 7.8 |
| void | 7.8 - 8.2 |
| near_void | 8.2 - 8.6 |
| sub_filament | 8.6 - 9.2 |
| cool_filament | 9.2 - 9.8 |
| warm_filament | 9.8 - 10.5 |
| proto_cluster | 10.5 - 11.2 |
| cluster_halo | 11.2 - 12.0 |
| cluster_core | 12.0 - 13.0 |
| extreme_peak | 13.0 - 15.0 |

## Usage Example

```python
import numpy as np, json

# Load global statistics
with open('processed/global_statistics.json') as f:
    stats = json.load(f)
sigma_t0 = stats[0]['std']     # 0.4318
sigma_t99 = stats[99]['std']   # 0.4983

# Load histogram matrix
hist = np.load('processed/histogram_matrix.npy')  # (100, 128)
edges = np.load('processed/histogram_edges.npy')  # (129,)

# Load subsampled 3D data for quick preview
sub = np.load('processed/subsampled_32.npy')      # (100, 32, 32, 32)

# Load tracked voxels
track = np.load('processed/track_data.npy')       # (100, 5000)
# track[t, i] = density of voxel i at time t
```
"""
with open(os.path.join(OUT, "README.md"), 'w') as f:
    f.write(readme)
print("  -> README.md")

# ============================================================================
print("\n" + "=" * 60)
print("DONE! All secondary data in: %s" % OUT)
print("=" * 60)
