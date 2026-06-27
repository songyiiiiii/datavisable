"""
task4_brush_render.py — 刷选分密度层体渲染 (RWB 高饱和, 白底)
展示不同密度区间在空间中的分布形态
"""
import numpy as np, pyvista as pv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

STEP = 73
data = load_timestep(STEP).astype(np.float32)
d = np.ascontiguousarray(np.transpose(data, (2,1,0)))
g = pv.ImageData()
g.dimensions=(129,129,129); g.origin=(0,0,0); g.spacing=(1,1,1)
g.cell_data["density"] = d.flatten(order="C")
g = g.cell_data_to_point_data()

# 5 个密度区间 (对应刷选范围)
bands = [
    ( 7.5,  8.5, (0.13,0.40,0.67), 0.08, 'Void  空洞 (7.5–8.5)'),       # 深蓝
    ( 8.5,  9.5, (0.35,0.70,0.90), 0.15, 'Sheet 薄片 (8.5–9.5)'),       # 浅蓝
    ( 9.5, 10.5, (0.80,0.80,0.82), 0.22, 'Filament 纤维 (9.5–10.5)'),   # 灰白
    (10.5, 12.0, (0.95,0.60,0.40), 0.35, 'Cluster 团簇 (10.5–12.0)'),   # 橙
    (12.0, 14.5, (0.85,0.12,0.12), 0.55, 'Node 节点 (12.0–14.5)'),      # 红
]

p = pv.Plotter(window_size=(1400, 1000), off_screen=True)
p.set_background('white')

for lo, hi, clr, op, label in bands:
    # 裁剪到密度区间
    clipped = g.threshold([lo, hi], scalars="density")
    if clipped.n_points > 10:
        iso = clipped.contour(isosurfaces=[(lo+hi)/2], scalars="density")
        if iso.n_points > 0:
            p.add_mesh(iso, color=clr, opacity=op, smooth_shading=True,
                       ambient=0.3, diffuse=0.6, specular=0.3, specular_power=15, label=label)

    # 也加一个更外层等值面增加厚度
    if hi - lo > 0.5:
        iso2 = g.contour(isosurfaces=[lo+0.3, hi-0.3], scalars="density")
        for iso_obj in [iso2]:
            if iso_obj.n_points > 10:
                clipped2 = iso_obj.threshold([lo, hi], scalars="density")
                if clipped2.n_points > 0:
                    p.add_mesh(clipped2, color=clr, opacity=op*0.5, smooth_shading=True,
                               ambient=0.4, diffuse=0.5, specular=0.2, specular_power=10)

# 框
p.add_mesh(pv.Box(bounds=(0,128,0,128,0,128)), color='#888888', opacity=0.15, style='wireframe')

p.camera.position = (300, 280, 260)
p.camera.focal_point = (64, 64, 64)
p.camera.up = (0, 0, 1)

p.add_text(f'Density Range Selection — t={STEP:03d}', position='upper_left',
           color='#1E293B', font_size=14, shadow=False)
p.add_text('|  Blue=Void  |  Light Blue=Sheet  |  Gray=Filament  |  Orange=Cluster  |  Red=Node  |',
           position='lower_left', color='#64748B', font_size=10)
p.add_text('Method: threshold-based volume rendering per density band',
           position='lower_right', color='#94A3B8', font_size=9)

out = os.path.join(OUTPUT_DIR, "report_images")
os.makedirs(out, exist_ok=True)
path = os.path.join(out, "fig4_brush_density_bands.png")
p.show(screenshot=path, auto_close=True)
print(f"Done -> {path}")
