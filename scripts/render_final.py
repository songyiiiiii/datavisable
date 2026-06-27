"""
render_final.py — PyVista 体渲染: 黑底 #09080D + 6段新配色 + 切片面 + 十字线
"""
import numpy as np, pyvista as pv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

LEVELS   = [8.0, 8.6, 9.1, 9.7, 10.3, 10.9, 11.8, 14.0]
COLORS   = [
    (0.05,0.15,0.35),  # 深海军蓝
    (0.18,0.55,0.68),  # 蓝绿/青
    (0.22,0.72,0.58),  # 翠绿
    (0.40,0.40,0.55),  # 灰蓝
    (0.50,0.45,0.72),  # 紫
    (0.92,0.28,0.28),  # 红
    (1.00,0.45,0.20),  # 橙红
    (1.00,0.85,0.25),  # 亮金
]
OPACITIES = [0.06, 0.10, 0.14, 0.22, 0.30, 0.42, 0.55, 0.68]

OUT = os.path.join(OUTPUT_DIR, "volume_final")
os.makedirs(OUT, exist_ok=True)
MID = GRID_SIZE // 2

def make_grid(d):
    d2 = np.ascontiguousarray(np.transpose(d.astype(np.float32),(2,1,0)))
    g = pv.ImageData(); g.dimensions=(129,129,129); g.origin=(0,0,0); g.spacing=(1,1,1)
    g.cell_data["density"] = d2.flatten(order="C"); return g.cell_data_to_point_data()

def render_one(step):
    data = load_timestep(step); grid = make_grid(data)
    p = pv.Plotter(window_size=(900,700), off_screen=True)
    p.set_background('#09080D')

    for lvl, clr, op in zip(LEVELS, COLORS, OPACITIES):
        iso = grid.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points>0:
            glow = lvl>=12.0
            p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True,
                       ambient=1.0 if glow else 0.18,
                       diffuse=0.25 if glow else 0.72,
                       specular=0.35, specular_power=16)

    # 切片面
    for normal, origin in [('z',(MID,MID,MID)),('y',(MID,MID,MID)),('x',(MID,MID,MID))]:
        sl = grid.slice(normal=normal, origin=origin)
        if sl.n_points>0: p.add_mesh(sl, cmap='coolwarm', clim=[7.5,14.5], opacity=0.30, show_scalar_bar=False)

    p.camera.position = (300, 280, 260); p.camera.focal_point = (64, 64, 64); p.camera.up = (0, 0, 1)
    p.show(screenshot=os.path.join(OUT,f"t{step:04d}.png"), auto_close=True)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--end', type=int, default=99)
    args = ap.parse_args()
    from tqdm import tqdm
    for s in tqdm(range(args.start, args.end+1), desc="Rendering"):
        render_one(s)
    print(f"Done -> {OUT}/")
