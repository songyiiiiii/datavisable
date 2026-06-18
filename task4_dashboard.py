# -*- coding: utf-8 -*-
"""
Task 4: Phase-Space Interactive Brushing Linked-View Dashboard
===============================================================
Dash app: histogram brush selection -> 3D scatter spatial view.
verify statistical tail -> cosmic web node correspondence.
"""

import numpy as np
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import *
from data_loader import load_timestep

print("=" * 60)
print("Task 4: Phase-Space Brushing Dashboard")
print("=" * 60)

# ── Preload 5 key time steps (full 128^3) ──
print("Preloading...")
DATA = {}
for ts in REPRESENTATIVE_STEPS:
    DATA[ts] = load_timestep(ts)
    print(f"  t={ts} loaded")

# Pre-compute histograms
HIST = {}
for ts in REPRESENTATIVE_STEPS:
    flat = DATA[ts].ravel()
    h, edges = np.histogram(flat, bins=128, range=DENSITY_RANGE)
    HIST[ts] = {"counts": h, "edges": edges, "centers": (edges[:-1]+edges[1:])/2}

# Subsampled coordinates for 3D (pre-compute XYZ grid once)
SS = 4  # subsample factor: 128/4 = 32^3 = 32,768 points
sub_size = GRID_SIZE // SS
X_sub = np.arange(0, GRID_SIZE, SS, dtype=np.float32)
Y_sub = np.arange(0, GRID_SIZE, SS, dtype=np.float32)
Z_sub = np.arange(0, GRID_SIZE, SS, dtype=np.float32)

# Pre-compute subsampled data for all 5 steps
SUB = {}
for ts in REPRESENTATIVE_STEPS:
    d = DATA[ts][::SS, ::SS, ::SS]  # (z,y,x) Fortran
    d_xyz = np.ascontiguousarray(np.transpose(d, (2, 1, 0)))  # -> (x,y,z) C-order
    SUB[ts] = d_xyz  # (32, 32, 32)

print("Preloading done.\n")

def btn_style(color):
    return {
        "padding": "5px 16px", "border": "1px solid " + GRAY_300, "borderRadius": "4px",
        "background": "white", "color": color, "fontWeight": "600", "cursor": "pointer",
        "fontSize": "13px",
    }

# ============================================================================
# Dash App
# ============================================================================
app = dash.Dash(__name__, title="Task 4 — Brushing Dashboard")
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("Nyx Phase-Space Brushing Dashboard", style={
            "color": BLACK, "fontWeight": "700", "fontSize": "20px", "margin": "8px 0 0 0"}),
        html.P("Select density range in histogram -> 3D view shows matching voxels",
               style={"color": GRAY_500, "fontSize": "13px", "margin": "0 0 8px 0"}),
    ], style={"textAlign": "center"}),

    # ── Controls row ──
    html.Div([
        html.Label("Time Step:", style={"fontWeight": "600", "color": GRAY_600, "marginRight": "10px"}),
        html.Button("t=0", id="bt0", n_clicks=0, style=btn_style(BLUE_500)),
        html.Button("t=25", id="bt25", n_clicks=0, style=btn_style(BLUE_300)),
        html.Button("t=50", id="bt50", n_clicks=0, style=btn_style(GRAY_500)),
        html.Button("t=75", id="bt75", n_clicks=0, style=btn_style(RED_300)),
        html.Button("t=99", id="bt99", n_clicks=0, style=btn_style(RED_500)),
        html.Span(id="step-indicator", children="t = 99",
                  style={"marginLeft": "15px", "fontSize": "18px", "fontWeight": "700",
                         "color": RED_500}),
    ], style={"display": "flex", "alignItems": "center", "gap": "6px",
              "padding": "8px 20px", "borderBottom": "1px solid " + GRAY_200}),

    # ── Main panels ──
    html.Div([
        # Left: Histogram
        html.Div([
            dcc.Graph(id="histogram", config={"displaylogo": False,
                       "modeBarButtonsToAdd": ["select2d"]},
                       style={"height": "45vh"}),
            html.Div(id="hist-stats", style={"padding": "8px 15px", "fontSize": "13px",
                      "color": GRAY_600, "background": GRAY_100,
                      "borderRadius": "4px", "margin": "5px 10px"}),
        ], style={"width": "42%", "padding": "5px"}),

        # Right: 3D scatter
        html.Div([
            dcc.Graph(id="scatter3d", config={"displaylogo": False},
                       style={"height": "70vh"}),
        ], style={"width": "58%", "padding": "5px"}),
    ], style={"display": "flex"}),

    # Store
    dcc.Store(id="cur-step", data=99),
    dcc.Store(id="sel-range", data=None),
], style={"backgroundColor": WHITE, "minHeight": "100vh", "fontFamily": "Arial, sans-serif"})

# ============================================================================
# Build histogram figure
# ============================================================================
def build_histogram(step, sel_range=None):
    hc = HIST[step]
    counts = hc["counts"]
    centers = hc["centers"]

    # Color bars based on selection
    colors = [GRAY_400] * len(centers)
    if sel_range:
        lo, hi = sel_range
        for i, c in enumerate(centers):
            if lo <= c <= hi:
                colors[i] = RED_500

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=centers, y=counts,
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="ln(rho)=%{x:.3f}<br>count=%{y:,}<extra></extra>",
        name="",
        showlegend=False,
    ))

    # Selection shape if range is set
    shapes = []
    if sel_range:
        lo, hi = sel_range
        shapes.append(dict(
            type="rect", x0=lo, x1=hi, y0=0, y1=counts.max()*1.05,
            fillcolor=RED_500, opacity=0.12, line_width=1, line_color=RED_500,
        ))

    fig.update_layout(
        title=dict(text=f"Density Histogram — t={step} (drag to select range)", font=dict(color=BLACK, size=13)),
        xaxis=dict(title="ln(rho)", range=DENSITY_RANGE, gridcolor=GRAY_200, color=GRAY_500),
        yaxis=dict(title="Voxel Count", type="log", gridcolor=GRAY_200, color=GRAY_500),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        dragmode="select", selectdirection="h",
        shapes=shapes,
        margin=dict(l=50, r=20, t=40, b=40),
        bargap=0,
    )
    return fig


# ============================================================================
# Build 3D scatter figure
# ============================================================================
def build_scatter(step, sel_range=None, max_pts=8000):
    d3 = SUB[step]  # (32, 32, 32) subsampled

    if sel_range:
        lo, hi = sel_range
        mask = (d3 >= lo) & (d3 <= hi)
        indices = np.argwhere(mask)  # (N, 3) -> (x, y, z)
        vals = d3[mask]
        n_total = mask.sum()
    else:
        indices = np.argwhere(np.ones_like(d3, dtype=bool))
        vals = d3.flatten()
        n_total = len(vals)

    if n_total == 0:
        fig = go.Figure()
        fig.update_layout(
            title="No voxels in selected range",
            scene=dict(xaxis=dict(range=[0,127]), yaxis=dict(range=[0,127]), zaxis=dict(range=[0,127])),
            paper_bgcolor=WHITE,
        )
        return fig, 0, 0

    # Subsample for display
    if n_total > max_pts:
        rng = np.random.default_rng(42)
        idx = rng.choice(n_total, size=max_pts, replace=False)
        indices = indices[idx]
        vals = vals[idx]

    # Scale coordinates from subsampled indices back to 128 grid
    px = indices[:, 0] * SS
    py = indices[:, 1] * SS
    pz = indices[:, 2] * SS

    title = f"3D View — t={step}"
    if sel_range:
        title += f" | ln(rho) in [{sel_range[0]:.2f}, {sel_range[1]:.2f}]"
        title += f" | {n_total:,} voxels"

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=px, y=py, z=pz,
        mode="markers",
        marker=dict(
            size=2.5, color=vals,
            colorscale=[
                [0.0, BLUE_700], [0.35, BLUE_300], [0.5, GRAY_400],
                [0.65, RED_300], [1.0, RED_500],
            ],
            cmin=DENSITY_RANGE[0], cmax=DENSITY_RANGE[1],
            opacity=0.55,
            colorbar=dict(
                title=dict(text="ln(rho)", font=dict(color=GRAY_600)),
                tickfont=dict(color=GRAY_500),
                len=0.55, thickness=12,
            ),
            showscale=True,
        ),
        hovertemplate="(%{x}, %{y}, %{z})<br>ln(rho)=%{marker.color:.3f}<extra></extra>",
        name="",
        showlegend=False,
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=BLACK, size=13)),
        scene=dict(
            xaxis=dict(title="X", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            yaxis=dict(title="Y", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            zaxis=dict(title="Z", range=[0,127], gridcolor=GRAY_200, color=GRAY_500, backgroundcolor=WHITE),
            aspectmode="cube",
            camera=dict(eye=dict(x=2.0, y=2.0, z=1.5)),
        ),
        paper_bgcolor=WHITE,
        margin=dict(l=0, r=0, t=40, b=0),
        uirevision=True,
    )

    return fig, n_total, d3.size


# ============================================================================
# Main callback
# ============================================================================
@app.callback(
    Output("histogram", "figure"),
    Output("scatter3d", "figure"),
    Output("hist-stats", "children"),
    Output("step-indicator", "children"),
    Output("step-indicator", "style"),
    Output("cur-step", "data"),
    Input("histogram", "selectedData"),
    Input("bt0", "n_clicks"),
    Input("bt25", "n_clicks"),
    Input("bt50", "n_clicks"),
    Input("bt75", "n_clicks"),
    Input("bt99", "n_clicks"),
    State("cur-step", "data"),
    prevent_initial_call=False,
)
def update_all(sel_data, bt0, bt25, bt50, bt75, bt99, cur_step):
    trig = ctx.triggered_id if ctx.triggered else ""
    if cur_step is None:
        cur_step = 99

    # Determine step
    step_map = {"bt0": 0, "bt25": 25, "bt50": 50, "bt75": 75, "bt99": 99}
    if trig in step_map:
        cur_step = step_map[trig]
        sel_range = None  # reset selection on step change
    elif trig == "histogram" and sel_data and "range" in sel_data:
        sel_range = [sel_data["range"]["x"][0], sel_data["range"]["x"][1]]
    else:
        sel_range = None

    # Build figures
    hist_fig = build_histogram(cur_step, sel_range)
    scat_fig, n_sel, n_total = build_scatter(cur_step, sel_range)

    # Stats
    if sel_range and n_sel > 0:
        pct = n_sel / n_total * 100
        stats_text = f"Selected: {n_sel:,} voxels ({pct:.2f}% of volume) | Range: [{sel_range[0]:.3f}, {sel_range[1]:.3f}]"
        if pct < 2:
            stats_text += "  ← High-density tail: these should correspond to cosmic web nodes!"
    else:
        stats_text = "Drag in the histogram to select a density range. Try selecting the far-right tail (top 1%) to see cosmic web nodes."

    # Step indicator
    step_color = get_time_color(cur_step)
    indicator_style = {
        "marginLeft": "15px", "fontSize": "18px", "fontWeight": "700", "color": step_color,
    }

    return hist_fig, scat_fig, stats_text, f"t = {cur_step}", indicator_style, cur_step


# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Open http://127.0.0.1:8050 in your browser")
    print("  Drag in histogram to select density range")
    print("  3D view updates to show matching voxels")
    print("  Click time step buttons to switch")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=8050)
