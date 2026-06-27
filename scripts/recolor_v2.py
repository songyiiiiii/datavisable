"""
recolor_v2.py — 将现有 100 张体渲染 PNG 重新映射为新配色
#48BFE3 低 / #9C89B8 中 / #F25F5C 高 / #FFE066 峰值
叠加白色切片十字线
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

# 新配色: low=#48BFE3, mid=#9C89B8, high=#F25F5C, peak=#FFE066
BLUE  = np.array([0.282, 0.749, 0.890])   # #48BFE3
PURP  = np.array([0.612, 0.537, 0.722])   # #9C89B8
RED   = np.array([0.949, 0.373, 0.361])   # #F25F5C
GOLD  = np.array([1.000, 0.878, 0.400])   # #FFE066
WHITE = np.array([1.0, 1.0, 1.0])

def remap_color(t):
    """t 0..1: 蓝→紫→红→金"""
    t = np.clip(t, 0, 1)
    if t < 0.33:
        s = t / 0.33
        return BLUE * (1-s) + PURP * s
    elif t < 0.66:
        s = (t - 0.33) / 0.33
        return PURP * (1-s) + RED * s
    else:
        s = (t - 0.66) / 0.34
        return RED * (1-s) + GOLD * s

COLORS = np.array([remap_color(i/255) for i in range(256)])  # lookup table

def process_one(step):
    img = Image.open(os.path.join(SRC, f"layer_composite_t{step:04d}.png")).convert("RGBA")
    arr = np.array(img, dtype=np.float32) / 255.0

    rgb = arr[:,:,:3]
    alpha = arr[:,:,3]

    # 亮度 → colormap index
    lum = 0.299*rgb[:,:,0] + 0.587*rgb[:,:,1] + 0.114*rgb[:,:,2]
    idx = np.clip((lum * 255).astype(int), 0, 255)

    # 应用新 colormap
    new_rgb = COLORS[idx]  # (H, W, 3)

    # 背景检测: 原图白/亮色区域 → 换成网站背景色 #09080D
    bg_color = np.array([0.035, 0.031, 0.051])
    is_bg = lum > 0.85  # 白底区域
    is_fg = ~is_bg

    # 前景: 原 alpha 混合; 背景: 直接换成暗色
    blend = alpha[:,:,np.newaxis] / 255.0 * 0.75
    final = new_rgb * blend + bg_color * (1 - blend)
    # 强制背景像素为暗色
    final[is_bg] = bg_color
    final = np.clip(final * 255, 0, 255).astype(np.uint8)

    pil = Image.fromarray(final, 'RGB')
    draw = ImageDraw.Draw(pil)
    w, h = pil.size
    cx, cy = w//2, h//2

    # 白色十字线
    for x in range(0, w, 12):
        draw.line([(x, cy), (min(x+6, w), cy)], fill=(255,255,255,110), width=1)
    for y in range(0, h, 12):
        draw.line([(cx, y), (cx, min(y+6, h))], fill=(255,255,255,110), width=1)
    # 对角线 (Y 切片)
    diag = min(w,h)//2
    for d in range(-diag, diag, 12):
        draw.line([(cx+d, cy+d), (cx+min(d+6,diag), cy+min(d+6,diag))], fill=(255,255,255,80), width=1)

    # 中心点
    draw.ellipse([cx-5,cy-5,cx+5,cy+5], outline=(255,255,255,150), width=2)

    pil.save(os.path.join(DST, f"t{step:04d}.png"))

if __name__ == "__main__":
    print("Remapping 100 volume renders → new cosmic palette")
    for step in tqdm(range(N_TIMESTEPS), desc="Recoloring"):
        process_one(step)
    print(f"Done -> {DST}/")
