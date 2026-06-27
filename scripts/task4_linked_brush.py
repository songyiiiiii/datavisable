"""
task4_linked_brush.py — 直方图刷选 + 对应密度区间体渲染 并排展示
左: 直方图(选中区间高亮)  右: 3D体渲染(仅该区间)
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pyvista as pv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

STEP = 73
data = load_timestep(STEP).astype(np.float32)
report = os.path.join(OUTPUT_DIR, "report_images")
os.makedirs(report, exist_ok=True)

# ── 公共 ──
d = np.ascontiguousarray(np.transpose(data, (2,1,0)))
g = pv.ImageData(); g.dimensions=(129,129,129); g.origin=(0,0,0); g.spacing=(1,1,1)
g.cell_data["density"] = d.flatten(order="C"); g = g.cell_data_to_point_data()

BANDS = [
    ( 7.5,  8.5, (0.13,0.40,0.67), 0.06, 'Void'),
    ( 8.5,  9.5, (0.35,0.70,0.90), 0.12, 'Sheet'),
    ( 9.5, 10.5, (0.80,0.80,0.82), 0.18, 'Filament'),
    (10.5, 12.0, (0.95,0.40,0.30), 0.30, 'Cluster'),
    (12.0, 14.5, (0.85,0.10,0.10), 0.50, 'Node'),
]

# ── 生成 5 张图 (直方图+体渲染 并排) ──
for lo, hi, clr, op, name in BANDS:
    fig = plt.figure(figsize=(16, 7))
    fig.patch.set_facecolor('white')

    # 左: 直方图
    ax1 = fig.add_axes([0.05, 0.12, 0.38, 0.78])
    ax1.set_facecolor('white')
    h, e = np.histogram(data.ravel(), bins=100, range=(7.5, 14.5))
    ctr = (e[:-1]+e[1:])/2
    colors = ['#B2182B' if lo <= c <= hi else '#92C5DE' for c in ctr]
    ax1.bar(ctr, h, width=0.07, color=colors, edgecolor='none')
    ax1.axvspan(lo, hi, color='#B2182B', alpha=0.08)
    in_pct = ((data.ravel()>=lo)&(data.ravel()<=hi)).sum()/data.size*100
    ax1.set_title(f'Density Histogram (t={STEP})\nSelected: [{lo:.1f}, {hi:.1f}] → {in_pct:.2f}%',
                  fontsize=13, fontweight='bold', color='#1E293B')
    ax1.set_xlabel('ln(ρ)', fontsize=11); ax1.set_ylabel('Count', fontsize=11)
    ax1.grid(True, alpha=0.25, color='#E2E6EC')

    # 右: 3D 体渲染
    ax2 = fig.add_axes([0.46, 0.05, 0.53, 0.92], projection='3d')
    ax2.set_facecolor('white')
    ax2.axis('off')
    ax2.set_title(f'{name} (ln ρ ∈ [{lo:.1f}, {hi:.1f}])',
                  fontsize=13, fontweight='bold', color='#1E293B', pad=8)

    # 渲染体素或等值面截图
    subvol = g.threshold([lo, hi], scalars="density")
    if subvol.n_points > 100:
        iso = subvol.contour(isosurfaces=[(lo+hi)/2], scalars="density")
    else:
        iso = subvol

    # 用 PyVista 渲染并嵌入
    rp = pv.Plotter(window_size=(700, 600), off_screen=True)
    rp.set_background('white')
    if iso.n_points > 0:
        rp.add_mesh(iso, color=clr, opacity=op, smooth_shading=True,
                    ambient=0.35, diffuse=0.55, specular=0.3, specular_power=15)
    rp.add_mesh(pv.Box(bounds=(0,128,0,128,0,128)), color='#CCCCCC', opacity=0.12, style='wireframe')
    rp.camera.position = (280, 260, 240)
    rp.camera.focal_point = (64, 64, 64)
    rp.camera.up = (0, 0, 1)
    tmp = os.path.join(report, f"_tmp_{name}.png")
    rp.show(screenshot=tmp, auto_close=True)

    img = plt.imread(tmp)
    ax2.imshow(img)
    os.remove(tmp)

    out = os.path.join(report, f"fig4_brush_{name.lower()}.png")
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  {name}: {out}")

# ── 合成一张全景图 ──
print("Generating composite...")
fig, axes = plt.subplots(5, 2, figsize=(18, 28), gridspec_kw={'width_ratios':[1, 1.3]})
fig.patch.set_facecolor('white')
for idx, (lo, hi, clr, op, name) in enumerate(BANDS):
    flat = data.ravel()
    # 直方图
    h, e = np.histogram(flat, bins=80, range=(7.5, 14.5))
    ctr = (e[:-1]+e[1:])/2
    in_pct = ((flat>=lo)&(flat<=hi)).sum()/flat.size*100
    colors = ['#B2182B' if lo<=c<=hi else '#92C5DE' for c in ctr]
    axes[idx,0].bar(ctr, h, width=0.08, color=colors, edgecolor='none')
    axes[idx,0].axvspan(lo, hi, color='#B2182B', alpha=0.08)
    axes[idx,0].set_ylabel(f'{name}\n{in_pct:.2f}%', fontsize=10, fontweight='bold')
    axes[idx,0].tick_params(labelsize=8)
    axes[idx,0].grid(True, alpha=0.2, color='#E2E6EC')

    # 3D 渲染
    subvol = g.threshold([lo, hi], scalars="density")
    iso = subvol.contour(isosurfaces=[(lo+hi)/2], scalars="density") if subvol.n_points>100 else subvol
    rp = pv.Plotter(window_size=(500, 400), off_screen=True)
    rp.set_background('white')
    if iso.n_points>0: rp.add_mesh(iso, color=clr, opacity=op, smooth_shading=True, ambient=0.35,diffuse=0.55,specular=0.3,specular_power=15)
    rp.add_mesh(pv.Box(bounds=(0,128,0,128,0,128)), color='#CCCCCC', opacity=0.1, style='wireframe')
    rp.camera.position=(260,240,220); rp.camera.focal_point=(64,64,64); rp.camera.up=(0,0,1)
    tmp=os.path.join(report,f"_tmp_{idx}.png"); rp.show(screenshot=tmp,auto_close=True)
    axes[idx,1].imshow(plt.imread(tmp)); axes[idx,1].axis('off'); os.remove(tmp)

axes[0,0].set_title('Density Histogram (Brush Selection)', fontsize=14, fontweight='bold')
axes[0,1].set_title('3D Spatial Distribution (Filtered Voxels)', fontsize=14, fontweight='bold')
fig.suptitle(f'Linked Brushing: Histogram → 3D View  (t={STEP:03d})', fontsize=18, fontweight='bold', y=0.99)
out = os.path.join(report, "fig4_linked_brush_full.png")
fig.savefig(out, dpi=120, bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"Composite -> {out}")
