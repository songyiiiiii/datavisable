// ============================================================================
// NetworkGraph.jsx V3 — 白管 + 青→玫红节点, 自动标注 Top5 超级枢纽
// ============================================================================
import React, { useMemo, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';

function Edge({ from, to, frac }) {
  const start = new THREE.Vector3(from.x, from.y, from.z);
  const end = new THREE.Vector3(to.x, to.y, to.z);
  const mid = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5);
  const length = start.distanceTo(end);

  const curve = useMemo(() => {
    const ctrl = mid.clone().add(new THREE.Vector3(
      (Math.random()-0.5)*length*0.12, 
      (Math.random()-0.5)*length*0.12, 
      (Math.random()-0.5)*length*0.12
    ));
    return new THREE.QuadraticBezierCurve3(start, ctrl, end);
  }, [from, to]);

  const tubeGeo = useMemo(() => new THREE.TubeGeometry(curve, 10, 0.15 + frac * 0.35, 6, false), [curve, frac]);
  const color = frac > 0.4 ? '#30eefce7' : 'rgba(255,255,255,0.3)';
  const opacity = frac > 0.4 ? 0.55 : 0.18;

  return (
    <mesh geometry={tubeGeo}>
      <meshBasicMaterial color={color} transparent opacity={opacity} depthWrite={false} />
    </mesh>
  );
}

function NetworkNodes({ graph }) {
  if (!graph?.nodes) return null;

  const maxVol = Math.max(...graph.nodes.map(n => n.volume), 1);
  
  // 【新增】：找出前 5 个体积最大的节点 (超级枢纽)
  const sortedNodes = useMemo(() => {
    return [...graph.nodes].sort((a, b) => b.volume - a.volume);
  }, [graph.nodes]);
  
  const topNodes = sortedNodes.slice(0, 5);
  const topNodeIds = new Set(topNodes.map(n => n.id));

  const nodeMap = {};
  graph.nodes.forEach(n => { nodeMap[n.id] = n; });

  return (
    <group>
      {/* 渲染连接边 */}
      {graph.edges?.map((e, i) => {
        const from = nodeMap[e.source], to = nodeMap[e.target];
        if (!from || !to) return null;
        return <Edge key={i} from={from} to={to} frac={e.filament_frac || 0.3} />;
      })}

      {/* 渲染节点 */}
      {graph.nodes.map((n) => {
        const isHub = topNodeIds.has(n.id);
        // 若是枢纽，体积放大 1.5 倍
        const volScale = (0.4 + (n.volume / maxVol) * 2.2) * (isHub ? 1.8 : 1.0);
        
        // 颜色和发光：普通节点玫红，枢纽节点变为亮金色
        const color = isHub ? '#FFD940' : '#EC4899'; 
        const emissiveIntensity = isHub ? 1.2 : 0.55;

        return (
          <group key={n.id} position={[n.x, n.y, n.z]}>
            {/* 节点球体 */}
            <mesh>
              <sphereGeometry args={[volScale, 16, 16]} />
              <meshStandardMaterial 
                color={color} 
                emissive={color} 
                emissiveIntensity={emissiveIntensity} 
                roughness={0.18} 
                metalness={0.05} 
              />
            </mesh>
            
            {/* 【新增】：如果是枢纽节点，在头顶悬浮显示标签 */}
            {isHub && (
              <Html position={[0, volScale + 6, 0]} center>
                <div style={{
                  color: '#FFD940',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  fontFamily: 'monospace',
                  textShadow: '0 0 20px rgba(255, 217, 64, 0.8), 0 0 10px rgba(0,0,0,0.9)',
                  backgroundColor: 'rgba(0,0,0,0.4)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '1px solid rgba(255, 217, 64, 0.3)',
                  pointerEvents: 'none'
                }}>
                  HUB-{n.id}
                </div>
              </Html>
            )}
          </group>
        );
      })}
    </group>
  );
}

export default function NetworkGraph({ dataUrl }) {
  const [graph, setGraph] = useState(null);
  useEffect(() => { 
    if (dataUrl) fetch(dataUrl).then(r=>r.json()).then(setGraph).catch(()=>setGraph(null)); 
  }, [dataUrl]);

  return (
    <Canvas camera={{ position: [140,120,160], fov:50, near:1, far:500 }} gl={{ antialias:true, alpha:true }} style={{background:'transparent'}}>
      <ambientLight intensity={0.3} />
      <pointLight position={[200,200,200]} intensity={0.5} />
      <NetworkNodes graph={graph} />
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(128,128,128)]}/>
        <lineBasicMaterial color="#2A3040" transparent opacity={0.12}/>
      </lineSegments>
      <OrbitControls enableDamping dampingFactor={0.1} minDistance={30} maxDistance={350} target={[64,64,64]}/>
    </Canvas>
  );
}