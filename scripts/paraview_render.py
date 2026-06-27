"""
paraview_render.py — ParaView 体渲染导出脚本
=============================================
运行方式 (不需要打开 ParaView GUI):
  pvpython paraview_render.py          (ParaView Python)
  pvbatch  paraview_render.py          (无头批量渲染)
  paraview --script=paraview_render.py (GUI 模式)

如果没有 pvpython, 在 ParaView 安装目录找:
  C:\Program Files\ParaView 5.xx\bin\pvpython.exe

或直接用 conda/pip:
  conda install -c conda-forge paraview
"""

import os, sys
import numpy as np

# ── 加载 Nyx .dat ──
DATA_DIR = r"e:\数据可视化\Nyx"
OUT_DIR  = r"e:\数据可视化\output\paraview_renders"
os.makedirs(OUT_DIR, exist_ok=True)

GRID_SIZE = 128
STEP = 73  # 测试帧

# 读 Nyx raw float32, F-order (Z,Y,X)
raw = np.fromfile(os.path.join(DATA_DIR, f"{STEP:04d}.dat"), dtype="<f4")
data_zyx = raw.reshape((GRID_SIZE, GRID_SIZE, GRID_SIZE), order='F')
# 转 C-order (X,Y,Z) for VTK
data_xyz = np.ascontiguousarray(np.transpose(data_zyx, (2, 1, 0)))

# ── ParaView 管线 ──
from paraview.simple import *

# 1. 导入 numpy 数组
vtk_data = servermanager.Fetch(TrivialProducer())
# 简化写法: 用 ProgrammableSource 或先存 vti

# 2. 体渲染
volume = Volume(Input=vtk_data)
volume.Representation = 'Volume'
volumeDisplay = GetDisplayProperties(volume)
volumeDisplay.SetRepresentationType('Volume')

# 传递函数
from paraview.servermanager import CreateRenderView
tf = GetColorTransferFunction('density')
tf.ApplyPreset('Cool to Warm', True)  # 蓝→红
tf.RescaleTransferFunction(7.5, 14.5)

otf = GetOpacityTransferFunction('density')
otf.RescaleTransferFunction(7.5, 14.5)
# 低密度透明, 中密度可见, 高密度不透明
otf.Points = [7.5, 0.0, 0.5, 0.0,
              8.5, 0.03, 0.5, 0.0,
              10.0, 0.08, 0.5, 0.0,
              12.0, 0.35, 0.5, 0.0,
              14.5, 0.85, 0.5, 0.0]

# 3. 相机
view = GetActiveView()
view.CameraPosition = [300, 280, 260]
view.CameraFocalPoint = [64, 64, 64]
view.CameraViewUp = [0, 0, 1]
view.Background = [0.035, 0.031, 0.051]  # #09080D

# 4. 渲染
view.ViewSize = [1200, 900]
Render()

# 5. 导出
out_path = os.path.join(OUT_DIR, f"paraview_t{STEP:04d}.png")
SaveScreenshot(out_path, view)
print(f"Done -> {out_path}")

print("""
========================================
ParaView 渲染完成。批量 100 帧循环写法：
========================================

for step in range(100):
    # 读数据 → 更新 volume → Render → SaveScreenshot

或使用 ParaView Python State 文件 (.pvsm) 保存管线配置，
然后 pvpython 脚本加载状态文件批量处理。
""")
