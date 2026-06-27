"""
export_volume_texture.py — 导出 Nyx 密度场为 WebGL 体渲染 3D 纹理
=================================================================
输出: output/webgl/
  volume_t064.raw       — 64³ Float32 密度场 (二进制)
  volume_t128.raw       — 128³ Float32 密度场
  volume_meta.json      — 元信息 (尺寸, 范围, timestep)
  slices_t064/          — 64张PNG切片 (Z轴), 供三向切片参考

用法: python export_volume_texture.py [timestep] [--size 64|128]
"""

import numpy as np
import os, sys, json, struct
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

def export_step(step=73, size=64):
    print(f"Exporting Nyx Volume Texture — t={step}, size={size}^3")
    print("=" * 60)

    # 加载
    data = load_timestep(step).astype(np.float32)
    print(f"  Loaded: {data.shape}, range [{data.min():.3f}, {data.max():.3f}]")

    # 降采样
    if size < 128:
        ss = 128 // size
        data_sub = data[::ss, ::ss, ::ss].copy()
    else:
        data_sub = data.copy()

    print(f"  Downsampled: {data_sub.shape}")

    # ZYX (F-order) → XYZ (C-order) 转置使 WebGL XYZ 直接索引
    data_xyz = np.ascontiguousarray(np.transpose(data_sub, (2, 1, 0)))

    out_dir = os.path.join(OUTPUT_DIR, "webgl")
    os.makedirs(out_dir, exist_ok=True)

    # 写 raw binary
    raw_path = os.path.join(out_dir, f"volume_t{size:03d}_step{step:03d}.raw")
    data_xyz.tofile(raw_path)
    print(f"  -> {raw_path} ({os.path.getsize(raw_path):,} bytes)")

    # 元信息 JSON
    meta = {
        "step": step,
        "size": size,
        "densityRange": [float(data_sub.min()), float(data_sub.max())],
        "globalRange": list(DENSITY_RANGE),
        "format": "float32",
        "byteOrder": "little",
        "axes": "XYZ (C-order)",
    }
    meta_path = os.path.join(out_dir, f"volume_meta_t{step:03d}.json")
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"  → {meta_path}")

    # 导出一组 PNG 切片供静态参考
    slices_dir = os.path.join(out_dir, f"slices_t{step:03d}")
    os.makedirs(slices_dir, exist_ok=True)
    vmin, vmax = DENSITY_RANGE
    for z in range(0, size, max(1, size // 16)):
        slice_xy = data_sub[z, :, :]  # Z 切片 (F-order)
        # 映射到 0-255
        img_data = np.clip((slice_xy - vmin) / (vmax - vmin) * 255, 0, 255).astype(np.uint8)
        # Coolwarm 色映射
        r = np.clip(2 * img_data.astype(float)/255 - 1, 0, 1)
        b = np.clip(1 - 2 * img_data.astype(float)/255, 0, 1)
        g = 1 - r - b
        rgb = np.stack([r, g, b], axis=-1)
        rgba = np.dstack([(rgb*255).astype(np.uint8), np.full_like(img_data, 255)])
        img = Image.fromarray(rgba, 'RGBA')
        img.save(os.path.join(slices_dir, f"slice_z{z:03d}.png"))
    print(f"  → {slices_dir}/ ({len(os.listdir(slices_dir))} PNGs)")

    print("\nDone. Copy output/webgl/ to React public/data/")
    return raw_path, meta_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('step', nargs='?', type=int, default=73)
    parser.add_argument('--size', type=int, default=64)
    args = parser.parse_args()
    export_step(args.step, args.size)
