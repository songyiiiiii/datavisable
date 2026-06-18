# Nyx Cosmic Density — Visual Analytics

> 基于 Nyx 宇宙学模拟数据的交互式可视分析系统  
> Interactive visual analytics of Nyx cosmological simulation density fields

## 数据集

100 个时间步的 Nyx 气体密度场，128³ 体素，float32 小端字节序，列优先（Fortran）存储。密度值约 7.75–14.45（ln ρ），跨越约 3 个数量级。

## 项目结构

```
├── config.py                 # 全局配置（配色、路径、参数）
├── data_loader.py            # 数据读取（.dat → numpy）
├── app.py                    # Dash Web 仪表盘
├── task1_explorer.py         # 独立 3D 交互窗口（PyVista）
├── task_integrated.py        # 集成桌面面板（所有任务）
├── task1_volume_rendering.py # 等值面渲染脚本
├── task2_evolution_analysis.py
├── task3_statistical_tracking.py
├── task4_dashboard.py        # 刷选仪表盘
├── task4_generate_figs.py    # 刷选展示图
├── task5_timewheel.py        # TimeWheel 模块
├── task_icicle_dendro.py     # 冰柱图 + 树状图
├── gen_report_tables.py      # 报告表格生成
├── Nyx/                      # 原始数据（不纳入版本控制）
├── output/                   # 渲染输出
└── report/                   # 技术报告（5 份）
```

## 五个任务

| # | 任务 | 核心技术 |
|---|------|---------|
| 1 | **体数据渲染** | PyVista 多层等值面 + Blinn-Phong 光照，51 帧时间序列 |
| 2 | **演化特征分析** | 五图协同（统计面板、小提琴图、联合分布、团块化指标） |
| 3 | **直方图时序追踪** | 100 步演化热力图、时间导数、FWHM 追踪、三阶段模型 |
| 4 | **相空间刷选** | Plotly Dash 联动仪表盘，直方图框选 ↔ 3D 视图实时映射 |
| 5 | **TimeWheel + 层次可视化** | 极坐标螺旋时间轮、八叉树冰柱图、密度流动矩阵 |

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
