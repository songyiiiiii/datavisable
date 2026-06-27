// ============================================================================
// CompositionChart.jsx — 光谱渐变发光带图 (彻底替换气泡，实现丝滑渐变)
// 核心理念：将绝对占比进行归一化，变成1.0x对比。使用单独的区域渐变发光。
// ============================================================================
import React, { useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend } from 'recharts';

// 这里的颜色经过精心设计，映射光谱的中间断层。
// 从 Void (亮蓝绿) -> Node (亮粉红) 的视觉阶跃。
const SERIES = [
  { key: 'void',     color: '#ff032d', label: '空洞 / Void' },      // 亮蓝绿
  { key: 'sheet',    color: '#f10ccb', label: '薄片 / Sheet' },     // 蒂芙尼蓝
  { key: 'filament', color: '#035bff', label: '纤维 / Filament' },  // 珊瑚橙
  { key: 'node',     color: '#00fffb', label: '节点 / Node' },      // 亮粉红
];

export default function CompositionChart({ data = [] }) {
  // 核心数据转换：将"原始占比"转换为"相对于 t=0 的增长倍率"并保留原本数值
  const normalizedData = useMemo(() => {
    if (!data || data.length === 0) return [];
    const baseline = data[0];
    return data.map(d => {
      const norm = { t: d.t, _raw: d };
      SERIES.forEach(({ key }) => {
        // 计算倍率 (用于绘制高度)
        norm[`${key}_norm`] = baseline[key] > 0 ? d[key] / baseline[key] : 1;
      });
      return norm;
    });
  }, [data]);

  if (!data || data.length === 0) {
    return <div className="w-full h-full flex items-center justify-center text-[#6B6880] text-[12px]">加载演化数据中...</div>;
  }

  return (
    <div className="w-full h-full relative flex flex-col">
      {/* 精简顶部图例，只保留颜色小点，让视觉更干净 */}
      <div className="shrink-0 flex justify-center gap-5 py-0.5 pb-1">
        {SERIES.map(({ key, color, label }) => (
          <div key={key} className="flex items-center gap-1.5 opacity-80 hover:opacity-100 transition-opacity">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}></span>
            <span className="text-[10px] text-[#C5C3D8] font-mono tracking-wide">{label}</span>
          </div>
        ))}
      </div>

      <div className="flex-1 w-full min-h-0 relative">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={normalizedData} margin={{ top: 2, right: 0, left: 0, bottom: 2 }}>
            <CartesianGrid strokeDasharray="2 4" stroke="#242233" strokeOpacity={0.2} vertical={false} />
            
            <XAxis 
              dataKey="t" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#6B6880', fontSize: 8 }} 
              tickFormatter={(t) => t % 25 === 0 ? `t=${t}` : ''}
            />
            
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: '#6B6880', fontSize: 8 }} 
              tickFormatter={(val) => `${val.toFixed(1)}x`}
              domain={[0.8, 'auto']} 
            />
            
            <ReferenceLine y={1} stroke="#6B6880" strokeDasharray="2 3" opacity={0.3} />
            
            <Tooltip
              contentStyle={{
                background: 'rgba(13, 11, 20, 0.95)',
                border: '1px solid #48BFE3',
                borderRadius: '6px', 
                fontSize: '11px', 
                fontFamily: 'monospace',
                color: '#C5C3D8', 
                padding: '6px 10px',
                boxShadow: '0 0 15px rgba(72, 191, 227, 0.15)'
              }}
              formatter={(value, name) => {
                const s = SERIES.find(x => x.key === name);
                return [
                  <span className="font-bold" style={{ color: s?.color }}>
                    {value.toFixed(2)}x
                  </span>,
                  s?.label || name
                ];
              }}
              labelFormatter={(t) => `时间步 t = ${t}`}
            />

            {/* 
              【终极渐变技】：
              这里我们为每一个 Area 加上一个从 y=0 到 y=1 的线性渐变 (LinearGradient)。
              底部设定为极暗/透明，顶部设定为纯亮色。
              最终视觉上，4 条带状会像 4 根高亮的发光霓虹管/激光束。
            */}
            {SERIES.map(({ key, color }) => (
              <Area
                key={key}
                type="monotone"
                dataKey={`${key}_norm`}
                stroke={color}
                strokeWidth={2.5}
                fill={`url(#gradient_${key})`}
                fillOpacity={1} 
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0, fill: '#FFFFFF', stroke: color }}
                isAnimationActive={false}
              />
            ))}

            {/* 定义每个序列独有的渐变发光效果 */}
            <defs>
              {SERIES.map(({ key, color }) => (
                <linearGradient key={`gradient_${key}`} id={`gradient_${key}`} x1="0" y1="0" x2="0" y2="1">
                  {/* 底部透明或极淡，融入背景 */}
                  <stop offset="5%" stopColor={color} stopOpacity={0} />
                  {/* 中间向外发光 */}
                  <stop offset="30%" stopColor={color} stopOpacity={0.2} />
                  {/* 顶部高亮 */}
                  <stop offset="100%" stopColor={color} stopOpacity={0.4} />
                </linearGradient>
              ))}
            </defs>

          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}