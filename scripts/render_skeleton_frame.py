"""
render_skeleton_frame.py — 单帧骨架渲染测试
高对比度：白底 + 亮金骨架线 + 红节点
"""
import numpy as np, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

step = 73
print(f"Rendering skeleton frame t={step}")

data = load_timestep(step).astype(np.float64)

# 快速骨架: 取高密度等值面 (rho > 11.5) 作骨架代理
from scipy.ndimage import gaussian_filter, sobel
s = gaussian_filter(data, sigma=1.2)

# 密度梯度幅值
gx = sobel(s, axis=2) / 2.0
gy = sobel(s, axis=1) / 2.0
gz = sobel(s, axis=0) / 2.0
grad = np.sqrt(gx**2 + gy**2 + gz**2)

# 骨架 = 高密度 + 中等梯度 (排除均匀区域和边界)
skeleton = (data > 10.8) & (grad > 0.015) & (grad < 0.12)
print(f"  Skeleton voxels: {skeleton.sum()} / {skeleton.size} ({skeleton.sum()/skeleton.size*100:.1f}%)")

# PyVista 渲染
import pyvista as pv

d_xyz = np.ascontiguousarray(np.transpose(data.astype(np.float32), (2,1,0)))
grid = pv.ImageData()
grid.dimensions = (129,129,129)
grid.origin = (0,0,0); grid.spacing = (1,1,1)
grid.cell_data["density"] = d_xyz.flatten(order="C")
grid = grid.cell_data_to_point_data()

p = pv.Plotter(window_size=(1600,1200), off_screen=True)
p.set_background('white')

# 半透明等值面作背景
for lvl, clr, op in [(8.5, (0.78,0.82,0.88), 0.03), (10.5, (0.55,0.60,0.68), 0.04)]:
    iso = grid.contour(isosurfaces=[lvl], scalars="density")
    if iso.n_points > 0:
        p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True, ambient=0.5, diffuse=0.5)

# 高密度等值面 (亮金色骨架 - 用 contour 取 rho>11.5)
for lvl, clr, op in [(11.5, (0.85,0.62,0.08), 0.35), (12.8, (0.95,0.35,0.05), 0.55)]:
    iso = grid.contour(isosurfaces=[lvl], scalars="density")
    if iso.n_points > 0:
        p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True, ambient=0.6, diffuse=0.3, specular=0.5, specular_power=18)

# 极高峰值节点
peak = grid.contour(isosurfaces=[13.5], scalars="density")
if peak.n_points > 0:
    p.add_mesh(peak, color=(0.88, 0.15, 0.05), opacity=0.72, smooth_shading=True, ambient=0.7, diffuse=0.2, specular=0.6, specular_power=25)

p.camera.position = (200, 200, 180)
p.camera.focal_point = (64, 64, 64)
p.camera.up = (0, 0, 1)

out = os.path.join(OUTPUT_DIR, "skeleton_frames")
os.makedirs(out, exist_ok=True)
path = os.path.join(out, f"t{step:04d}.png")
p.show(screenshot=path, auto_close=True)
print(f"Done -> {path}")
