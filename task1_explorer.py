# -*- coding: utf-8 -*-
"""
Task 1: Interactive 3D Cosmic Cube Explorer
============================================
Standalone PyVista interactive window.
- 8-layer isosurfaces: blue (voids) → gray (filaments) → red (clusters)
- Time slider scrubs 100 steps
- Mouse: rotate / zoom / pan
- Keyboard: Space=play/pause, ←→=step, S=screenshot
- White background, unified blue-gray-red palette

RUN: python task1_explorer.py
"""

import numpy as np
import pyvista as pv
import os, sys
sys.path.insert(0, r'e:\数据可视化')
from config import *
from data_loader import load_timestep

# ============================================================================
# Load all 100 steps
# ============================================================================
print("Loading 100 time steps (~800 MB)...")
ALL = np.zeros((N_TIMESTEPS, GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.float32)
for i in range(N_TIMESTEPS):
    ALL[i] = load_timestep(i)
    if (i + 1) % 25 == 0: print(f"  {i+1}/100")
print("Done.\n")

# ============================================================================
# Isosurface config
# ============================================================================
LEVELS = [8.0, 8.6, 9.1, 9.7, 10.3, 10.9, 11.8, 14.0]
COLORS = [
    (0.13, 0.40, 0.67),   # deep blue
    (0.35, 0.58, 0.80),   # blue
    (0.60, 0.75, 0.90),   # light blue
    (0.90, 0.90, 0.90),   # gray
    (0.95, 0.78, 0.68),   # warm pink
    (0.88, 0.50, 0.38),   # orange-red
    (0.75, 0.25, 0.22),   # red
    (0.60, 0.10, 0.15),   # deep red
]
OPACITIES = [0.08, 0.12, 0.18, 0.25, 0.32, 0.45, 0.55, 0.70]
CAMERA = [(200, 200, 180), (64, 64, 64), (0, 0, 1)]

# ============================================================================
# Grid builder
# ============================================================================
def make_grid(data_3d):
    """(z,y,x) Fortran -> PyVista ImageData with point data."""
    d = np.ascontiguousarray(np.transpose(data_3d, (2, 1, 0)))
    g = pv.ImageData()
    g.dimensions = (129, 129, 129)
    g.origin = (0, 0, 0)
    g.spacing = (1, 1, 1)
    g.cell_data["density"] = d.flatten(order="C")
    return g.cell_data_to_point_data()


def build_isosurfaces(plotter, grid):
    """Add 8-layer isosurfaces, return actor list."""
    actors = []
    for i, lvl in enumerate(LEVELS):
        iso = grid.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points > 0:
            glow = (i >= 5)
            act = plotter.add_mesh(
                iso, color=COLORS[i], opacity=OPACITIES[i],
                smooth_shading=True,
                ambient=1.0 if glow else 0.18,
                diffuse=0.25 if glow else 0.72,
                specular=0.35, specular_power=14,
                name=f"iso_{i}",
            )
            actors.append(act)
    return actors


# ============================================================================
# Interactive state
# ============================================================================
current_step = 0
playing = False
iso_actors = []

plotter = pv.Plotter(window_size=(1400, 920))
plotter.set_background(WHITE)

# Initial render
grid = make_grid(ALL[0])
iso_actors = build_isosurfaces(plotter, grid)

# Camera
plotter.camera_position = CAMERA

# HUD text
txt_step = plotter.add_text("t = 0", position="upper_right", font_size=30,
                             color=BLUE_700, font="arial", shadow=False)
txt_info = plotter.add_text(
    "[Space] Play/Pause  [← →] Step  [S] Screenshot  [R] Reset Camera",
    position="upper_left", font_size=11, color=GRAY_500, font="arial", shadow=False)
txt_stats = plotter.add_text("", position="lower_left", font_size=11,
                              color=GRAY_600, font="arial", shadow=False)
txt_legend = plotter.add_text(
    "VOIDS (blue)  |  FILAMENTS (gray)  |  CLUSTERS (red, glow)",
    position="lower_right", font_size=10, color=GRAY_400, font="arial", shadow=False)

# Scalar bar
plotter.add_scalar_bar(
    title="ln(rho)", vertical=True,
    position_x=0.04, position_y=0.15, width=0.04, height=0.40,
    color=GRAY_600, title_font_size=11, label_font_size=9,
    bold=False, italic=False, shadow=False, outline=False,
    background_color=WHITE, n_labels=5,
)

# ============================================================================
# Update function
# ============================================================================
def update_scene(step):
    global iso_actors
    for a in iso_actors:
        plotter.remove_actor(a)
    iso_actors.clear()

    g = make_grid(ALL[step])
    iso_actors = build_isosurfaces(plotter, g)

    d = ALL[step]
    txt_step.SetText(0, f"t = {step}")
    txt_stats.SetText(0, f"min: {d.min():.3f}  |  max: {d.max():.3f}  |  mean: {d.mean():.3f}  |  std: {d.std():.4f}")

    # Sync slider
    sl = plotter.widgets.slider_widgets
    if sl: sl[0].GetRepresentation().SetValue(step)

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
    if not playing: return
    current_step = (current_step + 1) % N_TIMESTEPS
    update_scene(current_step)


def on_key(*args):
    global current_step, playing
    evt = plotter.iren.get_key_event()
    if evt is None: return
    k = evt.GetKeySym().lower()

    if k == "space":
        playing = not playing
        s = "PLAYING" if playing else "PAUSED"
        txt_info.SetText(0, f"[{s}]  [Space] Play/Pause  [← →] Step  [S] Screenshot  [R] Reset")
        plotter.render()

    elif k == "left":
        playing = False
        current_step = max(0, current_step - 1)
        update_scene(current_step)

    elif k == "right":
        playing = False
        current_step = min(N_TIMESTEPS - 1, current_step + 1)
        update_scene(current_step)

    elif k == "r":
        plotter.camera_position = CAMERA
        plotter.render()

    elif k == "s":
        path = os.path.join(OUTPUT_DIR, f"screenshot_step{current_step:04d}.png")
        plotter.screenshot(path)
        print(f"  Screenshot saved: {path}")
        txt_info.SetText(0, f"Screenshot saved: screenshot_step{current_step:04d}.png")
        plotter.render()


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
    title_opacity=1.0,
)

plotter.iren.add_observer("KeyPressEvent", on_key)
plotter.iren.add_observer("TimerEvent", on_timer)
plotter.iren.create_timer(140)  # ~7 fps animation

# ============================================================================
print("=" * 60)
print("COSMIC CUBE EXPLORER — Interactive 3D Window")
print("=" * 60)
print("  Mouse drag     — rotate")
print("  Mouse scroll   — zoom")
print("  Middle drag    — pan")
print("  Slider         — scrub 100 time steps")
print("  Space          — play / pause (~7 fps)")
print("  Left / Right   — step frame by frame")
print("  R              — reset camera")
print("  S              — save screenshot to output/")
print("  Close window   — exit")
print("=" * 60)

plotter.show()
