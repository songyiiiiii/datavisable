// ============================================================================
// HistogramChart — 密度分布直方图 + Brush 区间刷选
// 升级：亮蓝绿 -> 粉红 平滑线性渐变热力图 + 刷选联动 + 容器自适应
// 修复：增加手动清除按钮解决无法取消刷选的问题
// ============================================================================
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export default function HistogramChart({ histogram, brushRange, onBrush, brushInfo }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    }
    const chart = chartRef.current;
    const { centers, counts } = histogram;

    // 寻找当前数据的最大值和最小值，用于归一化
    const maxCount = Math.max(...counts);
    const minCount = Math.min(...counts);
    const range = maxCount - minCount;

    // 【核心】：使用 HSL 颜色插值实现亮蓝绿到粉红的丝滑渐变
    const getHeatColor = (value) => {
      if (range === 0) return '#48BFE3';
      const t = (value - minCount) / range; 
      const lerp = (start, end, amt) => start + (end - start) * amt;
      const h = lerp(185, 355, t);
      const s = lerp(75, 85, t);
      const l = lerp(55, 60, t);
      return `hsl(${h}, ${s}%, ${l}%)`;
    };

    // 构建带动态颜色的数据
    const dataWithColor = counts.map((v, i) => {
      let finalColor = '';
      if (brushRange && brushRange[0] !== undefined) {
        const currentX = centers[i];
        const isSelected = (currentX >= brushRange[0] && currentX <= brushRange[1]);
        if (isSelected) {
          finalColor = getHeatColor(v);
        } else {
          finalColor = '#1A2B3C'; 
        }
      } else {
        finalColor = getHeatColor(v);
      }

      return { 
        value: v, 
        itemStyle: { 
          color: new echarts.graphic.LinearGradient(0, 1, 0, 0, [
            { offset: 0, color: '#0A1628' },
            { offset: 0.2, color: finalColor },
            { offset: 1, color: finalColor }
          ]),
          borderRadius: [2, 2, 0, 0] 
        } 
      };
    });

    chart.setOption({
      backgroundColor: 'transparent',
      grid: { left: 30, right: 5, top: 10, bottom: 48 },
      xAxis: {
        type: 'category',
        data: centers.map(c => c.toFixed(2)),
        axisLine: { lineStyle: { color: '#2A3040' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#8899AA',
          fontSize: 8,
          interval: 12, 
          rotate: 20,
        },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: '#2A3040', type: 'dashed' } },
        axisLabel: { color: '#64748B', fontSize: 8 },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#141720',
        borderColor: '#2A3040',
        textStyle: { color: '#C8CCD4', fontSize: 10 },
        formatter: p => {
          const d = p[0];
          return `ln(ρ) = ${d.name}<br/>Count: ${d.value.toLocaleString()}`;
        },
      },
      brush: {
        toolbox: ['rect', 'clear'], // 保留 clear
        brushLink: [],
        xAxisIndex: 0,
        brushStyle: { borderWidth: 1, color: 'rgba(242, 95, 92, 0.15)', borderColor: '#F25F5C' },
        throttleType: 'debounce',
        throttleDelay: 100,
        outOfBrush: { colorAlpha: 1 }, 
      },
      series: [{
        type: 'bar',
        data: dataWithColor,
        barWidth: '60%',
        emphasis: { 
          itemStyle: { 
            shadowBlur: 10, 
            shadowColor: 'rgba(255,255,255,0.3)' 
          } 
        },
      }],
    }, true);

    // ==========================================================
    // 【监听】：处理图表上的拖拽刷选
    // ==========================================================
    chart.off('brushSelected');
    chart.on('brushSelected', (params) => {
      // 如果是因为点击 clear 触发的，selected 长度将为 0，直接忽略并等待手动清除按钮触发
      if (!params.batch || params.batch.length === 0) return;

      const selected = params.batch[0].selected;
      if (selected && selected.length > 0) {
        const indices = selected[0].dataIndex;
        if (!indices || indices.length === 0) return;

        const lo = parseFloat(centers[indices[0]]);
        const hi = parseFloat(centers[indices[indices.length - 1]]);

        if (Math.abs(hi - lo) < 0.01) return;

        if (!isNaN(lo) && !isNaN(hi)) {
          onBrush([lo, hi]);
        }
      }
      // 移除了原来自动调用 onBrush(null) 的逻辑，防止误触闪回
    });

    // ==========================================================
    // 【自适应】：使用 ResizeObserver 监听容器自身尺寸变化
    // ==========================================================
    const resizeObserver = new ResizeObserver(() => {
      chart.resize();
    });
    resizeObserver.observe(ref.current);

    return () => { 
      resizeObserver.disconnect();
    };
  }, [histogram, brushRange, onBrush]);

  useEffect(() => {
    return () => { chartRef.current?.dispose(); chartRef.current = null; };
  }, []);

  // ==========================================================
  // 【新增】：手动清除刷选逻辑
  // ==========================================================
  const handleClearBrush = () => {
    if (chartRef.current) {
      // 1. 调用 ECharts 原生 API 清除图表上的高亮和框
      chartRef.current.dispatchAction({
        type: 'brush',
        areas: []
      });
    }
    // 2. 强制将父组件状态置为 null，粒子云会立刻回到全量渲染
    onBrush(null);
  };

  return (
    <div className="w-full h-full flex flex-col relative">
      {/* 【新增】：清除刷选按钮。只有当有刷选时才显示 */}
      {brushInfo && (
        <button 
          onClick={handleClearBrush}
          className="absolute -top-1 right-0 z-10 px-2 py-0.5 text-[10px] font-mono bg-black/60 backdrop-blur-sm border border-white/10 rounded text-[#F25F5C] hover:bg-[#F25F5C]/20 transition-colors"
        >
          ✕ 清除选择
        </button>
      )}
      
      <div ref={ref} className="flex-1 w-full h-full" />
      {brushInfo && (
        <div className="flex items-center justify-center gap-1.5 text-[10px] text-gray-500 h-5 bg-[#1A1825] mx-2 mb-1 rounded border border-[#242233]">
          <span className="text-blue-400">[</span>
          <span className="text-red-400 font-mono tabular-nums">{brushInfo.lo?.toFixed(1)}</span>
          <span className="text-gray-600">,</span>
          <span className="text-red-400 font-mono tabular-nums">{brushInfo.hi?.toFixed(1)}</span>
          <span className="text-blue-400">]</span>
          <span className="text-gray-600 mx-1">|</span>
          <span className="text-gray-400 tabular-nums">占比 {brushInfo.pct}%</span>
        </div>
      )}
    </div>
  );
}