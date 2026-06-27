// ============================================================================
// TransitionMatrix.jsx — 状态转移矩阵热力图 (ECharts) V2
// ============================================================================
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';

const LABELS = ['Void', 'Sheet', 'Filament', 'Node'];

export default function TransitionMatrix() {
  const ref = useRef(null);
  const chartRef = useRef(null);
  const [matrix, setMatrix] = useState(null);

  // 加载数据
  useEffect(() => {
    fetch('/data/sankey_transition.json')
      .then(r => r.json())
      .then(data => {
        const raw = Array.from({ length: 4 }, () => Array(4).fill(0));
        data.links.forEach(l => {
          const si = LABELS.findIndex(x => l.source.toLowerCase().includes(x.toLowerCase()));
          const ti = LABELS.findIndex(x => l.target.toLowerCase().includes(x.toLowerCase()));
          if (si >= 0 && ti >= 0) raw[si][ti] += l.value;
        });
        const m = raw.map(row => {
          const sum = row.reduce((a, b) => a + b, 1);
          return row.map(v => +(v / sum * 100).toFixed(1));
        });
        setMatrix(m);
      })
      .catch(e => console.warn('Transition matrix data failed:', e));
  }, []);

  // 渲染图表
  useEffect(() => {
    if (!ref.current || !matrix) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    const c = chartRef.current;

    c.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        backgroundColor: '#1A1825', borderColor: '#242233',
        textStyle: { color: '#C5C3D8', fontSize: 11 },
        formatter: p => `${LABELS[p.data[1]]} → ${LABELS[p.data[0]]}<br/>转移率: <b>${p.data[2]}%</b>`,
      },
      grid: { left: 50, right: 15, top: 12, bottom: 45 },
      xAxis: {
        type: 'category', data: LABELS, position: 'top',
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { color: '#C5C3D8', fontSize: 10, fontWeight: 'bold' },
      },
      yAxis: {
        type: 'category', data: LABELS,
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { color: '#C5C3D8', fontSize: 10, fontWeight: 'bold' },
      },
      visualMap: {
        min: 0, max: 100, calculable: false, show: true,
        orient: 'horizontal', left: 'center', bottom: 2,
        inRange: { color: ['#0D0B14', '#3E5BA3', '#75CBD1', '#F2D2FF'] },
        textStyle: { color: '#6B6880', fontSize: 8 },
      },
      series: [{
        type: 'heatmap',
        data: matrix.flatMap((row, i) => row.map((v, j) => [j, i, v])),
        label: { show: true, color: '#C5C3D8', fontSize: 13, fontWeight: 'bold', fontFamily: 'monospace' },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
      }],
    }, true);

    const ro = new ResizeObserver(() => c.resize());
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, [matrix]);

  useEffect(() => () => { chartRef.current?.dispose(); chartRef.current = null; }, []);

  return <div ref={ref} className="w-full h-full" />;
}
