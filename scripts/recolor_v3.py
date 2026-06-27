"""
recolor_v3.py — 色相映射: 原蓝→新蓝, 原灰→新紫, 原红→新红, 原白底→暗色背景
"""
import numpy as np
from PIL import Image, ImageDraw
import os, sys
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS

SRC = os.path.join(OUTPUT_DIR, "task1")
DST = os.path.join(OUTPUT_DIR, "volume_final")
os.makedirs(DST, exist_ok=True)

BLUE_NEW  = np.array([72, 191, 227])    # #48BFE3
PURP_NEW  = np.array([156, 137, 184])   # #9C89B8
RED_NEW   = np.array([242, 95, 92])     # #F25F5C
GOLD_NEW  = np.array([255, 224, 102])   # #FFE066
BG_COLOR  = np.array([9, 8, 13])        # #09080D

def process_one(step):
    img = Image.open(os.path.join(SRC, f"layer_composite_t{step:04d}.png")).convert("RGB")
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    lum = 0.299*r + 0.587*g + 0.114*b

    out = np.zeros((h, w, 3), dtype=np.float32)

    # 白底 → 暗色背景
    is_bg = lum > 235
    out[is_bg] = BG_COLOR.astype(np.float32)

    # 蓝色区域 (b > r, b > g) → 新蓝→新紫
    is_blue = (b > r*1.05) & (b > g*1.05) & ~is_bg
    t_blue = np.clip((b[is_blue] - r[is_blue]) / np.maximum(b[is_blue], 1), 0, 1)
    for c in range(3):
        out[:,:,c][is_blue] = BLUE_NEW[c]*(1-t_blue) + PURP_NEW[c]*t_blue

    # 红色区域 (r > g, r > b) → 新红→新金
    is_red = (r > g*1.05) & (r > b*1.05) & ~is_bg & ~is_blue
    t_red = np.clip((r[is_red] - g[is_red]) / np.maximum(r[is_red], 1), 0, 1)
    for c in range(3):
        out[:,:,c][is_red] = RED_NEW[c]*(1-t_red) + GOLD_NEW[c]*t_red

    # 灰色/中间 → 新紫色
    is_gray = (~is_bg) & (~is_blue) & (~is_red)
    out[is_gray] = PURP_NEW.astype(np.float32)

    out = np.clip(out, 0, 255).astype(np.uint8)

    pil = Image.fromarray(out, 'RGB')
    draw = ImageDraw.Draw(pil)
    cx, cy = w//2, h//2

    # 白色十字线
    for x in range(0, w, 12):
        draw.line([(x,cy),(min(x+6,w),cy)], fill=(255,255,255,110), width=1)
    for y in range(0, h, 12):
        draw.line([(cx,y),(cx,min(y+6,h))], fill=(255,255,255,110), width=1)
    # 对角线
    diag = min(w,h)//2
    for d in range(-diag, diag, 12):
        x1,y1 = cx+d, cy+d
        x2,y2 = cx+min(d+6,diag), cy+min(d+6,diag)
        draw.line([(x1,y1),(x2,y2)], fill=(255,255,255,80), width=1)
    draw.ellipse([cx-5,cy-5,cx+5,cy+5], outline=(255,255,255,150), width=2)

    pil.save(os.path.join(DST, f"t{step:04d}.png"))

if __name__ == "__main__":
    print("Remapping 100 volume renders → hue-based new palette")
    for step in tqdm(range(N_TIMESTEPS), desc="Recoloring"):
        process_one(step)
    print(f"Done -> {DST}/")
