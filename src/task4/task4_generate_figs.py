# -*- coding: utf-8 -*-
"""Generate Task 4 static figures — brushing linked-view demonstration."""
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sys
sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_timestep

print("Task 4: Generating static figures...")
SS = 4

def load_sub(ts):
    d = load_timestep(ts)[::SS, ::SS, ::SS]
    return np.ascontiguousarray(np.transpose(d, (2, 1, 0)))

def mk_scatter(d_xyz, mask, max_pts=6000, cmap="RdBu_r", cmin=7.5, cmax=15.0):
    """Build Scatter3d trace for voxels matching mask."""
    idx = np.argwhere(mask)
    vals = d_xyz[mask]
    if len(idx) > max_pts:
        rng = np.random.default_rng(42)
        si = rng.choice(len(idx), size=max_pts, replace=False)
        idx, vals = idx[si], vals[si]
    return go.Scatter3d(
        x=idx[:,0]*SS, y=idx[:,1]*SS, z=idx[:,2]*SS, mode="markers",
        marker=dict(size=2.5, color=vals, colorscale=cmap, cmin=cmin, cmax=cmax,
                    opacity=0.55, colorbar=dict(
                        title=dict(text="ln(rho)", font=dict(color=GRAY_600)),
                        tickfont=dict(color=GRAY_500), len=0.55, thickness=12)),
        showlegend=False,
    )

def scene3d():
    return dict(xaxis=dict(range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
                yaxis=dict(range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
                zaxis=dict(range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
                aspectmode="cube", camera=dict(eye=dict(x=2.0,y=2.0,z=1.5)))

# ── Load data ──
d99 = load_sub(99)
d0 = load_sub(0)
flat99 = d99.ravel()
hist99, edges = np.histogram(flat99, bins=128, range=DENSITY_RANGE)
centers = (edges[:-1]+edges[1:])/2
p99, p95, p75, p25, p05, p01 = np.percentile(flat99, [99,95,75,25,5,1])

# ============================================================================
# Fig 4a: Full view
# ============================================================================
print("Fig 4a...")
fig = make_subplots(1,2, column_widths=[0.38,0.62],
                    specs=[[{"type":"xy"},{"type":"scene"}]],
                    subplot_titles=("Histogram","3D — All Voxels"))
fig.add_trace(go.Bar(x=centers, y=hist99, marker_color=GRAY_400, showlegend=False), 1,1)
fig.add_trace(mk_scatter(d99, np.ones_like(d99,dtype=bool)), 1,2)
fig.update_layout(title=dict(text="Fig 4a: Full View — All Voxels (t=99)", font=dict(color=BLACK,size=14)),
                  paper_bgcolor=WHITE, height=480, scene=scene3d())
fig.write_image(os.path.join(OUTPUT_DIR,"fig4a_full.png"), width=1400, height=480)

# ============================================================================
# Fig 4b: Top 1% — cluster nodes
# ============================================================================
print("Fig 4b...")
colors = [RED_500 if c>=p99 else GRAY_300 for c in centers]
fig = make_subplots(1,2, column_widths=[0.38,0.62],
                    specs=[[{"type":"xy"},{"type":"scene"}]],
                    subplot_titles=("Histogram — Top 1%","3D — Cluster Nodes"))
fig.add_trace(go.Bar(x=centers, y=hist99, marker_color=colors, showlegend=False), 1,1)
fig.add_trace(mk_scatter(d99, d99>=p99, cmap="Reds", cmin=p99, cmax=15.0), 1,2)
fig.update_layout(title=dict(text=f"Fig 4b: Brushing Top 1% (ln(rho) > {p99:.2f}) — Cosmic Web Nodes", font=dict(color=BLACK,size=14)),
                  paper_bgcolor=WHITE, height=480, scene=scene3d())
fig.write_image(os.path.join(OUTPUT_DIR,"fig4b_top1pct.png"), width=1400, height=480)

# ============================================================================
# Fig 4c: Bottom 5% — voids
# ============================================================================
print("Fig 4c...")
colors = [BLUE_500 if c<=p05 else GRAY_300 for c in centers]
fig = make_subplots(1,2, column_widths=[0.38,0.62],
                    specs=[[{"type":"xy"},{"type":"scene"}]],
                    subplot_titles=("Histogram — Bottom 5%","3D — Voids"))
fig.add_trace(go.Bar(x=centers, y=hist99, marker_color=colors, showlegend=False), 1,1)
fig.add_trace(mk_scatter(d99, d99<=p05, cmap="Blues", cmin=7.5, cmax=p05), 1,2)
fig.update_layout(title=dict(text=f"Fig 4c: Brushing Bottom 5% (ln(rho) < {p05:.2f}) — Cosmic Voids", font=dict(color=BLACK,size=14)),
                  paper_bgcolor=WHITE, height=480, scene=scene3d())
fig.write_image(os.path.join(OUTPUT_DIR,"fig4c_bottom5pct.png"), width=1400, height=480)

# ============================================================================
# Fig 4d: Middle 50% — filaments
# ============================================================================
print("Fig 4d...")
colors = [GRAY_600 if p25<=c<=p75 else GRAY_300 for c in centers]
fig = make_subplots(1,2, column_widths=[0.38,0.62],
                    specs=[[{"type":"xy"},{"type":"scene"}]],
                    subplot_titles=("Histogram — Middle 50%","3D — Filamentary Web"))
fig.add_trace(go.Bar(x=centers, y=hist99, marker_color=colors, showlegend=False), 1,1)
fig.add_trace(mk_scatter(d99, (d99>=p25)&(d99<=p75), cmap="Greys", cmin=p25, cmax=p75), 1,2)
fig.update_layout(title=dict(text="Fig 4d: Brushing IQR — Filamentary Cosmic Web Structure", font=dict(color=BLACK,size=14)),
                  paper_bgcolor=WHITE, height=480, scene=scene3d())
fig.write_image(os.path.join(OUTPUT_DIR,"fig4d_mid_filaments.png"), width=1400, height=480)

# ============================================================================
# Fig 4e: t=0 vs t=99 top 1% comparison
# ============================================================================
print("Fig 4e...")
flat0 = d0.ravel()
hist0, _ = np.histogram(flat0, bins=128, range=DENSITY_RANGE)
p99_0 = np.percentile(flat0, 99)
c0_colors = [RED_500 if c>=p99_0 else GRAY_300 for c in centers]
c99_colors = [RED_500 if c>=p99 else GRAY_300 for c in centers]

fig = make_subplots(2,2, column_widths=[0.5,0.5],
                    specs=[[{"type":"xy"},{"type":"scene"}],[{"type":"xy"},{"type":"scene"}]],
                    subplot_titles=("t=0 Histogram","t=0 Top 1%","t=99 Histogram","t=99 Top 1%"))
fig.add_trace(go.Bar(x=centers, y=hist0, marker_color=c0_colors, showlegend=False), 1,1)
fig.add_trace(mk_scatter(d0, d0>=p99_0, cmap="Reds", cmin=p99_0, cmax=15.0), 1,2)
fig.add_trace(go.Bar(x=centers, y=hist99, marker_color=c99_colors, showlegend=False), 2,1)
fig.add_trace(mk_scatter(d99, d99>=p99, cmap="Reds", cmin=p99, cmax=15.0), 2,2)
fig.update_layout(title=dict(text="Fig 4e: Brushing Comparison — t=0 vs t=99 (Top 1%)", font=dict(color=BLACK,size=14)),
                  paper_bgcolor=WHITE, height=700,
                  scene=scene3d(), scene2=scene3d())
fig.write_image(os.path.join(OUTPUT_DIR,"fig4e_comparison.png"), width=1400, height=700)

print("Done! 5 figures generated.")
