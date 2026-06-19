# Nyx Cosmic Density — Visual Analytics

> 基于 Nyx 宇宙学模拟数据的交互式可视分析系统  
> Interactive visual analytics of Nyx cosmological simulation density fields  
> **100 时间步 × 128³ 体素 × 5 任务 × 统一白底蓝灰红配色**

---

## 数据集

100 个时间步的 Nyx 气体密度场，128³ 体素，float32 小端字节序，列优先（Fortran 顺序：Z→Y→X）存储。物理量为气体密度自然对数 ln(ρ)，值范围约 7.75–14.45，跨越约 3 个数量级线性空间。

**数据量**：100 × 128³ × 4 字节 ≈ 800MB（原始 `.dat` 文件），不纳入版本控制。

### 读取方式

```python
import numpy as np
raw = np.fromfile("Nyx/0099.dat", dtype="<f4")           # 小端 float32
data_3d = raw.reshape((128, 128, 128), order='F')         # Fortran 列优先 (Z,Y,X)
```

---

## 项目结构

```
datavisable/
├── config.py                 # 全局配置（配色方案、路径常量、传递函数参数）
├── data_loader.py            # 数据读取模块（.dat → NumPy 3D 数组）
├── app.py                    # Dash Web 仪表盘入口
├── desktop_app.py            # 🆕 桌面集成面板（推荐使用，无浏览器依赖）
├── start.bat                 # Windows 一键启动脚本
├── readme.md                 # 本文档
├── 作业原题.md                # Nyx 大作业原始题目
│
├── src/                      # 源代码（按任务组织）
│   ├── process_data.py       # 数据处理管道（原始 → 二级数据）
│   ├── task1/                # 任务1：体渲染
│   │   ├── task1_volume_rendering.py    # 等值面渲染脚本
│   │   └── task1_explorer.py           # 独立 3D 交互窗口 (PyVista)
│   ├── task2/                # 任务2：演化特征分析
│   │   └── task2_evolution_analysis.py
│   ├── task3/                # 任务3：直方图时序追踪
│   │   └── task3_statistical_tracking.py
│   ├── task4/                # 任务4：相空间刷选仪表盘
│   │   ├── task4_dashboard.py
│   │   └── task4_generate_figs.py
│   ├── task5/                # 任务5：TimeWheel + 层次可视化
│   │   └── task5_timewheel.py
│   └── extra/                # 附加可视化
│       ├── task_icicle_dendro.py     # 冰柱图 + 树状图 + 流动矩阵
│       └── gen_report_tables.py      # 技术报告表格生成
│
├── processed/                # 二级数据产品（8 类，可直接分析）
│   ├── README.md             # 数据使用说明
│   ├── global_statistics.json / .csv
│   ├── histogram_matrix.npy / histogram_derivative.npy
│   ├── category_fractions.csv
│   ├── track_data.npy / track_summary.json
│   ├── subsampled_32.npy
│   └── evolution_summary.json
│
├── report/                   # 技术报告（Markdown）
│   ├── data_description.md   # 统一数据描述（处理平台/原则/分类体系）
│   ├── task1_report.md       # 任务1：体渲染 + 传递函数 + 光照
│   ├── task1_code_index.md   # 任务1：关键代码位置 + 算法索引
│   ├── task2_report.md       # 任务2：演化特征分析
│   ├── task3_report.md       # 任务3：直方图时序追踪
│   └── task4_report.md       # 任务4：相空间刷选分析
│
├── output/                   # 渲染输出
│   ├── task1/                # 100 帧等值面 PNG + 8s 视频
│   │   ├── layer_composite_t0000.png ~ t0099.png
│   │   └── nyx_100frames_8s.mp4
│   ├── task2/                # 5 张演化分析图
│   ├── task3/                # 5 张直方图追踪图
│   ├── task4/                # 5 张刷选分析图
│   ├── task5/                # TimeWheel 螺旋图 + 旋转视图
│   ├── icicle_dendro/        # 冰柱图 + 树状图 + 流动矩阵
│   └── report_tables/        # 14 张技术报告表格图
│
└── Nyx/                      # 原始数据（.gitignore）
    ├── 0000.dat ~ 0099.dat
```

---

## 快速启动

### 安装依赖

```bash
pip install numpy matplotlib scipy pyvista plotly dash dash-bootstrap-components tqdm
```

### 桌面集成面板（推荐）

```bash
python desktop_app.py
```

弹出原生窗口，包含全部 5 个任务的图表：

```
┌──────────┬──────────────────────┬──────────────┐
│ TimeWheel│  3D Render (CENTER)  │  Sparklines  │
│  径向统计 │  100帧等值面渲染      │  σ + mean    │
├──────────┴──────────────────────┴──────────────┤
│  Category Streamgraph (密度分类河流图)         │
├──────────────────────┬─────────────────────────┤
│  Brush Histogram     │  3D Particles (linked)  │
│  直方图拖拽刷选        │  空间粒子联动            │
├──────────────────────┴─────────────────────────┤
│  ──Time Slider 0-99── [Play] t=42 ──Status──│
└────────────────────────────────────────────────┘
```

- 拖拽直方图框选密度区间 → 右侧 3D 粒子图实时联动
- 时间滑块驱动全窗口 6 个子图
- 无浏览器、无服务器、无端口冲突

### Web 仪表盘

```bash
python app.py
# → 浏览器打开 http://127.0.0.1:<port>
```

### 一键启动 (Windows)

双击 `start.bat`

---

## 五个任务

| # | 任务 | 技术栈 | 产出 |
|---|------|--------|------|
| 1 | **体数据渲染** | PyVista 8层等值面 + Blinn-Phong 光照，1.6x 视角，100 帧 | `output/task1/` 100 PNG + 8s MP4 |
| 2 | **演化特征分析** | 统计指标体系（μ/σ/γ₁/γ₂/IQR/百分位），五图协同 | `output/task2/` 5 张 PNG |
| 3 | **直方图时序追踪** | 100 步演化热力图、时间导数、FWHM 追踪、山脊图 | `output/task3/` 5 张 PNG |
| 4 | **相空间刷选** | 直方图框选 ↔ 3D 粒子联动，统计↔空间双向映射 | `output/task4/` 5 张 PNG |
| 5 | **TimeWheel + 层次可视化** | 径向统计演化网络、八叉树冰柱图、密度流动矩阵 | `output/task5/` + `icicle_dendro/` |

---

## 二级数据产品

原始数据经 `src/process_data.py` 一次性处理，生成 8 类可复用数据：

| 数据文件 | 格式 | 维度 | 说明 |
|---------|------|------|------|
| `global_statistics.json` | JSON | 100 条 | 每步完整统计（μ/σ/γ₁/γ₂/百分位/空洞峰值占比） |
| `global_statistics.csv` | CSV | 100 行 | 同上表格格式，可直接导入 Excel/R/Python |
| `histogram_matrix.npy` | NumPy | 100×128 | 全时间步密度直方图矩阵 |
| `histogram_derivative.npy` | NumPy | 100×128 | 直方图时间导数 dH/dt（质量流动方向与速率） |
| `category_fractions.csv` | CSV | 100×11 | 10 类密度区间 × 100 步体积占比 |
| `track_data.npy` | NumPy | 100×5000 | 5000 体素跨时间密度追踪 |
| `subsampled_32.npy` | NumPy | 100×32³ | 4×子采样快速 3D 预览 |
| `evolution_summary.json` | JSON | — | 核心演化指标摘要 |

### 密度分类体系（10 类）

| 类别 | ln(ρ) 范围 | 颜色 | 物理含义 |
|------|-----------|------|---------|
| deep_void | 7.5–7.8 | `#071840` | 极端低密度空洞 |
| void | 7.8–8.2 | `#1A4A7A` | 宇宙空洞主体 |
| near_void | 8.2–8.6 | `#2166AC` | 空洞边界过渡区 |
| sub_filament | 8.6–9.2 | `#4393C3` | 纤维-空洞界面 |
| cool_filament | 9.2–9.8 | `#8899AA` | 冷纤维网骨架 |
| warm_filament | 9.8–10.5 | `#AABBAA` | 暖纤维-团簇过渡 |
| proto_cluster | 10.5–11.2 | `#F4A582` | 原团簇引力坍缩区 |
| cluster_halo | 11.2–12.0 | `#D6604D` | 暗物质晕外围 |
| cluster_core | 12.0–13.0 | `#B2182B` | 致密气体团簇核心 |
| extreme_peak | 13.0–15.0 | `#6B0015` | 最致密结构 |

---

## 数据处理管道

```bash
python src/process_data.py
```

8 步流程：加载 100 步 → 全局统计 → 直方图矩阵 → 分类占比 → 时间导数 → 体素追踪 → 子采样 → 演化摘要。

---

## 配色方案

全项目统一 **白底 + 蓝灰红** 渐变色板：

| 色阶 | 颜色 | 色值 | 含义 |
|------|------|------|------|
| 深蓝 | `#1A4A7A` | 空洞/早期宇宙 |
| 中蓝 | `#2166AC` | 近空洞/纤维过渡 |
| 浅蓝 | `#4393C3` | 亚纤维 |
| 灰色 | `#666666` / `#999999` | 纤维网骨架 |
| 浅红 | `#D6604D` / `#F4A582` | 团簇晕/原团簇 |
| 红色 | `#B2182B` | 团簇核心/晚期宇宙 |
| 深红 | `#8B1A2B` / `#6B0015` | 极端峰 |

- 背景色：`#FFFFFF`（纯白）
- 网格线：`#E8E8E8`（浅灰）
- 文字色：`#1A1A1A`（标题）/ `#666666`（正文）/ `#999999`（辅助）

---

## 核心发现

| 指标 | t=0 | t=99 | 变化 | 含义 |
|------|-----|------|------|------|
| σ（标准差） | 0.432 | 0.498 | **+15.4%** | 团块化加剧 |
| IQR | 0.535 | 0.625 | **+16.7%** | 密度离散度上升 |
| P99−P01 跨度 | 2.098 | 2.414 | **+15.1%** | 两极分化 |
| 空洞占比 (ln<8.5) | 0.31% | 2.99% | **~10×** | 空洞体积扩张 |
| 最小值 | 7.984 | 7.753 | −0.231 | 空洞持续加深 |
| 最大值 | 13.843 | 14.449 | +0.606 | 团簇峰值增强 |
| 分布模式 | 9.404 | 9.229 | −0.176 | 典型密度向低端偏移 |
| FWHM | 0.820 | 0.938 | **+14.3%** | 分布显著展宽 |

**三阶段演化模型**：
- **Phase I (t=0–30)**：线性增长期，窄峰高中心，初始引力不稳定性
- **Phase II (t=30–70)**：加速演化期，峰宽化尾发育，非线性坍缩启动
- **Phase III (t=70–99)**：渐近趋稳期，宽峰长尾，准平衡态逼近

---

## 平台

- **OS**: Windows 11 Home China 10.0.26100
- **CPU**: Intel Core i7 (13th Gen)
- **GPU**: NVIDIA GeForce RTX 4060 Laptop (8GB VRAM), driver 560.94
- **Python**: 3.11
- **核心库**: NumPy 1.26 / PyVista 0.48.4 / VTK 9.6.2 / Matplotlib 3.8 / Plotly 5.24 / Dash 2.18 / SciPy 1.11

---

## 许可

仅用于学术研究与教育目的。Nyx 模拟数据版权归原始模拟作者所有。
