# 任务一：关键代码位置与算法索引

> 项目根目录 `e:\数据可视化\`

## 一、代码文件索引

| 文件 | 用途 | 关键行 |
|------|------|--------|
| `config.py` | 全局配置（配色、路径、传递函数参数） | L129–149（`TF_CONFIG` 传递函数参数定义） |
| `data_loader.py` | 数据读取（小端 float32, Fortran 顺序） | L17–27（`read_nyx_dat` 核心读取函数） |
| `task1_pyvista_frames.py` | 离屏渲染 51 帧 PyVista 等值面图像 | 全文（128 行） |
| `app.py` | Dash Web 集成（图片展示 + TimeWheel + 滑块联动） | L44–56（`fig_task1_image` 帧查找）、L210–257（`layout_task1_merged` 布局） |

## 二、核心算法

### 算法 1：数据读取与坐标转换

**文件**：`data_loader.py` L17–27  
**函数**：`read_nyx_dat(filepath)`

```
输入: Nyx .dat 文件路径
输出: (128, 128, 128) float32 NumPy 数组，索引顺序 data[z, y, x]

步骤:
1. np.fromfile(path, dtype="<f4")    → 小端 float32 读取 → 2,097,152 个值
2. reshape((128,128,128), order='F')  → Fortran 列优先重组 (Z→Y→X)
3. 返回 data_3d
```

**坐标系转换**（用于 PyVista/VTK，期望 C 顺序 X→Y→Z）：
```python
# config.py / task1_pyvista_frames.py 等
data_xyz = np.ascontiguousarray(np.transpose(data_3d, (2, 1, 0)))
# data_xyz 索引顺序: [x, y, z]
```

### 算法 2：PyVista 网格构建 + 体素→格点插值

**文件**：`task1_pyvista_frames.py`  
**函数**：`make_grid(data_3d)`

```
输入: data_3d shape (128,128,128) Fortran 顺序
输出: PyVista ImageData，含 point_data["density"]

步骤:
1. transpose (2,1,0) → C 顺序 (x,y,z)
2. np.ascontiguousarray → 确保内存连续
3. pv.ImageData()
     .dimensions = (129,129,129)    # 128 体素 → 129 格点
     .spacing = (1,1,1)
4. cell_data["density"] = data_xyz.flatten(order="C")
5. cell_data_to_point_data()        # ★ 关键：体素→格点插值
     ↑ 不执行此步骤会导致:
       TypeError: Contour filter only works on point data
```

### 算法 3：多层等值面传递函数

**文件**：`task1_pyvista_frames.py`  
**常量**：`ISO_LEVELS`, `ISO_COLORS`, `ISO_OPACITIES`

```
参数定义:
  ISO_LEVELS    = [8.0, 8.6, 9.1, 9.7, 10.3, 10.9, 11.8, 14.0]
  ISO_COLORS[i] = 蓝→灰→红 8 级渐变
  ISO_OPACITIES  = [0.08, 0.12, 0.18, 0.25, 0.32, 0.45, 0.55, 0.70]

渲染循环:
  for i, lvl in enumerate(ISO_LEVELS):
      iso = grid.contour(isosurfaces=[lvl], scalars="density")
      if iso.n_points > 0:
          glow = (i >= 5)                    # L6-8 → emissive
          ambient = 1.0 if glow else 0.18
          diffuse = 0.25 if glow else 0.72
          plotter.add_mesh(iso,
              color=ISO_COLORS[i],
              opacity=ISO_OPACITIES[i],
              ambient=ambient, diffuse=diffuse,
              specular=0.35, specular_power=14)
```

**传递函数设计原理**：

| 密度区间 | 不透明度 | 光照模式 | 视觉意图 |
|---------|---------|---------|---------|
| ln ρ < 9.2（空洞） | 0.08–0.18 | 标准 | 半透明蓝色，"呼吸"可见 |
| 9.2–10.5（纤维） | 0.25–0.32 | 标准 | 半透明灰色，展示骨架 |
| ln ρ > 10.5（团簇） | 0.45–0.70 | emissive 发光 | 不透明红/橙，视觉焦点 |

### 算法 4：Blinn-Phong 光照模型

**实现位置**：PyVista `add_mesh()` 参数  

**数学公式**：
$$I = k_a I_a + k_d (N \cdot L) I_d + k_s (N \cdot H)^\alpha I_s$$

| 符号 | 参数名 | 标准层值 | 发光层值 |
|------|--------|---------|---------|
| $k_a$ | `ambient` | 0.18 | 1.00 |
| $k_d$ | `diffuse` | 0.72 | 0.25 |
| $k_s$ | `specular` | 0.35 | 0.35 |
| $\alpha$ | `specular_power` | 14 | 14 |
| $L$ | 光源方向 | (200, 200, 180) 斜上方 | 同 |
| $N$ | 法线 | VTK 中心差分自动计算 ∇ρ | 同 |

### 算法 5：离屏渲染流水线

**文件**：`task1_pyvista_frames.py` `render()` 函数

```
输入: step (时间步索引), data_3d
输出: PNG 文件 → output/task1/layer_composite_t{step:04d}.png

步骤:
1. make_grid(data_3d)                         → PyVista ImageData
2. pv.Plotter(off_screen=True)                → 无窗口离屏渲染
3. plotter.set_background(WHITE)               → 纯白背景
4. for each isosurface level:                  → 8 层等值面
       grid.contour(isosurfaces=[lvl])
       plotter.add_mesh(iso, ...)
5. plotter.camera_position = FIXED_CAMERA     → 固定视角
6. plotter.screenshot(output_path)             → 直接写 PNG
7. plotter.close()                             → 释放 GPU 资源
```

**性能**：单帧约 1.2 秒（8 层 contour + mesh 渲染 + PNG 编码），51 帧总耗时约 60 秒。

### 算法 6：Web 帧切换与 TimeWheel 联动

**文件**：`app.py`  
**函数**：`t1_update()`（L293–316）、`fig_timewheel()`（L69–110）

**帧查找**：
```
当前滑块值 → 最近预渲染帧:
  steps = [0, 2, 4, ..., 98, 99]              # 51 帧
  nearest = min(steps, key=lambda x: abs(x - step))
  → 加载 output/task1/layer_composite_t{nearest:04d}.png
  → base64 编码嵌入 <img>
  → 帧切换延迟 < 50ms
```

**TimeWheel 联动**：
```
同一滑块触发两个 Output:
  Output 1: t1-image-wrap  (PNG 图片)
  Output 2: t1-timewheel   (Plotly 极坐标螺旋图)
  
  TimeWheel 数据:
    - 100 步预计算 (TW_MEANS, TW_STDS, TW_THETA, TW_RADIUS)
    - 极坐标散点: r=半径(2→10), θ=角度(0→10π)
    - 颜色: get_time_color(t) 蓝→灰→红
    - 大小: 18 + std*50
    - 当前步高亮: 大标记 + 粗边框 + 文字标签
```

## 三、数据流全景

```
Nyx .dat (100 files, 8MB each, little-endian float32)
    │
    ▼ read_nyx_dat()
    │  np.fromfile(dtype="<f4") + reshape(order='F')
    ▼
(128, 128, 128) float32  [z, y, x] Fortran order
    │
    ├──▶ 统计分析 (Task 2/3)
    │    compute_statistics() → mean/std/skew/kurt/percentiles
    │    compute_density_histogram() → 128-bin histogram
    │
    ├──▶ 离屏渲染 (Task 1)
    │    transpose(2,1,0) → C order [x,y,z]
    │    → pv.ImageData → cell_data_to_point_data()
    │    → 8× contour(isosurfaces=[lvl])
    │    → add_mesh(color, opacity, Blinn-Phong)
    │    → screenshot → 51 PNG frames (task1/)
    │
    └──▶ Dash Web (app.py)
         html.Img(base64 PNG) + dcc.Slider
         + go.Scatterpolar(TimeWheel)
         → http://127.0.0.1:8051
```

## 四、关键参数速查

| 参数 | 值 | 位置 |
|------|-----|------|
| 网格分辨率 | 128³ | `config.py` L105 |
| 时间步数 | 100 | `config.py` L106 |
| 等值面层数 | 8 | `task1_pyvista_frames.py` |
| 渲染帧数 | 51（每 2 步） | `app.py` L53 |
| 相机位置 | (200,200,180)→(64,64,64) | `task1_pyvista_frames.py` |
| 输出尺寸 | 1200×800 | `task1_pyvista_frames.py` |
| DPI | 300（matplotlib）/ 离屏原生（PyVista） | `config.py` L64 |
| Web 端口 | 8051 | `app.py` L393 |
| 子采样因子（3D 交互） | 4× (128→32) | `app.py` L33 |
