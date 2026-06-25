# -*- coding: utf-8 -*-
"""
Nyx Cosmic Density — Unified Visual Analytics Dashboard
=========================================================
Single Dash app: Task 1(+5) 3D + TimeWheel | Task 2 Evolution | Task 3 Histogram | Task 4 Brushing
Run: python app.py -> http://127.0.0.1:8051
"""

import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64, os

from config import *
from data_loader import load_timestep

# ============================================================================
# Preload — all 100 steps for TimeWheel + 51-frame Task 1
# ============================================================================
print("Preloading all 100 time steps for TimeWheel...")
ALL_100 = {}
for i in range(N_TIMESTEPS):
    ALL_100[i] = load_timestep(i)
    if (i+1) % 25 == 0: print(f"  {i+1}/100")

# TimeWheel pre-computed data
TW_MEANS = np.array([ALL_100[t].mean() for t in range(N_TIMESTEPS)])
TW_STDS  = np.array([ALL_100[t].std()  for t in range(N_TIMESTEPS)])
TW_MINS  = np.array([ALL_100[t].min()  for t in range(N_TIMESTEPS)])
TW_MAXS  = np.array([ALL_100[t].max()  for t in range(N_TIMESTEPS)])
means_100 = TW_MEANS  # alias for sparklines
stds_100  = TW_STDS   # alias for sparklines

# Pre-compute 10 radial metrics for all steps
_TW_RAW = np.zeros((N_TIMESTEPS, 10))
for t in range(N_TIMESTEPS):
    d = ALL_100[t].ravel()
    _TW_RAW[t] = [
        (d < 8.5).sum() / d.size * 100,  # Void%
        (d > 12.0).sum() / d.size * 100, # Peak%
        np.mean((d-d.mean())**4)/d.std()**4 - 3,  # Kurtosis
        np.mean((d-d.mean())**3)/d.std()**3,       # Skewness
        np.percentile(d,75)-np.percentile(d,25),    # IQR
        d.std(), d.mean(), d.min(), d.max(),        # Std, Mean, Min, Max
        np.percentile(d,99)-np.percentile(d,1),     # Spread
    ]
_TW_VMIN = _TW_RAW.min(axis=0); _TW_VMAX = _TW_RAW.max(axis=0)
_TW_VRNG = _TW_VMAX - _TW_VMIN; _TW_VRNG[_TW_VRNG==0] = 1
TW_NORMED = (_TW_RAW - _TW_VMIN) / _TW_VRNG * 8 + 1  # [1, 9] normalized

# Pre-load 32^3 data for go.Volume real-time rendering
TW_THETA = np.linspace(0, 10 * np.pi, N_TIMESTEPS)
TW_RADIUS = np.linspace(2, 10, N_TIMESTEPS)

# Task 4 data (5 key steps)
T4_STEPS = REPRESENTATIVE_STEPS
SUB4 = {}
HIST4 = {}
for ts in T4_STEPS:
    d = ALL_100[ts][::4, ::4, ::4]
    SUB4[ts] = np.ascontiguousarray(np.transpose(d, (2, 1, 0)))
    h, e = np.histogram(ALL_100[ts].ravel(), bins=128, range=DENSITY_RANGE)
    HIST4[ts] = {"counts": h, "edges": e, "centers": (e[:-1]+e[1:])/2}

print("Ready.\n")

# Task 1 frame steps
T1_STEPS = list(range(100))  # all 100 frames

# Pre-load 32^3 data for go.Volume real-time rendering
VOL_SS = 4  # 128 -> 32
VOL_SIZE = GRID_SIZE // VOL_SS
VOL_DATA = {}
VOL_X = np.arange(0, GRID_SIZE, VOL_SS, dtype=np.float32)
VOL_Y = np.arange(0, GRID_SIZE, VOL_SS, dtype=np.float32)
VOL_Z = np.arange(0, GRID_SIZE, VOL_SS, dtype=np.float32)
for ts in T1_STEPS:
    d = ALL_100[ts][::VOL_SS, ::VOL_SS, ::VOL_SS]
    d_xyz = np.ascontiguousarray(np.transpose(d, (2, 1, 0)))
    VOL_DATA[ts] = d_xyz.flatten(order="C")

# ============================================================================
# Figure builders
# ============================================================================
def fig_task1_image(step):
    """Load pre-rendered PNG frame for given time step."""
    nearest = min(T1_STEPS, key=lambda x: abs(x - step))
    pad = str(nearest).zfill(4)
    path = os.path.join(OUTPUT_DIR, "task1", f"layer_composite_t{pad}.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            enc = base64.b64encode(f.read()).decode()
        return html.Img(src=f"data:image/png;base64,{enc}",
                        style={"width": "100%", "display": "block"})
    return html.Div("Image not found", style={"color": "red", "padding": "40px"})


def fig_t1_volume(step):
    """Multi-layer isosurface via Plotly go.Isosurface (matching PyVista layers)."""
    nearest = min(T1_STEPS, key=lambda x: abs(x - step))
    if nearest not in VOL_DATA:
        nearest = min(VOL_DATA.keys(), key=lambda x: abs(x - nearest))
    values = VOL_DATA[nearest].reshape(VOL_SIZE, VOL_SIZE, VOL_SIZE)

    fig = go.Figure()

    iso_levels = [8.0, 8.6, 9.2, 9.8, 10.5, 11.2, 12.0, 14.0]
    iso_colors = [BLUE_700, BLUE_500, BLUE_300, GRAY_400, RED_100, RED_300, RED_500, RED_700]
    iso_alpha  = [0.06, 0.10, 0.15, 0.22, 0.32, 0.45, 0.58, 0.72]

    for lvl, clr, alpha in zip(iso_levels, iso_colors, iso_alpha):
        fig.add_trace(go.Isosurface(
            x=VOL_X, y=VOL_Y, z=VOL_Z, value=values,
            isomin=lvl, isomax=lvl,
            surface=dict(count=1, fill=0.9),
            caps=dict(x_show=False, y_show=False, z_show=False),
            opacity=alpha,
            colorscale=[[0, clr], [1, clr]],
            showscale=False, hoverinfo="skip",
            lighting=dict(ambient=0.3, diffuse=0.7, specular=0.3, roughness=0.5, fresnel=0.2),
            lightposition=dict(x=300, y=300, z=400),
        ))

    fig.update_layout(
        title=dict(text=f"Task 1: Multi-Layer Isosurface — t={step} (drag to rotate)",
                   font=dict(color=BLACK, size=13)),
        scene=dict(
            xaxis=dict(title="X", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            yaxis=dict(title="Y", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            zaxis=dict(title="Z", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            aspectmode="cube", camera=dict(eye=dict(x=2.2, y=2.2, z=1.8)), bgcolor=WHITE,
        ),
        paper_bgcolor=WHITE, margin=dict(l=0, r=0, t=40, b=0),
        uirevision="task1-volume",
    )
    return fig


def fig_t1_particles(step, brush_range=None):
    """3D particle scatter linked to brush selection."""
    SS = 4
    # Get nearest key step
    ks = REPRESENTATIVE_STEPS
    ns = min(ks, key=lambda x: abs(x - step))
    if ns not in SUB4:
        d = ALL_100[ns][::SS, ::SS, ::SS]
        SUB4[ns] = np.ascontiguousarray(np.transpose(d, (2, 1, 0)))
    d3 = SUB4[ns]
    idx = np.argwhere(np.ones_like(d3, dtype=bool))
    vals = d3.flatten()

    if brush_range is not None:
        mask = (vals >= brush_range[0]) & (vals <= brush_range[1])
        idx = idx[mask]; vals = vals[mask]

    n_total = len(vals)
    if n_total > 5000:
        rng = np.random.default_rng(42)
        si = rng.choice(n_total, size=5000, replace=False)
        idx = idx[si]; vals = vals[si]

    fig = go.Figure()
    if len(vals) > 0:
        # Simple blue-gray-red gradient matching project palette
        colors = []
        for v in vals:
            t = np.clip((v - 7.5) / 7.5, 0, 1)
            if t < 0.3:
                c = (0.13 + 0.7*t, 0.40 + 0.5*t, 0.67 - 0.5*t)
            elif t < 0.5:
                s = (t - 0.3) / 0.2
                c = (0.34 + 0.56*s, 0.55 + 0.35*s, 0.52 + 0.38*s)
            elif t < 0.7:
                s = (t - 0.5) / 0.2
                c = (0.90 + 0.05*s, 0.90 - 0.12*s, 0.90 - 0.22*s)
            else:
                s = (t - 0.7) / 0.3
                c = (0.95 - 0.35*s, 0.78 - 0.68*s, 0.68 - 0.58*s)
            colors.append(f"rgb({int(255*c[0])},{int(255*c[1])},{int(255*c[2])})")
        fig.add_trace(go.Scatter3d(
            x=idx[:, 0] * SS, y=idx[:, 1] * SS, z=idx[:, 2] * SS,
            mode="markers",
            marker=dict(size=3, color=colors, opacity=0.6),
            showlegend=False,
            hovertemplate="(%{x},%{y},%{z})<br>ln(rho)=%{text:.3f}<extra></extra>",
            text=[float(v) for v in vals],
        ))

    title = f"3D Particles — t={step}"
    if brush_range:
        title += f" | [{brush_range[0]:.2f},{brush_range[1]:.2f}] → {n_total:,} vox"
    fig.update_layout(
        title=dict(text=title, font=dict(color=RED_500 if brush_range else BLACK, size=11)),
        scene=dict(
            xaxis=dict(title="X", range=[0, 127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            yaxis=dict(title="Y", range=[0, 127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            zaxis=dict(title="Z", range=[0, 127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            aspectmode="cube", camera=dict(eye=dict(x=2.0, y=2.0, z=1.5)),
        ),
        paper_bgcolor=WHITE, margin=dict(l=0, r=0, t=35, b=0),
        height=330, uirevision="t1-particles",
    )
    return fig
    nearest = min(T1_STEPS, key=lambda x: abs(x - step))
    path = os.path.join(OUTPUT_DIR, "task1", f"layer_composite_t{nearest:04d}.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            enc = base64.b64encode(f.read()).decode()
        return html.Img(src=f"data:image/png;base64,{enc}",
                        style={"width": "100%", "display": "block"})
    return html.Div("Image not found", style={"color": "red", "padding": "40px"})


def fig_t1_histogram(step, brush_range=None):
    """Mini brushable histogram for Panel 1."""
    h, e = np.histogram(ALL_100[step].ravel(), bins=64, range=DENSITY_RANGE)
    ctr = (e[:-1]+e[1:])/2
    clrs = [RED_500 if (brush_range and brush_range[0]<=c<=brush_range[1]) else GRAY_400 for c in ctr]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=ctr, y=h, marker=dict(color=clrs, line_width=0),
                         hovertemplate="ln(rho)=%{x:.3f}<br>count=%{y:,}<extra></extra>",
                         showlegend=False))
    shapes = []
    if brush_range:
        shapes.append(dict(type="rect", x0=brush_range[0], x1=brush_range[1],
                           y0=0, y1=h.max()*1.05, fillcolor=RED_500, opacity=0.12,
                           line_width=1, line_color=RED_500))
    fig.update_layout(
        title=dict(text=f"Density Histogram — t={step} (drag to brush)", font=dict(color=BLACK, size=11)),
        xaxis=dict(title="ln(rho)", range=DENSITY_RANGE, gridcolor=GRAY_200, color=GRAY_500),
        yaxis=dict(title="Count", gridcolor=GRAY_200, color=GRAY_500),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE, dragmode="select", selectdirection="h",
        shapes=shapes, margin=dict(l=40, r=10, t=30, b=30), bargap=0, height=220,
    )
    return fig


def fig_t1_sparklines(step, brush_range=None):
    """Evolution sparklines: sigma + mean trends with current step marker + brush info."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        subplot_titles=("Std sigma (clumpification)", "Mean ln(rho) (void expansion)"),
                        vertical_spacing=0.25)

    ts = np.arange(N_TIMESTEPS)
    fig.add_trace(go.Scatter(x=ts, y=stds_100, mode="lines",
                             line=dict(color=RED_500, width=1.8), name="sigma",
                             hovertemplate="t=%{x}<br>sigma=%{y:.4f}"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[step], y=[stds_100[step]], mode="markers",
                             marker=dict(color=BLUE_500, size=12, line=dict(color=BLACK, width=1.5)),
                             name="current", showlegend=False), row=1, col=1)

    fig.add_trace(go.Scatter(x=ts, y=means_100, mode="lines",
                             line=dict(color=BLUE_500, width=1.8), name="mean",
                             hovertemplate="t=%{x}<br>mean=%{y:.3f}"), row=2, col=1)
    fig.add_trace(go.Scatter(x=[step], y=[means_100[step]], mode="markers",
                             marker=dict(color=RED_500, size=12, line=dict(color=BLACK, width=1.5)),
                             name="current", showlegend=False), row=2, col=1)

    # Brush annotation
    annotation_text = ""
    if brush_range:
        d = ALL_100[step].ravel()
        n = int(((d>=brush_range[0])&(d<=brush_range[1])).sum())
        pct = n/d.size*100
        annotation_text = f"Brush [{brush_range[0]:.2f},{brush_range[1]:.2f}] → {n:,} voxels ({pct:.2f}%)"

    fig.update_layout(
        title=dict(text=annotation_text or "Drag in histogram to brush density range",
                   font=dict(color=RED_500 if brush_range else GRAY_500, size=10)),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        margin=dict(l=45, r=10, t=35, b=25), height=220, showlegend=False,
    )
    fig.update_xaxes(gridcolor=GRAY_200, color=GRAY_400)
    fig.update_yaxes(gridcolor=GRAY_200, color=GRAY_400)
    return fig


def fig_timewheel(step, rotation_deg=0):
    """
    Radial Statistical Evolution View (fig5a_timewheel_full replica).
    Center time axis + peripheral metric axes + chord-like fiber bundles.
    """
    # 10 metrics arranged around circle
    metrics = [
        ("Void Frac %",    0),
        ("Peak Frac %",    1),
        ("Exc.Kurtosis g2",2),
        ("Skewness g1",    3),
        ("IQR",            4),
        ("Std sigma",      5),
        ("Mean ln(rho)",   6),
        ("Min ln(rho)",    7),
        ("Max ln(rho)",    8),
        ("P99-P01 Spread", 9),
    ]
    N = len(metrics)
    rot = np.radians(rotation_deg)

    # Pre-computed normalized metric values
    normed = TW_NORMED  # (100, 10), range [1, 9]

    fig = go.Figure()

    # ── Metric axes (radial spokes) ──
    for i, (name, _) in enumerate(metrics):
        angle = 2 * np.pi * i / N + rot
        # Axis line from center to edge
        fig.add_trace(go.Scatter(
            x=[0, 10 * np.cos(angle)], y=[0, 10 * np.sin(angle)],
            mode="lines",
            line=dict(color=GRAY_400, width=3),
            hoverinfo="skip", showlegend=False,
        ))
        # Label at end
        fig.add_trace(go.Scatter(
            x=[11.5 * np.cos(angle)], y=[11.5 * np.sin(angle)],
            mode="text",
            text=[name],
            textfont=dict(color=BLACK, size=11, family="Arial"),
            hoverinfo="skip", showlegend=False,
        ))
        # Tick marks
        for t_val in [2, 4, 6, 8]:
            fx = t_val * np.cos(angle); fy = t_val * np.sin(angle)
            fig.add_trace(go.Scatter(
                x=[fx-0.05*np.cos(angle+np.pi/2), fx+0.05*np.cos(angle+np.pi/2)],
                y=[fy-0.05*np.sin(angle+np.pi/2), fy+0.05*np.sin(angle+np.pi/2)],
                mode="lines", line=dict(color=GRAY_300, width=0.5),
                hoverinfo="skip", showlegend=False,
            ))

    # ── Fiber bundles: all 100 time steps as semi-transparent lines ──
    for t in range(N_TIMESTEPS):
        color = get_time_color(t)
        alpha_val = 0.28 if t != step else 1.0
        lw = 1.8 if t != step else 4.0
        px, py = [], []
        for i in range(N):
            angle = 2 * np.pi * i / N + rot
            r = normed[t, i]
            px.append(r * np.cos(angle)); py.append(r * np.sin(angle))
        px.append(px[0]); py.append(py[0])  # close polygon
        fig.add_trace(go.Scatter(
            x=px, y=py, mode="lines",
            line=dict(color=color, width=lw),
            opacity=alpha_val,
            hoverinfo="skip", showlegend=False,
        ))

    # ── Central time axis (horizontal) ──
    fig.add_trace(go.Scatter(
        x=[-8, 8], y=[0, 0], mode="lines",
        line=dict(color=GRAY_500, width=3.5),
        hoverinfo="skip", showlegend=False,
    ))
    tick_positions = [0, 25, 50, 75, 99]
    for ts in tick_positions:
        tx = -7 + (ts / 99) * 14
        fig.add_trace(go.Scatter(
            x=[tx], y=[0], mode="markers+text",
            marker=dict(size=5, color=GRAY_500),
            text=[f"t={ts}"], textposition="top center",
            textfont=dict(size=8, color=GRAY_500),
            hoverinfo="skip", showlegend=False,
        ))
    # Current step indicator on time axis
    cx = -7 + (step / 99) * 14
    fig.add_trace(go.Scatter(
        x=[cx], y=[0], mode="markers",
        marker=dict(size=14, color=get_time_color(step), line=dict(color=BLACK, width=2)),
        hoverinfo="skip", showlegend=False,
    ))

    # ── Decagon frame ──
    frame_x, frame_y = [], []
    for i in range(N+1):
        angle = 2 * np.pi * (i % N) / N + rot
        frame_x.append(10 * np.cos(angle)); frame_y.append(10 * np.sin(angle))
    fig.add_trace(go.Scatter(
        x=frame_x, y=frame_y, mode="lines",
        line=dict(color=GRAY_300, width=1.2, dash="dot"),
        hoverinfo="skip", showlegend=False,
    ))

    fig.update_layout(
        title=dict(text=f"Radial Statistical Evolution — t={step} (rot={rotation_deg}°)",
                   font=dict(color=BLACK, size=14)),
        xaxis=dict(visible=False, range=[-13, 13]),
        yaxis=dict(visible=False, range=[-13, 13], scaleanchor="x"),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        margin=dict(l=5, r=5, t=40, b=5),
        height=550,
    )
    return fig


def fig_task4_histogram(step, sel_range=None):
    hc = HIST4[step]
    counts, centers = hc["counts"], hc["centers"]
    colors = [RED_500 if sel_range and sel_range[0]<=c<=sel_range[1] else GRAY_400
              for c in centers]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=centers, y=counts, marker=dict(color=colors, line_width=0),
                         hovertemplate="ln(rho)=%{x:.3f}<br>count=%{y:,}<extra></extra>",
                         showlegend=False))
    shapes = []
    if sel_range:
        shapes.append(dict(type="rect", x0=sel_range[0], x1=sel_range[1],
                           y0=0, y1=counts.max()*1.05,
                           fillcolor=RED_500, opacity=0.12, line_width=1, line_color=RED_500))
    fig.update_layout(
        title=dict(text=f"Density Histogram — t={step}  (drag to select range)", font=dict(color=BLACK, size=12)),
        xaxis=dict(title="ln(rho)", range=DENSITY_RANGE, gridcolor=GRAY_200, color=GRAY_500),
        yaxis=dict(title="Count", type="log", gridcolor=GRAY_200, color=GRAY_500),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE, dragmode="select", selectdirection="h",
        shapes=shapes, margin=dict(l=45, r=15, t=35, b=35), bargap=0,
    )
    return fig


def fig_task4_scatter(step, sel_range=None, max_pts=6000):
    d3 = SUB4[step]
    if sel_range:
        lo, hi = sel_range
        mask = (d3 >= lo) & (d3 <= hi)
    else:
        mask = np.ones_like(d3, dtype=bool)
    idx_all = np.argwhere(mask)
    vals_all = d3[mask]
    n_total = len(vals_all)
    if n_total == 0:
        return go.Figure(), 0
    if n_total > max_pts:
        rng = np.random.default_rng(42)
        si = rng.choice(n_total, size=max_pts, replace=False)
        idx_all, vals_all = idx_all[si], vals_all[si]
    px, py, pz = idx_all[:,0]*4, idx_all[:,1]*4, idx_all[:,2]*4
    title = f"3D View — t={step}"
    if sel_range:
        title += f" | ln(rho) in [{sel_range[0]:.2f}, {sel_range[1]:.2f}] | {n_total:,} voxels"
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=px, y=py, z=pz, mode="markers",
        marker=dict(size=2.5, color=vals_all,
                    colorscale=[[0,BLUE_700],[0.35,BLUE_300],[0.5,GRAY_400],[0.65,RED_300],[1,RED_500]],
                    cmin=7.5, cmax=15, opacity=0.55,
                    colorbar=dict(title=dict(text="ln(rho)", font=dict(color=GRAY_600)),
                                  tickfont=dict(color=GRAY_500), len=0.55, thickness=12)),
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(color=BLACK, size=12)),
        scene=dict(xaxis=dict(title="X",range=[0,127],gridcolor=GRAY_200,color=GRAY_500,backgroundcolor=WHITE),
                   yaxis=dict(title="Y",range=[0,127],gridcolor=GRAY_200,color=GRAY_500,backgroundcolor=WHITE),
                   zaxis=dict(title="Z",range=[0,127],gridcolor=GRAY_200,color=GRAY_500,backgroundcolor=WHITE),
                   aspectmode="cube", camera=dict(eye=dict(x=2.0,y=2.0,z=1.5))),
        paper_bgcolor=WHITE, margin=dict(l=0,r=0,t=35,b=0), uirevision=True,
    )
    return fig, n_total


# ============================================================================
# App
# ============================================================================
app = dash.Dash(__name__, title="Nyx Visual Analytics", suppress_callback_exceptions=True)
server = app.server

TAB_STYLE = {"padding": "10px 20px", "border": "none", "background": "none",
             "fontSize": "14px", "fontWeight": "600", "cursor": "pointer",
             "color": GRAY_400, "borderBottom": "2px solid transparent"}
TAB_ACTIVE = {**TAB_STYLE, "color": BLUE_500, "borderBottomColor": BLUE_500}

BTN = {"padding":"5px 12px","border":"1px solid "+GRAY_300,"borderRadius":"4px",
       "background":"white","cursor":"pointer","fontSize":"13px","color":GRAY_700}

app.layout = html.Div([
    dcc.Tabs(id="main-tabs", value="task1", children=[
        dcc.Tab(label="Task 1+5 — 3D View + TimeWheel", value="task1", style=TAB_STYLE, selected_style=TAB_ACTIVE),
        dcc.Tab(label="Task 2 — Evolution", value="task2", style=TAB_STYLE, selected_style=TAB_ACTIVE),
        dcc.Tab(label="Task 3 — Histogram Tracking", value="task3", style=TAB_STYLE, selected_style=TAB_ACTIVE),
        dcc.Tab(label="Task 4 — Brushing Dashboard", value="task4", style=TAB_STYLE, selected_style=TAB_ACTIVE),
    ], style={"borderBottom": "1px solid "+GRAY_200, "padding": "0 10px"}),
    html.Div(id="tab-content", style={"padding": "10px"}),
    dcc.Store(id="t1-step", data=0),
    dcc.Store(id="t4-step", data=99),
    dcc.Store(id="t4-range", data=None),
], style={"backgroundColor": WHITE, "minHeight": "100vh", "fontFamily": "Arial,sans-serif"})


# ============================================================================
# Tab switching
# ============================================================================
@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def switch_tab(tab):
    if tab == "task1": return layout_task1_merged()
    elif tab == "task2": return layout_static_figs("task2", "Task 2 — Cosmic Density Evolution Analysis", [
        ("fig2a_stats_dashboard.png", "Fig 2a: Four-panel statistical evolution dashboard."),
        ("fig2b_violin_evolution.png", "Fig 2b: Violin plot — density distribution at 5-step intervals."),
        ("fig2c_histogram_compare.png", "Fig 2c: t=0 vs t=99 histogram overlay."),
        ("fig2d_joint_dist.png", "Fig 2d: Hexbin joint distribution of voxel densities."),
        ("fig2e_clumpification.png", "Fig 2e: Clumpification quantification metrics."),
    ], summary=(
        "Over 100 time steps, sigma increased +15.4%, IQR grew +16.7%, "
        "P99-P01 spread widened +15.1%. Voids deepen, peaks intensify — "
        "quantifying irreversible clumpification driven by dark matter gravity."
    ))
    elif tab == "task3": return layout_static_figs("task3", "Task 3 — Histogram Temporal Tracking", [
        ("fig3a_heatmap.png", "Fig 3a: Density distribution evolution heatmap across 100 steps."),
        ("fig3b_peak_width.png", "Fig 3b: Distribution peak and FWHM tracking (+14.3% width growth)."),
        ("fig3c_fractions.png", "Fig 3c: Void/peak volume fractions (void fraction grew 10x)."),
        ("fig3d_derivative.png", "Fig 3d: Temporal derivative — mass transfer to both tails."),
        ("fig3e_ridge.png", "Fig 3e: Ridge plot of 11 key time steps."),
    ], summary=(
        "Void fraction (ln<8.5) grew from 0.31% to 2.99%. "
        "Mode shifted 9.404->9.229. FWHM +14.3%. "
        "Systematic mass transfer from mid-densities toward both tails."
    ))
    elif tab == "task4": return layout_task4()
    return html.Div()


# ============================================================================
# Layout — Task 1+5 merged: 3D render + TimeWheel, shared slider
# ============================================================================
def layout_task1_merged():
    return html.Div([
        html.Div([
            html.H1("Nyx Cosmic Density – Integrated Visual Explorer",
                    style={"color": BLACK, "fontSize": "20px", "margin": "5px 0 2px"}),
            html.P("3D Model + TimeWheel + Brush Histogram + Sparklines – one slider drives all",
                   style={"color": GRAY_500, "fontSize": "13px", "margin": "0 0 8px"}),
        ], style={"textAlign": "center"}),

        # Main grid: 3D render CENTERED, supporting panels around it
        html.Div([
            # Left-top: TimeWheel – radial statistical context
            html.Div([
                dcc.Graph(id="t1-timewheel", figure=fig_timewheel(0),
                          config={"displaylogo": False}, style={"height": "100%", "width": "100%"}),
            ], style={"gridArea": "tw", "minHeight": "0", "minWidth": "0"}),

            # CENTER: 3D rendered model – main visualization (spans both rows)
            html.Div([
                html.Div(id="t1-image-wrap", children=fig_task1_image(0),
                         style={"border": "1px solid " + GRAY_200, "borderRadius": "4px",
                                "overflow": "hidden", "height": "100%", "display": "flex",
                                "alignItems": "center", "justifyContent": "center"}),
            ], style={"gridArea": "render", "minHeight": "0", "minWidth": "0"}),

            # Right-top: Sparklines – temporal evolution trends
            html.Div([
                dcc.Graph(id="t1-sparklines", config={"displaylogo": False},
                          style={"height": "100%", "width": "100%"}),
            ], style={"gridArea": "spark", "minHeight": "0", "minWidth": "0"}),

            # Bottom-left: Brush Histogram – density distribution
            html.Div([
                dcc.Graph(id="t1-histogram",
                          config={"displaylogo": False,
                                  "modeBarButtonsToAdd": ["select2d"]},
                          style={"height": "100%", "width": "100%"}),
            ], style={"gridArea": "hist", "minHeight": "0", "minWidth": "0"}),

            # Bottom-right: 3D Particles – linked brush selection view
            html.Div([
                dcc.Graph(id="t1-particles", config={"displaylogo": False},
                          style={"height": "100%", "width": "100%"}),
            ], style={"gridArea": "parts", "minHeight": "0", "minWidth": "0"}),
        ], style={
            "display": "grid",
            "gridTemplateAreas": """
                "tw    render spark"
                "hist  render parts"
            """,
            "gridTemplateColumns": "1.2fr 1.9fr 1.2fr",
            "gridTemplateRows": "1fr 1fr",
            "maxWidth": "1440px",
            "margin": "0 auto",
            "gap": "8px",
            "height": "calc(100vh - 205px)",
            "minHeight": "480px",
            "padding": "0 4px",
        }),

        # Rotation slider
        html.Div([
            html.Span("TimeWheel Rotation: ", style={"color": GRAY_500, "fontSize": "12px"}),
            dcc.Slider(id="t1-rotation", min=0, max=360, value=0, step=5,
                       marks={0: "0°", 90: "90°", 180: "180°", 270: "270°", 360: "360°"},
                       tooltip={"placement": "bottom"}),
        ], style={"maxWidth": "1440px", "margin": "2px auto 0", "display": "flex",
                  "gap": "10px", "alignItems": "center", "padding": "0 4px"}),

        # Shared time slider
        html.Div([
            html.Button("|<< 0", id="t1-bt0", n_clicks=0, style=BTN),
            html.Button("<", id="t1-prev", n_clicks=0, style=BTN),
            html.Button("Play", id="t1-play", n_clicks=0,
                        style={**BTN, "background": BLUE_500, "color": "white",
                               "borderColor": BLUE_500, "fontWeight": "600"}),
            html.Button(">", id="t1-next", n_clicks=0, style=BTN),
            html.Button("99 >>|", id="t1-bt99", n_clicks=0, style=BTN),
            html.Span("t = 0", id="t1-step-label",
                      style={"fontSize": "24px", "fontWeight": "700",
                             "color": BLUE_700, "marginLeft": "12px", "minWidth": "60px"}),
            dcc.Slider(id="t1-slider", min=0, max=99, value=0, step=1,
                       marks={0: "0", 25: "25", 50: "50", 75: "75", 99: "99"},
                       tooltip={"placement": "bottom"}),
        ], style={"maxWidth": "1440px", "margin": "4px auto 0", "display": "flex",
                  "gap": "6px", "alignItems": "center", "padding": "0 4px"}),

        html.P("Space = Play/Pause | Arrow keys = Step | Drag in histogram to brush density range",
               style={"textAlign": "center", "color": GRAY_400,
                      "fontSize": "11px", "marginTop": "2px"}),

        dcc.Store(id="t1-brush", data=None),
        dcc.Interval(id="t1-timer", interval=160, disabled=True),
    ])



def layout_static_figs(folder, title, figs, summary=None):
    cards = []
    for fname, caption in figs:
        path = os.path.join(OUTPUT_DIR, folder, fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                enc = base64.b64encode(f.read()).decode()
            cards.append(html.Div([
                html.Img(src=f"data:image/png;base64,{enc}", style={"width":"100%","display":"block"}),
                html.Div(caption, style={"padding":"10px 14px","fontSize":"13px","color":GRAY_600,
                         "borderTop":"1px solid "+GRAY_200,"lineHeight":"1.6"}),
            ], style={"border":"1px solid "+GRAY_200,"borderRadius":"6px","overflow":"hidden",
                      "marginBottom":"16px","background":"white"}))
    summary_block = None
    if summary:
        summary_block = html.Div(summary, style={
            "maxWidth":"1100px","margin":"0 auto 16px","padding":"14px 18px",
            "fontSize":"14px","color":GRAY_700,"lineHeight":"1.8",
            "background":GRAY_100,"borderRadius":"6px","borderLeft":"4px solid "+BLUE_500})
    return html.Div([
        html.H2(title, style={"color":BLACK,"fontSize":"20px","textAlign":"center","margin":"8px 0 12px","fontWeight":"700"}),
        summary_block if summary_block else None,
        html.Div(cards, style={"maxWidth":"1100px","margin":"0 auto"}),
    ])


def layout_task4():
    return html.Div([
        html.H2("Phase-Space Brushing Linked-View Dashboard",
                style={"color":BLACK,"fontSize":"20px","textAlign":"center","margin":"8px 0 2px","fontWeight":"700"}),
        html.P("Select a density range in the histogram -> 3D view shows matching voxels",
               style={"color":GRAY_500,"fontSize":"13px","textAlign":"center","margin":"0 0 8px"}),
        html.Div(
            "Brushing the top 1% reveals cluster nodes; bottom 5% reveals voids. "
            "At t=0, high-density voxels are scattered; by t=99, gravitational collapse organized them into compact filamentary nodes.",
            style={"maxWidth":"1100px","margin":"0 auto 12px","padding":"14px 18px",
                   "fontSize":"14px","color":GRAY_700,"lineHeight":"1.8",
                   "background":GRAY_100,"borderRadius":"6px","borderLeft":"4px solid "+RED_500}),
        html.Div([
            html.Label("Time Step:", style={"fontWeight":"600","color":GRAY_600,"marginRight":"8px"}),
            html.Button("t=0", id="t4-bt0", n_clicks=0, style=btn_style(BLUE_700)),
            html.Button("t=25", id="t4-bt25", n_clicks=0, style=btn_style(BLUE_300)),
            html.Button("t=50", id="t4-bt50", n_clicks=0, style=btn_style(GRAY_500)),
            html.Button("t=75", id="t4-bt75", n_clicks=0, style=btn_style(RED_300)),
            html.Button("t=99", id="t4-bt99", n_clicks=0, style=btn_style(RED_500)),
            html.Span("t = 99", id="t4-step-indicator",
                      style={"marginLeft":"12px","fontSize":"18px","fontWeight":"700","color":RED_500}),
        ], style={"display":"flex","alignItems":"center","gap":"5px","padding":"6px 15px","borderBottom":"1px solid "+GRAY_200}),
        html.Div([
            html.Div([
                dcc.Graph(id="t4-histogram", config={"displaylogo":False,"modeBarButtonsToAdd":["select2d"]},
                          style={"height":"42vh"}),
                html.Div(id="t4-stats", style={"padding":"6px 12px","fontSize":"12px","color":GRAY_600,
                          "background":GRAY_100,"borderRadius":"4px","margin":"3px 8px"}),
            ], style={"width":"42%","padding":"4px"}),
            html.Div([
                dcc.Graph(id="t4-scatter", config={"displaylogo":False}, style={"height":"68vh"}),
            ], style={"width":"58%","padding":"4px"}),
        ], style={"display":"flex"}),
    ])


def btn_style(color):
    return {"padding":"4px 12px","border":"1px solid "+GRAY_300,"borderRadius":"4px",
            "background":"white","color":color,"fontWeight":"600","cursor":"pointer","fontSize":"13px"}


# ============================================================================
# Task 1+5 callback — shared slider drives both 3D image + TimeWheel
# ============================================================================
@app.callback(
    Output("t1-image-wrap", "children"),
    Output("t1-step-label", "children"),
    Output("t1-step-label", "style"),
    Output("t1-slider", "value"),
    Output("t1-step", "data"),
    Output("t1-timewheel", "figure"),
    Output("t1-histogram", "figure"),
    Output("t1-particles", "figure"),
    Output("t1-sparklines", "figure"),
    Output("t1-brush", "data"),
    Input("t1-slider", "value"),
    Input("t1-rotation", "value"),
    Input("t1-histogram", "selectedData"),
    Input("t1-bt0", "n_clicks"), Input("t1-bt99", "n_clicks"),
    Input("t1-prev", "n_clicks"), Input("t1-next", "n_clicks"),
    Input("t1-timer", "n_intervals"),
    State("t1-step", "data"),
    State("t1-brush", "data"),
    prevent_initial_call=False,
)
def t1_update(slider_val, rotation_deg, sel_data, bt0, bt99, prev, nxt, timer_n, cur_step, brush_data):
    trig = ctx.triggered_id if ctx.triggered else ""
    if cur_step is None: cur_step = 0
    if rotation_deg is None: rotation_deg = 0

    step_map = {"t1-bt0": 0, "t1-bt99": 99}
    if trig in step_map: cur_step = step_map[trig]
    elif trig == "t1-prev": cur_step = max(0, cur_step - 1)
    elif trig == "t1-next": cur_step = min(99, cur_step + 1)
    elif trig == "t1-slider": cur_step = slider_val if slider_val is not None else 0
    elif trig == "t1-timer": cur_step = (cur_step + 1) % 100

    if trig == "t1-histogram" and sel_data and "range" in sel_data:
        brush_data = [sel_data["range"]["x"][0], sel_data["range"]["x"][1]]

    style = {"fontSize": "24px", "fontWeight": "700", "color": get_time_color(cur_step),
             "marginLeft": "12px", "minWidth": "60px"}

    vol_fig = fig_task1_image(cur_step)
    tw_fig = fig_timewheel(cur_step, rotation_deg)
    hist_fig = fig_t1_histogram(cur_step, brush_data)
    part_fig = fig_t1_particles(cur_step, brush_data)
    spark_fig = fig_t1_sparklines(cur_step, brush_data)

    return (vol_fig, f"t = {cur_step}", style, cur_step, cur_step,
            tw_fig, hist_fig, part_fig, spark_fig, brush_data)


@app.callback(Output("t1-timer", "disabled"), Input("t1-play", "n_clicks"),
              State("t1-timer", "disabled"), prevent_initial_call=True)
def t1_toggle_play(n, disabled): return not disabled


# ============================================================================
# Task 4 callbacks
# ============================================================================
@app.callback(
    Output("t4-histogram","figure"), Output("t4-scatter","figure"), Output("t4-stats","children"),
    Output("t4-step-indicator","children"), Output("t4-step-indicator","style"), Output("t4-step","data"),
    Input("t4-histogram","selectedData"), Input("t4-bt0","n_clicks"), Input("t4-bt25","n_clicks"),
    Input("t4-bt50","n_clicks"), Input("t4-bt75","n_clicks"), Input("t4-bt99","n_clicks"),
    State("t4-step","data"), prevent_initial_call=False,
)
def t4_update(sel_data, bt0, bt25, bt50, bt75, bt99, cur_step):
    trig = ctx.triggered_id if ctx.triggered else ""
    if cur_step is None: cur_step = 99
    step_map = {"t4-bt0":0,"t4-bt25":25,"t4-bt50":50,"t4-bt75":75,"t4-bt99":99}
    if trig in step_map: cur_step = step_map[trig]; sel_range = None
    elif trig == "t4-histogram" and sel_data and "range" in sel_data:
        sel_range = [sel_data["range"]["x"][0], sel_data["range"]["x"][1]]
    else: sel_range = None
    hist_fig = fig_task4_histogram(cur_step, sel_range)
    scat_fig, n_sel = fig_task4_scatter(cur_step, sel_range)
    total = SUB4[cur_step].size
    if sel_range and n_sel > 0:
        pct = n_sel/total*100
        st = f"Selected: {n_sel:,} voxels ({pct:.2f}%) | [{sel_range[0]:.3f}, {sel_range[1]:.3f}]"
        if pct < 2: st += "  <-- High-density tail = cluster nodes!"
    else: st = "Drag in the histogram to select a density range."
    ind_style = {"marginLeft":"12px","fontSize":"18px","fontWeight":"700","color":get_time_color(cur_step)}
    return hist_fig, scat_fig, st, f"t = {cur_step}", ind_style, cur_step


# ============================================================================
if __name__ == "__main__":
    print("="*60)
    print("Nyx Dashboard: http://127.0.0.1:5002")
    print("  4 tabs: 3D+TimeWheel | Evolution | Histogram | Brushing")
    print("="*60)
    app.run(debug=False, host="127.0.0.1", port=5003)
