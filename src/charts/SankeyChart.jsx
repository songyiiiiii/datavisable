// ============================================================================
// SankeyChart.jsx — 宇宙结构转变交互式桑基图 (ECharts)
// 功能：多时间层节点 + 分段数切换交互 + 动态结论面板
// 修复：悬浮提示精准显示“t=XX 结构 -> t=XX 结构”，无未知信息。
// ============================================================================
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';

// 颜色映射表 (输出颜色，用于连线渐变和最终环形图)
const COLORS = {
  'Void': '#48BFE3',
  'Sheet': '#00f7ff',
  'Filament': '#ff007b',
  'Node': '#00f0a8',
};

// 中文名称映射表
const STRUCT_NAMES = {
  'Void': '空洞',
  'Sheet': '薄片',
  'Filament': '纤维',
  'Node': '节点'
};

// 生成双色渐变边 (从源颜色渐变到目标颜色)
const getGradientColor = (sourceType, targetType) => {
  const srcColor = COLORS[sourceType] || '#6B6880';
  const tgtColor = COLORS[targetType] || '#6B6880';
  return {
    type: 'linear',
    x: 0, y: 0, x2: 1, y2: 0,
    colorStops: [
      { offset: 0, color: srcColor },
      { offset: 1, color: tgtColor }
    ]
  };
};

// 根据分段数生成模拟数据 (并嵌入中文名称用于Tooltip)
const generateSankeyData = (numSegments = 5) => {
  const steps = Array.from({ length: numSegments }, (_, i) => Math.round((i / (numSegments - 1)) * 99));
  if (steps[steps.length - 1] !== 99) steps[steps.length - 1] = 99;
  
  const types = ['Void', 'Sheet', 'Filament', 'Node'];
  const nodes = [];
  const links = [];

  steps.forEach((step, idx) => {
    types.forEach(type => {
      const id = `t=${step} ${type}`;
      let size = 0;
      // 模拟体素占比演化 (随阶段变化)
      if (type === 'Void') size = 30 + idx * 15;
      else if (type === 'Sheet') size = 40 - idx * 5;
      else if (type === 'Filament') size = 20 + idx * 8;
      else if (type === 'Node') size = 5 + idx * 12;
      
      nodes.push({
        name: id, // ECharts 需要这个作为唯一ID
        // 我们自定义一个字段存中文名，供Tooltip使用
        structName: STRUCT_NAMES[type] || type, 
        itemStyle: { color: COLORS[type], opacity: 0.85 },
        symbolSize: Math.max(10, Math.min(25, 6 + size / 4))
      });
    });
  });

  // 2. 生成连接边（只在相邻的时间步之间产生流动）
  for (let i = 0; i < steps.length - 1; i++) {
    const curStep = steps[i];
    const nextStep = steps[i+1];
    
    types.forEach(srcType => {
      types.forEach(tgtType => {
        let amount = 0;
        const srcId = `t=${curStep} ${srcType}`;
        const tgtId = `t=${nextStep} ${tgtType}`;

        // 模拟动态迁移逻辑：
        if (srcType === tgtType) {
          amount = 300000 + Math.random() * 100000 * (i + 1) / steps.length;
        } else if (srcType === 'Sheet' && tgtType === 'Filament') {
          amount = 100000 + Math.random() * 50000;
        } else if (srcType === 'Filament' && tgtType === 'Node') {
          amount = 80000 + Math.random() * 40000;
        } else if (Math.random() > 0.85) {
          amount = 20000 + Math.random() * 30000;
        }

        if (amount > 1000) {
          links.push({
            source: srcId,
            target: tgtId,
            value: Math.round(amount),
            // 自定义的元数据，用于精准呈现 Tooltip
            sourceStruct: STRUCT_NAMES[srcType] || srcType,
            targetStruct: STRUCT_NAMES[tgtType] || tgtType,
            sourceTime: curStep,
            targetTime: nextStep,
            lineStyle: {
              color: getGradientColor(srcType, tgtType),
              opacity: 0.35,
              curveness: 0.4
            }
          });
        }
      });
    });
  }
  return { nodes, links, steps };
};

export default function SankeyChart() {
  const ref = useRef(null);
  const chartRef = useRef(null);
  const [segments, setSegments] = useState(5);
  const [data, setData] = useState(() => generateSankeyData(5));

  // 当分段数改变时，重新生成数据并渲染图表
  useEffect(() => {
    const newData = generateSankeyData(segments);
    setData(newData);
    renderChart(newData);
  }, [segments]);

  // 渲染图表的核心函数
  const renderChart = (data) => {
    if (!ref.current || !data.nodes) return;
    if (!chartRef.current) {
      chartRef.current = echarts.init(ref.current, null, { renderer: 'canvas' });
    }
    const c = chartRef.current;

    c.setOption({
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        triggerOn: 'mousemove',
        backgroundColor: '#1A1825', 
        borderColor: '#48BFE3',
        textStyle: { color: '#C5C3D8', fontSize: 12, fontFamily: 'monospace' },
        // ==================================================
        // 【核心修复】：使用预先打包的 structName 和 sourceStruct/targetStruct
        // ==================================================
        formatter: (p) => {
          if (p.dataType === 'edge') {
            // 连线悬停：直接使用我们自己在 links 里注入的中文名和时间
            const srcTime = p.data.sourceTime;
            const tgtTime = p.data.targetTime;
            const srcName = p.data.sourceStruct;
            const tgtName = p.data.targetStruct;
            
            return `<b>${srcName}</b> (t=${srcTime}) → <b>${tgtName}</b> (t=${tgtTime})<br/>转化体素: <span style="color:${COLORS[p.data.sourceStruct] || '#6B6880'}">${p.data.value.toLocaleString()}</span>`;
          } else {
            // 节点悬停：直接使用我们在 nodes 里注入的 structName
            const name = p.data.structName || '节点';
            const parts = p.name?.split(' ') || [];
            const time = parts[1] || '?';
            return `${name}  (t=${time})`;
          }
        },
      },
      series: [{
        type: 'sankey',
        layout: 'none', 
        layoutIterations: 0,
        nodeAlign: 'left',
        nodeWidth: 20,
        nodeGap: 12,
        draggable: true,
        focusNodeAdjacency: 'allEdges',
        data: data.nodes.map(n => ({
          ...n,
          emphasis: { itemStyle: { shadowBlur: 15, shadowColor: 'rgba(255,255,255,0.3)' } }
        })),
        links: data.links,
        label: {
          show: true,
          position: 'right',
          color: '#8898AA',
          fontSize: 10,
          fontFamily: 'monospace',
          formatter: (p) => p.data.structName || p.name.split(' ')[2]
        },
        lineStyle: {
          color: 'gradient',
          opacity: 0.35,
          curveness: 0.4
        },
        emphasis: {
          lineStyle: {
            opacity: 0.9,
            width: 5
          }
        },
      }],
    }, true);

    const resizeObserver = new ResizeObserver(() => { chartRef.current?.resize(); });
    resizeObserver.observe(ref.current);
    return () => { resizeObserver.disconnect(); };
  };

  useEffect(() => () => { chartRef.current?.dispose(); chartRef.current = null; }, []);

  // 计算演化的最终物质分布形态（用于右侧结论）
  const finalStats = data.nodes.filter(n => n.name.includes('t=99')).reduce((acc, node) => {
    const type = node.name.split(' ')[2];
    acc[type] = node.symbolSize || 0;
    return acc;
  }, {});
  const dominantType = Object.entries(finalStats).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Void';

  return (
    <div className="w-full h-full flex flex-col md:flex-row gap-4 p-2 relative font-sans text-[#E0E6ED]">
      
      {/* 左侧：桑基图主体 (占 75%) */}
      <div className="flex-[0.75] w-full h-full min-h-[250px] relative">
        <div ref={ref} className="w-full h-full" />
        
        {/* 底部交互按钮组：控制分段数 */}
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-10 flex gap-2 bg-black/60 backdrop-blur-sm border border-white/10 rounded-lg p-1 shadow-lg">
          {[2, 3, 4, 5].map(num => (
            <button
              key={num}
              onClick={() => setSegments(num)}
              className={`px-3 py-1 text-[11px] font-mono rounded transition-colors ${segments === num ? 'text-[#48BFE3] bg-[#48BFE3]/20 border border-[#48BFE3]/30' : 'text-[#8898AA] hover:text-[#E0E6ED]'}`}
            >
              {num}段
            </button>
          ))}
        </div>
      </div>

      {/* 右侧：结论与文字解释 (占 25%) */}
      <div className="flex-[0.25] w-full h-full flex flex-col gap-2 border-l border-white/10 pl-3 bg-black/20 backdrop-blur-sm rounded-lg p-2">
        
        <div className="text-[14px] font-bold border-b border-white/10 pb-1 mb-1 flex items-center gap-2">
          <span className="text-[#48BFE3]">✦</span> 演化结论洞察
        </div>

        <div className="flex-1 flex flex-col gap-2 text-[11px] leading-relaxed text-[#8898AA] overflow-y-auto pr-1">
          <div className="bg-black/30 border border-white/5 rounded p-2">
            <div className="text-[12px] font-bold text-[#E0E6ED] mb-0.5">📊 物质流动总览</div>
            <p>
              通过 {segments} 段式时间切分，清晰展示了宇宙结构从 <span className="text-[#48BFE3]">早期均匀分布</span> 向 <span className="text-[#FFD940]">成熟宇宙网</span> 的演化路径。
            </p>
          </div>

          <div className="bg-black/30 border border-white/5 rounded p-2">
            <div className="text-[12px] font-bold text-[#E0E6ED] mb-0.5">🔥 核心物理机制</div>
            <ul className="list-disc list-inside space-y-0.5 pl-1">
              <li>物质持续从 <span className="text-[#00f7ff]">薄片 (Sheet)</span> 向 <span className="text-[#ff007b]">纤维 (Filament)</span> 转移。</li>
              <li>高密度 <span className="text-[#00f0a8]">节点 (Node)</span> 通过引力坍缩不断吞噬周围纤维，质量呈指数级增长。</li>
              <li>占比最大的 <span className="text-[#48BFE3]">空洞 (Void)</span> 持续膨胀，驱动宇宙两极分化。</li>
            </ul>
          </div>

          <div className="bg-black/30 border border-white/5 rounded p-2 mt-auto">
            <div className="text-[12px] font-bold text-[#E0E6ED] mb-1">📈 演化终态预测</div>
            <div className="flex items-center gap-3">
              <div className="relative w-16 h-16 rounded-full border-2 border-white/10 flex items-center justify-center text-[10px] text-center text-[#E0E6ED] font-bold leading-tight bg-black/20">
                {STRUCT_NAMES[dominantType]}
                <div className="absolute -inset-1 rounded-full opacity-30" style={{
                  background: `conic-gradient(${Object.entries(finalStats).map(([key, val]) => `${COLORS[key]} 0% ${(val / 25) * 100}%`).join(', ')})`
                }}></div>
              </div>
              <div className="flex-1 text-[10px]">
                <p>演化至 t=99 时，由 <span className="text-[#48BFE3] font-bold">{STRUCT_NAMES[dominantType]}</span> 占据绝对主导，宇宙网结构趋于稳定。</p>
                <p className="text-[9px] text-[#6B6880] mt-0.5">* 悬浮图表节点或连线可见详细迁移数据。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}