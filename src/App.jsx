import React, { useState, useEffect, useRef } from 'react';
import useCosmosData from './data/useCosmosData';
import HistogramChart from './charts/HistogramChart';
import CompositionChart from './charts/CompositionChart';
import ParticlePanel from './three/ParticlePanel';
import NetworkGraph from './three/NetworkGraph';
import SankeyChart from './charts/SankeyChart';
import TransitionMatrix from './charts/TransitionMatrix';
import SlicePreview from './three/SlicePreview';

// 【1. 全局毛玻璃卡片组件】
const Card = ({ children, className = '' }) => (
  <div className={`border border-white/10 shadow-lg shadow-black/30 rounded-lg p-2 transition-all ${className}`}>
    {children}
  </div>
);

const SecTitle = ({ zh, en, desc }) => (
  <div className="mb-1 shrink-0">
    <div className="flex items-center gap-1.5">
      <span className="text-[16px] font-bold text-[#E0E6ED]">{zh}</span>
      <span className="text-[11px] text-[#8898AA] font-mono">/ {en}</span>
      <div className="flex-1 border-b border-white/10 ml-1" />
    </div>
    {desc && <p className="text-[12px] text-[#8898AA] mt-1 leading-relaxed">{desc}</p>}
  </div>
);

// 【智能分析结论面板组件】
const AnalysisPanel = ({ timeStep, stats }) => {
  if (!stats) {
    return <div className="flex-1 flex items-center justify-center text-[#8898AA] text-[12px]">等待数据分析中...</div>;
  }

  let phase = "早期均匀期";
  let phaseEmoji = "🌌";
  if (timeStep >= 80) { phase = "成熟宇宙网"; phaseEmoji = "🕸️"; }
  else if (timeStep >= 45) { phase = "引力坍缩期"; phaseEmoji = "⚡"; }
  else if (timeStep >= 20) { phase = "结构雏形期"; phaseEmoji = "🌱"; }

  const sigmaGrowth = ((stats.std - 1.45) / 1.45 * 100).toFixed(0);
  
  let statusTag = "平稳演化";
  let tagColor = "#48BFE3"; 
  if (parseFloat(sigmaGrowth) > 10) { statusTag = "剧烈坍缩中"; tagColor = "#F25F5C"; } 
  else if (parseFloat(sigmaGrowth) > 5) { statusTag = "结构加速成型"; tagColor = "#FFD940"; }

  const conclusions = [
    `📊 **当前阶段**：${phaseEmoji} ${phase} (t=${timeStep})`,
    `📈 **演化趋势**：标准差较初始值提升了 **${sigmaGrowth}%**，物质聚集效应显著。`,
    `🌀 **结构特征**：空洞占比已达 **${stats.voidPct.toFixed(2)}%**，高密度峰值占比 **${stats.peakPct.toFixed(3)}%**。`,
    `🔥 **动态诊断**：当前系统处于 **${statusTag}** 状态。`
  ];

  return (
    <div className="w-full h-full flex flex-col text-[#E0E6ED] overflow-y-auto pr-1">
      <div className="flex-1 space-y-2.5">
        {conclusions.map((text, index) => (
          <div 
            key={index} 
            className="p-2 rounded border-l-2 bg-white/5 border-white/10"
            style={{ borderLeftColor: index === 0 ? tagColor : '#ffffff20' }}
          >
            <div 
              className="text-[13px] leading-relaxed text-[#8898AA]"
              dangerouslySetInnerHTML={{ __html: text.replace(/\*\*(.*?)\*\*/g, '<span class="font-bold text-[#E0E6ED]">$1</span>') }}
            />
          </div>
        ))}
      </div>
      <div className="mt-2 pt-2 border-t border-white/10 text-[10px] text-[#4A4860] flex justify-between">
        <span>基于当前时间步智能分析</span>
        <span className="text-[#48BFE3] opacity-50">✦ 动态更新</span>
      </div>
    </div>
  );
};

export default function App() {
  const { timeStep, setTimeStep, playing, setPlaying, nextStep, prevStep, histogram, voxelSample, brushRange, setBrushRange, brushInfo, MOCK_CUR, evolutionTrends } = useCosmosData(73);

  const [leftW, setLeftW] = useState(340); 
  const [rightW, setRightW] = useState(390);
  const [landscapeW, setLandscapeW] = useState(80); // 新增：景观图宽度
  const [hoverSlice, setHoverSlice] = useState(null);
  const [showNetwork, setShowNetwork] = useState(false);
  const [bgImage, setBgImage] = useState('');
  const fileInputRef = useRef(null);

  // 【初始加载：随机背景图】
  useEffect(() => {
    const randomStep = Math.floor(Math.random() * 100);
    const pad = String(randomStep).padStart(4, '0');
    setBgImage(`/output/volume_final/t${pad}.png`);
  }, []);

  // 【处理本地上传图片】
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setBgImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // 左侧面板拖拽
  const dragW = (side) => (e) => {
    e.preventDefault();
    const sx = e.clientX, sw = side === 'left' ? leftW : rightW;
    const m = (ev) => {
      const d = side === 'left' ? ev.clientX - sx : sx - ev.clientX;
      const set = side === 'left' ? setLeftW : setRightW;
      set(Math.max(250, Math.min(550, sw + d)));
    };
    const u = () => { document.removeEventListener('mousemove', m); document.removeEventListener('mouseup', u); };
    document.addEventListener('mousemove', m); document.addEventListener('mouseup', u);
  };

  // 【新增：景观图面板拖拽】
  const dragLandscape = (e) => {
    e.preventDefault();
    const sx = e.clientX;
    const sw = landscapeW;
    const m = (ev) => {
      const d = ev.clientX - sx;
      setLandscapeW(Math.max(60, Math.min(300, sw + d)));
    };
    const u = () => { document.removeEventListener('mousemove', m); document.removeEventListener('mouseup', u); };
    document.addEventListener('mousemove', m); document.addEventListener('mouseup', u);
  };

  const pad = (n) => String(n).padStart(4, '0');
  const volSrc = `/output/volume_final/t${pad(timeStep)}.png`;
  const twSrc = `/output/timewheel_frames/tw_${pad(timeStep)}.png`;
  const skelSrc = `/output/skeleton_frames/t${pad(timeStep)}.png`;
  const sXY = `/output/slices/xy/t${pad(timeStep)}.png`;
  const sXZ = `/output/slices/xz/t${pad(timeStep)}.png`;
  const sYZ = `/output/slices/yz/t${pad(timeStep)}.png`;

  return (
    <div className="w-screen h-screen overflow-y-auto relative font-sans bg-[#09080D]">
      
      {/* 全局背景层 */}
      <div 
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          backgroundImage: `url(${bgImage})`,
          backgroundSize: 'cover', 
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          filter: 'grayscale(100%) brightness(0.45) blur(2px)',
          opacity: '0.55'
        }}
      />

      {/* 隐藏的文件上传 Input */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileUpload} 
        accept="image/*" 
        style={{ display: 'none' }} 
      />

      {/* UI 内容层 */}
      <div className="relative z-10 w-full flex flex-col gap-1 p-1.5 min-w-[1280px]">
        <Header 
          timeStep={timeStep} 
          prevStep={prevStep} 
          nextStep={nextStep} 
          onLogoClick={() => fileInputRef.current?.click()} 
        />
        
        {/* 三列主视图 + 形态景观图窄列 */}
        <div className="flex gap-1.5 flex-[1.2] min-h-[550px]">
          
          {/* ==================== LEFT PANEL ==================== */}
          <div className="shrink-0 flex flex-col gap-1 relative" style={{ width: leftW }}>
            <div className="absolute -right-1 top-0 bottom-0 w-2.5 cursor-col-resize z-20 rounded hover:bg-white/20 bg-white/5" onMouseDown={dragW('left')} />
            
            <Card className="flex flex-col flex-[0.2] bg-black/5 backdrop-blur-sm border-white/15">
              <SecTitle zh="动态分析结论" en="Analysis" desc={`基于 t=${timeStep} 的全局统计特征生成的最新物理洞察。`} />
              <div className="flex-1 min-h-[100px]">
                <AnalysisPanel timeStep={timeStep} stats={MOCK_CUR} />
              </div>
            </Card>

            {/* 密度直方图 + 粒子联动 (上下堆叠) */}
            <Card className="flex flex-col flex-[0.5] bg-black/5 backdrop-blur-sm border-white/15">
              <SecTitle zh="密度分布与粒子联动" en="Density & Particles" desc="上方拖拽刷选密度区间，下方联动高亮物理结构。" />
              <div className="flex-1 flex flex-col gap-2 min-h-[0]">
                <div className="flex-1 min-h-[120px]">
                  <HistogramChart histogram={histogram} brushRange={brushRange} onBrush={setBrushRange} brushInfo={brushInfo} />
                </div>
                <div className="flex-1 min-h-[120px] overflow-hidden rounded border border-white/5 bg-black/10">
                  <ParticlePanel voxelSample={voxelSample} brushRange={brushRange} />
                </div>
              </div>
            </Card>

            <Card className="flex-[0.3] flex flex-col bg-black/5 backdrop-blur-sm border-white/15">
              <SecTitle zh="结构成分演化" en="Composition" desc="空洞膨胀，节点坍缩，两极分化。" />
              <div className="flex-1 min-h-[80px]">
                <CompositionChart data={evolutionTrends} />
              </div>
              <div className="flex gap-1.5 mt-0.5">
                {[{l:'Void',c:'#4FA8F7'},{l:'Sheet',c:'#2CDA9D'},{l:'Filament',c:'#FF8C42'},{l:'Node',c:'#FF4D4D'}].map(({l,c})=>(
                  <div key={l} className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-sm" style={{backgroundColor:c}}/><span className="text-[8px] text-[#8898AA]">{l}</span></div>
                ))}
              </div>
            </Card>
          </div>

          {/* ==================== 形态景观图窄列 (可拖拽调节宽度) ==================== */}
          <div 
            className="shrink-0 relative rounded-lg overflow-hidden border border-white/10 bg-black/80 backdrop-blur-md shadow-xl cursor-pointer hover:border-[#48BFE3] transition-colors group"
            style={{ width: landscapeW }}
            onClick={() => setHoverSlice({ 
              src: `/output/morpho_landscape/landscape_t${pad(timeStep)}.png`, 
              label: '密度拓扑截面 (Density Topological Slices)' 
            })}
          >
            {/* 右侧拖拽手柄 */}
            <div 
              className="absolute -right-1 top-0 bottom-0 w-2.5 cursor-col-resize z-20 rounded hover:bg-white/20 bg-white/5"
              onMouseDown={dragLandscape}
              onClick={(e) => e.stopPropagation()} // 防止触发图片点击
            />
            
            <img 
              src={`/output/morpho_landscape/landscape_t${pad(timeStep)}.png`} 
              alt="Morphological Landscape" 
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]" 
            />
            {/* 底部标签 */}
            <div className="absolute bottom-0 left-0 right-0 text-center text-[8px] text-[#8898AA] bg-black/80 py-1 font-mono border-t border-white/10 group-hover:text-[#E0E6ED] transition-colors leading-tight">
              {landscapeW >= 120 ? '密度拓扑截面' : '拓扑截面'}
            </div>
            {/* 顶部标注 */}
            <div className="absolute top-2 left-0 right-0 text-center">
              <span className="text-[7px] text-[#48BFE3] bg-black/60 px-1 py-0.5 rounded font-mono">
                {landscapeW >= 120 ? '形态景观' : '景观'}
              </span>
            </div>
            {/* 宽度指示器 (拖拽时显示) */}
            <div className="absolute top-1/2 right-1 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-[7px] text-[#8898AA] bg-black/80 px-1 py-0.5 rounded font-mono">{landscapeW}px</span>
            </div>
          </div>

          {/* ==================== CENTER PANEL ==================== */}
          <div className="flex-1 flex flex-col gap-1" style={{ minWidth: 500 }}>
            <Card className="flex-1 flex flex-col relative bg-black/20 backdrop-blur-sm border-white/10">
              
              <div className="absolute top-3 left-3 z-20 flex items-center bg-black/40 backdrop-blur-md border border-white/10 rounded-lg overflow-hidden shadow-lg">
                <button 
                  onClick={() => setShowNetwork(false)} 
                  className={`px-3 py-1 text-[11px] font-mono transition-colors ${!showNetwork ? 'text-[#48BFE3] bg-[#48BFE3]/20' : 'text-[#8898AA] hover:text-[#E0E6ED]'}`}
                >
                  体渲染
                </button>
                <button
                  onClick={() => setShowNetwork(true)}
                  className={`px-3 py-1 text-[11px] font-mono transition-colors ${showNetwork ? 'text-[#48BFE3] bg-[#48BFE3]/20' : 'text-[#8898AA] hover:text-[#E0E6ED]'}`}
                >
                  网络拓扑
                </button>
              </div>

              <div className="relative w-full rounded border border-white/10 bg-black/10 overflow-hidden" style={{ height: '75%', minHeight: '250px' }}>
                
                {/* 主渲染内容 */}
                <div className={`absolute inset-0 flex items-center justify-center transition-opacity duration-300 ${showNetwork ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
                  <img src={volSrc} alt="volume" className="max-w-full max-h-full object-contain" />
                  
                  {/* 结构骨架 (悬浮在右上角) */}
                  <div className="absolute top-2 right-2 w-[20%] aspect-square rounded border border-white/10 bg-black/40 backdrop-blur-sm overflow-hidden shadow-lg">
                    <img src={skelSrc} alt="skeleton" className="w-full h-full object-cover opacity-90 hover:opacity-100 transition-opacity" />
                    <div className="absolute bottom-0 left-0 right-0 text-center text-[9px] text-[#8898AA] bg-black/80 py-0.5 font-mono">结构骨架</div>
                  </div>

                  {/* 切片 3D 位置预览 (悬浮在右下角) */}
                  <div className="absolute bottom-2 right-2 w-[26%] aspect-square rounded border border-white/10 bg-black/40 backdrop-blur-sm overflow-hidden shadow-lg">
                    <SlicePreview sXY={sXY} sXZ={sXZ} sYZ={sYZ} />
                    <div className="absolute bottom-0 left-0 right-0 text-center text-[9px] text-[#48BFE3] bg-black/80 py-0.5 font-mono">切片三维位置</div>
                  </div>
                </div>

                <div className={`absolute inset-0 transition-opacity duration-300 ${showNetwork ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
                  <NetworkGraph dataUrl={`/data/network_t${pad(timeStep)}.json`} />
                </div>
              </div>

              <div className="flex items-center gap-3 px-2 h-[32px] shrink-0">
              <span className="text-[14px] font-bold text-[#E0E6ED] font-mono shrink-0">t={pad(timeStep)}</span>
              <input
                type="range"
                min="0" 
                max="99" 
                value={timeStep} 
                onChange={e=>setTimeStep(+e.target.value)} 
                className="flex-1" 
                style={{ accentColor: '#48BFE3' }}
              />
              <span className="text-[12px] text-[#8898AA] font-mono shrink-0">099</span>
              <button onClick={()=>setPlaying(!playing)} className="w-8 h-8 rounded-full border border-white/20 flex items-center justify-center shrink-0" style={{ background: 'rgba(72, 191, 227, 0.15)', color: '#48BFE3' }}>
                {playing?<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6zM14 4h4v16h-4z"/></svg>:<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>}
              </button>
              <span className="text-[12px] text-[#8898AA] font-mono shrink-0">{playing?'播放':'暂停'}·24FPS</span>
            </div>

              <div className="w-full flex gap-1 shrink-0" style={{ height: '25%', minHeight: '80px', marginTop: '2px' }}>
                {showNetwork ? (
                  <div className="w-full h-full relative bg-black/20 border border-white/10 rounded overflow-hidden flex flex-col p-2">
                    <div className="absolute top-2 left-2 z-10 flex gap-2 bg-black/40 backdrop-blur-md border border-white/10 rounded p-1.5 shadow-lg">
                      <div className="px-2 border-r border-white/10">
                        <div className="text-[9px] text-[#8898AA] font-mono">节点</div>
                        <div className="text-[14px] font-bold text-[#48BFE3] font-mono">{MOCK_CUR.netNodeCount}</div>
                      </div>
                      <div className="px-2 border-r border-white/10">
                        <div className="text-[9px] text-[#8898AA] font-mono">连接度</div>
                        <div className="text-[14px] font-bold text-[#FFD940] font-mono">{MOCK_CUR.netAvgDegree.toFixed(2)}</div>
                      </div>
                      <div className="px-2">
                        <div className="text-[9px] text-[#8898AA] font-mono">枢纽</div>
                        <div className="text-[14px] font-bold text-[#F25F5C] font-mono">{MOCK_CUR.netHubCount}</div>
                      </div>
                    </div>
                    <div className="flex-1 flex flex-col justify-end gap-1 mt-6 pl-1 pr-1 pb-1">
                      <div className="w-full bg-black/20 border border-white/10 rounded p-2 text-[11px] leading-relaxed text-[#8898AA]">
                        <div className="font-bold text-[#E0E6ED] mb-0.5">🔭 拓扑结构洞察</div>
                        当前网络由 <span className="text-[#48BFE3] font-bold">{MOCK_CUR.netNodeCount}</span> 个节点和平均 <span className="text-[#FFD940] font-bold">{MOCK_CUR.netAvgDegree.toFixed(2)}</span> 的连接度构成。 
                        网络密度达到 <span className="text-[#48BFE3] font-bold">{(MOCK_CUR.netDensity * 100).toFixed(0)}%</span>，模块化指数为 <span className="text-[#FFD940] font-bold">{MOCK_CUR.netModularity.toFixed(2)}</span>。
                        <span className="block mt-1 text-[#E0E6ED]">{MOCK_CUR.netStructureLabel}</span>
                      </div>
                      <div className="w-full bg-black/20 border border-white/10 rounded p-1.5 text-[10px] text-[#8898AA] flex items-center gap-2">
                        <span className="text-[#48BFE3]">💡</span>在引力主导下，宇宙网物质持续向"枢纽"聚集，形成幂律分布。粉红节点为 Top5 枢纽。
                      </div>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex-1 h-full rounded border border-white/10 bg-black/10 overflow-hidden relative cursor-pointer hover:border-[#48BFE3] transition-colors"
                         onClick={() => setHoverSlice(hoverSlice?.src===sXY ? null : {src:sXY, label:'XY 俯视 (Z=64)'})}>
                      <img src={sXY} alt="XY" className="w-full h-full object-cover" />
                      <div className="absolute bottom-0 left-0 right-0 text-center text-[10px] text-[#9C89B8] font-mono bg-black/70 py-0.5">XY 俯视 (Z=64)</div>
                    </div>
                    <div className="flex-1 h-full rounded border border-white/10 bg-black/10 overflow-hidden relative cursor-pointer hover:border-[#48BFE3] transition-colors"
                         onClick={() => setHoverSlice(hoverSlice?.src===sXZ ? null : {src:sXZ, label:'XZ 侧视 (Y=64)'})}>
                      <img src={sXZ} alt="XZ" className="w-full h-full object-cover" />
                      <div className="absolute bottom-0 left-0 right-0 text-center text-[10px] text-[#9C89B8] font-mono bg-black/70 py-0.5">XZ 侧视 (Y=64)</div>
                    </div>
                    <div className="flex-1 h-full rounded border border-white/10 bg-black/10 overflow-hidden relative cursor-pointer hover:border-[#48BFE3] transition-colors"
                         onClick={() => setHoverSlice(hoverSlice?.src===sYZ ? null : {src:sYZ, label:'YZ 正视 (X=64)'})}>
                      <img src={sYZ} alt="YZ" className="w-full h-full object-cover" />
                      <div className="absolute bottom-0 left-0 right-0 text-center text-[10px] text-[#9C89B8] font-mono bg-black/70 py-0.5">YZ 正视 (X=64)</div>
                    </div>
                  </>
                )}
              </div>
            </Card>
            
            
            
            <Card className="h-[100px] shrink-0 bg-black/10 backdrop-blur-sm border-white/10">
              <SecTitle zh="演化时间线" en="Timeline" desc="t=0 早期均匀分布 → t=99 成熟宇宙网。点击跳转。" />
              <div className="flex gap-1 h-10 overflow-x-auto pb-1">
                {Array.from({length:100},(_,t)=>(
                  <button key={t} onClick={()=>setTimeStep(t)} className={`shrink-0 w-[64px] rounded border overflow-hidden relative ${t===timeStep?'border-[#48BFE3] ring-1 ring-[#48BFE3]/40 scale-105 z-10':'border-white/10 hover:border-white/40 opacity-60 hover:opacity-100'}`}>
                    <img src={`/output/volume_final/t${pad(t)}.png`} alt={`t${t}`} className="w-full h-full object-cover" loading="lazy"/>
                    <span className="absolute bottom-0 left-0 right-0 text-center text-[9px] font-mono font-bold bg-black/80 text-[#E0E6ED]">{t}</span>
                  </button>
                ))}
              </div>
            </Card>
          </div>

          {/* ==================== RIGHT PANEL ==================== */}
          <div className="shrink-0 flex flex-col gap-1 relative" style={{ width: rightW }}>
            <div className="absolute -left-1 top-0 bottom-0 w-2.5 cursor-col-resize z-20 rounded hover:bg-white/20 bg-white/5" onMouseDown={dragW('right')} />
            
            {/* 相图 Phase Portrait */}
            <Card className="flex flex-col flex-[0.50] bg-black/5 backdrop-blur-sm border-white/15 overflow-hidden">
              <SecTitle zh="密度-梯度相图" en="Phase Portrait" desc="ρ vs |∇ρ| — 展示宇宙结构在相空间中的分布。" />
              <div className="flex-1 flex items-center justify-center overflow-hidden">
                <img src={`/output/phase_portrait/phase_t${pad(timeStep)}.png`}
                  alt="Phase Portrait" className="max-w-full max-h-full object-contain" />
              </div>
              <div className="text-[9px] text-[#6B6880] p-0.5 border-t border-white/5 text-center">左下=空洞 · 中带=纤维 · 右上=团簇 · 顶=核心</div>
            </Card>

            {/* 时间轮 */}
            <Card className="flex flex-col flex-[0.50] bg-black/5 backdrop-blur-sm border-white/15">
              <SecTitle zh="统计特征签名 · 时间轮" en="TimeWheel" desc="100步各成10边形统计指纹。" />
              <div className="flex-1 flex items-center justify-center overflow-hidden">
                <img src={twSrc} alt="TimeWheel" className="max-w-full max-h-full object-contain" />
              </div>
              <MetricLabels current={MOCK_CUR} />
            </Card>
          </div>
        </div>

        {/* 底部融合窗口 (桑基图 + 转移矩阵) */}
        <Card className="w-full h-[420px] shrink-0 bg-black/10 backdrop-blur-sm border-white/15 flex flex-row overflow-hidden mt-2 p-3 gap-3">
          
          {/* 左侧：桑基图 (占 65%) */}
          <div className="flex-[0.65] w-full h-full relative border-r border-white/10 pr-3">
            
            {/* 左上角文字解释区 */}
            <div className="absolute top-0 left-2 z-10 pointer-events-none flex flex-col gap-0.5">
              <div className="flex items-center gap-2">
                <span className="text-[14px] font-bold text-[#E0E6ED]">物质演化流</span>
                <span className="text-[10px] text-[#8898AA] font-mono border border-white/10 bg-black/40 px-1.5 py-0.5 rounded">Sankey</span>
              </div>
              <p className="text-[9px] text-[#6B6880] max-w-[500px] mt-0.5">
                展示不同演化阶段的体素迁移路径。线条粗细与颜色代表转化体素量。
              </p>
            </div>

            {/* 桑基图主体 */}
            <div className="w-full h-full pt-8 pl-1">
              <SankeyChart />
            </div>
          </div>

          {/* 右侧：转移矩阵及结论 (占 35%) */}
          <div className="flex-[0.35] w-full h-full flex flex-col gap-2 pr-1">
            
            {/* 顶部标题 */}
            <div className="flex items-center gap-2 mb-0.5 shrink-0">
              <span className="text-[14px] font-bold text-[#E0E6ED]">状态转移矩阵</span>
              <span className="text-[10px] text-[#8898AA] font-mono border border-white/10 bg-black/40 px-1.5 py-0.5 rounded">Heatmap</span>
            </div>

            {/* 矩阵主体 (需要占满剩余空间) */}
            <div className="flex-1 min-h-[0] w-full relative">
              <TransitionMatrix timeStep={timeStep} />
            </div>

            {/* 动态文字结论块 */}
            <div className="bg-black/30 border border-white/5 rounded p-1.5 mt-1.5 text-[10px] leading-relaxed text-[#8898AA] shrink-0">
              <span className="text-[#E0E6ED] font-bold">🧬 动态定量洞察：</span>
              {timeStep < 45 ? (
                <>
                  <span className="text-[#48BFE3]">Void</span> 与 <span className="text-[#F25F5C]">Node</span> 的高对角线值表明
                  <span className="text-[#C5C3D8] font-bold"> 极端结构具有极强的演化惯性</span>。
                  大多数物质在早期停留在原本的结构状态中，迁移较为平缓。
                </>
              ) : (
                <>
                  <span className="text-[#FF8C42]">Filament</span>→<span className="text-[#F25F5C]">Node</span> 的转移率随引力坍缩显著提升，
                  反映了<span className="text-[#C5C3D8] font-bold">物质正沿着宇宙网骨架坠入高密度核心</span>。
                  这是暗物质主导宇宙结构形成的直接量化证据。
                </>
              )}
            </div>

          </div>
        </Card>

      </div>
    </div>
  );
}

// 【右下角微组件】：宇宙网成分占比动态环形图
const CompositionDonut = ({ trends, step }) => {
  const current = trends[step] || { void: 85, sheet: 10, filament: 4, node: 1 };
  const data = [
    { name: '空洞 Void', value: current.void, color: '#4FA8F7' },
    { name: '薄片 Sheet', value: current.sheet, color: '#2CDA9D' },
    { name: '纤维 Filament', value: current.filament, color: '#FF8C42' },
    { name: '节点 Node', value: current.node, color: '#FF4D4D' },
  ];
  const maxLabel = data.reduce((a, b) => a.value > b.value ? a : b);

  return (
    <div className="flex flex-col items-center justify-center w-full h-full bg-black/20 rounded border border-white/5 p-2">
      <div className="text-[11px] text-[#8898AA] font-mono mb-1">宇宙网成分占比</div>
      <div className="relative w-20 h-20 rounded-full" style={{
        background: `conic-gradient(${data.map(d => `${d.color} 0% ${d.value}%`).join(', ')})`
      }}>
        <div className="absolute inset-2 rounded-full bg-[#13121A] flex items-center justify-center text-[10px] text-[#E0E6ED] font-bold">
          {maxLabel.name.split(' ')[0]}
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-2 mt-1.5 w-full">
        {data.map(d => (
          <div key={d.name} className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full" style={{ background: d.color }}></span>
            <span className="text-[8px] text-[#8898AA] font-mono">{d.value.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

function MetricLabels({ current }) {
  const colorTheme = {
    voidPct: '#48BFE3',
    peakPct: '#FFE066',
    kurt: '#9C89B8',
    skew: '#9C89B8',
    std: '#14f3fa',
    mean: '#48BFE3',
    min: '#6B6880',   
    max: '#e30ea0'    
  };
  
  const items = [
    ['空洞占比',  (current?.voidPct ?? 0).toFixed(2) + '%', colorTheme.voidPct],
    ['峰值占比',  (current?.peakPct ?? 0).toFixed(3) + '%', colorTheme.peakPct],
    ['峰度',      (current?.kurt ?? 0).toFixed(3), colorTheme.kurt],
    ['偏度',      (current?.skew ?? 0).toFixed(3), colorTheme.skew],
    ['标准差σ',   (current?.std ?? 0).toFixed(4), colorTheme.std],
    ['均值μ',     (current?.mean ?? 0).toFixed(4), colorTheme.mean],
    ['最小值',    (current?.minVal ?? current?.min ?? 0).toFixed(3), colorTheme.min],
    ['最大值',    (current?.maxVal ?? current?.max ?? 0).toFixed(3), colorTheme.max]
  ];

  return (
    <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[12px] mt-1 p-1.5 rounded bg-black/20 backdrop-blur-sm border border-white/10">
      {items.map(([l, v, c]) => (
        <div key={l} className="flex justify-between">
          <span className="text-[#8898AA] text-[11px]">{l}</span>
          <span className="font-mono font-bold tabular-nums text-[13px]" style={{ color: c }}>{v}</span>
        </div>
      ))}
    </div>
  );
}

function Header({ timeStep, prevStep, nextStep, onLogoClick }) {
  return (
    <Card className="h-[36px] shrink-0 flex items-center px-3 gap-3 !py-0 bg-black/10 backdrop-blur-sm border-white/15">
      <div 
        className="w-7 h-7 rounded flex items-center justify-center shrink-0 cursor-pointer hover:scale-105 transition-transform"
        style={{ background: 'rgba(72, 191, 227, 0.15)', border: '1px solid rgba(72, 191, 227, 0.3)' }}
        onClick={onLogoClick}
        title="点击更换背景图片"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#48BFE3" strokeWidth="1.5"><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="10" strokeDasharray="4 3" opacity="0.3"/></svg>
      </div>
      <span className="text-[16px] font-bold text-[#E0E6ED] shrink-0">宇宙演化探索器</span>
      <span className="text-[12px] text-[#8898AA] font-mono shrink-0">Nyx 128³ · 100 Steps</span>
      <div className="w-px h-5 bg-white/10 shrink-0" />
      <span className="text-[26px] font-bold text-[#48BFE3] font-mono leading-none">t={String(timeStep).padStart(3,'0')}</span>
      <div className="flex-1" />
      <div className="flex items-center gap-2 shrink-0"><span className="text-[11px] text-[#8898AA] font-mono">低密度</span><div className="w-36 h-2.5 rounded-full" style={{ background: 'linear-gradient(to right,#0D2659,#2E8CAD,#38B894,#8073B8,#EB4747,#FFD940)' }}/><span className="text-[11px] text-[#8898AA] font-mono">高密度</span></div>
    </Card>
  );
}