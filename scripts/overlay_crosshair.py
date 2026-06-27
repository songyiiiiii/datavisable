"""
overlay_crosshair.py — 在原 100 张体渲染 PNG 上叠加切片十字线
==============================================================
读取 output/task1/layer_composite_tXXXX.png (保留原色/比例/背景)
绘制三条切片平面十字线 → 输出 output/volume_final/tXXXX.png

3 条线分别对应 Z=64(Y切面水平线), X=64(YZ切面竖线), Y=64(XZ切面斜线/对角线)
在 2D 投影中分别表现为: 水平线, 竖直线, 45°对角线
"""

import os, sys
from PIL import Image, ImageDraw
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS

SRC = os.path.join(OUTPUT_DIR, "task1")
DST = os.path.join(OUTPUT_DIR, "volume_final")
os.makedirs(DST, exist_ok=True)

def process_one(step):
    img = Image.open(os.path.join(SRC, f"layer_composite_t{step:04d}.png"))
    w, h = img.size
    draw = ImageDraw.Draw(img, 'RGBA')

    cx, cy = w // 2, h // 2

    # ── 水平线 (Z 切片: 俯视 XY 平面) ──
    for x in range(0, w, 10):
        draw.line([(x, cy), (min(x+5, w), cy)], fill=(255,255,255,100), width=1)

    # ── 竖直线 (X 切片: 侧视 YZ 平面) ──
    for y in range(0, h, 10):
        draw.line([(cx, y), (cx, min(y+5, h))], fill=(255,255,255,100), width=1)

    # ── 对角线 (Y 切片: 侧视 XZ 平面, 在 2D 投影中近似对角) ──
    diag_len = min(w, h) // 2
    for d in range(-diag_len, diag_len, 10):
        x1, y1 = cx + d, cy + d
        x2, y2 = cx + min(d+5, diag_len), cy + min(d+5, diag_len)
        draw.line([(x1, y1), (x2, y2)], fill=(255,255,255,80), width=1)

    # ── 中心交叉点 ──
    r = 6
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(255,255,255,160), width=2)

    # ── 边缘小标记 ──
    for side in [0.25, 0.5, 0.75]:
        # 上下
        x = int(w * side)
        draw.line([(x, 0), (x, 6)], fill=(180,180,180,120), width=1)
        draw.line([(x, h-1), (x, h-7)], fill=(180,180,180,120), width=1)
        # 左右
        y = int(h * side)
        draw.line([(0, y), (6, y)], fill=(180,180,180,120), width=1)
        draw.line([(w-1, y), (w-7, y)], fill=(180,180,180,120), width=1)

    img.save(os.path.join(DST, f"t{step:04d}.png"))

if __name__ == "__main__":
    print(f"Overlaying crosshairs on {N_TIMESTEPS} existing renders...")
    for step in tqdm(range(N_TIMESTEPS), desc="Processing"):
        process_one(step)
    print(f"Done -> {DST}/")
