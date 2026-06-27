// ============================================================================
// RadarChart — 径向统计特征 (左侧上半)
// 蓝色=Early(t=0) vs 红色=Late(t=99)  半透明面积层叠
// ============================================================================
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const INDICATORS = [
  { name: 'Mean\n均值',     max: 10.5 },
  { name: 'Std\n标准差',    max: 0.6  },
  { name: 'Skew\n偏度',     max: 1.0  },
  { name: 'Kurt\n峰度',     max: 2.2  },
  { name: 'Peak%\n峰值占比', max: 0.2  },
  { name: 'Void%\n空洞占比', max: 4.0  },
];

export default function RadarChart({ t0, t99, current }) {
  const ref = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    }
    const chart = chartRef.current;

    const early = [
      t0.mean, t0.std * 10, t0.skew, t0.kurt / 2, t0.peakPct * 100, t0.voidPct,
    ];
    const late  = [
      t99.mean, t99.std * 10, t99.skew, t99.kurt / 2, t99.peakPct * 100, t99.voidPct,
    ];
    const cur   = [
      current.mean, current.std * 10, current.skew, current.kurt / 2, current.peakPct * 100, current.voidPct,
    ];

    chart.setOption({
      color: ['#2166AC', '#B2182B', '#F4A582'],
      legend: {
        bottom: 0,
        textStyle: { color: '#8899AA', fontSize: 10 },
        data: ['Early (t=0)', 'Late (t=99)', `Current (t=${String(current.t).padStart(3, '0')})`],
      },
      radar: {
        center: ['50%', '48%'],
        radius: '62%',
        axisName: { color: '#8899AA', fontSize: 9, borderRadius: 3, padding: [2, 4] },
        axisLine: { lineStyle: { color: '#2A3040' } },
        splitLine: { lineStyle: { color: '#2A3040', type: 'dashed' } },
        splitArea: { areaStyle: { color: ['#141720', '#181B25'] } },
        indicator: INDICATORS,
      },
      series: [
        {
          type: 'radar',
          name: 'Early (t=0)',
          data: [{ value: early, name: 'Early (t=0)' }],
          lineStyle: { width: 1.5, opacity: 0.7 },
          areaStyle: { opacity: 0.12 },
          symbol: 'none',
        },
        {
          type: 'radar',
          name: 'Late (t=99)',
          data: [{ value: late, name: 'Late (t=99)' }],
          lineStyle: { width: 1.5, opacity: 0.8 },
          areaStyle: { opacity: 0.15 },
          symbol: 'none',
        },
        {
          type: 'radar',
          name: `Current (t=${String(current.t).padStart(3, '0')})`,
          data: [{ value: cur, name: `t=${current.t}` }],
          lineStyle: { width: 2.5, opacity: 1 },
          areaStyle: { opacity: 0 },
          symbol: 'circle',
          symbolSize: 4,
          itemStyle: { borderColor: '#fff', borderWidth: 1 },
        },
      ],
    }, true);

    return () => { /* chart disposed externally */ };
  }, [t0, t99, current]);

  // 响应窗口大小
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
