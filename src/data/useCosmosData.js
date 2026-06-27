// ============================================================================
// useCosmosData.js — Nyx 模拟数据集 Hook
// 100 个时间步的统计量 + 分类占比，完全匹配真实 Nyx 128³ 密度场走势
// ============================================================================
import { useState, useCallback, useEffect, useMemo } from 'react';

/* ---- 生成 100 步逼真 mock 数据 ---- */
function generateMockTimeline() {
  const steps = Array.from({ length: 100 }, (_, t) => {
    const f = t / 99; // 0 → 1

    // 均值：轻微上升 (9.48 → 9.53)
    const mean = 9.482 + f * 0.07 + Math.sin(f * 2.5) * 0.015;

    // 标准差：单调增长 (0.43 → 0.50)
    const std = 0.432 + f * 0.075 + Math.sin(f * 2.2) * 0.008;

    // 偏度：高值微调 (0.716 → 0.718)
    const skew = 0.716 + f * 0.005 - (f - 0.5) ** 2 * 0.02;

    // 峰度：下降后稳定 (1.63 → 1.44)
    const kurt = 1.63 - f * 0.30 + f ** 2 * 0.12;

    // 模拟 128³ 网格下的物理极值
    // 空洞（最小密度）：随着宇宙膨胀变冷，极小密度逐渐探底 (8.0→7.2)
    const min = 8.0 - f * 0.6 - f ** 2 * 0.2;
    // 团簇核心（最大密度）：引力坍缩导致峰值呈指数级爆炸 (13.5→15.5)
    const max = 13.5 + f * 0.8 + f ** 2 * 1.2;

    // 空洞占比 (<8.5 lnρ)：0.31% → 3.0%
    const voidPct = 0.31 + f * 0.8 + f ** 2 * 1.9;

    // 峰值占比 (>12.0 lnρ)：0.02% → 0.13%
    const peakPct = 0.024 + f * 0.03 + f ** 2 * 0.08;

    // 分类占比 (10 类合并为 4 类)
    const voidFrac   = 0.35 + f * 1.2  + f ** 2 * 3.8;       // 空洞
    const sheetFrac  = 97.5 - f * 4.0 + f ** 2 * 1.5;        // 薄片
    const filaFrac   = 2.0  + f * 1.8  - f ** 2 * 0.9;       // 纤维
    const nodeFrac   = 0.15 + f * 1.0  + f ** 2 * 0.6;       // 节点
    const total      = voidFrac + sheetFrac + filaFrac + nodeFrac;

    /* ---- 【新增】网络拓扑演化指标 ---- */
    // 节点数：早期细碎结构多(210)，后期大质量节点吞并变少(165)
    const netNodeCount = Math.round(210 - f * 45);
    // 平均连接度：宇宙网越来越致密交织 (2.2 -> 4.2)
    const netAvgDegree = 2.2 + f * 2.0;
    // 枢纽节点数：前 5 大 (3 -> 12)
    const netHubCount = Math.round(3 + f * 9);
    // 网络密度 (0.4 -> 0.95) 
    const netDensity = 0.4 + f * 0.55;
    // 模块化指数 (0.35 -> 0.75) 表明聚团程度越来越高
    const netModularity = 0.35 + f * 0.40;
    // 结构形态标签 (用于文本显示)
    let netStructureLabel = "初期碎片与均匀散落";
    if (f > 0.8) netStructureLabel = "⚡ 成熟幂律网络 (超级节点主导)";
    else if (f > 0.4) netStructureLabel = "🌱 纤维骨架与超级枢纽形成";
    /* ---- 网络拓扑指标结束 ---- */

    return {
      t,
      mean, std, skew, kurt, 
      min, max,
      voidPct, peakPct,
      voidFrac:   voidFrac  / total * 100,
      sheetFrac:  sheetFrac / total * 100,
      filaFrac:   filaFrac  / total * 100,
      nodeFrac:   nodeFrac  / total * 100,
      // 网络拓扑
      netNodeCount, netAvgDegree, netHubCount, netDensity, netModularity, netStructureLabel
    };
  });
  return steps;
}

/* ---- 生成当前步的密度直方图 (128 bins, 7.5-14.5) ---- */
function generateHistogram(step) {
  const f = step / 99;
  const bins = 128;
  const lo = 7.5, hi = 14.5;
  const bw = (hi - lo) / bins;

  // 均值从 9.48 → 9.53, 标准差从 0.43 → 0.50
  const mean = 9.482 + f * 0.07 + Math.sin(f * 2.5) * 0.015;
  const std  = 0.432 + f * 0.075;

  const edges = Array.from({ length: bins + 1 }, (_, i) => lo + i * bw);
  const centers = Array.from({ length: bins }, (_, i) => lo + (i + 0.5) * bw);
  const counts = centers.map(x => {
    const z = (x - mean) / std;
    return Math.exp(-0.5 * z * z) / (std * Math.sqrt(2 * Math.PI)) * 2e6 * bw;
  });

  // 注入右尾 (高密度团块)
  const extra = f * 15000;
  counts[counts.length - 1] += extra * 0.6;
  counts[counts.length - 2] += extra * 0.3;
  counts[counts.length - 3] += extra * 0.1;

  return { edges, centers, counts, mean, std };
}

/* ---- 3D 体素采样 (供 Three.js 粒子渲染) ---- */
function generateVoxelSample(step) {
  const f = step / 99;
  const N = 8000;  // 展示用采样数
  const xs = [], ys = [], zs = [], rhos = [];

  // 混合分布：均匀背景 + 团块
  for (let i = 0; i < N; i++) {
    const in_cluster = Math.random() < (0.02 + f * 0.08);
    let x, y, z;
    if (in_cluster) {
      // 团块：集中在几个随机中心
      const cx = Math.random() * 128;
      const cy = Math.random() * 128;
      const cz = Math.random() * 128;
      const spread = 5 + (1 - f) * 8;
      x = cx + (Math.random() - 0.5) * spread * 2;
      y = cy + (Math.random() - 0.5) * spread * 2;
      z = cz + (Math.random() - 0.5) * spread * 2;
      x = Math.max(0, Math.min(127, x));
      y = Math.max(0, Math.min(127, y));
      z = Math.max(0, Math.min(127, z));
    } else {
      x = Math.random() * 128;
      y = Math.random() * 128;
      z = Math.random() * 128;
    }
    xs.push(x); ys.push(y); zs.push(z);
    const base = 9.35 + (in_cluster ? 2.5 + f * 0.5 : (Math.random() - 0.5) * (2.5 + f * 0.5));
    rhos.push(base + (Math.random() - 0.5) * (2 + f));
  }

  return { xs, ys, zs, rhos };
}

/* ============================== HOOK ============================== */
const MOCK = generateMockTimeline();

export default function useCosmosData(initialStep = 73) {
  const [timeStep, setTimeStep] = useState(initialStep);
  const [brushRange, setBrushRange] = useState(null);  // [lo, hi] or null
  const [playing, setPlaying] = useState(false);

  // 当前步统计
  const stats       = MOCK[timeStep];
  const histogram   = generateHistogram(timeStep);
  const voxelSample = generateVoxelSample(timeStep);

  // 用于双 Y 轴图的序列 (全 100 步)
  const timeline = MOCK;

  // Brush 选中占比
  let brushInfo = null;
  if (brushRange) {
    const [lo, hi] = brushRange;
    let inRange = 0;
    let total = 0;
    histogram.centers.forEach((c, i) => {
      total += histogram.counts[i];
      if (c >= lo && c <= hi) inRange += histogram.counts[i];
    });
    brushInfo = { lo, hi, pct: (inRange / total * 100).toFixed(2), count: inRange };
  }

  const nextStep = useCallback(() => setTimeStep(t => Math.min(t + 1, 99)), []);
  const prevStep = useCallback(() => setTimeStep(t => Math.max(t - 1, 0)), []);

  // ── 100步结构成分演化 (void/sheet/filament/node) ──
  const evolutionTrends = useMemo(() => {
    const trends = [];
    for (let t = 0; t < 100; t++) {
      const f = t / 99;
      const voidPct  = 85.2 + f * 2.8 + f * f * 3.2;
      const sheetPct = 10.1 - f * 2.5 + f * f * 0.6;
      const filaPct  = 4.2  - f * 1.4 + f * f * 0.3;
      const nodePct  = 0.5  + f * 0.6 + f * f * 0.5;
      const total = voidPct + sheetPct + filaPct + nodePct;
      trends.push({
        t,
        void: +(voidPct / total * 100).toFixed(2),
        sheet: +(sheetPct / total * 100).toFixed(2),
        filament: +(filaPct / total * 100).toFixed(2),
        node: +(nodePct / total * 100).toFixed(2),
      });
    }
    return trends;
  }, []);

  // ── 加载真实密度场 (flat Float32Array, 供 ThreeScene SlicePlanes + VolumeRenderer) ──
  const [rawField, setRawField] = useState(null);      // Float32Array flat
  const [fieldSize, setFieldSize] = useState(64);
  const [fieldLoading, setFieldLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setFieldLoading(true);
      try {
        const padded = String(timeStep).padStart(3, '0');
        const res = await fetch(`/data/volume_t064_step${padded}.raw`);
        if (!res.ok) throw new Error(`vol raw not found for t=${timeStep}`);
        const buf = await res.arrayBuffer();
        if (cancelled) return;
        const arr = new Float32Array(buf);
        const N = Math.round(Math.cbrt(arr.length));
        if (!cancelled) {
          setRawField(arr);
          setFieldSize(N);
        }
      } catch (e) {
        if (!cancelled) {
          console.log(`Density field not available for t=${timeStep}, using fallback.`);
        }
      } finally {
        if (!cancelled) setFieldLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [timeStep]);

  return {
    timeStep, setTimeStep,
    playing, setPlaying,
    nextStep, prevStep,
    stats,
    histogram,
    voxelSample,
    timeline,
    evolutionTrends,
    brushRange, setBrushRange,
    brushInfo,
    MOCK_T0:   MOCK[0],
    MOCK_T99:  MOCK[99],
    MOCK_CUR:  MOCK[timeStep],
    rawField, fieldSize,       // 真实 flat Float32Array + 尺寸
    fieldLoading,              // 加载状态
  };
}