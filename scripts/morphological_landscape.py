"""
morphological_landscape.py — 三向形态景观图并排 (实心坐标系 + 镜头拉近)
XY/XZ/YZ 三截面, 每个截面密度做高度, 渐变色彩
"""
import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

STEP = 73
data = load_timestep(STEP).astype(np.float64)
mid = GRID_SIZE // 2

# 三个方向截面
slices = {
    'XY 俯视 (Z=64)': data[mid, :, :],      # data[Z, Y, X]
    'XZ 侧视 (Y=64)': data[:, mid, :],       # data[Z, Y, X] with Y fixed
    'YZ 正视 (X=64)': data[:, :, mid],        # data[Z, Y, X] with X fixed
}

# 【修改】：将画布宽高比稍微调宽一点，适应横屏显示
fig, axes = plt.subplots(3, 1, figsize=(13, 16), subplot_kw={'projection': '3d'})
fig.patch.set_facecolor('#09080D')

X = np.arange(128)
Y = np.arange(128)

ls = LightSource(azdeg=315, altdeg=45)

for ax, (title, z_data) in zip(axes, slices.items()):
    ax.set_facecolor('#09080D')
    xx, yy = np.meshgrid(X, Y)
    
    # 提高垂直放缩比例，让山峰更陡峭、更震撼
    z_norm = (z_data.T - 7.5) / 7.0 * 45  # 从 30 提高到 45

    # 渐变色彩: 低密度→深蓝, 高密度→亮金 (使用 viridis 色阶)
    colors = plt.cm.viridis((z_data.T - 7.5) / 7.0)

    ax.plot_surface(xx, yy, z_norm, facecolors=colors,
                    rstride=2, cstride=2, linewidth=0,
                    antialiased=True, shade=True, lightsource=ls, alpha=0.92)

    # 白线框 (稀疏化，避免视觉杂乱)
    ax.plot_wireframe(xx[::5, ::5], yy[::5, ::5], z_norm[::5, ::5],
                      color='white', linewidth=0.12, alpha=0.15, rstride=1, cstride=1)

    ax.set_title(title, color='white', fontsize=14, pad=5, fontweight='bold')
    ax.set_xlabel('X', color='#8898AA', fontsize=10)
    ax.set_ylabel('Y', color='#8898AA', fontsize=10)
    ax.set_zlabel('ln(ρ)', color='#8898AA', fontsize=10, labelpad=-2)
    ax.tick_params(colors='#6B6880', labelsize=7, pad=-2)
    
    # ==========================================================
    # 【核心修改】：将透明坐标系改为深空实心坐标系
    # ==========================================================
    # 面板填充颜色改为极深的半透明星空蓝 (#0C0D45)，并带一点点透明度
    ax.xaxis.pane.set_facecolor('#0C0D45')
    ax.yaxis.pane.set_facecolor('#0C0D45')
    ax.zaxis.pane.set_facecolor('#0C0D45')
    ax.xaxis.pane.set_edgecolor('#ffffff20') # 边缘微微泛白
    ax.yaxis.pane.set_edgecolor('#ffffff20')
    ax.zaxis.pane.set_edgecolor('#ffffff20')
    # 重点：打开填充开关
    ax.xaxis.pane.fill = True
    ax.yaxis.pane.fill = True
    ax.zaxis.pane.fill = True
    
    ax.grid(True, color='#ffffff15', linewidth=0.4)
    
    # ==========================================================
    # 【核心修改】：拉近镜头
    # ==========================================================
    # 降低 dist 值让相机靠近，放大海拔细节
    ax.dist = 5.8 
    # 降低仰角，让山峰看起来更高
    ax.view_init(elev=25, azim=-60)
    
    # 限制 Z 轴范围，去除多余空白，让山峰撑满画面
    ax.set_zlim(0, 45) 

    # 隐藏 3D 面板边框 (外框线条)
    ax.xaxis.line.set_color((1,1,1,0))
    ax.yaxis.line.set_color((1,1,1,0))
    ax.zaxis.line.set_color((1,1,1,0))

# 总标题
fig.suptitle(f'Morphological Landscape — t={STEP:03d}  |  Three Orthogonal Slices  |  Z = ln(ρ)',
             color='white', fontsize=18, y=0.98)

out = os.path.join(OUTPUT_DIR, "morpho_landscape")
os.makedirs(out, exist_ok=True)
path = os.path.join(out, f"landscape_t{STEP:04d}.png")
fig.savefig(path, dpi=120, bbox_inches='tight', facecolor='#09080D')
plt.close(fig)
print(f"Done -> {path}")