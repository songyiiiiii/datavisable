// ============================================================================
// AnalysisPanel.jsx — 全局面板智能分析结论生成器
// 可以根据当前时间步、统计特征、物理演化规律渲染动态结论。
// ============================================================================
import React from 'react';

export default function AnalysisPanel({ timeStep, stats }) {
  // 如果没有统计数据，显示加载中
  if (!stats) {
    return <div className="flex-1 flex items-center justify-center text-[#6B6880] text-[12px]">等待数据分析中...</div>;
  }

  // --- 1. 基于当前步生成物理结论逻辑 (可根据真实物理公式替换) ---
  // 定义阶段划分
  let phase = "早期均匀期";
  let phaseEmoji = "🌌";
  if (timeStep >= 80) { phase = "成熟宇宙网"; phaseEmoji = "🕸️"; }
  else if (timeStep >= 45) { phase = "引力坍缩期"; phaseEmoji = "⚡"; }
  else if (timeStep >= 20) { phase = "结构雏形期"; phaseEmoji = "🌱"; }

  // 基于标准差(Sigma)和空洞占比计算演化特征
  const sigmaGrowth = ((stats.std - 1.45) / 1.45 * 100).toFixed(0);
  const voidGrowth = ((stats.voidPct - 0.31) / 0.31 * 100).toFixed(0);
  
  // 判断数据处于什么状态 (生成标签)
  let statusTag = "平稳演化";
  let tagColor = "#48BFE3"; // 蓝绿
  if (parseFloat(sigmaGrowth) > 10) {
    statusTag = "剧烈坍缩中";
    tagColor = "#F25F5C"; // 玫红
  } else if (parseFloat(sigmaGrowth) > 5) {
    statusTag = "结构加速成型";
    tagColor = "#FFD940"; // 亮黄
  }

  // --- 2. 组装结论文本数组 ---
  const conclusions = [
    `📊 **当前阶段**：${phaseEmoji} ${phase} (t=${timeStep})`,
    `📈 **演化趋势**：标准差较初始值提升了 **${sigmaGrowth}%**，物质聚集效应显著。`,
    `🌀 **结构特征**：空洞占比已达 **${stats.voidPct.toFixed(2)}%**，高密度峰值占比 **${stats.peakPct.toFixed(3)}%**。`,
    `🔥 **动态诊断**：当前系统处于 **${statusTag}** 状态。`
  ];

  return (
    <div className="w-full h-full flex flex-col text-[#C5C3D8] overflow-y-auto pr-1">
      <div className="flex-1 space-y-3">
        {conclusions.map((text, index) => (
          <div 
            key={index} 
            className="p-2 rounded border-l-2 bg-[#1A1825]/50 border-[#242233]"
            style={{ borderLeftColor: index === 0 ? tagColor : '#2A3040' }}
          >
            {/* 使用 dangerouslySetInnerHTML 渲染 markdown 格式的加粗 */}
            <div 
              className="text-[13px] leading-relaxed text-[#8898AA]"
              dangerouslySetInnerHTML={{ __html: text.replace(/\*\*(.*?)\*\*/g, '<span class="font-bold text-[#C5C3D8]">$1</span>') }}
            />
          </div>
        ))}
      </div>
      
      {/* 底部提示微交互 */}
      <div className="mt-2 pt-2 border-t border-[#242233] text-[10px] text-[#4A4860] flex justify-between">
        <span>基于当前时间步智能分析</span>
        <span className="text-[#48BFE3] opacity-50">✦ 动态更新</span>
      </div>
    </div>
  );
}