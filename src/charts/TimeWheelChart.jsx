// ============================================================================
// TimeWheelChart V4 — 完全重写: category轴 + 可见纤维束 + 径向辐条
// ============================================================================
import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

const METRICS = ['Void%','Peak%','Kurt','Skew','IQR','Std','Mean','Min','Max','P99-P01'];
const N = 100;

function genNormed() {
  const raw = [];
  for (let t = 0; t < N; t++) {
    const f = t / 99;
    raw.push([
      0.31+f*1.2+f**2*2.5, 0.024+f*0.03+f**2*0.12,
      1.63-f*0.30+f**2*0.12, 0.716+f*0.005-(f-0.5)**2*0.02,
      0.535+f*0.12, 0.432+f*0.075+Math.sin(f*2.2)*0.008,
      9.482+f*0.07+Math.sin(f*2.5)*0.015, 7.985-f*0.25,
      13.84+f*0.55, 2.098+f*0.42,
    ]);
  }
  const cols = [];
  for (let i = 0; i < 10; i++) {
    const col = raw.map(r => r[i]);
    const mn = Math.min(...col), mx = Math.max(...col);
    const rng = mx - mn || 1;
    cols.push({ mn, rng, values: col.map(v => (v-mn)/rng*8+1) });
  }
  return cols;
}
const TW = genNormed();

// 蓝绿→紫→红→金
function colorFn(t) {
  const f = t / 99;
  let r,g,b;
  if (f<0.25){const s=f/0.25; r=0.05+0.52*s; g=0.15+1.60*s; b=0.35+1.32*s;}
  else if(f<0.5){const s=(f-0.25)/0.25; r=0.57+0.45*s; g=1.75-2.00*s; b=1.67-1.08*s;}
  else if(f<0.75){const s=(f-0.5)/0.25; r=1.02-0.52*s; g=-0.25+0.70*s; b=0.59-0.14*s;}
  else{const s=(f-0.75)/0.25; r=0.50+2.00*s; g=0.45+1.60*s; b=0.45-0.60*s;}
  r=Math.max(0,Math.min(1,r)); g=Math.max(0,Math.min(1,g)); b=Math.max(0,Math.min(1,b));
  return `rgb(${Math.round(r*255)},${Math.round(g*255)},${Math.round(b*255)})`;
}

export default function TimeWheelChart({ timeStep }) {
  const ref = useRef(null);
  const chartRef = useRef(null);
  const step = typeof timeStep === 'number' ? timeStep : 73;

  useEffect(() => {
    if (!ref.current) return;
    if (!chartRef.current) chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    const c = chartRef.current;

    const series = [];

    // === 纤维束: 每步一个10边形, 高可见度 ===
    for (let t = 0; t < N; t++) {
      const isCur = t === step;
      const alpha = isCur ? 1.0 : 0.35;       // 提高透明度
      const lw = isCur ? 4.5 : 1.5;
      const color = colorFn(t);

      const data = [];
      for (let i = 0; i < 10; i++) {
        data.push({ value: [METRICS[i], TW[i].values[t]] });
      }
      data.push({ value: [METRICS[0], TW[0].values[t]] }); // 闭合

      series.push({
        type: 'line',
        data,
        coordinateSystem: 'polar',
        smooth: false,
        symbol: 'none',
        lineStyle: { color, width: lw, opacity: alpha },
        z: isCur ? 1000 : t,
        silent: true,
        polyline: false,
      });
    }

    // === 十边形参考框 ===
    const frameData = METRICS.map((m, i) => ({ value: [m, 10] }));
    frameData.push({ value: [METRICS[0], 10] });
    series.push({
      type: 'line', data: frameData, coordinateSystem: 'polar',
      symbol: 'none', silent: true, z: -1,
      lineStyle: { color: '#444466', width: 0.8, type: 'dotted' },
    });

    // === 10条径向刻度线 (从中心到r=10) ===
    for (let i = 0; i < 10; i++) {
      series.push({
        type: 'line',
        data: [{ value: [METRICS[i], 0] }, { value: [METRICS[i], 10] }],
        coordinateSystem: 'polar',
        symbol: 'none', silent: true, z: -2,
        lineStyle: { color: '#333355', width: 0.8 },
      });
      // 刻度标记 at r=2,4,6,8
      for (const r of [2,4,6,8]) {
        series.push({
          type: 'line',
          data: [
            { value: [METRICS[i], r] },
            { value: [METRICS[(i+1)%10], r] },
          ],
          coordinateSystem: 'polar',
          symbol: 'none', silent: true, z: -2,
          lineStyle: { color: '#222244', width: 0.3, type: 'dashed' },
        });
      }
    }

    c.setOption({
      backgroundColor: 'transparent',
      polar: {
        radius: ['5%', '78%'],
        center: ['50%', '48%'],
      },
      angleAxis: {
        type: 'category',
        data: METRICS,
        boundaryGap: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#C5C3D8', fontSize: 8, fontWeight: 'bold', margin: 8 },
        splitLine: { show: false },
      },
      radiusAxis: {
        type: 'value', min: 0, max: 11,
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { show: false }, splitLine: { show: false },
      },
      series,
    }, true);

    return () => {};
  }, [step]);

  useEffect(() => {
    const onR = () => chartRef.current?.resize();
    window.addEventListener('resize', onR);
    return () => window.removeEventListener('resize', onR);
  }, []);
  useEffect(() => () => { chartRef.current?.dispose(); chartRef.current = null; }, []);

  return <div ref={ref} className="w-full h-full" />;
}
