// ============================================================================
// EvolutionChart — 全域统计演化 (右侧上半)  双 Y 轴折线
// 左Y (Log): Std 标准差 (深灰)  右Y (Linear): Mean 均值 (蓝)
// 右侧垂直虚线标记当前时间步
// ============================================================================
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

export default function EvolutionChart({ timeline, timeStep }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    }
    const chart = chartRef.current;

    const ts = timeline.map(d => d.t);
    const stdVals = timeline.map(d => d.std);
    const meanVals = timeline.map(d => d.mean);
    const skewVals = timeline.map(d => d.skew);

    const maxStd = Math.ceil(Math.max(...stdVals) * 100) / 100 + 0.02;

    chart.setOption({
      backgroundColor: 'transparent',
      grid: { left: 48, right: 50, top: 18, bottom: 28 },
      legend: {
        bottom: 0,
        textStyle: { color: '#8899AA', fontSize: 9 },
        data: ['Std (σ)', 'Mean (μ)', 'Skew (γ₁)'],
        itemWidth: 12, itemHeight: 2,
      },
      xAxis: {
        type: 'category',
        data: ts.map(t => String(t)),
        axisLine: { lineStyle: { color: '#2A3040' } },
        axisTick: { show: false },
        axisLabel: { color: '#64748B', fontSize: 7, interval: 9 },
        splitLine: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: 'σ (Std)',
          nameTextStyle: { color: '#8899AA', fontSize: 8 },
          min: 0.38, max: maxStd,
          axisLine: { show: true, lineStyle: { color: '#555555' } },
          axisLabel: { color: '#8899AA', fontSize: 8 },
          splitLine: { lineStyle: { color: '#2A3040', type: 'dashed' } },
        },
        {
          type: 'value',
          name: 'μ (Mean)',
          nameTextStyle: { color: '#4393C3', fontSize: 8 },
          min: 9.44, max: 9.58,
          axisLine: { show: true, lineStyle: { color: '#4393C3' } },
          axisLabel: { color: '#4393C3', fontSize: 8 },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: 'Std (σ)',
          type: 'line',
          yAxisIndex: 0,
          data: stdVals,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#9C89B8', width: 1.6 },
          areaStyle: { color: 'rgba(85,85,85,0.06)' },
        },
        {
          name: 'Mean (μ)',
          type: 'line',
          yAxisIndex: 1,
          data: meanVals,
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#48BFE3', width: 1.8 },
        },
        {
          name: 'Skew (γ₁)',
          type: 'line',
          yAxisIndex: 0,
          data: skewVals.map(v => v * (maxStd / 1.2)),
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#F25F5C', width: 0.8, type: 'dotted' },
        },
      ],
      // 当前时间步标记线
      ...(typeof timeStep === 'number' ? {
        graphic: [
          {
            type: 'line',
            shape: { x1: 0, y1: 0, x2: 0, y2: 1 },
            left: `${(timeStep / 99) * 100}%`,
            top: '8%',
            invisible: false,
            style: { stroke: '#FFE066', lineWidth: 1, lineDash: [4, 3] },
            z: 100,
          },
        ],
      } : {}),
    }, true);

    return () => { /* preserved */ };
  }, [timeline, timeStep]);

  useEffect(() => {
    const onResize = () => chartRef.current?.resize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    return () => { chartRef.current?.dispose(); chartRef.current = null; };
  }, []);

  return <div ref={ref} className="w-full h-full" />;
}
