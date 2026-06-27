"""
recolor_renders.py — 重新着色体渲染PNG: 白底 + 红白蓝 + 切片十字线
=================================================================
读取 output/task1/layer_composite_tXXXX.png
处理: 提取亮度 → RWB colormap → 白色背景 → 中心十字线
输出: output/renders_rwb/tXXXX.png (100张)

用法: python recolor_renders.py
"""

import numpy as np
from PIL import Image, ImageDraw
import os, sys
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE

SRC = os.path.join(OUTPUT_DIR, "task1")
DST = os.path.join(OUTPUT_DIR, "renders_rwb")
os.makedirs(DST, exist_ok=True)

# 中心切片位置
MID = GRID_SIZE // 2  # 64

def process_one(step):
    src_path = os.path.join(SRC, f"layer_composite_t{step:04d}.png")
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img, dtype=np.float32)

    # --- 1. 提取亮度 ---
    # 原图 RGBA, 取 RGB 亮度
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3] / 255.0
    lum = 0.299 * rgb[:,:,0] + 0.587 * rgb[:,:,1] + 0.114 * rgb[:,:,2]
    lum = lum / 255.0  # 0..1

    # --- 2. RWB colormap ---
    # 亮度 0(暗/空洞) → 蓝, 0.5(中) → 白, 1(亮/峰) → 红
    t = np.clip(lum, 0, 1)

    # 三段: blue→white→red
    r = np.where(t < 0.5, t * 2.0, 1.0)
    g = 1.0 - 2.0 * np.abs(t - 0.5)
    b = np.where(t < 0.5, 1.0, 2.0 * (1.0 - t))

    r = np.clip(r, 0, 1)
    g = np.clip(g, 0, 1)
    b = np.clip(b, 0, 1)

    # 白色背景: 低alpha/暗色区域 → 白
    bg_white = 1.0
    # alpha 混合: src over white
    blend_a = np.clip(lum * alpha[:,:,np.newaxis] * 0.85, 0, 1)
    r_out = r * blend_a[:,:,0] + bg_white * (1 - blend_a[:,:,0])
    g_out = g * blend_a[:,:,0] + bg_white * (1 - blend_a[:,:,0])
    b_out = b * blend_a[:,:,0] + bg_white * (1 - blend_a[:,:,0])

    rgb_out = np.stack([r_out, g_out, b_out], axis=-1)
    rgb_out = np.clip(rgb_out * 255, 0, 255).astype(np.uint8)

    # --- 3. 绘制切片十字线 ---
    h, w = rgb_out.shape[:2]
    pil_img = Image.fromarray(rgb_out, 'RGB')
    draw = ImageDraw.Draw(pil_img)

    # 中心十字线 (表示 Z=64 切片位置)
    cx, cy = w // 2, h // 2
    line_color = (30, 30, 30, 180)  # dark semi-transparent
    dash = [8, 6]

    # 水平线
    for x in range(0, w, 14):
        x1 = min(x + 8, w)
        draw.line([(x, cy), (x1, cy)], fill=(30,30,30), width=1)

    # 竖直线
    for y in range(0, h, 14):
        y1 = min(y + 8, h)
        draw.line([(cx, y), (cx, y1)], fill=(30,30,30), width=1)

    # --- 4. 边缘刻度标记 ---
    # X 轴标记
    for frac in [0.25, 0.5, 0.75]:
        x = int(w * frac)
        draw.line([(x, h-1), (x, h-6)], fill=(80,80,80), width=1)
        draw.line([(x, 0), (x, 5)], fill=(80,80,80), width=1)

    # Y 轴标记
    for frac in [0.25, 0.5, 0.75]:
        y = int(h * frac)
        draw.line([(w-1, y), (w-6, y)], fill=(80,80,80), width=1)
        draw.line([(0, y), (5, y)], fill=(80,80,80), width=1)

    # 保存
    dst_path = os.path.join(DST, f"t{step:04d}.png")
    pil_img.save(dst_path)
    return dst_path

if __name__ == "__main__":
    print(f"Recoloring {N_TIMESTEPS} renders: RWB + white bg + crosshairs")
    for step in tqdm(range(N_TIMESTEPS), desc="Processing"):
        process_one(step)
    print(f"Done -> {DST}/")
