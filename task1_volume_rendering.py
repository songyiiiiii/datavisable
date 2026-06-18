# -*- coding: utf-8 -*-
"""
Task 1: Interactive 3D Density Visualization with Time Slider
=============================================================
PyVista native window — multi-layer semi-transparent isosurfaces.
Blue (low density / voids) → Gray (mid) → Red (high density / peaks).

RUN THIS SCRIPT DIRECTLY in your terminal / IDE, NOT through Claude Code bash.
  python task1_volume_rendering.py

Controls:
  Drag slider  — scrub 100 time steps
  Space        — play / pause animation (~6 fps)
  Left / Right — step one frame
  S            — save screenshot to output/
  Mouse        — rotate / zoom / pan
"""

import numpy as np
import pyvista as pv
import os

from config import *
from data_loader import load_timestep

# ============================================================================
# Load all 100 time steps
# ============================================================================
print("Loading 100 time steps...")
all_data = np.zeros((N_TIMESTEPS, GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.float32)
for i in range(N_TIMESTEPS):
    all_data[i] = load_timestep(i)
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/100")
print("Done.\n")

# ============================================================================
# Isosurface levels, colors, opacities
# ============================================================================
N_ISOS = 8
ISO_LEVELS = np.linspace(8.0, 14.0, N_ISOS)

# Blue → Light Gray → Red gradient
ISO_COLORS = [
    (0.13, 0.40, 0.67),   # blue      — deepest voids
    (0.35, 0.58, 0.80),   # light blue
    (0.60, 0.75, 0.90),   # pale blue — filaments
    (0.90, 0.90, 0.90),   # gray       — mid density
    (0.95, 0.78, 0.68),   # warm pink  — clusters
    (0.88, 0.50, 0.38),   # orange-red
    (0.75, 0.25, 0.22),   # red        — dense nodes
    (0.60, 0.10, 0.15),   # dark red   — extreme peaks
]
ISO_OPACITIES = [0.03, 0.06, 0.10, 0.16, 0.24, 0.35, 0.48, 0.65]


# ============================================================================
def make_grid(data_3d):
    """(z,y,x) Fortran -> PyVista ImageData with point data."""
    data_xyz = np.ascontiguousarray(np.transpose(data_3d, (2, 1, 0)))
    grid = pv.ImageData()
    grid.dimensions = (GRID_SIZE + 1, GRID_SIZE + 1, GRID_SIZE + 1)
    grid.origin = (0, 0, 0)
    grid.spacing = (1, 1, 1)
    grid.cell_data["density"] = data_xyz.flatten(order="C")
    return grid.cell_data_to_point_data()


def build_isosurfaces(plotter, grid):
    """Add multi-layer isosurfaces and return the actor list."""
    actors = []
    for i, lvl in enumerate(ISO_LEVELS):
        iso = grid.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points > 0:
            act = plotter.add_mesh(
                iso,
                color=ISO_COLORS[i],
                opacity=ISO_OPACITIES[i],
                smooth_shading=True,
                specular=0.35,
                specular_power=12,
                diffuse=0.75,
                ambient=0.18,
            )
            actors.append(act)
    return actors


# ============================================================================
# Plotter
# ============================================================================
current_step = 0
playing = False
iso_actors = []

plotter = pv.Plotter(window_size=(1400, 900))
plotter.set_background(WHITE)

# Initial render
grid = make_grid(all_data[0])
iso_actors = build_isosurfaces(plotter, grid)

# Camera
plotter.camera_position = [(200, 200, 180), (64, 64, 64), (0, 0, 1)]

# HUD text
txt_step = plotter.add_text("t = 0", position="upper_right", font_size=28,
                             color=BLUE_700, font="arial")
txt_info = plotter.add_text(
    "[Space] Play/Pause  [<- ->] Step  [S] Screenshot",
    position="upper_left", font_size=11, color=GRAY_500, font="arial")
txt_stats = plotter.add_text("", position="lower_left", font_size=11,
                              color=GRAY_600, font="arial")

# ============================================================================
# Update function
# ============================================================================
def update_scene(step):
    global iso_actors
    # Remove old
    for a in iso_actors:
        plotter.remove_actor(a)
    iso_actors.clear()
    # Build new
    g = make_grid(all_data[step])
    iso_actors = build_isosurfaces(plotter, g)
    # Labels
    d = all_data[step]
    txt_step.SetText(0, f"t = {step}")
    txt_stats.SetText(0,
        f"min: {d.min():.3f} | max: {d.max():.3f} | mean: {d.mean():.3f} | std: {d.std():.4f}")
    # Slider
    sl = plotter.widgets.slider_widgets
    if sl:
        sl[0].GetRepresentation().SetValue(step)
    plotter.render()


# ============================================================================
# Callbacks
# ============================================================================
def on_slider(value):
    global current_step, playing
    playing = False
    current_step = int(round(value))
    update_scene(current_step)


def on_timer(*args):
    global current_step, playing
    if not playing:
        return
    current_step = (current_step + 1) % N_TIMESTEPS
    update_scene(current_step)


def on_key(*args):
    global current_step, playing
    evt = plotter.iren.get_key_event()
    if evt is None:
        return
    k = evt.GetKeySym().lower()

    if k == "space":
        playing = not playing
        s = "PLAYING" if playing else "PAUSED"
        txt_info.SetText(0, f"[{s}]  [Space] Play/Pause  [<- ->] Step  [S] Screenshot")
        plotter.render()
    elif k == "left":
        playing = False
        current_step = max(0, current_step - 1)
        update_scene(current_step)
    elif k == "right":
        playing = False
        current_step = min(N_TIMESTEPS - 1, current_step + 1)
        update_scene(current_step)
    elif k == "s":
        p = os.path.join(OUTPUT_DIR, f"screenshot_step{current_step:04d}.png")
        plotter.screenshot(p)
        print(f"Screenshot: {p}")


# ============================================================================
# Slider widget
# ============================================================================
plotter.add_slider_widget(
    callback=on_slider,
    rng=[0, N_TIMESTEPS - 1],
    value=0,
    title="Time Step",
    title_color=GRAY_600,
    color=GRAY_400,
    pointa=(0.15, 0.05),
    pointb=(0.85, 0.05),
    style="modern",
    title_height=16,
)

plotter.iren.add_observer("KeyPressEvent", on_key)
plotter.iren.add_observer("TimerEvent", on_timer)
plotter.iren.create_timer(150)

# ============================================================================
print("=" * 60)
print("CONTROLS")
print("  Slider       — scrub time steps 0–99")
print("  Space        — play / pause animation")
print("  Left / Right — step one frame")
print("  S            — save screenshot")
print("  Mouse drag   — rotate | Scroll — zoom | Middle — pan")
print("=" * 60)

plotter.show()
