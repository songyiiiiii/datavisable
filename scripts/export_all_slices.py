"""
export_all_slices.py — 批量导出 100 步的三向切片 PNG
=====================================================
为每个时间步导出 XY(中心Z), XZ(中心Y), YZ(中心X) 三张切片。
红白蓝 diverging colormap, 128×128 分辨率。

输出: output/slices/
  xy/t0000.png ... xy/t0099.png
  xz/t0000.png ... xz/t0099.png
  yz/t0000.png ... yz/t0099.png

用法: python export_all_slices.py [--start 0] [--end 99]
"""

import numpy as np
import os, sys
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, N_TIMESTEPS, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

# 原始红白蓝 diverging colormap
def apply_rwb(data_2d, vmin=7.5, vmax=14.5):
    """红白蓝映射: 低密度→蓝(#2166AC), 中→白, 高→红(#B2182B)"""
    t = np.clip((data_2d - vmin) / (vmax - vmin), 0, 1)
    # blue(0.13,0.40,0.67) → white(1,1,1) → red(0.70,0.09,0.17)
    if t.ndim == 0:
        t = np.array([t])
    r = np.where(t < 0.5, 0.13 + 1.74*t, 1.0 - 0.6*(t-0.5)*2)
    g = np.where(t < 0.5, 0.40 + 1.20*t, 1.0 - 1.82*(t-0.5)*2)
    b = np.where(t < 0.5, 0.67 + 0.66*t, 1.0 - 1.66*(t-0.5)*2)
    rgb = np.stack([r,g,b], axis=-1)
    rgb = np.clip(rgb, 0, 1)
    return (rgb * 255).astype(np.uint8)

def export_all(step_from=0, step_to=99):
    out = os.path.join(OUTPUT_DIR, "slices")
    for d in ['xy', 'xz', 'yz']:
        os.makedirs(os.path.join(out, d), exist_ok=True)

    mid = GRID_SIZE // 2  # 64

    for step in tqdm(range(step_from, step_to + 1), desc="Exporting slices"):
        data = load_timestep(step)
        # data shape: (128,128,128) F-order (Z,Y,X)
        # XY slice: data[mid_z, :, :]
        # XZ slice: data[:, mid_y, :]
        # YZ slice: data[:, :, mid_x]

        xy = data[mid, :, :]        # (128,128)
        xz = data[:, mid, :]        # (128,128)
        yz = data[:, :, mid]        # (128,128)

        for name, arr in [('xy', xy), ('xz', xz), ('yz', yz)]:
            img_data = apply_rwb(arr)
            img = Image.fromarray(img_data, 'RGB')
            img.save(os.path.join(out, name, f"t{step:04d}.png"))

    print(f"Done -> {out}/")
    print(f"  xy/: {len(os.listdir(os.path.join(out,'xy')))} PNGs")
    print(f"  xz/: {len(os.listdir(os.path.join(out,'xz')))} PNGs")
    print(f"  yz/: {len(os.listdir(os.path.join(out,'yz')))} PNGs")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--end', type=int, default=99)
    args = p.parse_args()
    export_all(args.start, args.end)
