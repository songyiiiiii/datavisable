"""
render_volume_with_slices.py — PyVista 体渲染: 白底 + 原配色 + 三向切片
======================================================================
重新渲染 100 帧: 白色背景, 8层蓝灰红等值面, XY/XZ/YZ 三个切片平面, 十字准线

用法: python render_volume_with_slices.py [--start 0] [--end 99]
输出: output/volume_final/tXXXX.png
"""

import numpy as np, pyvista as pv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

# ── 等值面配置 (与 task1_explorer.py 一致) ──
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

OUT = os.path.join(OUTPUT_DIR, "volume_final")
os.makedirs(OUT, exist_ok=True)
MID = GRID_SIZE // 2  # 64

def make_grid(data_3d):
    d = np.ascontiguousarray(np.transpose(data_3d, (2,1,0)))
    g = pv.ImageData()
    g.dimensions = (129,129,129)
    g.origin = (0,0,0); g.spacing = (1,1,1)
    g.cell_data["density"] = d.flatten(order="C")
    return g.cell_data_to_point_data()

def render_one(step):
    data = load_timestep(step)
    grid = make_grid(data)

    p = pv.Plotter(window_size=(1600,1200), off_screen=True)
    p.set_background('white')

    # ── 8层等值面 ──
    for lvl, clr, op in zip(LEVELS, COLORS, OPACITIES):
        iso = grid.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points > 0:
            glow = (lvl >= 11.8)
            p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True,
                       ambient=1.0 if glow else 0.18,
                       diffuse=0.25 if glow else 0.72,
                       specular=0.35, specular_power=14)

    # ── 三向切片平面 ──
    slice_args = dict(cmap='coolwarm', clim=[7.5,14.5], opacity=0.60, show_scalar_bar=False)
    xy = grid.slice(normal='z', origin=(MID, MID, MID))
    if xy.n_points > 0: p.add_mesh(xy, **slice_args)
    xz = grid.slice(normal='y', origin=(MID, MID, MID))
    if xz.n_points > 0: p.add_mesh(xz, **slice_args)
    yz = grid.slice(normal='x', origin=(MID, MID, MID))
    if yz.n_points > 0: p.add_mesh(yz, **slice_args)

    # ── 切片边框 (用 Line 画矩形框) ──
    def rect_lines(cx, cy, cz, nx, ny, nz):
        """在平面中心(cx,cy,cz)画矩形框, nx,ny,nz定义法向"""
        hw = 64  # 半宽
        if nz == 1:  # XY plane
            pts = [(cx-hw, cy-hw, cz), (cx+hw, cy-hw, cz), (cx+hw, cy+hw, cz),
                   (cx-hw, cy+hw, cz), (cx-hw, cy-hw, cz)]
        elif ny == 1:  # XZ plane
            pts = [(cx-hw, cy, cz-hw), (cx+hw, cy, cz-hw), (cx+hw, cy, cz+hw),
                   (cx-hw, cy, cz+hw), (cx-hw, cy, cz-hw)]
        else:  # YZ plane
            pts = [(cx, cy-hw, cz-hw), (cx, cy+hw, cz-hw), (cx, cy+hw, cz+hw),
                   (cx, cy-hw, cz+hw), (cx, cy-hw, cz-hw)]
        lines = np.array([[2, i, i+1] for i in range(len(pts)-1)]).flatten()
        poly = pv.PolyData(np.array(pts), lines=lines)
        return poly

    p.add_mesh(rect_lines(MID, MID, MID, 0, 0, 1), color='#555555', line_width=1.5, opacity=0.40)
    p.add_mesh(rect_lines(MID, MID, MID, 0, 1, 0), color='#555555', line_width=1.5, opacity=0.40)
    p.add_mesh(rect_lines(MID, MID, MID, 1, 0, 0), color='#555555', line_width=1.5, opacity=0.40)

    # ── 十字准线 ──
    p.add_mesh(pv.Line((0, MID, MID), (128, MID, MID)), color='#333333', line_width=1.5, opacity=0.50)
    p.add_mesh(pv.Line((MID, 0, MID), (MID, 128, MID)), color='#333333', line_width=1.5, opacity=0.50)
    p.add_mesh(pv.Line((MID, MID, 0), (MID, MID, 128)), color='#333333', line_width=1.5, opacity=0.50)

    # ── 边框 ──
    outline = pv.Box(bounds=(0,128, 0,128, 0,128))
    p.add_mesh(outline, color='#999999', opacity=0.22, style='wireframe', line_width=0.8)

    # ── 相机 ──
    p.camera.position = (200, 200, 180)
    p.camera.focal_point = (64, 64, 64)
    p.camera.up = (0, 0, 1)

    # ── 标题 ──
    p.add_text(f"Cosmic Web — t={step:03d}", position='upper_left',
               color='#333333', font_size=13, shadow=False)
    p.add_text("Blue: Voids  |  Gray: Filaments  |  Red: Clusters\n"
               f"Slice planes at X=Y=Z={MID}  |  white bg",
               position='lower_left', color='#888888', font_size=9, shadow=False)

    path = os.path.join(OUT, f"t{step:04d}.png")
    p.show(screenshot=path, auto_close=True)
    return path

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=99)
    args = ap.parse_args()

    print(f"Rendering t={args.start}..{args.end} (white bg + slices + crosshairs)")
    for step in range(args.start, args.end + 1):
        p = render_one(step)
        if (step+1) % 10 == 0:
            print(f"  {step+1}/100")
    print(f"Done -> {OUT}/")
