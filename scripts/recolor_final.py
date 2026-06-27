"""
recolor_final.py — 亮度映射: 暗区(原图等值面)→新配色, 亮区(原图白底)→网站背景 #09080D
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

# 6-stop: 深蓝→青绿→翠绿→紫→红→金 (暖橙替换为蓝绿/青)
def build_lut():
    lut = np.zeros((256, 3), dtype=np.float32)
    stops = [
        (0.00, 0.05, 0.15, 0.35),   # #0D2659 深海军蓝 (极低密度)
        (0.20, 0.18, 0.55, 0.68),   # #2E8CAD 蓝绿/青 (纤维结构) ← 替换暖橙
        (0.45, 0.22, 0.72, 0.58),   # #38B894 翠绿 (过渡区)
        (0.65, 0.50, 0.45, 0.72),   # #8073B8 紫 (团簇外围)
        (0.85, 0.92, 0.28, 0.28),   # #EB4747 红 (高密核心)
        (1.00, 1.00, 0.85, 0.25),   # #FFD940 亮金 (极高峰值)
    ]
    for i in range(256):
        t = i / 255.0
        lo, hi = stops[0], stops[-1]
        for j in range(len(stops)-1):
            if t <= stops[j+1][0]:
                lo, hi = stops[j], stops[j+1]
                break
        s = (t - lo[0]) / max(hi[0]-lo[0], 0.001)
        lut[i] = [lo[1]+(hi[1]-lo[1])*s, lo[2]+(hi[2]-lo[2])*s, lo[3]+(hi[3]-lo[3])*s]
    return lut

LUT = build_lut()
BG = np.array([0.035, 0.031, 0.051], dtype=np.float32)  # #09080D

def process_one(step):
    img = Image.open(os.path.join(SRC, f"layer_composite_t{step:04d}.png")).convert("RGB")
    arr = np.array(img, dtype=np.float32) / 255.0
    h, w = arr.shape[:2]

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    lum = 0.299*r + 0.587*g + 0.114*b  # 0..1

    # 降低白底阈值，更多像素保留为前景
    is_bg = lum > 0.90
    # 拉伸对比度：暗区更暗，亮区更亮
    lum_boost = np.clip((lum - 0.1) / 0.85, 0, 1)
    idx = np.clip((lum_boost * 255).astype(int), 0, 255)

    out = LUT[idx]  # 全图映射
    out[is_bg] = BG  # 白底区域强制暗色

    out = np.clip(out * 255, 0, 255).astype(np.uint8)

    # 十字线
    pil = Image.fromarray(out, 'RGB')
    draw = ImageDraw.Draw(pil)
    cx, cy = w//2, h//2
    for x in range(0, w, 12):
        draw.line([(x,cy),(min(x+6,w),cy)], fill=(255,255,255,110), width=1)
    for y in range(0, h, 12):
        draw.line([(cx,y),(cx,min(y+6,h))], fill=(255,255,255,110), width=1)
    diag = min(w,h)//2
    for d in range(-diag, diag, 12):
        draw.line([(cx+d,cy+d),(cx+min(d+6,diag),cy+min(d+6,diag))], fill=(255,255,255,80), width=1)
    draw.ellipse([cx-5,cy-5,cx+5,cy+5], outline=(255,255,255,150), width=2)

    pil.save(os.path.join(DST, f"t{step:04d}.png"))

if __name__ == "__main__":
    print(f"Brightness-based remap: {N_TIMESTEPS} frames")
    for step in tqdm(range(N_TIMESTEPS), desc="Recoloring"):
        process_one(step)
    print(f"Done -> {DST}/")
