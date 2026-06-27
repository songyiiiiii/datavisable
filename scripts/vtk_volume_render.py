"""
vtk_volume_render.py — VTK GPU Ray-Casting 体渲染 (ParaView 同款引擎)
不需要安装 ParaView, 使用系统已有的 VTK/PyVista 依赖
"""
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import OUTPUT_DIR, GRID_SIZE, DENSITY_RANGE
from data_loader import load_timestep

OUT = os.path.join(OUTPUT_DIR, "paraview_renders")
os.makedirs(OUT, exist_ok=True)
STEP = 73

def render_vtk_volume(step=STEP):
    print(f"VTK GPU Volume Rendering — t={step}")
    data_3d = load_timestep(step).astype(np.float32)

    # ── 转 C-order (X fastest) ──
    data_xyz = np.ascontiguousarray(np.transpose(data_3d, (2, 1, 0)))
    flat = data_xyz.ravel(order='C')

    # ── vtkImageData ──
    img = vtk.vtkImageData()
    img.SetDimensions(GRID_SIZE, GRID_SIZE, GRID_SIZE)
    img.SetSpacing(1, 1, 1)
    img.SetOrigin(0, 0, 0)

    arr = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_FLOAT)
    arr.SetName("density")
    img.GetPointData().SetScalars(arr)

    # ── 传递函数: 不透明度 ──
    otf = vtk.vtkPiecewiseFunction()
    otf.AddPoint(7.5,  0.0)
    otf.AddPoint(8.3,  0.02)
    otf.AddPoint(9.0,  0.05)
    otf.AddPoint(9.8,  0.10)
    otf.AddPoint(10.8, 0.22)
    otf.AddPoint(11.8, 0.40)
    otf.AddPoint(13.0, 0.65)
    otf.AddPoint(14.5, 0.88)

    # ── 传递函数: 颜色 (复刻网站配色) ──
    ctf = vtk.vtkColorTransferFunction()
    ctf.AddRGBPoint(7.5,  0.05, 0.15, 0.35)   # 深海军蓝
    ctf.AddRGBPoint(8.5,  0.18, 0.55, 0.68)   # 蓝绿/青
    ctf.AddRGBPoint(9.7,  0.22, 0.72, 0.58)   # 翠绿
    ctf.AddRGBPoint(10.8, 0.50, 0.45, 0.72)   # 紫
    ctf.AddRGBPoint(12.5, 0.92, 0.28, 0.28)   # 红
    ctf.AddRGBPoint(14.5, 1.00, 0.85, 0.25)   # 亮金

    # ── GPU 体渲染 Mapper ──
    volume_prop = vtk.vtkVolumeProperty()
    volume_prop.SetColor(ctf)
    volume_prop.SetScalarOpacity(otf)
    volume_prop.ShadeOn()
    volume_prop.SetInterpolationTypeToLinear()
    volume_prop.SetAmbient(0.25)
    volume_prop.SetDiffuse(0.7)
    volume_prop.SetSpecular(0.3)
    volume_prop.SetSpecularPower(18)

    mapper = vtk.vtkGPUVolumeRayCastMapper()
    mapper.SetInputData(img)
    mapper.SetBlendModeToComposite()

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volume_prop)

    # ── 渲染器 ──
    renderer = vtk.vtkRenderer()
    renderer.AddVolume(volume)
    renderer.SetBackground(0.035, 0.031, 0.051)  # #09080D

    # ── 相机 ──
    camera = renderer.GetActiveCamera()
    camera.SetPosition(300, 280, 260)
    camera.SetFocalPoint(64, 64, 64)
    camera.SetViewUp(0, 0, 1)
    camera.SetClippingRange(1, 1000)

    # ── 窗口 ──
    rw = vtk.vtkRenderWindow()
    rw.SetSize(1200, 900)
    rw.SetOffScreenRendering(1)
    rw.AddRenderer(renderer)

    # ── 渲染 ──
    rw.Render()

    # ── 导出 PNG ──
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(rw)
    w2i.Update()

    writer = vtk.vtkPNGWriter()
    out_path = os.path.join(OUT, f"vtk_volume_t{step:04d}.png")
    writer.SetFileName(out_path)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

    print(f"Done -> {out_path}")
    return out_path

if __name__ == "__main__":
    render_vtk_volume(STEP)
