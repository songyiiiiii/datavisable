# 宇宙演化探索器 — 集成可视分析面板技术报告

## 1. 系统架构

系统采用 **前后端分离 + 离线预处理** 架构：

```
Nyx 128³ .dat (100 时间步)
    │
    ├── Python 预处理管线 ──────────────────────────┐
    │   • Hessian 特征分析 → 骨架/节点提取           │
    │   • 密度梯度计算 → Phase Portrait 相图         │
    │   • T-web 分类 → 转移矩阵 / 桑基图              │
    │   • 密度场 → 形态景观图 (3D terrain)            │
    │   • 体渲染 → PyVista/VTK GPU 离屏渲染          │
    │   • 图结构 → 网络拓扑 JSON                      │
    │                                                │
    └── React 前端仪表盘 ───────────────────────────┘
        • 布局: Tailwind CSS 暗色主题 (#09080D)
        • 3D: React Three Fiber (粒子云/网络拓扑/切片预览)
        • 2D: ECharts (直方图/桑基图/转移矩阵)
        • 渲染: PNG 嵌入 (体渲染/骨架/时间轮/相图/景观图)
```

**技术栈**: React 18 + Vite + Tailwind CSS + ECharts 5 + Three.js (R3F/Drei) + Python (NumPy/SciPy/PyVista/Matplotlib/Plotly)

---

## 2. 面板布局设计

仪表盘采用 CSS Flexbox 九宫格式分区：

| 区域 | 尺寸 | 核心内容 | 交互 |
|------|------|----------|------|
| **Header** | 42px | 时间步显示、密度色条 | 步进按钮 |
| **左上** | 370px × 300px | 3D 粒子云 (R3F Points + Additive Blending) | 旋转/缩放 |
| **左中** | 370px 自适应 | 密度分布直方图 (ECharts Bar + Brush) | 拖拽刷选 |
| **左下** | 370px 自适应 | 结构成分演化 (Recharts 堆叠面积图) | 悬停提示 |
| **中央上** | flex-1 | 体渲染 GPU (PyVista 8 层等值面离屏渲染) | 进度条切换 |
| **中央下** | 25% | 三相切片 (XY/XZ/YZ) | 点击放大 |
| **右上** | 370px | 形态景观图 (matplotlib 3D surface) + 相图 + 时间轮 (Plotly) | 悬停放大 |
| **底部** | 400px | 桑基图 (ECharts) + 状态转移矩阵 (ECharts heatmap) | — |
| **时间线** | 100px | 100 帧缩略图横排 | 点击跳转 |

---

## 3. 可视化技术详解

### 3.1 体渲染 (Volume Rendering)

采用 **PyVista 离屏渲染**，每帧生成 900×700 PNG。渲染管线包含 8 层半透明等值面 (isosurface)，密度阈值为 [8.0, 8.6, 9.1, 9.7, 10.3, 10.9, 11.8, 14.0] ln(ρ)。颜色映射使用 6 段发散色阶：深海军蓝 (#0D2659) → 蓝绿 (#2E8CAD) → 翠绿 (#38B894) → 紫 (#8073B8) → 红 (#EB4747) → 亮金 (#FFD940)。不透明度从 0.06 (低密度空洞) 到 0.68 (高密度核心) 递增。相机位置 (300, 280, 260)，焦点 (64, 64, 64)。每帧嵌入三个正交切片平面 (coolwarm colormap) 和白色十字准线。

### 3.2 三维粒子云

基于 **React Three Fiber (R3F)** 实现。从 128³ 数据集中随机采样 8000 个体素，使用 `THREE.Points` + `BufferGeometry` + `AdditiveBlending` 构建。每个粒子位置映射到 (x, y, z) 坐标，颜色由密度值决定：低密度 (#0D4DF2) → 高密度 (#FF260D)。64×64 径向渐变纹理赋予粒子发光效果。OrbitControls 提供旋转、缩放交互。与直方图刷选联动：选择区间后粒子云实时过滤显示。

### 3.3 时间轮 (TimeWheel)

使用 **Plotly** 生成 SVG，完全复刻原始 Python `fig_timewheel()` 算法。每个时间步形成 10 边形"统计指纹"，10 个指标为：Void%、Peak%、Kurtosis、Skewness、IQR、Std、Mean、Min、Max、P99-P01 Spread。数据经 Min-Max 归一化至 [1, 9]。100 条历史轨迹以半透明 (α=0.28) 绘制，当前步以完全不透明高亮 (α=1.0, lw=3.5)。中心水平轴标记演化进度 (t=0→99)。色阶：早期蓝绿 → 中期紫 → 晚期红金。

### 3.4 桑基图 + 转移矩阵

基于真实 Nyx 数据的 **T-web 分类** (密度阈值法): Void (<8.5), Sheet (8.5–9.7), Filament (9.7–11.2), Node (≥11.2)。对 t=0→t=99 随机采样 200K 体素，计算 4×4 转移矩阵。核心发现：

| 从 \ 到 | Void | Sheet | Filament | Node |
|---------|------|-------|----------|------|
| Void | **74.8%** | 24.9% | 0.3% | 0.0% |
| Sheet | 3.8% | **88.3%** | 7.9% | 0.0% |
| Filament | 0.2% | 48.0% | **51.0%** | 0.8% |
| Node | 0.0% | 2.8% | 64.2% | **33.0%** |

桑基图使用 ECharts Sankey 渲染，转移矩阵使用 ECharts Heatmap + ResizeObserver 自适应。配色与相图统一（珍珠水蓝→黄昏深蓝→极深海军蓝）。

### 3.5 Phase Portrait (密度-梯度相图)

利用密度梯度 |∇ρ| 与暗物质速度场的数学相关性，计算 128³ 体数据的 3D Sobel 梯度幅值。随机采样 50K 体素，使用 matplotlib hexbin 绘制二维对数密度分布图。色阶：珍珠水蓝 (#75CBD1) → 黄昏深蓝 (#3E5BA3) → 极深海军蓝 (#0C0D45)。标注四个特征区域：空洞 (低ρ低∇ρ)、纤维 (中ρ中∇ρ)、团簇边缘 (高ρ高∇ρ)、核心 (极高ρ低∇ρ)。100 帧全部预渲染。

### 3.6 网络拓扑 (Cosmic Web Graph)

基于 **Hessian 矩阵特征值分析** (T-web 分类) 提取宇宙网节点。计算 3×3 Hessian 矩阵的解析特征值 (向量化 Cardano 三角解)，将体素分为 Void (0 负特征值)、Sheet (1)、Filament (2)、Node (3)。对 Node 区域做 3D 连通分量标记，取体积最大的 Top 200 节点。边检测沿 Bresenham 3D 线段计算纤维占比 (>25%)，每节点保留最强 6 条连接。R3F 渲染：节点为发光球体 (亮蓝绿→亮玫红渐变色阶)，边为白色半透明 Bezier 管状曲线，高纤维占比边加粗加亮。100 步全部导出为 JSON。

### 3.7 形态景观图 (Morphological Landscape)

从 128³ 数据中提取三个正交截面 (XY/Z=64, XZ/Y=64, YZ/X=64)，使用 matplotlib 3D `plot_surface` 将密度映射为高度 (Z 轴)。viridis 色阶着色，LightSource 光照 (315° azimuth, 45° altitude)，白色线框覆盖。3×1 竖向排列，坐标轴和面板边框设为透明。相机距离 5.8，仰角 25°。100 帧全部预渲染。

---

## 4. 交互联动机制

- **直方图刷选 ↔ 粒子云**: ECharts brush 事件 → `brushRange` 状态更新 → ParticlePanel 过滤粒子
- **时间滑块 ↔ 全面板**: `timeStep` 状态驱动 8 个独立组件同步更新 (体渲染/切片/骨架/时间轮/景观图/相图/网络拓扑/缩略图)
- **动画播放**: setInterval 120ms 触发 `nextStep` (≈8 FPS)
- **面板宽度**: 原生 mousedown/move/up 事件监听，左右面板 250–550px 可调
- **切片放大**: 点击切片缩略图 → 70vw×70vh 固定弹窗

---

## 5. 数据管线性能

| 处理步骤 | 单帧耗时 | 100 帧总耗时 |
|----------|---------|-------------|
| 体渲染 (PyVista) | ~2.0s | ~3.5 min |
| 切片导出 (NumPy+PIL) | ~0.01s | ~1 min |
| 骨架渲染 (PyVista) | ~1.8s | ~3 min |
| 网络提取 (Hessian+连通分量) | ~8s | ~13 min |
| 相图 (matplotlib hexbin) | ~0.5s | ~1 min |
| 形态景观 (matplotlib 3D) | ~1.5s | ~2.5 min |
| 时间轮 (Plotly) | ~3s | ~5 min |
| **总计** | — | **~30 min** |

所有预渲染结果以 PNG/JSON 格式静态托管，前端通过 `<img>` 标签直接加载，响应延迟 < 50ms。
