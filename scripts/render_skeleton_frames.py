"""
render_skeleton_frames.py — 批量渲染 100 帧骨架图
白底 + 淡灰低密度背景 + 金/橙高密度骨架 + 红节点
"""
import numpy as np, pyvista as pv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE
from data_loader import load_timestep

OUT = os.path.join(OUTPUT_DIR, "skeleton_frames")
os.makedirs(OUT, exist_ok=True)

def render_one(step):
    data = load_timestep(step).astype(np.float32)
    d = np.ascontiguousarray(np.transpose(data, (2,1,0)))
    g = pv.ImageData()
    g.dimensions = (129,129,129); g.origin = (0,0,0); g.spacing = (1,1,1)
    g.cell_data["density"] = d.flatten(order="C")
    g = g.cell_data_to_point_data()

    p = pv.Plotter(window_size=(800,600), off_screen=True)
    p.set_background('#09080D')  # 暗色背景

    # 淡蓝背景等值面
    for lvl, clr, op in [(8.5,(0.15,0.45,0.55),0.03),(10.0,(0.40,0.55,0.65),0.04)]:
        iso = g.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points>0: p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True, ambient=0.5,diffuse=0.5)

    # 金色骨架 #FFE066
    for lvl, clr, op in [(11.5,(1.0,0.88,0.40),0.45),(12.5,(0.98,0.82,0.30),0.60)]:
        iso = g.contour(isosurfaces=[lvl], scalars="density")
        if iso.n_points>0: p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True, ambient=0.7,diffuse=0.2,specular=0.6,specular_power=22)

    # 红色节点 #F25F5C
    peak = g.contour(isosurfaces=[13.5], scalars="density")
    if peak.n_points>0: p.add_mesh(peak, color=(0.95,0.37,0.36), opacity=0.72, smooth_shading=True, ambient=0.7,diffuse=0.2,specular=0.55,specular_power=28)

    p.camera.position = (200,200,180); p.camera.focal_point = (64,64,64); p.camera.up = (0,0,1)
    p.show(screenshot=os.path.join(OUT,f"t{step:04d}.png"), auto_close=True)

if __name__ == "__main__":
    from tqdm import tqdm
    print("Rendering 100 skeleton frames...")
    for s in tqdm(range(N_TIMESTEPS)): render_one(s)
    print(f"Done -> {OUT}/")
