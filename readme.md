# Nyx Cosmic Density — Visual Analytics

> 基于 Nyx 宇宙学模拟数据的交互式可视分析系统  
> Interactive visual analytics of Nyx cosmological simulation density fields

## 数据集

100 个时间步的 Nyx 气体密度场，128³ 体素，float32 小端字节序，列优先（Fortran）存储。密度值约 7.75–14.45（ln ρ），跨越约 3 个数量级。原始数据约 800MB，位于 `Nyx/` 目录（不纳入版本控制）。

### 二级数据产品

原始数据经 `process_data.py` 处理后，在 `processed/` 目录生成 8 类可直接用于可视分析的二级数据：

| 数据文件 | 格式 | 维度 | 说明 |
|---------|------|------|------|
| `global_statistics.json` | JSON | 100 条 | 每步完整统计：均值、标准差、偏度、峰度、百分位(P1/P5/P10/P25/P50/P75/P90/P95/P99)、IQR、空洞/峰值占比 |
| `global_statistics.csv` | CSV | 100 行 | 同上，表格格式，可直接导入 Excel/R/Python |
| `histogram_matrix.npy` | NumPy | 100×128 | 所有时间步的密度直方图矩阵，可直接绘制热力图 |
| `histogram_derivative.npy` | NumPy | 100×128 | 直方图时间导数 dH/dt，揭示密度质量在区间间的流动方向和速率 |
| `category_fractions.csv` | CSV | 100×11 | 10 个密度子类的体积占比随时间演化 |
| `track_data.npy` | NumPy | 100×5000 | 5000 个随机采样体素跨 100 步的密度追踪数据 |
| `subsampled_32.npy` | NumPy | 100×32³ | 4 倍子采样三维数据，用于快速 3D 预览 |
| `evolution_summary.json` | JSON | — | 核心演化指标摘要（σ +15.4%、空洞占比 10× 增长等） |

**密度分类体系**（10 类，用于 `category_fractions.csv`）：

| 类别 | ln(ρ) 范围 | 物理含义 |
|------|-----------|---------|
| deep_void | 7.5–7.8 | 极端低密度 |
| void | 7.8–8.2 | 宇宙空洞主体 |
| near_void | 8.2–8.6 | 空洞边界过渡 |
| sub_filament | 8.6–9.2 | 纤维-空洞界面 |
| cool_filament | 9.2–9.8 | 冷纤维网骨架 |
| warm_filament | 9.8–10.5 | 暖纤维-团簇过渡 |
| proto_cluster | 10.5–11.2 | 原团簇引力坍缩区 |
| cluster_halo | 11.2–12.0 | 暗物质晕外围 |
| cluster_core | 12.0–13.0 | 致密气体节点 |
| extreme_peak | 13.0–15.0 | 最致密结构 |

## 项目结构

```
├── config.py                 # 全局配置（配色、路径、参数）
├── data_loader.py            # 数据读取（.dat → numpy）
├── app.py                    # Dash Web 仪表盘（入口）
├── src/
│   ├── process_data.py       # 数据处理管道（原始→二级数据）
│   ├── task_integrated.py    # 集成桌面面板（所有任务一个窗口）
│   ├── task1/                # 体渲染
│   ├── task2/                # 演化分析
│   ├── task3/                # 直方图追踪
│   ├── task4/                # 刷选仪表盘
│   ├── task5/                # TimeWheel
│   └── extra/                # 冰柱图 + 树状图 + 表格生成
├── processed/                # 二级数据产品（处理管道输出）
├── report/                   # 技术报告（5 份 + 代码索引）
├── output/                   # 渲染输出（图表、帧、视频）
└── Nyx/                      # 原始数据（不纳入版本控制）
```

## 五个任务

| # | 任务 | 核心技术 |
|---|------|---------|
| 1 | **体数据渲染** | PyVista 多层等值面 + Blinn-Phong 光照，51 帧时间序列 |
| 2 | **演化特征分析** | 五图协同（统计面板、小提琴图、联合分布、团块化指标） |
| 3 | **直方图时序追踪** | 100 步演化热力图、时间导数、FWHM 追踪、三阶段模型 |
| 4 | **相空间刷选** | Plotly Dash 联动仪表盘，直方图框选 ↔ 3D 视图实时映射 |
| 5 | **TimeWheel + 层次可视化** | 极坐标螺旋时间轮、八叉树冰柱图、密度流动矩阵 |

## 数据处理管道

运行一次即可从原始 `.dat` 文件生成全部二级数据：

```bash
python src/process_data.py
```

处理流程（8 步）：

| 步骤 | 操作 | 输出 |
|------|------|------|
| 0 | 加载 100 步原始数据（~800MB） | 内存中的 NumPy 数组 |
| 1 | 计算每步统计量（均值/std/偏度/峰度/百分位） | `global_statistics.json` / `.csv` |
| 2 | 构建 128 区间密度直方图矩阵 | `histogram_matrix.npy` |
| 3 | 计算 10 类密度区间体积占比 | `category_fractions.csv` |
| 4 | 计算直方图时间导数（中心差分） | `histogram_derivative.npy` |
| 5 | 随机采样 5000 体素跨时间追踪 | `track_data.npy` + 追踪摘要 |
| 6 | 4 倍子采样生成 32³ 快速预览数据 | `subsampled_32.npy` |
| 7 | 生成演化摘要（三阶段模型等） | `evolution_summary.json` |

**使用示例**：

```python
import numpy as np, json

# 加载统计数据
with open('processed/global_statistics.json') as f:
    stats = json.load(f)
print(stats[0]['std'], '->', stats[99]['std'])  # 0.4318 -> 0.4983

# 加载直方图矩阵
hist = np.load('processed/histogram_matrix.npy')       # (100, 128)
deriv = np.load('processed/histogram_derivative.npy')   # (100, 128)

# 加载子采样三维数据
sub = np.load('processed/subsampled_32.npy')           # (100, 32, 32, 32)

# 加载体素追踪
track = np.load('processed/track_data.npy')            # (100, 5000)
```

## 快速启动

```bash
# 安装依赖
pip install numpy matplotlib pyvista plotly dash dash-bootstrap-components scipy tqdm

# Web 仪表盘（Task 1+5 集成、Task 2、Task 3、Task 4）
python app.py
# → 浏览器打开 http://127.0.0.1:8051

# 独立 3D 交互窗口（鼠标旋转/缩放宇宙方块）
python task1_explorer.py

# 集成桌面面板（所有任务一个窗口）
python task_integrated.py

# 生成技术报告表格
python gen_report_tables.py
```

## 配色方案

统一白底 + 蓝灰红渐变色板，感知均匀设计：

- **蓝色** `#2166AC` — 低密度空洞（早期宇宙）
- **灰色** `#666666` — 中间密度纤维网
- **红色** `#B2182B` — 高密度团簇（晚期宇宙）

## 核心发现

| 指标 | t=0 → t=99 | 含义 |
|------|-----------|------|
| σ | +15.4% | 团块化加剧 |
| IQR | +16.7% | 密度离散度上升 |
| P99−P01 | +15.1% | 两极分化 |
| 空洞占比 (ln<8.5) | 0.31% → 2.99% | 空洞扩张约 10 倍 |
| 最小值 | 7.984 → 7.753 | 空洞加深 |
| 最大值 | 13.843 → 14.449 | 峰区增强 |

## 平台

- Python 3.11 + NumPy + Matplotlib + PyVista 0.48 + VTK 9.6 + Plotly + Dash
- NVIDIA RTX 4060 Laptop GPU (8GB VRAM)
- Windows 11

## 许可

仅用于学术研究与教育目的。Nyx 模拟数据版权归原始模拟作者所有。
