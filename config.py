# -*- coding: utf-8 -*-
"""
Nyx 宇宙学模拟可视分析 — 统一配置文件 v2
===========================================
极简黑白灰 + 蓝红配色方案
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import os

# ============================================================================
# 路径配置
# ============================================================================
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_DIR, "Nyx")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================================
# 极简黑白灰 + 蓝红配色
# ============================================================================

# ── 基础色 ──
WHITE      = "#FFFFFF"
BLACK      = "#1A1A1A"
GRAY_100   = "#F5F5F5"
GRAY_200   = "#E8E8E8"
GRAY_300   = "#CCCCCC"
GRAY_400   = "#999999"
GRAY_500   = "#666666"
GRAY_600   = "#444444"
GRAY_700   = "#333333"
GRAY_800   = "#222222"

# ── 主色：蓝（空洞/低密度/早期） ──
BLUE_700   = "#1A4A7A"
BLUE_500   = "#2166AC"
BLUE_300   = "#4393C3"
BLUE_100   = "#92C5DE"

# ── 主色：红（团簇/高密度/晚期） ──
RED_700    = "#8B1A2B"
RED_500    = "#B2182B"
RED_300    = "#D6604D"
RED_100    = "#F4A582"

# ── 功能色别名 ──
COLOR_VOID      = BLUE_500      # 空洞 → 蓝
COLOR_FILAMENT  = GRAY_500      # 纤维 → 灰
COLOR_CLUSTER   = RED_300       # 团簇 → 浅红
COLOR_PEAK      = RED_500       # 峰区 → 红
COLOR_EARLY     = BLUE_500      # 早期时间步 → 蓝
COLOR_LATE      = RED_500       # 晚期时间步 → 红
COLOR_MEAN      = GRAY_700      # 均值线 → 深灰
COLOR_MEDIAN    = GRAY_500      # 中位数线 → 灰
COLOR_STD       = RED_500       # 标准差 → 红
COLOR_IQR       = BLUE_500      # IQR → 蓝
COLOR_SKEW      = RED_300       # 偏度 → 浅红
COLOR_KURT      = BLUE_300      # 峰度 → 浅蓝

# ── 5 个代表性时间步的配色（蓝 → 灰 → 红） ──
COLORS_TIMESTEPS = {
    0:  BLUE_700,    # 早期均匀
    25: BLUE_300,    # 开始演化
    50: GRAY_500,    # 过渡态
    75: RED_300,     # 团块化明显
    99: RED_500,     # 终态
}

# ============================================================================
# matplotlib 全局样式 — 纯白背景极简风
# ============================================================================

rcParams.update({
    # 背景
    "figure.facecolor": WHITE,
    "axes.facecolor": WHITE,
    "savefig.facecolor": WHITE,

    # 边框 & 刻度
    "axes.edgecolor": GRAY_300,
    "axes.linewidth": 0.8,
    "xtick.color": GRAY_500,
    "ytick.color": GRAY_500,
    "xtick.major.size": 3,
    "ytick.major.size": 3,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,

    # 网格
    "grid.color": GRAY_200,
    "grid.alpha": 1.0,
    "grid.linewidth": 0.5,

    # 文字
    "text.color": GRAY_700,
    "axes.labelcolor": GRAY_600,
    "axes.titlecolor": BLACK,

    # 图例
    "legend.facecolor": WHITE,
    "legend.edgecolor": GRAY_300,
    "legend.labelcolor": GRAY_600,
    "legend.framealpha": 0.9,

    # 字体
    "font.sans-serif": ["Noto Sans SC", "SimHei", "Microsoft YaHei", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "axes.unicode_minus": False,

    # 输出
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# ============================================================================
# 数据参数
# ============================================================================
GRID_SIZE = 128
N_TIMESTEPS = 100
N_VOXELS = GRID_SIZE ** 3  # 2,097,152
DENSITY_RANGE = (7.5, 15.0)
HIST_BINS = 128
REPRESENTATIVE_STEPS = [0, 25, 50, 75, 99]

# ============================================================================
# 传递函数参数（用于体渲染）
# ============================================================================
TF_CONFIG = {
    "void_range":     (7.5, 8.5),
    "filament_range": (8.5, 10.5),
    "cluster_range":  (10.5, 12.0),
    "peak_range":     (12.0, 15.0),
    "void_alpha":      0.03,
    "filament_alpha":  0.08,
    "cluster_alpha":   0.25,
    "peak_alpha":      0.70,
    "ambient":  0.25,
    "diffuse":  0.70,
    "specular": 0.25,
    "specular_power": 12.0,
    "colormap_name": "coolwarm",  # 蓝-白-红发散色图
}

# ============================================================================
# 工具函数
# ============================================================================

def get_time_color(step):
    """返回给定时间步的颜色（蓝→灰→红渐变）"""
    if step in COLORS_TIMESTEPS:
        return COLORS_TIMESTEPS[step]
    steps = np.array(list(COLORS_TIMESTEPS.keys()))
    from matplotlib.colors import to_rgb
    colors_rgb = np.array([to_rgb(c) for c in COLORS_TIMESTEPS.values()])
    idx = np.searchsorted(steps, step)
    if idx == 0:
        return COLORS_TIMESTEPS[steps[0]]
    if idx >= len(steps):
        return COLORS_TIMESTEPS[steps[-1]]
    lo, hi = steps[idx - 1], steps[idx]
    t = (step - lo) / (hi - lo) if hi > lo else 0
    rgb = colors_rgb[idx - 1] * (1 - t) + colors_rgb[idx] * t
    from matplotlib.colors import to_hex
    return to_hex(rgb)


def apply_style(ax, title="", xlabel="", ylabel="", grid=True):
    """统一应用极简图表样式"""
    ax.set_facecolor(WHITE)
    if title:
        ax.set_title(title, fontweight="bold", color=BLACK)
    if xlabel:
        ax.set_xlabel(xlabel, color=GRAY_600)
    if ylabel:
        ax.set_ylabel(ylabel, color=GRAY_600)
    if grid:
        ax.grid(True, alpha=0.6, color=GRAY_200, linestyle="-", linewidth=0.5)
    ax.tick_params(colors=GRAY_500)
    for spine in ax.spines.values():
        spine.set_color(GRAY_300)
        spine.set_linewidth(0.8)
    return ax


print(f"[OK] Config v2 loaded")
print(f"  Style: Minimal B&W + Blue/Red")
print(f"  Data: {GRID_SIZE}^3 grid, {N_TIMESTEPS} steps")
