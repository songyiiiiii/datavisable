# Processed Data Documentation

## File Index

| File | Format | Size | Content |
|------|--------|------|---------|
| global_statistics.json/csv | JSON/CSV | 100 records | Per-timestep stats (mean, std, skew, kurt, percentiles, fractions) |
| histogram_matrix.npy | NPY int32 | 100x128 | Density histograms for all time steps |
| histogram_derivative.npy | NPY float32 | 100x128 | Time-derivative of histograms dH/dt |
| histogram_summary.json | JSON | ¡ª | Histogram metadata (edges, peaks per step) |
| category_fractions.csv | CSV | 100x11 | Volume % for 10 density categories per step |
| track_data.npy | NPY float32 | 100x5000 | 5000 tracked voxels across 100 steps |
| track_summary.json | JSON | ¡ª | Tracking statistics |
| subsampled_32.npy | NPY float32 | 100x32x32x32 | 4x subsampled 3D data |
| evolution_summary.json | JSON | ¡ª | Key evolution metrics summary |

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
