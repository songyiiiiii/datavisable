# -*- coding: utf-8 -*-
"""
Nyx 宇宙学模拟数据集 — 数据加载模块
=====================================
读取小端字节序 float32、列优先（Fortran 顺序）的 Nyx .dat 文件。
"""

import numpy as np
import os
from glob import glob
from tqdm import tqdm

from config import DATA_DIR, GRID_SIZE, N_TIMESTEPS, N_VOXELS, OUTPUT_DIR

# ============================================================================
# 核心读取函数
# ============================================================================

def read_nyx_dat(filepath):
    """
    读取单个 Nyx .dat 文件。

    参数
    ----------
    filepath : str
        .dat 文件的路径

    返回
    -------
    numpy.ndarray, shape (128, 128, 128), dtype float32
        3D 密度场（对数密度，ln ρ），
        列优先顺序（Z → Y → X，Fortran 顺序）
    """
    raw = np.fromfile(filepath, dtype="<f4")  # 小端 float32
    if raw.size != N_VOXELS:
        raise ValueError(
            f"预期 {N_VOXELS} 个值 ({GRID_SIZE}³)，但文件包含 {raw.size} 个值：{filepath}"
        )
    # 列优先 (Fortran) 顺序：第一个索引 = Z，最后一个索引 = X
    data_3d = raw.reshape((GRID_SIZE, GRID_SIZE, GRID_SIZE), order="F")
    return data_3d


def load_timestep(step):
    """
    按索引加载时间步。

    参数
    ----------
    step : int
        时间步索引（0–99）

    返回
    -------
    numpy.ndarray, shape (128, 128, 128)
    """
    fname = f"{step:04d}.dat"
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"时间步 {step} 不存在：{path}")
    return read_nyx_dat(path)


def load_all_timesteps(verbose=True):
    """
    将所有 100 个时间步加载到内存（约 800 MiB）。

    返回
    -------
    numpy.ndarray, shape (100, 128, 128, 128), dtype float32
    """
    all_data = np.zeros((N_TIMESTEPS, GRID_SIZE, GRID_SIZE, GRID_SIZE), dtype=np.float32)
    rng = range(N_TIMESTEPS)
    if verbose:
        rng = tqdm(rng, desc="正在加载所有时间步", unit="step")
    for i in rng:
        all_data[i] = load_timestep(i)
    return all_data


def get_available_steps():
    """返回可用时间步的排序列表。"""
    pattern = os.path.join(DATA_DIR, "*.dat")
    files = glob(pattern)
    steps = sorted([int(os.path.splitext(os.path.basename(f))[0]) for f in files])
    return steps


# ============================================================================
# 统计工具
# ============================================================================

def compute_statistics(data_3d):
    """
    计算 3D 密度场的综合统计量。

    返回
    -------
    dict，包含 min、max、mean、std、median 和百分位数
    """
    flat = data_3d.ravel()
    p01, p05, p25, p50, p75, p95, p99 = np.percentile(flat, [1, 5, 25, 50, 75, 95, 99])

    # 偏度与峰度（使用 Fisher 定义：正态分布时偏度=0，峰度=0）
    from scipy.stats import skew, kurtosis
    skew_val = skew(flat)
    kurt_val = kurtosis(flat)  # 超额峰度

    return {
        "min": flat.min(),
        "max": flat.max(),
        "mean": flat.mean(),
        "std": flat.std(),
        "median": p50,
        "p01": p01, "p05": p05, "p25": p25,
        "p50": p50, "p75": p75, "p95": p95, "p99": p99,
        "iqr": p75 - p25,
        "spread_99_01": p99 - p01,
        "skewness": skew_val,
        "kurtosis": kurt_val,
    }


def compute_density_histogram(data_3d, bins=128, range_=(7.5, 15.0)):
    """
    计算密度直方图。

    返回
    -------
    hist : 计数
    edges : 区间边界
    centers : 区间中心
    """
    flat = data_3d.ravel()
    hist, edges = np.histogram(flat, bins=bins, range=range_)
    centers = (edges[:-1] + edges[1:]) / 2
    return hist, edges, centers


# ============================================================================
# 密度过滤（用于任务 4 刷选）
# ============================================================================

def create_density_mask(data_3d, lo, hi):
    """
    为落在密度区间 [lo, hi] 内的体素创建布尔掩码。

    返回
    -------
    与 data_3d 形状相同的布尔掩码
    """
    return (data_3d >= lo) & (data_3d <= hi)


def filter_voxels(data_3d, lo, hi):
    """
    返回密度在 [lo, hi] 内的所有体素坐标。

    返回
    -------
    coords : (N, 3) 数组，包含 (z, y, x) 索引
    values : (N,)   数组，包含密度值
    """
    mask = create_density_mask(data_3d, lo, hi)
    indices = np.argwhere(mask)  # (N, 3) -> (z, y, x)
    values = data_3d[mask]
    return indices, values


# ============================================================================
# 缓存
# ============================================================================

# 内存缓存，避免重复加载
_cache = {}

def get_cached(step):
    """获取缓存的时间步，必要时加载。"""
    if step not in _cache:
        _cache[step] = load_timestep(step)
    return _cache[step]


print("[OK] Data loader ready")
print(f"  Data dir: {DATA_DIR}")
print(f"  Available steps: {len(get_available_steps())} ({get_available_steps()[0]}–{get_available_steps()[-1]})")
